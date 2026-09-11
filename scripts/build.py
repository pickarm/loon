#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RULE_DIR = ROOT / "rules"
REPORT_DIR = ROOT / "build"
CONFIG_PATH = ROOT / "sources" / "sources.json"
PREVIOUS_REPORT = ROOT / ".previous-report.json"
RULE_TYPES = {"DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD", "DOMAIN-WILDCARD", "IP-CIDR", "IP-CIDR6", "IP-ASN", "GEOIP", "PROCESS-NAME", "PROCESS-PATH", "USER-AGENT", "URL-REGEX", "PROTOCOL", "DST-PORT", "SRC-PORT", "SRC-IP", "RULE-SET"}
DOMAIN_TYPES = {"DOMAIN", "DOMAIN-SUFFIX"}
FETCH_CACHE: dict[str, str] = {}


def run(*args: str) -> str:
    p = subprocess.run(args, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.returncode:
        raise RuntimeError(f"command failed: {' '.join(args)}\n{p.stderr.strip()}")
    return p.stdout.strip()


def upstream_heads(cfg: dict) -> dict[str, str]:
    commits = {}
    for name, meta in cfg["upstreams"].items():
        out = run("git", "ls-remote", meta["repo"], f"refs/heads/{meta['ref']}")
        commits[name] = out.split()[0] if out else "unknown"
    return commits


def raw_url(meta: dict, path: str) -> str:
    repo = meta["repo"].removesuffix(".git")
    m = re.match(r"https://github\.com/([^/]+)/([^/]+)$", repo)
    if not m:
        raise ValueError(f"only github.com upstreams are supported: {repo}")
    owner, name = m.groups()
    return f"https://raw.githubusercontent.com/{owner}/{name}/{meta['ref']}/{path}"


def fetch_text(url: str, retries: int = 3) -> str:
    if url in FETCH_CACHE:
        return FETCH_CACHE[url]
    req = urllib.request.Request(url, headers={"User-Agent": "pickarm-loon-builder/1.0"})
    last = None
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=45) as resp:
                text = resp.read().decode("utf-8", errors="ignore")
                FETCH_CACHE[url] = text
                return text
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                raise
            last = exc
        except Exception as exc:
            last = exc
        time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"download failed: {url}: {last}")


def clean_domain(value: str) -> str:
    return value.strip().strip(".\"").lower()


def normalize_rule(line: str, fmt: str = "rule") -> str | None:
    line = line.strip().lstrip("-").strip()
    if not line or line.startswith(("#", "//", ";", "payload:")):
        return None
    if fmt == "dnsmasq":
        m = re.search(r"(?:server|address)=/([^/]+)/", line)
        return f"DOMAIN-SUFFIX,{clean_domain(m.group(1))}" if m else None
    if fmt == "domain":
        value = clean_domain(line.split()[0])
        return f"DOMAIN-SUFFIX,{value}" if value and not value.startswith(("!", "@@", "||")) else None
    line = line.strip("'\"")
    parts = [p.strip() for p in line.split(",")]
    if len(parts) < 2:
        return f"DOMAIN-SUFFIX,{clean_domain(line)}" if re.fullmatch(r"[A-Za-z0-9._*-]+\.[A-Za-z0-9.-]+", line) else None
    rtype = parts[0].upper()
    if rtype not in RULE_TYPES:
        return None
    value = clean_domain(parts[1]) if rtype in DOMAIN_TYPES | {"DOMAIN-KEYWORD", "DOMAIN-WILDCARD"} else parts[1]
    if not value:
        return None
    out = f"{rtype},{value}"
    if rtype in {"IP-CIDR", "IP-CIDR6", "IP-ASN"} and any(p.lower() == "no-resolve" for p in parts[2:]):
        out += ",no-resolve"
    return out


def read_source(cfg: dict, repo_key: str, candidates: list[str], fmt: str, required: bool):
    meta = cfg["upstreams"][repo_key]
    last_error = None
    for path in candidates:
        url = raw_url(meta, path)
        try:
            text = fetch_text(url)
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                last_error = exc
                continue
            if required:
                raise
            return set(), None, None
        except Exception as exc:
            last_error = exc
            if required:
                raise
            return set(), None, None
        rules = {r for line in text.splitlines() if (r := normalize_rule(line, fmt))}
        digest = hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()[:16]
        return rules, path, digest
    if required:
        raise FileNotFoundError(f"required source not found: {repo_key}: {candidates}; last={last_error}")
    return set(), None, None


def read_override(name: str) -> set[str]:
    path = ROOT / "override" / name
    if not path.exists():
        return set()
    return {r for line in path.read_text(encoding="utf-8", errors="ignore").splitlines() if (r := normalize_rule(line))}


def split_rule(rule: str) -> tuple[str, str]:
    p = rule.split(",", 2)
    return p[0], p[1].lower()


def build_protection(rulesets):
    exact, suffix = set(), set()
    for rules in rulesets.values():
        for rule in rules:
            typ, value = split_rule(rule)
            if typ == "DOMAIN": exact.add(value)
            elif typ == "DOMAIN-SUFFIX": suffix.add(value)
    return exact, suffix


def protected_domain(typ, value, exact, suffixes):
    value = value.lower()
    if typ == "DOMAIN":
        return value in exact or any(value == s or value.endswith("." + s) for s in suffixes)
    if typ == "DOMAIN-SUFFIX":
        return any(value == s or value.endswith("." + s) for s in suffixes)
    return False


def domain_matches(rules, domain):
    domain = domain.lower()
    for rule in rules:
        typ, value = split_rule(rule)
        if typ == "DOMAIN" and domain == value: return True
        if typ == "DOMAIN-SUFFIX" and (domain == value or domain.endswith("." + value)): return True
    return False


def validate_expectations(built):
    checks = json.loads((ROOT / "tests" / "expectations.json").read_text(encoding="utf-8"))
    errors = []
    direct = built.get("China/Direct.list", set()) | built.get("Basic/LAN.list", set())
    for domain in checks.get("direct", []):
        if not domain_matches(direct, domain): errors.append(f"expected DIRECT domain missing: {domain}")
    for path, domains in checks.get("service", {}).items():
        for domain in domains:
            if not domain_matches(built.get(path, set()), domain): errors.append(f"expected {domain} missing from {path}")
    return errors


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true", help="compatibility flag; Raw sources are always refreshed")
    ap.add_argument("--max-drop", type=float, default=0.35)
    args = ap.parse_args()
    cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    commits = upstream_heads(cfg)
    raw_built, used_sources, items_by_path, source_hashes = {}, {}, {}, {}

    for item in cfg["rulesets"]:
        rules, used = set(), []
        for src in item.get("sources", []):
            got, path, digest = read_source(cfg, src["repo"], src["paths"], src.get("format", "rule"), src.get("required", True))
            rules |= got
            if path:
                sid = f"{src['repo']}:{path}"
                used.append(sid)
                if digest: source_hashes[sid] = digest
        raw_built[item["path"]], used_sources[item["path"]], items_by_path[item["path"]] = rules, used, item

    raw_built.setdefault("China/Direct.list", set()).update(read_override("direct.list"))
    raw_built.setdefault("Ads/Reject.list", set()).update(read_override("reject.list"))
    protected_sets = {p: r for p, r in raw_built.items() if items_by_path.get(p, {}).get("cn_protect")}
    direct_exact, direct_suffix = build_protection(protected_sets)

    built, removed_counts = {}, {}
    for path, rules in raw_built.items():
        item = items_by_path[path]
        if item.get("cn_guard"):
            kept, removed = set(), 0
            for rule in rules:
                typ, value = split_rule(rule)
                if typ in DOMAIN_TYPES and protected_domain(typ, value, direct_exact, direct_suffix): removed += 1
                else: kept.add(rule)
            rules, removed_counts[path] = kept, removed
        built[path] = rules
    built.setdefault("Proxy/Global.list", set()).update(read_override("proxy.list"))

    previous = {}
    if PREVIOUS_REPORT.exists():
        try: previous = json.loads(PREVIOUS_REPORT.read_text(encoding="utf-8")).get("rulesets", {})
        except Exception: previous = {}
    errors = []
    for path, rules in built.items():
        item, count = items_by_path[path], len(rules)
        minimum = int(item.get("min_rules", 0))
        if count < minimum: errors.append(f"{path}: {count} rules < min_rules {minimum}")
        old = int(previous.get(path, {}).get("count", 0) or 0)
        if old >= 50 and count < old * (1 - args.max_drop): errors.append(f"{path}: suspicious drop {old} -> {count}")
    errors += validate_expectations(built)
    if errors:
        print("Validation failed:", file=sys.stderr)
        for err in errors: print(f" - {err}", file=sys.stderr)
        return 2

    if RULE_DIR.exists():
        import shutil
        shutil.rmtree(RULE_DIR)
    for path, rules in built.items():
        item, out = items_by_path[path], RULE_DIR / path
        out.parent.mkdir(parents=True, exist_ok=True)
        head = ["# Generated by pickarm/loon. DO NOT EDIT THIS FILE DIRECTLY.", f"# NAME: {item['name']}", f"# POLICY: {item['policy']}", f"# RULES: {len(rules)}"]
        if removed_counts.get(path): head.append(f"# CN-GUARD-REMOVED: {removed_counts[path]}")
        head += [f"# SOURCE: {s}" for s in used_sources[path]]
        body = "\n".join(sorted(rules, key=lambda x: (x.split(",", 1)[0], x.lower())))
        out.write_text("\n".join(head) + "\n" + body + "\n", encoding="utf-8")

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report = {"generated_at": datetime.now(timezone.utc).isoformat(), "upstreams": commits, "source_hashes": source_hashes, "rulesets": {p: {"count": len(r), "cn_guard_removed": removed_counts.get(p, 0), "policy": items_by_path[p]["policy"]} for p, r in built.items()}, "total_rules": sum(len(v) for v in built.values())}
    (REPORT_DIR / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    run(sys.executable, str(ROOT / "scripts" / "render_config.py"))
    print(f"Built {len(built)} rulesets / {report['total_rules']} rules")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

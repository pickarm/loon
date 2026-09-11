#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / ".cache" / "upstreams"
RULE_DIR = ROOT / "rules"
REPORT_DIR = ROOT / "build"
CONFIG_PATH = ROOT / "sources" / "sources.json"
PREVIOUS_REPORT = ROOT / ".previous-report.json"

RULE_TYPES = {
    "DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD", "DOMAIN-WILDCARD",
    "IP-CIDR", "IP-CIDR6", "IP-ASN", "GEOIP", "PROCESS-NAME",
    "PROCESS-PATH", "USER-AGENT", "URL-REGEX", "PROTOCOL", "DST-PORT",
    "SRC-PORT", "SRC-IP", "RULE-SET"
}
DOMAIN_TYPES = {"DOMAIN", "DOMAIN-SUFFIX"}


def run(*args: str, cwd: Path | None = None) -> str:
    proc = subprocess.run(args, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if proc.returncode:
        raise RuntimeError(f"command failed: {' '.join(args)}\n{proc.stderr.strip()}")
    return proc.stdout.strip()


def clone_upstreams(cfg: dict, refresh: bool) -> dict[str, str]:
    CACHE.mkdir(parents=True, exist_ok=True)
    commits: dict[str, str] = {}
    for name, meta in cfg["upstreams"].items():
        dest = CACHE / name
        if refresh and dest.exists():
            shutil.rmtree(dest)
        if not dest.exists():
            sparse = meta.get("sparse") or []
            args = ["git", "clone", "--depth", "1", "--branch", meta["ref"], "--filter=blob:none"]
            if sparse:
                args += ["--no-checkout"]
            args += [meta["repo"], str(dest)]
            run(*args)
            if sparse:
                run("git", "sparse-checkout", "init", "--no-cone", cwd=dest)
                run("git", "sparse-checkout", "set", *sparse, cwd=dest)
                run("git", "checkout", meta["ref"], cwd=dest)
        else:
            run("git", "fetch", "--depth", "1", "origin", meta["ref"], cwd=dest)
            run("git", "reset", "--hard", "FETCH_HEAD", cwd=dest)
        commits[name] = run("git", "rev-parse", "HEAD", cwd=dest)
    return commits


def clean_domain(value: str) -> str:
    return value.strip().strip(".\"").lower()


def normalize_rule(line: str, fmt: str = "rule") -> str | None:
    line = line.strip().lstrip("-").strip()
    if not line or line.startswith(("#", "//", ";", "payload:")):
        return None
    if fmt == "dnsmasq":
        m = re.search(r"(?:server|address)=/([^/]+)/", line)
        if not m:
            return None
        domain = clean_domain(m.group(1))
        return f"DOMAIN-SUFFIX,{domain}" if domain else None
    if fmt == "domain":
        value = clean_domain(line.split()[0])
        if not value or value.startswith(("!", "@@", "||")):
            return None
        return f"DOMAIN-SUFFIX,{value}"

    line = line.strip("'\"")
    parts = [p.strip() for p in line.split(",")]
    if len(parts) < 2:
        if re.fullmatch(r"[A-Za-z0-9._*-]+\.[A-Za-z0-9.-]+", line):
            return f"DOMAIN-SUFFIX,{clean_domain(line)}"
        return None
    rtype = parts[0].upper()
    if rtype not in RULE_TYPES:
        return None
    value = parts[1]
    if rtype in DOMAIN_TYPES or rtype in {"DOMAIN-KEYWORD", "DOMAIN-WILDCARD"}:
        value = clean_domain(value)
    if not value:
        return None
    out = f"{rtype},{value}"
    if rtype in {"IP-CIDR", "IP-CIDR6", "IP-ASN"} and any(p.lower() == "no-resolve" for p in parts[2:]):
        out += ",no-resolve"
    return out


def read_source(repo: str, candidates: list[str], fmt: str, required: bool) -> tuple[set[str], str | None]:
    base = CACHE / repo
    selected = next((base / p for p in candidates if (base / p).is_file()), None)
    if selected is None:
        if required:
            raise FileNotFoundError(f"required source not found: {repo}: {candidates}")
        return set(), None
    rules: set[str] = set()
    for raw in selected.read_text(encoding="utf-8", errors="ignore").splitlines():
        rule = normalize_rule(raw, fmt)
        if rule:
            rules.add(rule)
    return rules, str(selected.relative_to(base))


def read_override(name: str) -> set[str]:
    path = ROOT / "override" / name
    if not path.exists():
        return set()
    out = set()
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        rule = normalize_rule(line)
        if rule:
            out.add(rule)
    return out


def split_rule(rule: str) -> tuple[str, str]:
    p = rule.split(",", 2)
    return p[0], p[1].lower()


def build_protection(rulesets: dict[str, set[str]]) -> tuple[set[str], set[str]]:
    exact, suffix = set(), set()
    for rules in rulesets.values():
        for rule in rules:
            typ, value = split_rule(rule)
            if typ == "DOMAIN":
                exact.add(value)
            elif typ == "DOMAIN-SUFFIX":
                suffix.add(value)
    return exact, suffix


def protected_domain(typ: str, value: str, exact: set[str], suffixes: set[str]) -> bool:
    value = value.lower()
    if typ == "DOMAIN":
        return value in exact or any(value == s or value.endswith("." + s) for s in suffixes)
    if typ == "DOMAIN-SUFFIX":
        return any(value == s or value.endswith("." + s) for s in suffixes)
    return False


def header(item: dict, used: list[str], count: int, removed: int) -> str:
    lines = [
        "# Generated by pickarm/loon. DO NOT EDIT THIS FILE DIRECTLY.",
        f"# NAME: {item['name']}",
        f"# POLICY: {item['policy']}",
        f"# RULES: {count}",
    ]
    if removed:
        lines.append(f"# CN-GUARD-REMOVED: {removed}")
    for src in used:
        lines.append(f"# SOURCE: {src}")
    return "\n".join(lines) + "\n"


def domain_matches(rules: set[str], domain: str) -> bool:
    domain = domain.lower()
    for rule in rules:
        typ, value = split_rule(rule)
        if typ == "DOMAIN" and domain == value:
            return True
        if typ == "DOMAIN-SUFFIX" and (domain == value or domain.endswith("." + value)):
            return True
    return False


def validate_expectations(built: dict[str, set[str]]) -> list[str]:
    checks = json.loads((ROOT / "tests" / "expectations.json").read_text(encoding="utf-8"))
    errors: list[str] = []
    direct = built.get("China/Direct.list", set()) | built.get("Basic/LAN.list", set())
    for domain in checks.get("direct", []):
        if not domain_matches(direct, domain):
            errors.append(f"expected DIRECT domain missing: {domain}")
    for path, domains in checks.get("service", {}).items():
        rules = built.get(path, set())
        for domain in domains:
            if not domain_matches(rules, domain):
                errors.append(f"expected {domain} missing from {path}")
    return errors


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true", help="re-clone upstreams")
    ap.add_argument("--max-drop", type=float, default=0.35)
    args = ap.parse_args()

    cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    commits = clone_upstreams(cfg, args.refresh)
    raw_built: dict[str, set[str]] = {}
    used_sources: dict[str, list[str]] = {}
    items_by_path: dict[str, dict] = {}

    for item in cfg["rulesets"]:
        rules: set[str] = set()
        used: list[str] = []
        for src in item.get("sources", []):
            got, path = read_source(src["repo"], src["paths"], src.get("format", "rule"), src.get("required", True))
            rules |= got
            if path:
                used.append(f"{src['repo']}:{path}")
        raw_built[item["path"]] = rules
        used_sources[item["path"]] = used
        items_by_path[item["path"]] = item

    raw_built.setdefault("China/Direct.list", set()).update(read_override("direct.list"))
    raw_built.setdefault("Ads/Reject.list", set()).update(read_override("reject.list"))

    protected_sets = {
        path: rules for path, rules in raw_built.items()
        if items_by_path.get(path, {}).get("cn_protect")
    }
    direct_exact, direct_suffix = build_protection(protected_sets)

    built: dict[str, set[str]] = {}
    removed_counts: dict[str, int] = {}
    for path, rules in raw_built.items():
        item = items_by_path[path]
        if item.get("cn_guard"):
            kept = set()
            removed = 0
            for rule in rules:
                typ, value = split_rule(rule)
                if typ in DOMAIN_TYPES and protected_domain(typ, value, direct_exact, direct_suffix):
                    removed += 1
                    continue
                kept.add(rule)
            rules = kept
            removed_counts[path] = removed
        built[path] = rules

    built.setdefault("Proxy/Global.list", set()).update(read_override("proxy.list"))

    previous = {}
    if PREVIOUS_REPORT.exists():
        try:
            previous = json.loads(PREVIOUS_REPORT.read_text(encoding="utf-8")).get("rulesets", {})
        except Exception:
            previous = {}

    errors: list[str] = []
    for path, rules in built.items():
        item = items_by_path[path]
        count = len(rules)
        minimum = int(item.get("min_rules", 0))
        if count < minimum:
            errors.append(f"{path}: {count} rules < min_rules {minimum}")
        old = int(previous.get(path, {}).get("count", 0) or 0)
        if old >= 50 and count < old * (1 - args.max_drop):
            errors.append(f"{path}: suspicious drop {old} -> {count}")

    errors += validate_expectations(built)
    if errors:
        print("Validation failed:", file=sys.stderr)
        for err in errors:
            print(f" - {err}", file=sys.stderr)
        return 2

    if RULE_DIR.exists():
        shutil.rmtree(RULE_DIR)
    for path, rules in built.items():
        item = items_by_path[path]
        out = RULE_DIR / path
        out.parent.mkdir(parents=True, exist_ok=True)
        body = "\n".join(sorted(rules, key=lambda x: (x.split(",", 1)[0], x.lower())))
        out.write_text(header(item, used_sources[path], len(rules), removed_counts.get(path, 0)) + body + "\n", encoding="utf-8")

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "upstreams": commits,
        "rulesets": {
            path: {"count": len(rules), "cn_guard_removed": removed_counts.get(path, 0), "policy": items_by_path[path]["policy"]}
            for path, rules in built.items()
        },
        "total_rules": sum(len(v) for v in built.values())
    }
    (REPORT_DIR / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    run(sys.executable, str(ROOT / "scripts" / "render_config.py"))
    print(f"Built {len(built)} rulesets / {report['total_rules']} rules")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

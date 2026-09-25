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
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RULE_DIR = ROOT / "rules"
REPORT_DIR = ROOT / "build"
CONFIG_PATH = ROOT / "sources" / "sources.json"
PREVIOUS_REPORT = ROOT / ".previous-report.json"
RULE_TYPES = {"DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD", "DOMAIN-WILDCARD", "IP-CIDR", "IP-CIDR6", "IP-ASN", "GEOIP", "PROCESS-NAME", "PROCESS-PATH", "USER-AGENT", "URL-REGEX", "PROTOCOL", "DST-PORT", "DEST-PORT", "SRC-PORT", "SRC-IP", "RULE-SET"}
LOGICAL_RULE_TYPES = {"AND", "OR", "NOT"}
DOMAIN_TYPES = {"DOMAIN", "DOMAIN-SUFFIX"}
FETCH_CACHE: dict[str, str] = {}
NOT_FOUND: set[str] = set()


def run(*args: str, timeout: int = 30) -> str:
    p = subprocess.run(
        args,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
    )
    if p.returncode:
        raise RuntimeError(f"command failed: {' '.join(args)}\n{p.stderr.strip()}")
    return p.stdout.strip()


def upstream_heads(cfg: dict) -> dict[str, str]:
    def one(name: str, meta: dict) -> tuple[str, str]:
        try:
            out = run("git", "ls-remote", meta["repo"], f"refs/heads/{meta['ref']}", timeout=20)
            return name, out.split()[0] if out else "unknown"
        except Exception as exc:
            print(f"[warn] upstream HEAD unavailable: {name}: {exc}", flush=True)
            return name, "unknown"

    commits: dict[str, str] = {}
    with ThreadPoolExecutor(max_workers=min(8, max(1, len(cfg["upstreams"])))) as pool:
        futures = [pool.submit(one, name, meta) for name, meta in cfg["upstreams"].items()]
        for future in as_completed(futures):
            name, sha = future.result()
            commits[name] = sha
            print(f"[head] {name}: {sha[:12] if sha != 'unknown' else sha}", flush=True)
    return commits


def raw_url(meta: dict, path: str) -> str:
    repo = meta["repo"].removesuffix(".git")
    m = re.match(r"https://github\.com/([^/]+)/([^/]+)$", repo)
    if not m:
        raise ValueError(f"only github.com upstreams are supported: {repo}")
    owner, name = m.groups()
    return f"https://raw.githubusercontent.com/{owner}/{name}/{meta['ref']}/{path}"


def fetch_text(url: str, retries: int = 3, timeout: int = 20) -> str:
    if url in FETCH_CACHE:
        return FETCH_CACHE[url]
    if url in NOT_FOUND:
        raise urllib.error.HTTPError(url, 404, "Not Found", hdrs=None, fp=None)

    last = None
    for attempt in range(retries):
        req = urllib.request.Request(url, headers={"User-Agent": "pickarm-loon-builder/1.1"})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                text = resp.read().decode("utf-8", errors="ignore")
                FETCH_CACHE[url] = text
                return text
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                NOT_FOUND.add(url)
                raise
            last = exc
        except Exception as exc:
            last = exc
        if attempt + 1 < retries:
            time.sleep(1.0 * (attempt + 1))
    raise RuntimeError(f"download failed: {url}: {last}")


def prefetch_sources(cfg: dict) -> None:
    urls: dict[str, str] = {}
    for item in cfg["rulesets"]:
        for src in item.get("sources", []):
            meta = cfg["upstreams"][src["repo"]]
            for path in src["paths"]:
                urls[raw_url(meta, path)] = f"{src['repo']}:{path}"

    print(f"[fetch] prefetching {len(urls)} unique source candidates", flush=True)

    def one(url: str, sid: str):
        try:
            text = fetch_text(url, retries=2, timeout=20)
            return sid, len(text.encode("utf-8", errors="ignore")), None
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                return sid, 0, "404"
            return sid, 0, f"HTTP {exc.code}"
        except Exception as exc:
            return sid, 0, str(exc)

    done = 0
    with ThreadPoolExecutor(max_workers=12) as pool:
        futures = {pool.submit(one, url, sid): sid for url, sid in urls.items()}
        for future in as_completed(futures):
            sid, size, err = future.result()
            done += 1
            if err:
                print(f"[fetch {done}/{len(urls)}] {sid}: {err}", flush=True)
            else:
                print(f"[fetch {done}/{len(urls)}] {sid}: {size / 1024:.1f} KiB", flush=True)


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
    if "," not in line:
        return (
            f"DOMAIN-SUFFIX,{clean_domain(line)}"
            if re.fullmatch(r"[A-Za-z0-9._*-]+\.[A-Za-z0-9.-]+", line)
            else None
        )

    raw_type, rest = line.split(",", 1)
    rtype = raw_type.strip().upper()

    # Upstream full-config lists may contain a terminal FINAL rule. Remote
    # rule bundles must never import that catch-all, and this project
    # intentionally publishes no explicit FINAL.
    if rtype == "FINAL":
        return None

    if rtype in LOGICAL_RULE_TYPES:
        rest = rest.strip()
        if not rest.startswith("(") or not rest.endswith(")"):
            raise ValueError(f"malformed logical rule: {line}")

        nested_types = {
            match.upper()
            for match in re.findall(r"\(([A-Za-z][A-Za-z0-9-]*)\s*,", rest)
        }
        unsupported_nested = sorted(
            nested_types - RULE_TYPES - LOGICAL_RULE_TYPES
        )
        if unsupported_nested:
            raise ValueError(
                f"unsupported nested rule type(s) {unsupported_nested}: {line}"
            )
        return f"{rtype},{rest}"

    if rtype not in RULE_TYPES:
        if re.fullmatch(r"[A-Z][A-Z0-9-]*", rtype):
            raise ValueError(f"unsupported rule type {rtype}: {line}")
        return None

    parts = [p.strip() for p in line.split(",")]
    value = (
        clean_domain(parts[1])
        if rtype in DOMAIN_TYPES | {"DOMAIN-KEYWORD", "DOMAIN-WILDCARD"}
        else parts[1]
    )
    if not value:
        return None
    out = f"{rtype},{value}"
    if rtype in {"IP-CIDR", "IP-CIDR6", "IP-ASN"} and any(
        p.lower() == "no-resolve" for p in parts[2:]
    ):
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
            print(f"[warn] optional source unavailable: {repo_key}:{path}: {exc}", flush=True)
            return set(), None, None
        rules: set[str] = set()
        for line_no, line in enumerate(text.splitlines(), start=1):
            try:
                rule = normalize_rule(line, fmt)
            except ValueError as exc:
                raise ValueError(f"{repo_key}:{path}:{line_no}: {exc}") from exc
            if rule:
                rules.add(rule)
        digest = hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()[:16]
        return rules, path, digest
    if required:
        raise FileNotFoundError(f"required source not found: {repo_key}: {candidates}; last={last_error}")
    return set(), None, None


def read_override(name: str) -> set[str]:
    path = ROOT / "override" / name
    if not path.exists():
        return set()

    rules: set[str] = set()
    for line_no, line in enumerate(
        path.read_text(encoding="utf-8", errors="ignore").splitlines(),
        start=1,
    ):
        try:
            rule = normalize_rule(line)
        except ValueError as exc:
            raise ValueError(f"override/{name}:{line_no}: {exc}") from exc
        if rule:
            rules.add(rule)
    return rules


def split_rule(rule: str) -> tuple[str, str]:
    p = rule.split(",", 2)
    return p[0], p[1].lower()


def build_protection(rulesets):
    exact, suffix = set(), set()
    for rules in rulesets.values():
        for rule in rules:
            typ, value = split_rule(rule)
            if typ == "DOMAIN":
                exact.add(value)
            elif typ == "DOMAIN-SUFFIX":
                suffix.add(value)
    return exact, suffix


def protected_domain(typ, value, exact, suffixes):
    value = value.lower().strip(".")
    if typ not in DOMAIN_TYPES or not value:
        return False
    if typ == "DOMAIN" and value in exact:
        return True
    labels = value.split(".")
    return any(".".join(labels[i:]) in suffixes for i in range(len(labels)))


def domain_matches(rules, domain):
    domain = domain.lower()
    for rule in rules:
        typ, value = split_rule(rule)
        if typ == "DOMAIN" and domain == value:
            return True
        if typ == "DOMAIN-SUFFIX" and (domain == value or domain.endswith("." + value)):
            return True
    return False


def validate_expectations(built):
    checks = json.loads((ROOT / "tests" / "expectations.json").read_text(encoding="utf-8"))
    errors = []
    direct = built.get("China/Direct.list", set()) | built.get("Basic/LAN.list", set())
    for domain in checks.get("direct", []):
        if not domain_matches(direct, domain):
            errors.append(f"expected DIRECT domain missing: {domain}")
    for path, domains in checks.get("service", {}).items():
        for domain in domains:
            if not domain_matches(built.get(path, set()), domain):
                errors.append(f"expected {domain} missing from {path}")
    for path, rules in checks.get("exact_rules", {}).items():
        available = built.get(path, set())
        for rule in rules:
            if rule not in available:
                errors.append(f"expected exact rule missing from {path}: {rule}")
    return errors


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true", help="compatibility flag; Raw sources are always refreshed")
    ap.add_argument("--max-drop", type=float, default=0.35)
    args = ap.parse_args()

    cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    print("[build] resolving upstream revisions", flush=True)
    commits = upstream_heads(cfg)

    prefetch_sources(cfg)

    raw_built, used_sources, items_by_path, source_hashes = {}, {}, {}, {}

    for item in cfg["rulesets"]:
        rules, used = set(), []
        for src in item.get("sources", []):
            got, path, digest = read_source(
                cfg,
                src["repo"],
                src["paths"],
                src.get("format", "rule"),
                src.get("required", True),
            )
            rules |= got
            if path:
                sid = f"{src['repo']}:{path}"
                used.append(sid)
                if digest:
                    source_hashes[sid] = digest
        raw_built[item["path"]], used_sources[item["path"]], items_by_path[item["path"]] = rules, used, item
        print(f"[parse] {item['path']}: {len(rules)} rules", flush=True)

    raw_built.setdefault("China/Direct.list", set()).update(read_override("direct.list"))
    if "Ads/Reject.list" in raw_built:
        raw_built["Ads/Reject.list"].update(read_override("reject.list"))
    protected_sets = {p: r for p, r in raw_built.items() if items_by_path.get(p, {}).get("cn_protect")}
    direct_exact, direct_suffix = build_protection(protected_sets)

    built, removed_counts = {}, {}
    for path, rules in raw_built.items():
        item = items_by_path[path]
        if item.get("cn_guard"):
            kept, removed = set(), 0
            for rule in rules:
                typ, value = split_rule(rule)
                if typ in DOMAIN_TYPES and protected_domain(typ, value, direct_exact, direct_suffix):
                    removed += 1
                else:
                    kept.add(rule)
            rules, removed_counts[path] = kept, removed
        built[path] = rules
    built.setdefault("Proxy/Global.list", set()).update(read_override("proxy.list"))

    previous = {}
    if PREVIOUS_REPORT.exists():
        try:
            previous = json.loads(PREVIOUS_REPORT.read_text(encoding="utf-8")).get("rulesets", {})
        except Exception:
            previous = {}

    errors = []
    for path, rules in built.items():
        item, count = items_by_path[path], len(rules)
        minimum = int(item.get("min_rules", 0))
        if count < minimum:
            errors.append(f"{path}: {count} rules < min_rules {minimum}")
        old = int(previous.get(path, {}).get("count", 0) or 0)
        if old >= 50 and count < old * (1 - args.max_drop):
            errors.append(f"{path}: suspicious drop {old} -> {count}")

    errors += validate_expectations(built)
    if errors:
        print("Validation failed:", file=sys.stderr, flush=True)
        for err in errors:
            print(f" - {err}", file=sys.stderr, flush=True)
        return 2

    if RULE_DIR.exists():
        import shutil
        shutil.rmtree(RULE_DIR)

    for path, rules in built.items():
        item, out = items_by_path[path], RULE_DIR / path
        out.parent.mkdir(parents=True, exist_ok=True)
        head = [
            "# Generated by pickarm/loon. DO NOT EDIT THIS FILE DIRECTLY.",
            f"# NAME: {item['name']}",
            f"# POLICY: {item['policy']}",
            f"# RULES: {len(rules)}",
        ]
        if removed_counts.get(path):
            head.append(f"# CN-GUARD-REMOVED: {removed_counts[path]}")
        head += [f"# SOURCE: {s}" for s in used_sources[path]]
        body = "\n".join(sorted(rules, key=lambda x: (x.split(",", 1)[0], x.lower())))
        out.write_text("\n".join(head) + "\n" + body + "\n", encoding="utf-8")

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "upstreams": commits,
        "source_hashes": source_hashes,
        "rulesets": {
            p: {
                "count": len(r),
                "cn_guard_removed": removed_counts.get(p, 0),
                "policy": items_by_path[p]["policy"],
            }
            for p, r in built.items()
        },
        "total_rules": sum(len(v) for v in built.values()),
    }
    (REPORT_DIR / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    run(sys.executable, str(ROOT / "scripts" / "render_config.py"), timeout=30)
    print(f"Built {len(built)} rulesets / {report['total_rules']} rules", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

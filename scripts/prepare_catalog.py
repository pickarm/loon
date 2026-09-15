#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / "sources" / "sources.json"
SOURCE_EXTENSIONS = ROOT / "sources" / "extensions"
EXPECTATIONS = ROOT / "tests" / "expectations.json"
TEST_EXTENSIONS = ROOT / "tests" / "extensions"

# This project intentionally does not generate a dedicated ad-blocking ruleset.
# Kelee-style plugin entries can still be enabled/disabled independently in Loon.
EXCLUDED_RULESET_PREFIXES = ("Ads/",)
EXCLUDED_POLICIES = {"REJECT"}


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def keep_ruleset(item: dict) -> bool:
    return (
        item.get("policy") not in EXCLUDED_POLICIES
        and not str(item.get("path", "")).startswith(EXCLUDED_RULESET_PREFIXES)
    )


def merge_rulesets() -> None:
    cfg = read_json(SOURCES)
    cfg.setdefault("upstreams", {})
    original = list(cfg.get("rulesets", []))
    base = [item for item in original if keep_ruleset(item)]
    excluded = len(original) - len(base)
    seen_names = {item["name"] for item in base}
    seen_paths = {item["path"] for item in base}
    extras: list[dict] = []

    if SOURCE_EXTENSIONS.exists():
        for path in sorted(SOURCE_EXTENSIONS.glob("*.json")):
            data = read_json(path)

            # Extensions may introduce a new upstream together with their rules.
            # Reusing an existing key is allowed only when the metadata is identical.
            for key, meta in data.get("upstreams", {}).items():
                current = cfg["upstreams"].get(key)
                if current is not None and current != meta:
                    raise ValueError(
                        f"conflicting upstream definition in {path}: {key}"
                    )
                cfg["upstreams"].setdefault(key, meta)

            for item in data.get("rulesets", []):
                if not keep_ruleset(item):
                    excluded += 1
                    continue
                if item["name"] in seen_names:
                    raise ValueError(f"duplicate ruleset name in {path}: {item['name']}")
                if item["path"] in seen_paths:
                    raise ValueError(f"duplicate ruleset path in {path}: {item['path']}")
                seen_names.add(item["name"])
                seen_paths.add(item["path"])
                extras.append(item)

    # Specific extension rules must be evaluated before broad China/Global tails.
    insert_at = next(
        (i for i, item in enumerate(base) if item["path"] in {"China/Direct.list", "China/ChinaIP.list", "Proxy/Global.list"}),
        len(base),
    )
    cfg["rulesets"] = base[:insert_at] + extras + base[insert_at:]

    # Drop upstream definitions that are no longer referenced (for example anti-AD).
    used_repos = {
        src["repo"]
        for item in cfg["rulesets"]
        for src in item.get("sources", [])
    }
    cfg["upstreams"] = {
        key: value for key, value in cfg.get("upstreams", {}).items() if key in used_repos
    }

    SOURCES.write_text(json.dumps(cfg, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print(
        f"[catalog] merged {len(extras)} extension rulesets; "
        f"excluded={excluded}; total={len(cfg['rulesets'])}"
    )


def merge_expectations() -> None:
    checks = read_json(EXPECTATIONS)
    checks.setdefault("direct", [])
    checks.setdefault("service", {})

    if TEST_EXTENSIONS.exists():
        for path in sorted(TEST_EXTENSIONS.glob("*.json")):
            data = read_json(path)
            for domain in data.get("direct", []):
                if domain not in checks["direct"]:
                    checks["direct"].append(domain)
            for ruleset, domains in data.get("service", {}).items():
                dest = checks["service"].setdefault(ruleset, [])
                for domain in domains:
                    if domain not in dest:
                        dest.append(domain)

    EXPECTATIONS.write_text(json.dumps(checks, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[catalog] semantic expectations={sum(len(v) for v in checks['service'].values())}")


def main() -> None:
    merge_rulesets()
    merge_expectations()


if __name__ == "__main__":
    main()

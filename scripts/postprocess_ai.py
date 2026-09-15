#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OVERRIDE = ROOT / "override" / "ai.list"
TARGETS = [
    ROOT / "rules" / "AI" / "OpenAI.list",
    ROOT / "rules" / "Bundles" / "AI.list",
]
REPORT = ROOT / "build" / "report.json"

RULE_TYPE_ORDER = {
    "DOMAIN": 0,
    "DOMAIN-SUFFIX": 1,
    "DOMAIN-WILDCARD": 2,
    "DOMAIN-KEYWORD": 3,
    "USER-AGENT": 4,
    "PROCESS-NAME": 5,
    "PROCESS-PATH": 6,
    "URL-REGEX": 7,
    "PROTOCOL": 8,
    "DST-PORT": 9,
    "SRC-PORT": 10,
    "SRC-IP": 11,
    "IP-ASN": 12,
    "IP-CIDR": 13,
    "IP-CIDR6": 14,
    "GEOIP": 15,
    "RULE-SET": 16,
}


def active_rules(path: Path) -> set[str]:
    return {
        line.strip()
        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines()
        if line.strip() and not line.lstrip().startswith(("#", "//", ";"))
    }


def sort_key(rule: str) -> tuple[int, str]:
    typ = rule.split(",", 1)[0].upper()
    return RULE_TYPE_ORDER.get(typ, 99), rule.lower()


def inject(path: Path, extra: set[str]) -> tuple[int, int]:
    if not path.exists():
        raise FileNotFoundError(path)

    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    headers = [line for line in lines if line.startswith("#")]
    before = active_rules(path)
    merged = before | extra

    new_headers: list[str] = []
    source_seen = False
    for line in headers:
        if line.startswith("# RULES:"):
            new_headers.append(f"# RULES: {len(merged)}")
        else:
            new_headers.append(line)
        if line == "# SOURCE-RULESET: override/ai.list" or line == "# SOURCE: override/ai.list":
            source_seen = True

    if not source_seen:
        marker = "# SOURCE-RULESET: override/ai.list" if "Bundles" in path.parts else "# SOURCE: override/ai.list"
        new_headers.append(marker)

    body = "\n".join(sorted(merged, key=sort_key))
    path.write_text("\n".join(new_headers) + "\n" + body + "\n", encoding="utf-8")
    return len(before), len(merged)


def update_report(old_count: int, new_count: int) -> None:
    if not REPORT.exists():
        return
    data = json.loads(REPORT.read_text(encoding="utf-8"))
    item = data.get("rulesets", {}).get("AI/OpenAI.list")
    if not item:
        return
    delta = new_count - int(item.get("count", old_count))
    item["count"] = new_count
    data["total_rules"] = int(data.get("total_rules", 0)) + delta
    REPORT.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    extra = active_rules(OVERRIDE)
    if not extra:
        raise RuntimeError("override/ai.list is empty")

    openai_before = openai_after = 0
    for target in TARGETS:
        before, after = inject(target, extra)
        print(f"[ai-postprocess] {target.relative_to(ROOT)}: {before} -> {after}")
        if target.name == "OpenAI.list":
            openai_before, openai_after = before, after

    update_report(openai_before, openai_after)

    ai_bundle = active_rules(ROOT / "rules" / "Bundles" / "AI.list")
    missing = sorted(extra - ai_bundle)
    if missing:
        raise RuntimeError("AI bundle missing overrides: " + ", ".join(missing))

    required = {
        "DOMAIN,humb.apple.com",
        "DOMAIN,register.appattest.apple.com",
        "DOMAIN,cdn.workos.com",
        "DOMAIN-SUFFIX,oaistatsig.com",
        "DOMAIN,ios.chat.openai.com",
    }
    # ios.chat.openai.com is covered by DOMAIN-SUFFIX,openai.com even when an exact
    # DOMAIN line is not present. Check it semantically rather than requiring a duplicate.
    semantic_missing = []
    for rule in required:
        if rule in ai_bundle:
            continue
        typ, value = rule.split(",", 1)
        if typ == "DOMAIN" and any(
            r.startswith("DOMAIN-SUFFIX,")
            and (value == r.split(",", 1)[1] or value.endswith("." + r.split(",", 1)[1]))
            for r in ai_bundle
        ):
            continue
        semantic_missing.append(rule)
    if semantic_missing:
        raise RuntimeError("AI semantic checks failed: " + ", ".join(semantic_missing))


if __name__ == "__main__":
    main()

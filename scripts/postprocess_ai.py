#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OPENAI_OVERRIDE = ROOT / "override" / "ai.list"
GEMINI_OVERRIDE = ROOT / "override" / "gemini.list"
OPENAI_TARGET = ROOT / "rules" / "AI" / "OpenAI.list"
GEMINI_TARGET = ROOT / "rules" / "AI" / "Gemini.list"
AI_BUNDLE = ROOT / "rules" / "Bundles" / "AI.list"
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
    "AND": 17,
    "OR": 18,
    "NOT": 19,
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


def inject(path: Path, extra: set[str], label: str) -> tuple[int, int]:
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
        if line == f"# SOURCE-RULESET: override/{label}.list" or line == f"# SOURCE: override/{label}.list":
            source_seen = True

    if not source_seen:
        marker = f"# SOURCE-RULESET: override/{label}.list" if "Bundles" in path.parts else f"# SOURCE: override/{label}.list"
        new_headers.append(marker)

    body = "\n".join(sorted(merged, key=sort_key))
    path.write_text("\n".join(new_headers) + "\n" + body + "\n", encoding="utf-8")
    return len(before), len(merged)


def update_report(changes: dict[str, int]) -> None:
    if not REPORT.exists():
        return
    data = json.loads(REPORT.read_text(encoding="utf-8"))
    delta = 0
    for name, count in changes.items():
        item = data.get("rulesets", {}).get(name)
        if not item:
            raise RuntimeError(f"Missing build report ruleset: {name}")
        delta += count - int(item["count"])
        item["count"] = count
    data["total_rules"] = int(data.get("total_rules", 0)) + delta
    REPORT.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    openai_extra = active_rules(OPENAI_OVERRIDE)
    gemini_extra = active_rules(GEMINI_OVERRIDE)
    if not openai_extra or not gemini_extra:
        raise RuntimeError("AI/Gemini overrides must not be empty")

    changes: dict[str, int] = {}
    for target, extra, label in (
        (OPENAI_TARGET, openai_extra, "ai"),
        (GEMINI_TARGET, gemini_extra, "gemini"),
    ):
        before, after = inject(target, extra, label)
        print(f"[ai-postprocess] {target.relative_to(ROOT)}: {before} -> {after}")
        changes[f"AI/{target.name}"] = after

    # Preserve all OpenAI + Gemini overrides in the same published AI bundle.
    # The generated config subscribes to this bundle BEFORE the generic DIRECT
    # one, so these exact hosts win even if DIRECT also contains them.
    for extra, label in ((openai_extra, "ai"), (gemini_extra, "gemini")):
        before, after = inject(AI_BUNDLE, extra, label)
        print(f"[ai-postprocess] {AI_BUNDLE.relative_to(ROOT)} [{label}]: {before} -> {after}")

    update_report(changes)

    ai_bundle = active_rules(AI_BUNDLE)
    missing = sorted((openai_extra | gemini_extra) - ai_bundle)
    if missing:
        raise RuntimeError("AI bundle missing overrides: " + ", ".join(missing))

    required = {
        "DOMAIN,humb.apple.com",
        "DOMAIN,register.appattest.apple.com",
        "DOMAIN,cdn.workos.com",
        "DOMAIN-SUFFIX,oaistatsig.com",
        "DOMAIN,ios.chat.openai.com",
        "AND,((DOMAIN-KEYWORD, chatgpt-async-webps-prod-), (DOMAIN-SUFFIX, webpubsub.azure.com))",
        "AND,((DOMAIN-KEYWORD, openaicom-api-), (DOMAIN-SUFFIX, azurefd.net))",
    }
    # ios.chat.openai.com is covered by DOMAIN-SUFFIX,openai.com.
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

    # These formerly went DIRECT or generic overseas. Require precise AI
    # domains; never permit broad suffixes such as googleapis.com.
    if any(rule.startswith(("DOMAIN-SUFFIX,google", "DOMAIN-KEYWORD,google")) for rule in gemini_extra):
        raise RuntimeError("Gemini override must use exact hosts rather than broad Google rules")
    required_gemini = {
        "gemini.google.com",
        "jnn-pa.googleapis.com",
        "waa-pa.clients6.google.com",
        "ogads-pa.clients6.google.com",
        "optimizationguide-pa.googleapis.com",
        "www.googleapis.com",
        "ogs.google.com",
        "ssl.gstatic.com",
        "fonts.googleapis.com",
        "www.gstatic.com",
    }
    if gemini_extra != {f"DOMAIN,{host}" for host in required_gemini}:
        raise RuntimeError("Gemini exact-host override list is incomplete or unexpectedly broad")
    if not gemini_extra.issubset(active_rules(GEMINI_TARGET)):
        raise RuntimeError("Gemini fine-grained list missing exact-host overrides")

    template = (ROOT / "templates" / "Loon.conf.tpl").read_text(encoding="utf-8")
    remote_rules = template.split("[Remote Rule]", 1)[1].split("[Host]", 1)[0]
    if remote_rules.find("{{REMOTE_RULES}}") < 0:
        raise RuntimeError("Loon template must publish generated Remote Rules")
    from render_config import BUNDLE_SPECS
    policies = [spec["policy"] for spec in BUNDLE_SPECS]
    if policies.index("🤖 AI平台") > policies.index("DIRECT"):
        raise RuntimeError("Gemini AI bundle must precede DIRECT bundle")


if __name__ == "__main__":
    main()

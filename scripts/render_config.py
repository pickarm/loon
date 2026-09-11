#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CFG = json.loads((ROOT / "sources" / "sources.json").read_text(encoding="utf-8"))
TEMPLATE = (ROOT / "templates" / "Loon.conf.tpl").read_text(encoding="utf-8")

FLAVORS = {
    "Loon.conf": "https://raw.githubusercontent.com/pickarm/loon/release/rules",
    "Loon-CN.conf": "https://cdn.jsdelivr.net/gh/pickarm/loon@release/rules",
    "Loon-Proxy.conf": "https://githubproxy.cc/https://raw.githubusercontent.com/pickarm/loon/release/rules"
}


def remote_rules(base: str) -> str:
    lines = []
    for item in CFG["rulesets"]:
        if not (ROOT / "rules" / item["path"]).exists():
            continue
        lines.append(f"{base}/{item['path']}, policy={item['policy']}, tag={item['tag']}, enabled=true")
    return "\n".join(lines)


def main() -> None:
    out_dir = ROOT / "config"
    out_dir.mkdir(parents=True, exist_ok=True)
    for filename, base in FLAVORS.items():
        text = TEMPLATE.replace("{{REMOTE_RULES}}", remote_rules(base))
        text = text.replace("{{CONFIG_VARIANT}}", filename)
        (out_dir / filename).write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()

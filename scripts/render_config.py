#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CFG = json.loads((ROOT / "sources" / "sources.json").read_text(encoding="utf-8"))
TEMPLATE = (ROOT / "templates" / "Loon.conf.tpl").read_text(encoding="utf-8")

FLAVORS = {
    "Loon.conf": {
        "rules_base": "https://raw.githubusercontent.com/pickarm/loon/release/rules",
        "github_mode": "raw",
    },
    "Loon-CN.conf": {
        "rules_base": "https://cdn.jsdelivr.net/gh/pickarm/loon@release/rules",
        "github_mode": "jsdelivr",
    },
    "Loon-Proxy.conf": {
        "rules_base": "https://githubproxy.cc/https://raw.githubusercontent.com/pickarm/loon/release/rules",
        "github_mode": "proxy",
    },
}

RAW_GITHUB = re.compile(
    r"https://raw\.githubusercontent\.com/"
    r"(?P<owner>[^/\s]+)/(?P<repo>[^/\s]+)/(?P<ref>[^/\s]+)/(?P<path>[^\s,\"]+)"
)


def remote_rules(base: str) -> str:
    lines = []
    for item in CFG["rulesets"]:
        if not (ROOT / "rules" / item["path"]).exists():
            continue
        lines.append(
            f"{base}/{item['path']}, policy={item['policy']}, "
            f"tag={item['tag']}, enabled=true"
        )
    return "\n".join(lines)


def rewrite_github_raw(text: str, mode: str) -> str:
    if mode == "raw":
        return text

    def repl(match: re.Match[str]) -> str:
        raw = match.group(0)
        if mode == "proxy":
            return f"https://githubproxy.cc/{raw}"
        if mode == "jsdelivr":
            owner = match.group("owner")
            repo = match.group("repo")
            ref = match.group("ref")
            path = match.group("path")
            return f"https://cdn.jsdelivr.net/gh/{owner}/{repo}@{ref}/{path}"
        raise ValueError(f"unknown github rewrite mode: {mode}")

    return RAW_GITHUB.sub(repl, text)


def main() -> None:
    out_dir = ROOT / "config"
    out_dir.mkdir(parents=True, exist_ok=True)

    for filename, flavor in FLAVORS.items():
        text = TEMPLATE.replace("{{REMOTE_RULES}}", remote_rules(flavor["rules_base"]))
        text = text.replace("{{CONFIG_VARIANT}}", filename)
        text = rewrite_github_raw(text, flavor["github_mode"])
        (out_dir / filename).write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()

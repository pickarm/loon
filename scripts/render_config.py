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

# Rules stay fine-grained, but their rendered Loon policies intentionally stay
# close to the user's 4LESS/ACL4SSR layout. New source-level policy names must
# be explicitly folded into this small set or CI/rendering will fail closed.
POLICY_ALIASES = {
    "DIRECT": "🎯 全球直连",
    "REJECT": "🛑 广告拦截",
    "🤖 OpenAI": "💬 Ai平台",
    "🤖 AI": "💬 Ai平台",
    "🤖 Claude": "💬 Ai平台",
    "🤖 Gemini": "💬 Ai平台",
    "🤖 Copilot": "💬 Ai平台",
    "💬 Telegram": "📲 电报消息",
    "💬 社交通讯": "🚀 节点选择",
    "📺 YouTube": "📹 油管视频",
    "🎬 Netflix": "🎥 奈飞视频",
    "🎬 流媒体": "🌍 国外媒体",
    "🎵 Spotify": "🌍 国外媒体",
    "🎵 TikTok": "🌍 国外媒体",
    "🧑‍💻 GitHub": "🚀 节点选择",
    "🧑‍💻 开发服务": "🚀 节点选择",
    "☁️ 云存储": "🚀 节点选择",
    "🔍 Google": "🚀 节点选择",
    "Ⓜ️ Microsoft": "Ⓜ️ 微软服务",
    "🍎 Apple": "🍎 苹果服务",
    "💳 金融支付": "🚀 节点选择",
    "🎮 游戏平台": "🎮 游戏平台",
    "🌍 国外网站": "🚀 节点选择",
}

RULESET_POLICY_OVERRIDES = {
    # 4LESS treats OneDrive as Microsoft traffic rather than a generic cloud group.
    "OneDrive": "Ⓜ️ 微软服务",
}

ALLOWED_OUTPUT_POLICIES = {
    "🚀 节点选择",
    "📲 电报消息",
    "💬 Ai平台",
    "📹 油管视频",
    "🎥 奈飞视频",
    "🌍 国外媒体",
    "Ⓜ️ 微软服务",
    "🍎 苹果服务",
    "🎮 游戏平台",
    "🎯 全球直连",
    "🛑 广告拦截",
}

RAW_GITHUB = re.compile(
    r"https://raw\.githubusercontent\.com/"
    r"(?P<owner>[^/\s]+)/(?P<repo>[^/\s]+)/(?P<ref>[^/\s]+)/(?P<path>[^\s,\"]+)"
)


def output_policy(item: dict) -> str:
    policy = RULESET_POLICY_OVERRIDES.get(item["name"])
    if policy is None:
        source_policy = item["policy"]
        if source_policy not in POLICY_ALIASES:
            raise ValueError(
                f"ruleset {item['name']}: source policy {source_policy!r} has no 4LESS mapping"
            )
        policy = POLICY_ALIASES[source_policy]
    if policy not in ALLOWED_OUTPUT_POLICIES:
        raise ValueError(f"ruleset {item['name']}: unsupported output policy {policy!r}")
    return policy


def validate_template_policy_groups() -> None:
    missing = []
    for policy in sorted(ALLOWED_OUTPUT_POLICIES):
        pattern = rf"(?m)^{re.escape(policy)}\s*="
        if re.search(pattern, TEMPLATE) is None:
            missing.append(policy)
    if missing:
        raise ValueError(
            "Loon template is missing rendered policy groups: " + ", ".join(missing)
        )


def remote_rules(base: str) -> str:
    lines = []
    for item in CFG["rulesets"]:
        if not (ROOT / "rules" / item["path"]).exists():
            continue
        policy = output_policy(item)
        lines.append(
            f"{base}/{item['path']}, policy={policy}, "
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
    validate_template_policy_groups()

    out_dir = ROOT / "config"
    out_dir.mkdir(parents=True, exist_ok=True)

    for filename, flavor in FLAVORS.items():
        text = TEMPLATE.replace("{{REMOTE_RULES}}", remote_rules(flavor["rules_base"]))
        text = text.replace("{{CONFIG_VARIANT}}", filename)
        text = rewrite_github_raw(text, flavor["github_mode"])
        (out_dir / filename).write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()

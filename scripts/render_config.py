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

# Rules remain fine-grained, but visible policies are intentionally compact.
# Ordinary overseas traffic is sent straight to the single fallback policy;
# only services that benefit from a persistent user-selected exit stay visible.
POLICY_ALIASES = {
    "DIRECT": "DIRECT",
    "🤖 OpenAI": "🤖 AI平台",
    "🤖 AI": "🤖 AI平台",
    "🤖 Claude": "🤖 AI平台",
    "🤖 Gemini": "🤖 AI平台",
    "🤖 Copilot": "🤖 AI平台",
    "💬 Telegram": "📲 电报消息",
    "💬 社交通讯": "兜底后备策略",
    "📺 YouTube": "📹 油管视频",
    "🎬 Netflix": "🎥 奈飞视频",
    "🎬 流媒体": "🌍 国外媒体",
    "🎵 Spotify": "🌍 国外媒体",
    "🎵 TikTok": "🌍 国外媒体",
    "🧑‍💻 GitHub": "兜底后备策略",
    "🧑‍💻 开发服务": "兜底后备策略",
    "☁️ 云存储": "兜底后备策略",
    "🔍 Google": "兜底后备策略",
    "Ⓜ️ Microsoft": "Ⓜ️ 微软服务",
    "🍎 Apple": "🍎 苹果服务",
    "💳 金融支付": "💳 金融平台",
    "🎮 游戏平台": "🎮 游戏平台",
    "🌍 国外网站": "兜底后备策略",
}

RULESET_POLICY_OVERRIDES = {
    "OneDrive": "Ⓜ️ 微软服务",
}

BUILTIN_POLICIES = {"DIRECT", "REJECT"}
VISIBLE_SERVICE_POLICIES = {
    "🤖 AI平台",
    "📲 电报消息",
    "📹 油管视频",
    "🎥 奈飞视频",
    "🌍 国外媒体",
    "Ⓜ️ 微软服务",
    "🍎 苹果服务",
    "🎮 游戏平台",
    "💳 金融平台",
}
SPECIAL_POLICIES = {"兜底后备策略"}
ALLOWED_OUTPUT_POLICIES = BUILTIN_POLICIES | VISIBLE_SERVICE_POLICIES | SPECIAL_POLICIES
FORBIDDEN_LEGACY_GROUPS = {
    "🚀 节点选择",
    "🚀 手动切换",
    "♻️ 自动选择",
    "🎯 全球直连",
    "🛑 广告拦截",
    "🐟 漏网之鱼",
    "🌐 国外网站",
}

RAW_GITHUB = re.compile(
    r"https://raw\.githubusercontent\.com/"
    r"(?P<owner>[^/\s]+)/(?P<repo>[^/\s]+)/(?P<ref>[^/\s]+)/(?P<path>[^\s,\"]+)"
)


def output_policy(item: dict) -> str:
    policy = RULESET_POLICY_OVERRIDES.get(item["name"])
    if policy is None:
        source_policy = item["policy"]
        if source_policy == "REJECT":
            raise ValueError(
                f"ruleset {item['name']}: ad/reject rules are disabled for this configuration"
            )
        if source_policy not in POLICY_ALIASES:
            raise ValueError(
                f"ruleset {item['name']}: source policy {source_policy!r} has no service mapping"
            )
        policy = POLICY_ALIASES[source_policy]
    if policy not in ALLOWED_OUTPUT_POLICIES:
        raise ValueError(f"ruleset {item['name']}: unsupported output policy {policy!r}")
    return policy


def group_line(name: str) -> str | None:
    match = re.search(rf"(?m)^{re.escape(name)}\s*=\s*(.+)$", TEMPLATE)
    return match.group(1) if match else None


def validate_template_policy_groups() -> None:
    missing = [policy for policy in sorted(VISIBLE_SERVICE_POLICIES) if group_line(policy) is None]
    if missing:
        raise ValueError(
            "Loon template is missing service policy groups: " + ", ".join(missing)
        )

    present_forbidden = [policy for policy in sorted(FORBIDDEN_LEGACY_GROUPS) if group_line(policy) is not None]
    if present_forbidden:
        raise ValueError(
            "Loon template still contains deprecated intermediary groups: "
            + ", ".join(present_forbidden)
        )

    fallback = group_line("兜底后备策略")
    if fallback is None:
        raise ValueError("Loon template is missing 兜底后备策略")
    if not fallback.startswith("fallback,"):
        raise ValueError("兜底后备策略 must remain a fallback group")
    if "节点" not in fallback:
        raise ValueError("兜底后备策略 must consume Remote Filter node sets directly")

    # Business groups must expose Remote Filter node sets directly. This blocks
    # the old second-level region groups from returning in future edits.
    for policy in sorted(VISIBLE_SERVICE_POLICIES):
        line = group_line(policy) or ""
        if not line.startswith("select,"):
            raise ValueError(f"{policy} must be a select group")
        if "节点" not in line:
            raise ValueError(f"{policy} must reference Remote Filter node sets directly")
        if "手动策略" in line or "时延优选" in line:
            raise ValueError(f"{policy} still references nested regional policy groups")

    # No old regional groups should remain as visible cards.
    if re.search(r"(?m)^(?:香港|台湾|日本|韩国|新加坡|美国).*(?:手动策略|时延优选)\s*=", TEMPLATE):
        raise ValueError("template still defines nested regional manual/latency groups")

    if "FINAL,兜底后备策略" not in TEMPLATE:
        raise ValueError("Loon FINAL must point directly to 兜底后备策略")


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

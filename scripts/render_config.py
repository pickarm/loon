#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RULE_DIR = ROOT / "rules"
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

# Fine-grained files stay in rules/* for maintenance and debugging. Loon only
# subscribes to the compact bundles below, so its Rules page stays close to the
# visible policy layout instead of showing 60+ individual rule subscriptions.
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
ALLOWED_OUTPUT_POLICIES = {"DIRECT"} | VISIBLE_SERVICE_POLICIES | SPECIAL_POLICIES
FORBIDDEN_LEGACY_GROUPS = {
    "🚀 节点选择",
    "🚀 手动切换",
    "♻️ 自动选择",
    "🎯 全球直连",
    "🛑 广告拦截",
    "🐟 漏网之鱼",
    "🌐 国外网站",
}

# Order here is also the order shown on Loon's Rules page.
BUNDLE_SPECS = [
    {"policy": "DIRECT", "path": "Bundles/Direct.list", "tag": "🎯 全球直连"},
    {"policy": "🤖 AI平台", "path": "Bundles/AI.list", "tag": "🤖 AI平台"},
    {"policy": "📲 电报消息", "path": "Bundles/Telegram.list", "tag": "📲 电报消息"},
    {"policy": "📹 油管视频", "path": "Bundles/YouTube.list", "tag": "📹 油管视频"},
    {"policy": "🎥 奈飞视频", "path": "Bundles/Netflix.list", "tag": "🎥 奈飞视频"},
    {"policy": "🌍 国外媒体", "path": "Bundles/Streaming.list", "tag": "🌍 国外媒体"},
    {"policy": "Ⓜ️ 微软服务", "path": "Bundles/Microsoft.list", "tag": "Ⓜ️ 微软服务"},
    {"policy": "🍎 苹果服务", "path": "Bundles/Apple.list", "tag": "🍎 苹果服务"},
    {"policy": "🎮 游戏平台", "path": "Bundles/Game.list", "tag": "🎮 游戏平台"},
    {"policy": "💳 金融平台", "path": "Bundles/Finance.list", "tag": "💳 金融平台"},
    {"policy": "兜底后备策略", "path": "Bundles/Fallback.list", "tag": "🐟 漏网之鱼"},
]

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
    if fallback is None or not fallback.startswith("fallback,"):
        raise ValueError("兜底后备策略 must remain a fallback group")
    if "节点" not in fallback:
        raise ValueError("兜底后备策略 must consume Remote Filter node sets directly")

    for policy in sorted(VISIBLE_SERVICE_POLICIES):
        line = group_line(policy) or ""
        if not line.startswith("select,"):
            raise ValueError(f"{policy} must be a select group")
        if "节点" not in line:
            raise ValueError(f"{policy} must reference Remote Filter node sets directly")
        if "手动策略" in line or "时延优选" in line:
            raise ValueError(f"{policy} still references nested regional policy groups")

    if re.search(r"(?m)^(?:香港|台湾|日本|韩国|新加坡|美国).*(?:手动策略|时延优选)\s*=", TEMPLATE):
        raise ValueError("template still defines nested regional manual/latency groups")
    if "FINAL,兜底后备策略" not in TEMPLATE:
        raise ValueError("Loon FINAL must point directly to 兜底后备策略")


def file_rules(path: Path) -> set[str]:
    rules: set[str] = set()
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if line and not line.startswith(("#", "//", ";")):
            rules.add(line)
    return rules


def build_bundles() -> list[dict]:
    grouped: dict[str, set[str]] = {spec["policy"]: set() for spec in BUNDLE_SPECS}
    sources: dict[str, list[str]] = {spec["policy"]: [] for spec in BUNDLE_SPECS}

    for item in CFG["rulesets"]:
        src = RULE_DIR / item["path"]
        if not src.exists():
            continue
        policy = output_policy(item)
        grouped.setdefault(policy, set()).update(file_rules(src))
        sources.setdefault(policy, []).append(item["path"])

    built_specs: list[dict] = []
    for spec in BUNDLE_SPECS:
        policy = spec["policy"]
        rules = grouped.get(policy, set())
        if not rules:
            raise ValueError(f"bundle {spec['path']} for {policy} is empty")
        out = RULE_DIR / spec["path"]
        out.parent.mkdir(parents=True, exist_ok=True)
        header = [
            "# Generated by pickarm/loon from fine-grained rules. DO NOT EDIT.",
            f"# TAG: {spec['tag']}",
            f"# POLICY: {policy}",
            f"# RULES: {len(rules)}",
        ]
        header += [f"# SOURCE-RULESET: {p}" for p in sources.get(policy, [])]
        body = "\n".join(sorted(rules, key=lambda x: (x.split(",", 1)[0], x.lower())))
        out.write_text("\n".join(header) + "\n" + body + "\n", encoding="utf-8")
        built_specs.append({**spec, "count": len(rules)})

    return built_specs


def remote_rules(base: str, bundles: list[dict]) -> str:
    lines = [
        f"{base}/{spec['path']}, policy={spec['policy']}, tag={spec['tag']}, enabled=true"
        for spec in bundles
    ]
    if len(lines) != len(BUNDLE_SPECS):
        raise ValueError(f"expected {len(BUNDLE_SPECS)} remote bundles, got {len(lines)}")
    return "\n".join(lines)


def rewrite_github_raw(text: str, mode: str) -> str:
    if mode == "raw":
        return text

    def repl(match: re.Match[str]) -> str:
        raw = match.group(0)
        if mode == "proxy":
            return f"https://githubproxy.cc/{raw}"
        if mode == "jsdelivr":
            return (
                f"https://cdn.jsdelivr.net/gh/{match.group('owner')}/{match.group('repo')}"
                f"@{match.group('ref')}/{match.group('path')}"
            )
        raise ValueError(f"unknown github rewrite mode: {mode}")

    return RAW_GITHUB.sub(repl, text)


def main() -> None:
    validate_template_policy_groups()
    bundles = build_bundles()
    print(
        "[bundle] "
        + ", ".join(f"{spec['tag']}={spec['count']}" for spec in bundles),
        flush=True,
    )

    out_dir = ROOT / "config"
    out_dir.mkdir(parents=True, exist_ok=True)
    for filename, flavor in FLAVORS.items():
        text = TEMPLATE.replace(
            "{{REMOTE_RULES}}", remote_rules(flavor["rules_base"], bundles)
        )
        text = text.replace("{{CONFIG_VARIANT}}", filename)
        text = rewrite_github_raw(text, flavor["github_mode"])
        (out_dir / filename).write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()

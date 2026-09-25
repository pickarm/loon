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
# subscribes to compact bundles, so the Rules page stays close to the visible
# policy layout instead of showing 60+ individual rule subscriptions.
POLICY_ALIASES = {
    "DIRECT": "DIRECT",
    "🤖 OpenAI": "🤖 AI平台",
    "🤖 AI": "🤖 AI平台",
    "🤖 Claude": "🤖 AI平台",
    "🤖 Gemini": "🤖 AI平台",
    "🤖 Copilot": "🤖 AI平台",
    "💬 Telegram": "📲 电报消息",
    "💬 社交通讯": "🌐 国外网站",
    "📺 YouTube": "🎬 流媒体",
    "🎬 Netflix": "🎬 流媒体",
    "🎬 流媒体": "🎬 流媒体",
    "🎵 Spotify": "🎬 流媒体",
    "🎵 TikTok": "🎬 流媒体",
    "🧑‍💻 GitHub": "🌐 国外网站",
    "🧑‍💻 开发服务": "🌐 国外网站",
    "☁️ 云存储": "🌐 国外网站",
    "🔍 Google": "🌐 国外网站",
    "Ⓜ️ Microsoft": "DIRECT",
    "🍎 Apple": "DIRECT",
    "💳 金融支付": "💳 金融平台",
    "🎮 游戏平台": "DIRECT",
    "🌍 国外网站": "🌐 国外网站",
}

RULESET_POLICY_OVERRIDES = {
    "OneDrive": "DIRECT",
}

VISIBLE_SERVICE_POLICIES = {
    "🌐 国外网站",
    "🤖 AI平台",
    "📲 电报消息",
    "🎬 流媒体",
    "💳 金融平台",
}
ALLOWED_OUTPUT_POLICIES = {"DIRECT"} | VISIBLE_SERVICE_POLICIES
FORBIDDEN_LEGACY_GROUPS = {
    "🚀 节点选择",
    "🚀 手动切换",
    "♻️ 自动选择",
    "🎯 全球直连",
    "🛑 广告拦截",
    "🐟 漏网之鱼",
    "兜底后备策略",
    "📹 油管视频",
    "🎥 奈飞视频",
    "🌍 国外媒体",
    "Ⓜ️ 微软服务",
    "🍎 苹果服务",
    "🎮 游戏平台",
}

# Remote Rule is first-match-wins. Fine-grained rule bundles may share one
# visible policy; UI groups remain compact while source rules stay auditable.
BUNDLE_SPECS = [
    {"policy": "🤖 AI平台", "path": "Bundles/AI.list", "tag": "🤖 AI平台"},
    {"policy": "📲 电报消息", "path": "Bundles/Telegram.list", "tag": "📲 电报消息"},
    {"policy": "🎬 流媒体", "path": "Bundles/YouTube.list", "tag": "📹 油管视频"},
    {"policy": "🎬 流媒体", "path": "Bundles/Netflix.list", "tag": "🎥 奈飞视频"},
    {"policy": "🎬 流媒体", "path": "Bundles/Streaming.list", "tag": "🎬 流媒体"},
    {"policy": "💳 金融平台", "path": "Bundles/Finance.list", "tag": "💳 金融平台"},
    {"policy": "DIRECT", "path": "Bundles/Direct.list", "tag": "🎯 全球直连"},
    {"policy": "🌐 国外网站", "path": "Bundles/Blacklist.list", "tag": "🧱 黑名单", "kind": "blacklist"},
    {"policy": "🌐 国外网站", "path": "Bundles/Fallback.list", "tag": "🐟 漏网之鱼", "kind": "fallback"},
]

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
    expected = [
        "♻️ 全局优选",
        "🌐 国外网站",
        "🤖 AI平台",
        "📲 电报消息",
        "🎬 流媒体",
        "💳 金融平台",
    ]

    group_block_match = re.search(r"(?s)\[Proxy Group\]\n(.*?)\n\[Rule\]", TEMPLATE)
    if not group_block_match:
        raise ValueError("Loon template is missing Proxy Group block")
    group_block = group_block_match.group(1)
    actual = re.findall(
        r"(?m)^([^#\n=]+?)\s*=\s*(?:select|url-test|fallback|load-balance),",
        group_block,
    )
    if actual != expected:
        raise ValueError(
            "visible policy groups must stay minimal; expected "
            + ", ".join(expected)
            + "; got "
            + ", ".join(actual)
        )

    auto = group_line("♻️ 全局优选")
    if auto is None or not auto.startswith("url-test,全球节点"):
        raise ValueError("♻️ 全局优选 must be the single global url-test over 全球节点")

    for policy in expected[1:]:
        line = group_line(policy) or ""
        if not line.startswith("select,"):
            raise ValueError(f"{policy} must be a select group")
        if "♻️ 全局优选" not in line or "全球节点" not in line:
            raise ValueError(f"{policy} must expose global auto and actual nodes")

    if re.search(r"(?m)^.*(?:时延优选|手动策略)\s*=", TEMPLATE):
        raise ValueError("template still defines regional manual/latency groups")

    present_forbidden = [
        policy for policy in sorted(FORBIDDEN_LEGACY_GROUPS)
        if group_line(policy) is not None
    ]
    if present_forbidden:
        raise ValueError(
            "Loon template still contains deprecated groups: "
            + ", ".join(present_forbidden)
        )

    filter_block_match = re.search(r"(?s)\[Remote Filter\]\n(.*?)\n\[Proxy Group\]", TEMPLATE)
    if not filter_block_match:
        raise ValueError("Loon template is missing Remote Filter block")
    filter_lines = re.findall(r"(?m)^([^#\n=]+?)\s*=\s*NameRegex,", filter_block_match.group(1))
    if filter_lines != ["全球节点"]:
        raise ValueError(
            "release config must render only 全球节点 Remote Filter; got "
            + ", ".join(filter_lines)
        )

    if re.search(r"(?m)^FINAL,", TEMPLATE):
        raise ValueError("release config must not define an explicit FINAL rule")


def file_rules(path: Path) -> set[str]:
    rules: set[str] = set()
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if line and not line.startswith(("#", "//", ";")):
            rules.add(line)
    return rules


def split_rule(rule: str) -> tuple[str, str]:
    parts = rule.split(",", 2)
    typ = parts[0].upper() if parts else ""
    value = parts[1].lower().strip(".") if len(parts) > 1 else ""
    return typ, value


def coverage_index(rules: set[str]) -> tuple[set[str], set[str], set[str]]:
    exact: set[str] = set()
    suffix: set[str] = set()
    other: set[str] = set()
    for rule in rules:
        typ, value = split_rule(rule)
        if typ == "DOMAIN":
            exact.add(value)
        elif typ == "DOMAIN-SUFFIX":
            suffix.add(value)
        else:
            other.add(rule)
    return exact, suffix, other


def covered_by(rule: str, index: tuple[set[str], set[str], set[str]]) -> bool:
    exact, suffixes, other = index
    typ, value = split_rule(rule)
    if typ == "DOMAIN":
        if value in exact:
            return True
        labels = value.split(".")
        return any(".".join(labels[i:]) in suffixes for i in range(len(labels)))
    if typ == "DOMAIN-SUFFIX":
        labels = value.split(".")
        return any(".".join(labels[i:]) in suffixes for i in range(len(labels)))
    return rule in other


def rule_sort_key(rule: str) -> tuple[int, str]:
    typ = rule.split(",", 1)[0].upper()
    return RULE_TYPE_ORDER.get(typ, 99), rule.lower()


def build_bundles() -> list[dict]:
    grouped: dict[str, set[str]] = {
        policy: set() for policy in ALLOWED_OUTPUT_POLICIES
    }
    sources: dict[str, list[str]] = {
        policy: [] for policy in ALLOWED_OUTPUT_POLICIES
    }
    raw_blacklist: set[str] = set()
    blacklist_sources: list[str] = []

    for item in CFG["rulesets"]:
        src = RULE_DIR / item["path"]
        if not src.exists():
            continue
        rules = file_rules(src)
        if item.get("blacklist_residual"):
            raw_blacklist.update(rules)
            blacklist_sources.append(item["path"])
            continue
        policy = output_policy(item)
        grouped.setdefault(policy, set()).update(rules)
        sources.setdefault(policy, []).append(item["path"])

    if not raw_blacklist:
        raise ValueError("blacklist source ruleset is missing or empty")

    # Blacklist is only the blocked-site residual: remove anything already
    # handled by a visible service group or DIRECT. The generic fallback group
    # intentionally does not exclude it, because many blocked sites live there.
    claimed: set[str] = set(grouped.get("DIRECT", set()))
    for policy in VISIBLE_SERVICE_POLICIES - {"🌐 国外网站"}:
        claimed.update(grouped.get(policy, set()))
    claimed_index = coverage_index(claimed)
    blacklist = {rule for rule in raw_blacklist if not covered_by(rule, claimed_index)}
    if not blacklist:
        raise ValueError("blacklist residual became empty after de-duplication")

    # Remove blacklisted domains from the generic fallback bundle so the same
    # domain is not represented twice at the published bundle layer.
    blacklist_index = coverage_index(blacklist)
    fallback = {
        rule
        for rule in grouped.get("🌐 国外网站", set())
        if not covered_by(rule, blacklist_index)
    }
    grouped["🌐 国外网站"] = fallback

    built_specs: list[dict] = []
    for spec in BUNDLE_SPECS:
        kind = spec.get("kind")
        policy = spec["policy"]
        if kind == "blacklist":
            rules = blacklist
            source_paths = blacklist_sources
        else:
            rules = grouped.get(policy, set())
            source_paths = sources.get(policy, [])

        if not rules:
            raise ValueError(f"bundle {spec['path']} for {spec['tag']} is empty")
        out = RULE_DIR / spec["path"]
        out.parent.mkdir(parents=True, exist_ok=True)
        header = [
            "# Generated by pickarm/loon from fine-grained rules. DO NOT EDIT.",
            f"# TAG: {spec['tag']}",
            f"# POLICY: {policy}",
            f"# RULES: {len(rules)}",
        ]
        if kind == "blacklist":
            header.append("# NOTE: blocked-site residual after removing DIRECT and named service groups")
        header += [f"# SOURCE-RULESET: {p}" for p in source_paths]
        body = "\n".join(sorted(rules, key=rule_sort_key))
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

# Loon Rules

面向中国大陆网络环境的 **Loon 配置 + 聚合规则库**。目标不是简单搬运某一个规则仓库，而是把多个头部上游的规则合并、清洗、去重，并用 CN Guard 尽量避免国内域名误走代理。

## 🚀 直接使用

GitHub Actions 会把可使用的配置与规则发布到 `release` 分支。

| 版本 | 推荐场景 | 配置地址 |
|---|---|---|
| 🇨🇳 **Loon-CN.conf** | 中国大陆，默认推荐 | `https://cdn.jsdelivr.net/gh/pickarm/loon@release/config/Loon-CN.conf` |
| 🌐 **Loon.conf** | GitHub Raw 可直连 | `https://raw.githubusercontent.com/pickarm/loon/release/config/Loon.conf` |
| 🚀 **Loon-Proxy.conf** | GitHub Raw 访问不稳定时 | `https://githubproxy.cc/https://raw.githubusercontent.com/pickarm/loon/release/config/Loon-Proxy.conf` |

第三方 GitHub 代理可能变化，因此 **默认优先使用 jsDelivr**；`githubproxy.cc` 作为备用，`ghfast.top` 可作为手工替换的第二备用。

> 公共配置不会保存任何私人订阅 URL、MITM CA、证书或密码。导入配置后，请在 Loon 中添加自己的节点订阅。

## 设计原则

1. **分类清晰**：策略组按 4LESS 一类的 Clash 配置思路拆分为 AI、流媒体、社交、开发、厂商、游戏、中国直连、国外代理等业务类别。
2. **多源聚合**：优先使用 `blackmatrix7/ios_rule_script`、`fmz200/wool_scripts`、`Loyalsoldier/surge-rules`、`felixonmars/dnsmasq-china-list`、`privacy-protection-tools/anti-AD`。
3. **CN Guard**：代理规则生成前会拿中国直连域名做冲突过滤；国内域名保护优先于“规则数量看起来很多”。
4. **自动更新**：每天北京时间 02:23 自动拉取上游最新提交，生成 `release` 分支。
5. **失败保护**：关键规则低于最低数量、关键测试域名缺失、规则数量异常骤降时，Actions 直接失败，不覆盖上一版可用规则。
6. **插件不重复造轮子**：插件部分沿用可莉等成熟 Loon 插件生态，本项目重点维护规则、策略与自动化。

## 当前规则分类

```text
rules/
├── AI/               # AI / OpenAI / Claude / Gemini / Copilot
├── Social/           # Telegram / Discord / Twitter / Facebook / Instagram
├── Streaming/        # YouTube / Netflix / Disney / Spotify / TikTok
├── Developer/        # GitHub / Docker / Cloudflare
├── Vendor/           # Google / Microsoft / Apple
├── Game/             # Steam / Epic / PlayStation / Xbox / Nintendo
├── China/            # Direct / ChinaIP
├── Proxy/            # Global
├── Ads/              # Reject
└── Basic/            # LAN
```

这只是第一版骨架，后续会继续向 4LESS 的细粒度分类补齐更多 AI、流媒体、国内应用、游戏、下载、金融、云服务、测速和特殊服务。

## 上游与构建方式

`sources/sources.json` 是唯一规则源清单。Loon 不直接请求十几个第三方规则地址，而是在 GitHub Runner 中自动拉取上游：

```text
blackmatrix7 / fmz200 / Loyalsoldier / dnsmasq-china-list / anti-AD
                              ↓
                   浅克隆 + sparse checkout
                              ↓
               统一解析 Loon / Surge / dnsmasq
                              ↓
                    规范化 + 去重
                              ↓
                      CN Guard
                              ↓
                   手工 override
                              ↓
             域名测试 + 数量阈值 + 骤降检测
                              ↓
          release/rules + 三套 Loon 配置
```

每次构建会在 `build/report.json` 保存上游 commit SHA、各规则集条目数以及 CN Guard 移除数量，方便定位是哪一个上游导致变化。

## 手工纠错

遇到上游误判时不需要 fork 上游：

- `override/direct.list`：强制直连，并进入 CN Guard 保护集合。
- `override/proxy.list`：强制代理，在 CN Guard 完成后追加。
- `override/reject.list`：强制拦截。

格式使用 Loon 标准规则，例如：

```text
DOMAIN-SUFFIX,example.com
DOMAIN,api.example.com
IP-CIDR,1.2.3.0/24,no-resolve
```

## 本地构建

需要 Python 3.10+ 和 Git：

```bash
python scripts/build.py --refresh
```

生成内容位于 `rules/`、`config/`、`build/report.json`。这些目录由 Actions 发布到 `release`，不提交到 `main`。

## 国内访问

```text
# 默认 CDN
https://cdn.jsdelivr.net/gh/pickarm/loon@release/...

# GitHub Raw
https://raw.githubusercontent.com/pickarm/loon/release/...

# GitHub Proxy 备用
https://githubproxy.cc/https://raw.githubusercontent.com/pickarm/loon/release/...
https://ghfast.top/https://raw.githubusercontent.com/pickarm/loon/release/...
```

公共反代属于第三方服务，不作为唯一依赖。

## 上游项目

感谢以下项目提供公开规则数据与 Loon 生态资源：

- `blackmatrix7/ios_rule_script`
- `fmz200/wool_scripts`
- `Loyalsoldier/surge-rules`
- `felixonmars/dnsmasq-china-list`
- `privacy-protection-tools/anti-AD`
- 可莉 Loon 插件资源

生成规则仍受各上游项目自身许可与版权约束。本仓库不会把用户私人订阅或证书内容写入公共文件。

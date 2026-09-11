# Loon Rules

面向中国大陆网络环境的 **Loon 配置 + 多源聚合规则库**。目标不是简单搬运某一个规则仓库，而是把多个高质量上游统一解析、去重、校验，并通过 CN Guard 尽量避免国内域名误走代理。

当前 V3 已拆分为 **62 个细粒度规则集**；规则可以继续细分，但生成到 Loon 的用户可见策略组刻意保持精简，并与现有 4LESS / ACL4SSR 使用习惯保持一致。实际规则总量、各分类条目数、上游 commit 与 CN Guard 移除数量以 `release/build/report.json` 为准。

## 🚀 直接使用

GitHub Actions 会把可使用的配置与规则发布到 `release` 分支。

| 版本 | 推荐场景 | 配置地址 |
|---|---|---|
| 🇨🇳 **Loon-CN.conf** | 中国大陆，默认推荐 | `https://cdn.jsdelivr.net/gh/pickarm/loon@release/config/Loon-CN.conf` |
| 🌐 **Loon.conf** | GitHub Raw 可直连 | `https://raw.githubusercontent.com/pickarm/loon/release/config/Loon.conf` |
| 🚀 **Loon-Proxy.conf** | GitHub Raw 访问不稳定时 | `https://githubproxy.cc/https://raw.githubusercontent.com/pickarm/loon/release/config/Loon-Proxy.conf` |

`Loon-CN.conf` 不只是把规则地址换成 jsDelivr：配置中的 Sub-Store parser、策略图标等 GitHub Raw 依赖也会一起重写为 jsDelivr。`Loon-Proxy.conf` 则统一改写为 `githubproxy.cc`。

第三方 GitHub 代理可能变化，因此 **默认优先使用 jsDelivr**；`githubproxy.cc` 作为备用，`ghfast.top` 可作为手工替换的第二备用。

> 公共配置不会保存任何私人订阅 URL、MITM CA、证书或密码。导入配置后，请在 Loon 中添加自己的节点订阅。

## 设计原则

1. **规则细、策略少**：规则文件持续细分，Loon 策略统一折叠到少量 4LESS 风格业务组，避免“一个规则集一个策略组”。
2. **多源聚合**：优先使用 `blackmatrix7/ios_rule_script`、`fmz200/wool_scripts`、`Loyalsoldier/surge-rules`、`felixonmars/dnsmasq-china-list`、`privacy-protection-tools/anti-AD`。
3. **CN Guard**：代理规则生成前使用国内直连集合做域名冲突过滤；国内域名保护优先于“规则数量看起来很多”。
4. **自动更新**：每天北京时间 02:23 自动拉取上游最新内容并生成 `release` 分支。
5. **失败保护**：关键规则低于最低数量、关键测试域名缺失、规则数量异常骤降时，Actions 直接失败，不覆盖上一版可用规则。
6. **策略组防膨胀**：渲染器维护 4LESS 策略白名单；新增源策略若没有明确映射到现有组，构建直接失败。
7. **可扩展目录**：基础目录在 `sources/sources.json`，增量版本放在 `sources/extensions/*.json`；构建前自动合并，并把细规则插在 China/Global 宽泛规则之前。
8. **可追溯**：记录上游 HEAD SHA、实际使用文件的 SHA256、每个规则集条目数和 CN Guard 移除数量。
9. **插件不重复造轮子**：插件部分沿用可莉等成熟 Loon 插件生态，本项目重点维护规则、策略与自动化。

## 当前规则分类

```text
rules/
├── AI/               # OpenAI / AI / Claude / Gemini / Copilot
├── Social/           # Telegram / Discord / Twitter / Facebook / Instagram / Reddit / WhatsApp
├── Streaming/        # YouTube / Netflix / Disney / Spotify / TikTok / Twitch / Prime Video / HBO / Hulu / Bahamut / Emby
├── Developer/        # GitHub / GitLab / Docker / Cloudflare
├── Storage/          # OneDrive / Dropbox / Google Drive
├── Vendor/           # Google / Google FCM / Microsoft / Bing / Apple
├── Finance/          # PayPal / Binance / OKX
├── Game/             # Steam / SteamCN / Epic / PlayStation / Xbox / Nintendo / Blizzard / EA / Riot / Ubisoft
├── Download/         # Download / PrivateTracker
├── Utility/          # Speedtest
├── ChinaApp/         # 抖音 / 小红书 / 快手 / 王者荣耀 / Soul / BiliBili
├── China/            # Direct / ChinaIP
├── Proxy/            # Global
├── Ads/              # Reject
└── Basic/            # LAN
```

## 4LESS 风格策略组

62 个规则集不会生成 62 个策略组，而是按用途合并：

| 规则类型 | Loon 策略组 |
|---|---|
| OpenAI / AI / Claude / Gemini / Copilot | `💬 Ai平台` |
| Telegram | `📲 电报消息` |
| YouTube | `📹 油管视频` |
| Netflix | `🎥 奈飞视频` |
| Disney / Spotify / TikTok / Twitch / Prime Video / HBO / Hulu / Bahamut / Emby | `🌍 国外媒体` |
| Microsoft / Bing / OneDrive | `Ⓜ️ 微软服务` |
| Apple | `🍎 苹果服务` |
| Steam / Epic / PlayStation / Xbox / Nintendo / Blizzard / EA / Riot / Ubisoft | `🎮 游戏平台` |
| Download / PT / SteamCN / BiliBili / 国内 App / China / LAN | `🎯 全球直连` |
| 广告规则 | `🛑 广告拦截` |
| 其他社交 / 开发 / Google / FCM / Google Drive / Dropbox / 金融 / Speedtest / Global Proxy | `🚀 节点选择` |
| 未匹配流量 | `🐟 漏网之鱼` |

节点层保持与 4LESS 接近的结构：`🚀 节点选择`、`🚀 手动切换`、`♻️ 自动选择`，再配香港、台湾、新加坡、日本、美国、韩国六个地区测速组以及奈飞节点筛选。这样规则覆盖可以继续增长，但日常操作界面不会随着规则数量一起膨胀。

## 上游与构建方式

基础规则源定义在 `sources/sources.json`，版本增量放在 `sources/extensions/*.json`；对应语义测试可以放 `tests/extensions/*.json`。`scripts/prepare_catalog.py` 在构建前完成去重与合并，并保证新增细规则位于 China/Global 宽泛规则之前。

构建器只下载当前规则集真正使用到的 Raw 文件，并通过 `git ls-remote` 记录对应上游 HEAD：

```text
sources.json + sources/extensions/*.json
                    ↓
           prepare_catalog.py
                    ↓
blackmatrix7 / fmz200 / Loyalsoldier / dnsmasq-china-list / anti-AD
                    ↓
       并发按需下载 Raw + 记录 upstream HEAD
                    ↓
         统一解析 Loon / Surge / dnsmasq
                    ↓
              规范化 + 去重
                    ↓
        国内保护集合 + CN Guard
                    ↓
             手工 override
                    ↓
语义测试 + 数量阈值 + 骤降检测 + 4LESS 策略白名单
                    ↓
    release/rules + 三套 Loon 配置 + report
```

每次构建会在 `build/report.json` 保存上游 HEAD commit SHA、实际使用源文件 SHA256、每个规则集最终条目数、CN Guard 移除数量和全部规则总量。

## 自动化

- **Pull Request**：只运行 Validate，真实拉取上游、合并扩展目录、构建全部规则并执行校验，不发布。
- **main / 定时任务**：构建通过后才更新 `release`。
- **并发保护**：同类旧任务会被新任务淘汰，避免旧构建阻塞最新规则发布。
- **骤降保护**：已有较大规则集若单次下降超过阈值，拒绝覆盖上一版。
- **策略白名单**：Remote Rule 引用的策略必须存在于 4LESS 风格白名单和模板中，否则拒绝渲染。

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

需要 Python 3.10+ 和 Git。在干净工作树中运行：

```bash
python scripts/prepare_catalog.py
python scripts/build.py --refresh
```

`prepare_catalog.py` 会在本地工作树临时把扩展目录合并进基础 JSON；构建完成后如需恢复仓库文件，可执行：

```bash
git restore -- sources/sources.json tests/expectations.json
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

生成规则仍受各上游项目自身许可与版权约束。本仓库不会把用户私人订阅、证书或口令内容写入公共文件。

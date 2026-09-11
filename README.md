# Loon Rules

面向中国大陆网络环境的 **Loon 配置 + 多源聚合规则库**。目标不是简单搬运某一个规则仓库，而是把多个高质量上游统一解析、去重、校验，并通过 CN Guard 尽量避免国内域名误走代理。

当前 V2 已拆分为 **52 个细粒度规则集**；实际规则总量、各分类条目数、上游 commit 与 CN Guard 移除数量以 `release/build/report.json` 为准。

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

1. **细粒度分类**：按 4LESS 一类的思路拆分 AI、社交、流媒体、开发、云存储、厂商、金融、游戏、国内应用、中国直连和国外代理等业务类别。
2. **多源聚合**：优先使用 `blackmatrix7/ios_rule_script`、`fmz200/wool_scripts`、`Loyalsoldier/surge-rules`、`felixonmars/dnsmasq-china-list`、`privacy-protection-tools/anti-AD`。
3. **CN Guard**：代理规则生成前使用国内直连集合做域名冲突过滤；国内域名保护优先于“规则数量看起来很多”。
4. **自动更新**：每天北京时间 02:23 自动拉取上游最新内容并生成 `release` 分支。
5. **失败保护**：关键规则低于最低数量、关键测试域名缺失、规则数量异常骤降时，Actions 直接失败，不覆盖上一版可用规则。
6. **可追溯**：记录上游 HEAD SHA、实际使用文件的 SHA256、每个规则集条目数和 CN Guard 移除数量。
7. **插件不重复造轮子**：插件部分沿用可莉等成熟 Loon 插件生态，本项目重点维护规则、策略与自动化。

## 当前规则分类

```text
rules/
├── AI/               # OpenAI / AI / Claude / Gemini / Copilot
├── Social/           # Telegram / Discord / Twitter / Facebook / Instagram / Reddit / WhatsApp
├── Streaming/        # YouTube / Netflix / Disney / Spotify / TikTok / Twitch / Prime Video / HBO / Hulu
├── Developer/        # GitHub / GitLab / Docker / Cloudflare
├── Storage/          # OneDrive / Dropbox
├── Vendor/           # Google / Microsoft / Apple
├── Finance/          # PayPal / Binance / OKX
├── Game/             # Steam / Epic / PlayStation / Xbox / Nintendo / Blizzard / EA / Riot / Ubisoft
├── ChinaApp/         # 抖音 / 小红书 / 快手 / 王者荣耀 / Soul（DIRECT）
├── China/            # Direct / ChinaIP
├── Proxy/            # Global
├── Ads/              # Reject
└── Basic/            # LAN
```

### 策略上的几个特殊处理

- **国内 App**：独立生成规则并强制 `DIRECT`，同时加入 CN Guard 保护集合。
- **金融支付**：`💳 金融支付` 默认 `DIRECT`，代理只提供手动地区策略，不使用测速组自动漂移出口 IP。
- **云存储**：`☁️ 云存储` 默认可直连，也可手动切换到代理。
- **游戏**：保留 `DIRECT`、游戏节点和地区节点选择，避免把所有游戏下载/联机流量强制塞进单一代理。

## 上游与构建方式

`sources/sources.json` 是唯一规则源清单。构建器不会再 clone 体积巨大的完整规则仓库，而是只下载当前规则集真正使用到的 Raw 文件，并通过 `git ls-remote` 记录对应上游 HEAD：

```text
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
      关键域名语义测试 + 数量阈值 + 骤降检测
                              ↓
          release/rules + 三套 Loon 配置 + report
```

下载使用有限超时和并发预取；某个大仓库不会因为自身 Git 历史体积拖慢整个日更流程。

每次构建会在 `build/report.json` 保存：

- 上游 HEAD commit SHA
- 实际使用源文件的 SHA256
- 每个规则集最终条目数
- 每个规则集被 CN Guard 移除的条目数
- 全部规则总量

## 自动化

- **Pull Request**：只运行 Validate，真实拉取上游、构建全部规则并执行校验，不发布。
- **main / 定时任务**：构建通过后才更新 `release`。
- **并发保护**：同类旧任务会被新任务淘汰，避免旧构建阻塞最新规则发布。
- **骤降保护**：已有较大规则集若单次下降超过阈值，拒绝覆盖上一版。

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

生成规则仍受各上游项目自身许可与版权约束。本仓库不会把用户私人订阅、证书或口令内容写入公共文件。

# Loon Rules

面向中国大陆网络环境的 **Loon 配置 + 多源聚合规则库**。规则数据来自多个成熟上游，经统一解析、去重、CN Guard 与语义测试后发布到 `release` 分支。

当前生成 **61 个细粒度规则集**。规则可以继续增加，但 Loon 用户可见策略保持精简：**规则细、组少、业务组里直接选具体节点**。

## 🚀 直接使用

| 版本 | 推荐场景 | 配置地址 |
|---|---|---|
| 🇨🇳 **Loon-CN.conf** | 中国大陆，默认推荐 | `https://cdn.jsdelivr.net/gh/pickarm/loon@release/config/Loon-CN.conf` |
| 🌐 **Loon.conf** | GitHub Raw 可直连 | `https://raw.githubusercontent.com/pickarm/loon/release/config/Loon.conf` |
| 🚀 **Loon-Proxy.conf** | GitHub Raw 不稳定时 | `https://githubproxy.cc/https://raw.githubusercontent.com/pickarm/loon/release/config/Loon-Proxy.conf` |

`Loon-CN.conf` 会同时把规则、Sub-Store parser、策略图标等 GitHub Raw 依赖改写为 jsDelivr。

> 公共配置不会保存私人订阅 URL、MITM CA、证书或密码。导入后请在 Loon 中添加自己的节点订阅。

## 策略结构

### 1. 发布配置只保留 6 个可见策略组

```text
♻️ 全局优选
🌐 国外网站
🤖 AI平台
📲 电报消息
🎬 流媒体
💳 金融平台
```

不再显示：

```text
香港手动策略 / 香港时延优选
台湾手动策略 / 台湾时延优选
日本手动策略 / 日本时延优选
……
兜底后备策略
微软服务
苹果服务
游戏平台
YouTube / Netflix / 国外媒体的独立策略组
```

其中 YouTube、Netflix 和其他国外媒体统一进入 `🎬 流媒体`；Microsoft、Apple、游戏规则默认直接 `DIRECT`，因此不再占用可见策略卡片。

### 2. 每个需要代理的业务组都可以直接手选明细节点

所有代理业务组都引用同一个 `全球节点` Remote Filter：

```text
🤖 AI平台
├── ♻️ 全局优选
├── 实际节点 A
├── 实际节点 B
├── 实际节点 C
└── DIRECT
```

`🌐 国外网站 / 📲 电报消息 / 🎬 流媒体 / 💳 金融平台` 同样如此。

### 3. 只有一个自动优选

```text
♻️ 全局优选 = url-test,全球节点,...
```

不会再生成任何国家/地区专属 `url-test`，所以不会出现没有节点却显示 `N/A / Failed` 的国家策略组。

### 4. 国家目录保留，但不渲染到 Loon

仓库仍保留 `sources/countries.json`，包含完整 ISO 3166-1 国家/地区目录与常用中文/城市别名，便于以后做节点分类或订阅预处理。

**发布到 Loon 的配置不会把这些国家逐个生成 Remote Filter。**

最终 `[Remote Filter]` 只有：

```text
全球节点
```

因此某个国家没有节点时，配置里根本没有对应的国家对象，也就不会显示空组。

## 规则映射

| 规则类型 | 输出策略 |
|---|---|
| OpenAI / Claude / Gemini / Copilot / AI | `🤖 AI平台` |
| Telegram | `📲 电报消息` |
| YouTube / Netflix / Disney / Spotify / TikTok / Twitch / Prime Video / HBO / Hulu / Bahamut / Emby | `🎬 流媒体` |
| PayPal / Binance / OKX | `💳 金融平台` |
| Microsoft / Bing / OneDrive / Apple / 游戏平台 | `DIRECT` |
| 其他海外社交 / GitHub / GitLab / Docker / Cloudflare / Google / Dropbox / Speedtest / Global Proxy | `🌐 国外网站` |
| 国内 App / China / LAN / Download / PT / SteamCN / BiliBili | `DIRECT` |

发布配置不再写入显式 `FINAL` 规则。只有命中现有本地/远程规则的流量才会被这些策略映射处理。

## 广告规则

**不生成独立广告规则集，也没有广告拦截策略组。**

Ads / REJECT 会在构建目录阶段排除。Loon 插件区与规则系统相互独立，插件可自行启停。

## 当前规则目录

```text
rules/
├── AI/
├── Social/
├── Streaming/
├── Developer/
├── Storage/
├── Vendor/
├── Finance/
├── Game/
├── Download/
├── Utility/
├── ChinaApp/
├── China/
├── Proxy/
└── Basic/
```

## 数据源

主要使用：

- `blackmatrix7/ios_rule_script`
- `fmz200/wool_scripts`
- `Loyalsoldier/surge-rules`
- `felixonmars/dnsmasq-china-list`
- 可莉 Loon 插件资源

基础目录在 `sources/sources.json`，增量目录放在 `sources/extensions/*.json`。构建前 `scripts/prepare_catalog.py` 会合并扩展规则、排除 Ads / REJECT、清理不再使用的上游，并保证细规则优先于 China / Global 宽泛规则。

## CN Guard

国内直连规则和 `cn_protect` 规则形成保护集合。海外规则发布前与该集合做冲突过滤，尽量避免国内域名误送入代理策略。

## 自动化

- Pull Request：真实拉取上游并完整 Validate，不发布。
- main / 定时任务：校验通过后更新 `release`。
- 每天北京时间 02:23 自动更新。
- 大规则集异常骤降会阻止发布。
- 关键域名有语义测试。
- `AND / OR / NOT` 逻辑规则会原样保留；发现未知规则类型时构建直接失败，不再静默丢规则。
- ChatGPT 的 Azure WebPubSub / Azure Front Door 动态后端规则有独立语义校验。
- 渲染器强制发布配置只能存在 6 个可见策略组、1 个 `url-test` 和 1 个 `全球节点` Remote Filter，并禁止显式 `FINAL`；任何地区手动/地区时延策略或空国家 Filter 都会让构建失败。

## 手工纠错

- `override/direct.list`：强制直连，并进入 CN Guard 保护集合。
- `override/proxy.list`：强制代理，在 CN Guard 完成后追加到 Global Proxy。

格式使用 Loon 标准规则：

```text
DOMAIN-SUFFIX,example.com
DOMAIN,api.example.com
IP-CIDR,1.2.3.0/24,no-resolve
```

## 本地构建

需要 Python 3.10+ 和 Git：

```bash
python scripts/prepare_catalog.py
python scripts/build.py --refresh
```

生成内容位于 `rules/`、`config/` 和 `build/report.json`。

生成规则仍受各上游项目自身许可与版权约束。本仓库不会把用户私人订阅、证书或口令写入公共文件。

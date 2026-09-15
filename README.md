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

### 1. 地区只做 Filter，不做二级策略组

节点通过 `[Remote Filter]` 按名称分为：

- 香港
- 台湾
- 日本
- 韩国
- 新加坡
- 美国
- 游戏节点
- 全球节点

**不再生成**：

```text
香港手动策略
香港时延优选
美国手动策略
美国时延优选
...
```

业务 `select` 直接引用地区 Filter，因此点进 `AI平台 / Telegram / YouTube / Netflix / 金融平台` 后看到的是 **具体节点名**，不是“地区优选组”。

某地区没有节点时，该 Filter 贡献 0 个节点，自然不会产生一个空的地区二级策略项，不再需要额外运行时守卫脚本。

### 2. 可见业务组保持精简

只保留真正有必要让用户单独指定出口的组：

```text
🤖 AI平台
📲 电报消息
📹 油管视频
🎥 奈飞视频
🌍 国外媒体
Ⓜ️ 微软服务
🍎 苹果服务
🎮 游戏平台
💳 金融平台
兜底后备策略
```

金融平台单独承载：

```text
PayPal / Binance / OKX
```

不会再拆成多个金融子组。

普通海外社交、GitHub/GitLab、Docker、Cloudflare、Google、Dropbox、Speedtest 以及 Global Proxy 等规则仍然保持细粒度，但 **直接交给 `兜底后备策略`**，不再额外占一个可见策略组。

### 3. 业务组直接选节点

例如 `🤖 AI平台` 直接从以下 Filter 展开具体节点：

```text
美国节点
新加坡节点
日本节点
香港节点
台湾节点
韩国节点
兜底后备策略
DIRECT
```

其中 `美国节点` 等不会作为一个新的策略卡片出现，而是提供其匹配到的实际代理节点。

### 4. 默认兜底

```text
兜底后备策略 = fallback,
  香港节点,
  台湾节点,
  日本节点,
  新加坡节点,
  美国节点,
  韩国节点,
  全球节点,
  DIRECT
```

普通未匹配流量直接：

```text
FINAL,兜底后备策略
```

## 规则映射

| 规则类型 | 输出策略 |
|---|---|
| OpenAI / Claude / Gemini / Copilot / AI | `🤖 AI平台` |
| Telegram | `📲 电报消息` |
| YouTube | `📹 油管视频` |
| Netflix | `🎥 奈飞视频` |
| Disney / Spotify / TikTok / Twitch / Prime Video / HBO / Hulu / Bahamut / Emby | `🌍 国外媒体` |
| Microsoft / Bing / OneDrive | `Ⓜ️ 微软服务` |
| Apple | `🍎 苹果服务` |
| Steam / Epic / PlayStation / Xbox / Nintendo / Blizzard / EA / Riot / Ubisoft | `🎮 游戏平台` |
| PayPal / Binance / OKX | `💳 金融平台` |
| 其他海外社交 / 开发 / Google / Dropbox / Speedtest / Global Proxy | `兜底后备策略` |
| 国内 App / China / LAN / Download / PT / SteamCN / BiliBili | `DIRECT` |

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
- 渲染器强制业务组直接引用 Remote Filter 节点集合，并禁止旧的“地区手动策略 / 地区时延优选 / 节点选择 / 广告拦截 / 漏网之鱼”等中间层重新出现。

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

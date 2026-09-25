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

### 1. 只保留一个全局自动优选

不再为香港、台湾、日本、新加坡、美国等地区分别生成 `url-test`。

现在只保留：

```text
♻️ 全局优选 = url-test,全球节点,...
```

因此不会再出现：

```text
香港时延优选
台湾时延优选
日本时延优选
美国时延优选
...
```

也不会因为某个地区暂时没有节点而出现一排 `Failed` 的空策略组。

### 2. 每个业务策略都可以直接手动选明细节点

所有业务 `select` 都直接引用 `全球节点` 这个 Remote Filter。Loon 会把该 Filter 匹配到的实际节点展开到策略组里，因此点进业务策略后可以直接选择具体节点，而不是只能继续进入地区组。

例如：

```text
🤖 AI平台
├── ♻️ 全局优选
├── 🇺🇸 US-01
├── 🇺🇸 US-02
├── 🇯🇵 JP-01
├── 🇸🇬 SG-01
└── DIRECT
```

当前可见业务组：

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
♻️ 全局优选
```

其中 `兜底后备策略` 也改为 `select`，默认提供：

```text
♻️ 全局优选
全部实际节点
DIRECT
```

### 3. 国家/地区只负责识别，不再变成策略卡片

`[Remote Filter]` 会从 `sources/countries.json` 生成完整国家/地区筛选目录：

- 覆盖 ISO 3166-1 的 249 个国家/地区。
- 额外加入 `XK / Kosovo`。
- 常用地区增加中文名、英文名、城市名和常见缩写。
- 其他地区至少支持国旗、ISO alpha-2、alpha-3 和英文国名识别。

例如加拿大、澳大利亚、德国、英国、法国、荷兰等以后新增节点时，无需再改模板即可自动识别。

这些国家 Filter **不会直接写进业务策略组**，所以没有节点的国家不会变成空的可见策略卡片。它们只用于节点分类和以后需要单独地区策略时复用。

### 4. 全球节点兜住未标准命名节点

业务策略最终都通过 `全球节点` 展开实际节点，所以即使某个机场节点名称没有国旗、ISO 代码或标准国家名，它仍然可以出现在手动选择列表里。

也就是说：

```text
国家识别成功  → 可分类
国家识别失败  → 仍可通过 全球节点 手动选择
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
- 渲染器强制只保留一个 `♻️ 全局优选`，业务组必须同时提供全局优选和 `全球节点` 明细选择，并禁止任何地区手动/地区时延策略重新出现。

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

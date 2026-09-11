# Loon Rules

面向中国大陆网络环境的 **Loon 配置 + 多源聚合规则库**。规则数据来自多个成熟上游，经统一解析、去重、CN Guard 与语义测试后发布到 `release` 分支。

当前生成 **61 个细粒度规则集**。规则可以继续增加，但用户实际操作的策略组保持精简：**先按地区组织节点，再由 AI / Telegram / YouTube / Netflix 等业务组直接选择地区策略**。

## 🚀 直接使用

| 版本 | 推荐场景 | 配置地址 |
|---|---|---|
| 🇨🇳 **Loon-CN.conf** | 中国大陆，默认推荐 | `https://cdn.jsdelivr.net/gh/pickarm/loon@release/config/Loon-CN.conf` |
| 🌐 **Loon.conf** | GitHub Raw 可直连 | `https://raw.githubusercontent.com/pickarm/loon/release/config/Loon.conf` |
| 🚀 **Loon-Proxy.conf** | GitHub Raw 不稳定时 | `https://githubproxy.cc/https://raw.githubusercontent.com/pickarm/loon/release/config/Loon-Proxy.conf` |

`Loon-CN.conf` 会同时把规则、Sub-Store parser、策略图标等 GitHub Raw 依赖改写为 jsDelivr。

> 公共配置不会保存私人订阅 URL、MITM CA、证书或密码。导入后请在 Loon 中添加自己的节点订阅。

## 策略结构

这套配置不再使用 `🚀 节点选择 / 🚀 手动切换 / ♻️ 自动选择 / 🐟 漏网之鱼 / 🛑 广告拦截` 这类中间策略组。

### 1. 地区节点层

节点先通过名称过滤到以下地区：

- 香港
- 台湾
- 日本
- 韩国
- 新加坡
- 美国
- 游戏节点
- 全球节点

每个主要地区同时提供两种策略：

```text
香港手动策略
香港时延优选

台湾手动策略
台湾时延优选

日本手动策略
日本时延优选

韩国手动策略
韩国时延优选

新加坡手动策略
新加坡时延优选

美国手动策略
美国时延优选
```

另外保留：

```text
游戏手动策略
全球手动策略
```

### 2. 默认兜底

```text
兜底后备策略
```

由各地区 `url-test` 结果组成。普通未匹配流量直接：

```text
FINAL,兜底后备策略
```

不再经过额外“节点选择”或“漏网之鱼”策略组。

### 3. 业务策略

当前只保留真正需要手工选择出口的业务组：

| 规则类型 | Loon 业务组 |
|---|---|
| OpenAI / Claude / Gemini / Copilot / AI | `🤖 AI平台` |
| Telegram | `📲 电报消息` |
| YouTube | `📹 油管视频` |
| Netflix | `🎥 奈飞视频` |
| Disney / Spotify / TikTok / Twitch / Prime Video / HBO / Hulu / Bahamut / Emby | `🌍 国外媒体` |
| Microsoft / Bing / OneDrive | `Ⓜ️ 微软服务` |
| Apple | `🍎 苹果服务` |
| Steam / Epic / PlayStation / Xbox / Nintendo / Blizzard / EA / Riot / Ubisoft | `🎮 游戏平台` |
| 其他海外社交 / 开发 / Google / Dropbox / 金融 / Speedtest / Global Proxy | `🌐 国外网站` |
| 国内 App / China / LAN / Download / PT / SteamCN / BiliBili | `DIRECT` |

例如 `🤖 AI平台` 中可以直接选择：

```text
兜底后备策略
美国时延优选 / 美国手动策略
新加坡时延优选 / 新加坡手动策略
日本时延优选 / 日本手动策略
香港时延优选 / 香港手动策略
台湾时延优选 / 台湾手动策略
韩国时延优选 / 韩国手动策略
全球手动策略
DIRECT
```

Telegram、YouTube、Netflix、国外媒体等也是同样思路，可以分别保存自己的地区选择。

微软、苹果和游戏平台默认把 `DIRECT` 放在第一项，但仍可以手工切到任意地区。

## 广告规则

**不生成独立广告规则集，也没有广告拦截策略组。**

构建目录会自动排除 `REJECT / Ads/*` 规则，因此不会再为了广告库下载、合并二十多万条规则。Loon 插件区与规则系统相互独立，插件可按个人需求自行启停。

## 当前规则目录

```text
rules/
├── AI/               # OpenAI / AI / Claude / Gemini / Copilot
├── Social/           # Telegram / Discord / Twitter / Facebook / Instagram / Reddit / WhatsApp
├── Streaming/        # YouTube / Netflix / Disney / Spotify / TikTok / Twitch / Prime / HBO / Hulu / Bahamut / Emby
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
└── Basic/            # LAN
```

## 数据源

主要使用：

- `blackmatrix7/ios_rule_script`
- `fmz200/wool_scripts`
- `Loyalsoldier/surge-rules`
- `felixonmars/dnsmasq-china-list`
- 可莉 Loon 插件资源

基础目录在 `sources/sources.json`，增量目录放在 `sources/extensions/*.json`。构建前 `scripts/prepare_catalog.py` 会：

1. 合并扩展规则；
2. 排除 Ads / REJECT；
3. 删除已经没有规则引用的上游；
4. 确保细规则排在 China / Global 宽泛规则之前。

## CN Guard

国内直连规则和标记为 `cn_protect` 的规则共同形成保护集合。海外规则在发布前与该集合做冲突过滤，尽量避免国内域名被错误送入代理策略。

## 自动化

- Pull Request：真实拉取上游并完整 Validate，不发布。
- main / 定时任务：校验通过后更新 `release`。
- 每天北京时间 02:23 自动更新。
- 大规则集异常骤降会阻止发布。
- 关键域名有语义测试。
- 渲染器检查所有业务规则必须映射到现有业务组。
- 渲染器同时禁止旧的“节点选择 / 广告拦截 / 漏网之鱼”等中间组重新混入模板。

## 手工纠错

- `override/direct.list`：强制直连，并进入 CN Guard 保护集合。
- `override/proxy.list`：强制代理，在 CN Guard 处理后追加到 Global Proxy。

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

构建完成后可恢复临时合并的目录文件：

```bash
git restore -- sources/sources.json tests/expectations.json
```

生成内容位于：

```text
rules/
config/
build/report.json
```

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

公共 GitHub 反代属于第三方服务，不作为唯一依赖。

生成规则仍受各上游项目自身许可与版权约束。本仓库不会把用户私人订阅、证书或口令写入公共文件。

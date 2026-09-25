# pickarm/loon generated config
# Variant: {{CONFIG_VARIANT}}
# Rules are generated from multiple upstream projects. Do not put private subscription URLs or MITM certificates in this public template.

[General]
ip-mode = v4-only
ipv6-vif = off
dns-server = system
sni-sniffing = true
disable-stun = true
# Most subscription nodes used with this profile only relay UDP. Disable UDP/443
# so HTTP/3/QUIC falls back to TCP, which is typically more stable for ChatGPT.
disable-udp-ports = 443
dns-reject-mode = LoopbackIP
domain-reject-mode = DNS
udp-fallback-mode = REJECT
wifi-access-http-port = 7222
wifi-access-socks5-port = 7221
allow-wifi-access = false
interface-mode = auto
test-timeout = 5
disconnect-on-policy-change = false
internet-test-url = http://connectivitycheck.platform.hicloud.com/generate_204
proxy-test-url = http://www.gstatic.com/generate_204
resource-parser = https://raw.githubusercontent.com/sub-store-org/Sub-Store/release/sub-store-parser.loon.min.js
skip-proxy = 192.168.0.0/16,10.0.0.0/8,172.16.0.0/12,localhost,*.local
bypass-tun = 10.0.0.0/8,100.64.0.0/10,127.0.0.0/8,169.254.0.0/16,172.16.0.0/12,192.0.0.0/24,192.0.2.0/24,192.88.99.0/24,192.168.0.0/16,198.51.100.0/24,203.0.113.0/24,224.0.0.0/4,255.255.255.255/32

[Proxy]

[Remote Proxy]
# 在 Loon 中添加你自己的订阅；公共模板不会保存私人订阅 URL。
# 对 UDP 仅做转发/中继的节点，建议保持 block-quic=true。
# 示例（不要直接使用）：sub = https://example.com/your-subscription,udp=true,block-quic=true,skip-cert-verify=false,enabled=true

[Remote Filter]
# 国家/地区筛选仅用于节点分类，不再生成地区手动/地区优选策略卡片。
# 目录覆盖 ISO 3166-1 国家/地区并额外包含 XK（Kosovo）；空筛选不会进入业务策略组。
{{COUNTRY_FILTERS}}

# 特殊分类
游戏节点 = NameRegex, FilterKey = "^(?=.*((?i)游戏|🎮|(\b(GAME)(\d+)?\b)))(?!.*((?i)回国|校园)).*$"
全球节点 = NameRegex, FilterKey = "^(?=.*(.))(?!.*((?i)群|邀请|返利|官网|客服|网址|订阅|流量|到期|机场|过期|已用|通知|国内|频道|教程|更新|作者|邮箱|(\b(USE|USED|TOTAL|EXPIRE|EMAIL|Panel|Channel|Author|Traffic)(\d+)?\b))).*$"

[Proxy Group]
# ---------------- 唯一自动优选 ----------------
# 只保留一个全局 url-test；不再按国家/地区生成时延优选组。
♻️ 全局优选 = url-test,全球节点,url = http://www.gstatic.com/generate_204,interval = 300,tolerance = 50

# ---------------- 默认兜底 ----------------
# select 直接引用全球节点 Filter，因此可以在 Loon 中手动选择任意明细节点。
兜底后备策略 = select,♻️ 全局优选,全球节点,DIRECT

# ---------------- 业务策略 ----------------
# 每个业务组都同时提供“全局优选”和全部实际节点；地区 Filter 不作为中间策略项出现。
🤖 AI平台 = select,♻️ 全局优选,全球节点,DIRECT
📲 电报消息 = select,♻️ 全局优选,全球节点,DIRECT
📹 油管视频 = select,♻️ 全局优选,全球节点,DIRECT
🎥 奈飞视频 = select,♻️ 全局优选,全球节点,DIRECT
🌍 国外媒体 = select,♻️ 全局优选,全球节点,DIRECT
Ⓜ️ 微软服务 = select,DIRECT,♻️ 全局优选,全球节点
🍎 苹果服务 = select,DIRECT,♻️ 全局优选,全球节点
🎮 游戏平台 = select,DIRECT,♻️ 全局优选,全球节点
💳 金融平台 = select,♻️ 全局优选,全球节点,DIRECT

[Rule]
GEOIP,CN,DIRECT
FINAL,兜底后备策略

[Remote Rule]
{{REMOTE_RULES}}

[Host]

[Rewrite]

[Script]

[Plugin]
# 插件生态沿用可莉；插件与规则策略相互独立，可在 Loon 中自行启停。
https://kelee.one/Tool/Loon/Lpx/Bilibili_remove_ads.lpx, enabled=true
https://kelee.one/Tool/Loon/Lpx/Amap_remove_ads.lpx, enabled=true
https://kelee.one/Tool/Loon/Lpx/AppleWeatherEnhancer.lpx, enabled=true
https://kelee.one/Tool/Loon/Lpx/Block_HTTPDNS.lpx, pin=true, enabled=true
https://kelee.one/Tool/Loon/Lpx/BlockAdvertisers.lpx, pin=true, enabled=true
https://kelee.one/Tool/Loon/Lpx/QuickSearch.lpx, enabled=true
https://kelee.one/Tool/Loon/Lpx/Prevent_DNS_Leaks.lpx, policy=兜底后备策略, enabled=true
https://kelee.one/Tool/Loon/Lpx/Node_detection_tool.lpx, enabled=true
https://kelee.one/Tool/Loon/Lpx/TestFlightRegionUnlock.lpx, policy=DIRECT, enabled=false
https://kelee.one/Tool/Loon/Lpx/BoxJs.lpx, policy=兜底后备策略, enabled=true
https://kelee.one/Tool/Loon/Lpx/Sub-Store.lpx, policy=兜底后备策略, enabled=true
https://kelee.one/Tool/Loon/Lpx/Script-Hub.lpx, policy=兜底后备策略, enabled=true

[Mitm]
# 公共模板故意不包含 CA、密码或私人证书。
skip-server-cert-verify = false

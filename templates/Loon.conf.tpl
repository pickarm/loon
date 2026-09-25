# pickarm/loon bootstrap config
# Variant: {{CONFIG_VARIANT}}
# IMPORTANT: this full config is for initial setup / rebuilding a profile only.
# After adding a private [Remote Proxy] subscription, DO NOT refresh/replace this whole
# remote config from GitHub: a full-config refresh can replace the local [Remote Proxy]
# section and remove your private node subscription.
# Ongoing updates should refresh node subscriptions, Remote Rule resources and plugins.
# Rules are generated from multiple upstream projects. Do not put private subscription URLs or MITM certificates in this public template.

[General]
ip-mode = v4-only
ipv6-vif = off
dns-server = system
sni-sniffing = true
# Allow application UDP to be relayed by proxy nodes. For VLESS + TCP + REALITY
# subscriptions, set udp=true so UDP is carried inside the VLESS TCP tunnel.
allow-udp-proxy = true
dns-reject-mode = LoopbackIP
domain-reject-mode = DNS
# Safety only: if a node is misconfigured and still reports no UDP capability,
# reject instead of leaking that UDP traffic directly.
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
# 私人区：首次导入后在 Loon 本地添加自己的节点订阅。
# 不要通过“更新整份远程配置”来更新本仓库，否则这一段会被公共模板覆盖为空。
# 日常只更新节点订阅 / Remote Rule / Plugin 资源。
# 本配置按 VLESS/TCP/REALITY 的 UDP-over-VLESS 使用方式设计：
# udp=true 会覆盖订阅节点默认的 UDP=false；block-quic=false 允许 QUIC、STUN、语音等 UDP 进入 VLESS 隧道。
# 示例（不要直接使用）：sub = https://example.com/your-subscription,udp=true,block-quic=false,skip-cert-verify=false,enabled=true

[Remote Filter]
# 发布配置只保留一个全局节点筛选。国家目录保留在仓库数据中，不渲染为空地区对象。
全球节点 = NameRegex, FilterKey = "^(?=.*(.))(?!.*((?i)群|邀请|返利|官网|客服|网址|订阅|流量|到期|机场|过期|已用|通知|国内|频道|教程|更新|作者|邮箱|(\b(USE|USED|TOTAL|EXPIRE|EMAIL|Panel|Channel|Author|Traffic)(\d+)?\b))).*$"

[Proxy Group]
# 只有一个自动测速组。
♻️ 全局优选 = url-test,全球节点,url = http://www.gstatic.com/generate_204,interval = 300,tolerance = 50

# 业务组全部可以直接展开 全球节点 里的明细节点进行手动选择。
🌐 国外网站 = select,♻️ 全局优选,全球节点,DIRECT
🤖 AI平台 = select,♻️ 全局优选,全球节点,DIRECT
📲 电报消息 = select,♻️ 全局优选,全球节点,DIRECT
🎬 流媒体 = select,♻️ 全局优选,全球节点,DIRECT
💳 金融平台 = select,♻️ 全局优选,全球节点,DIRECT

[Rule]
GEOIP,CN,DIRECT

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
https://kelee.one/Tool/Loon/Lpx/Prevent_DNS_Leaks.lpx, policy=🌐 国外网站, enabled=true
https://kelee.one/Tool/Loon/Lpx/Node_detection_tool.lpx, enabled=true
https://kelee.one/Tool/Loon/Lpx/TestFlightRegionUnlock.lpx, policy=DIRECT, enabled=false
https://kelee.one/Tool/Loon/Lpx/BoxJs.lpx, policy=🌐 国外网站, enabled=true
https://kelee.one/Tool/Loon/Lpx/Sub-Store.lpx, policy=🌐 国外网站, enabled=true
https://kelee.one/Tool/Loon/Lpx/Script-Hub.lpx, policy=🌐 国外网站, enabled=true

[Mitm]
# 公共模板故意不包含 CA、密码或私人证书。
skip-server-cert-verify = false

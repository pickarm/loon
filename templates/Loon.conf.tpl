# pickarm/loon generated config
# Variant: {{CONFIG_VARIANT}}
# Rules are generated from multiple upstream projects. Do not put private subscription URLs or MITM certificates in this public template.

[General]
ip-mode = v4-only
ipv6-vif = off
dns-server = system
sni-sniffing = true
disable-stun = true
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
# 示例（不要直接使用）：sub = https://example.com/your-subscription,udp=true,block-quic=true,skip-cert-verify=false,enabled=true

[Remote Filter]
香港节点 = NameRegex, FilterKey = "^(?=.*((?i)🇭🇰|香港|(\b(HK|HKG|Hong)(\d+)?\b)))(?!.*((?i)回国|校园|游戏|🎮|(\b(GAME)\b))).*$"
台湾节点 = NameRegex, FilterKey = "^(?=.*((?i)🇹🇼|台湾|(\b(TW|TWN|Tai|Taiwan)(\d+)?\b)))(?!.*((?i)回国|校园|游戏|🎮|(\b(GAME)\b))).*$"
日本节点 = NameRegex, FilterKey = "^(?=.*((?i)🇯🇵|日本|东京|大阪|(\b(JP|JPN|Japan)(\d+)?\b)))(?!.*((?i)回国|校园|游戏|🎮|(\b(GAME)\b))).*$"
韩国节点 = NameRegex, FilterKey = "^(?=.*((?i)🇰🇷|韩国|韓|首尔|(\b(KR|KOR|Korea)(\d+)?\b)))(?!.*((?i)回国|校园|游戏|🎮|(\b(GAME)\b))).*$"
新加坡节点 = NameRegex, FilterKey = "^(?=.*((?i)🇸🇬|新加坡|狮城|(\b(SG|SGP|Singapore)(\d+)?\b)))(?!.*((?i)回国|校园|游戏|🎮|(\b(GAME)\b))).*$"
美国节点 = NameRegex, FilterKey = "^(?=.*((?i)🇺🇸|美国|洛杉矶|圣何塞|西雅图|达拉斯|芝加哥|(\b(US|USA|United States)(\d+)?\b)))(?!.*((?i)回国|校园|游戏|🎮|(\b(GAME)\b))).*$"
游戏节点 = NameRegex, FilterKey = "^(?=.*((?i)游戏|🎮|(\b(GAME)(\d+)?\b)))(?!.*((?i)回国|校园)).*$"
全球节点 = NameRegex, FilterKey = "^(?=.*(.))(?!.*((?i)群|邀请|返利|官网|客服|网址|订阅|流量|到期|机场|过期|已用|通知|国内|频道|教程|更新|作者|邮箱|(\b(USE|USED|TOTAL|EXPIRE|EMAIL|Panel|Channel|Author|Traffic)(\d+)?\b))).*$"

[Proxy Group]
# ---------------- 地区手动策略 ----------------
香港手动策略 = select,香港节点,img-url = https://raw.githubusercontent.com/Orz-3/mini/master/Color/HK.png
台湾手动策略 = select,台湾节点,img-url = https://raw.githubusercontent.com/Orz-3/mini/master/Color/TW.png
日本手动策略 = select,日本节点,img-url = https://raw.githubusercontent.com/Orz-3/mini/master/Color/JP.png
韩国手动策略 = select,韩国节点,img-url = https://raw.githubusercontent.com/Orz-3/mini/master/Color/KR.png
新加坡手动策略 = select,新加坡节点,img-url = https://raw.githubusercontent.com/Orz-3/mini/master/Color/SG.png
美国手动策略 = select,美国节点,img-url = https://raw.githubusercontent.com/Orz-3/mini/master/Color/US.png
游戏手动策略 = select,游戏节点,img-url = https://raw.githubusercontent.com/Orz-3/mini/master/Color/GAME.png
全球手动策略 = select,全球节点,img-url = https://raw.githubusercontent.com/Orz-3/mini/master/Color/Global.png

# ---------------- 地区时延优选 ----------------
香港时延优选 = url-test,香港节点,interval = 300,tolerance = 50,img-url = https://raw.githubusercontent.com/Orz-3/mini/master/Color/HK.png
台湾时延优选 = url-test,台湾节点,interval = 300,tolerance = 50,img-url = https://raw.githubusercontent.com/Orz-3/mini/master/Color/TW.png
日本时延优选 = url-test,日本节点,interval = 300,tolerance = 50,img-url = https://raw.githubusercontent.com/Orz-3/mini/master/Color/JP.png
韩国时延优选 = url-test,韩国节点,interval = 300,tolerance = 50,img-url = https://raw.githubusercontent.com/Orz-3/mini/master/Color/KR.png
新加坡时延优选 = url-test,新加坡节点,interval = 300,tolerance = 50,img-url = https://raw.githubusercontent.com/Orz-3/mini/master/Color/SG.png
美国时延优选 = url-test,美国节点,interval = 300,tolerance = 100,img-url = https://raw.githubusercontent.com/Orz-3/mini/master/Color/US.png

# ---------------- 默认兜底 ----------------
# 默认优先香港；区域故障时依次切换。每个地区内部由 url-test 选择低延迟节点。
兜底后备策略 = fallback,香港时延优选,台湾时延优选,日本时延优选,韩国时延优选,新加坡时延优选,美国时延优选,interval = 300,max-timeout = 3000,img-url = https://github.com/shindgewongxj/WHATSINStash/raw/main/icon/fallback.png

# ---------------- 业务策略 ----------------
# 第一项即默认策略；你可以在 Loon 中为每一类业务单独选地区、自动优选或具体节点。
🤖 AI平台 = select,兜底后备策略,美国时延优选,美国手动策略,新加坡时延优选,新加坡手动策略,日本时延优选,日本手动策略,香港时延优选,香港手动策略,台湾时延优选,台湾手动策略,韩国时延优选,韩国手动策略,全球手动策略,DIRECT
📲 电报消息 = select,兜底后备策略,新加坡时延优选,新加坡手动策略,香港时延优选,香港手动策略,日本时延优选,日本手动策略,台湾时延优选,台湾手动策略,美国时延优选,美国手动策略,韩国时延优选,韩国手动策略,全球手动策略,DIRECT
📹 油管视频 = select,兜底后备策略,香港时延优选,香港手动策略,台湾时延优选,台湾手动策略,日本时延优选,日本手动策略,新加坡时延优选,新加坡手动策略,美国时延优选,美国手动策略,韩国时延优选,韩国手动策略,全球手动策略,DIRECT
🎥 奈飞视频 = select,兜底后备策略,香港时延优选,香港手动策略,台湾时延优选,台湾手动策略,日本时延优选,日本手动策略,新加坡时延优选,新加坡手动策略,美国时延优选,美国手动策略,韩国时延优选,韩国手动策略,全球手动策略,DIRECT
🌍 国外媒体 = select,兜底后备策略,香港时延优选,香港手动策略,台湾时延优选,台湾手动策略,日本时延优选,日本手动策略,新加坡时延优选,新加坡手动策略,美国时延优选,美国手动策略,韩国时延优选,韩国手动策略,全球手动策略,DIRECT
Ⓜ️ 微软服务 = select,DIRECT,兜底后备策略,香港时延优选,香港手动策略,台湾时延优选,台湾手动策略,日本时延优选,日本手动策略,新加坡时延优选,新加坡手动策略,美国时延优选,美国手动策略,韩国时延优选,韩国手动策略,全球手动策略
🍎 苹果服务 = select,DIRECT,兜底后备策略,香港时延优选,香港手动策略,台湾时延优选,台湾手动策略,日本时延优选,日本手动策略,新加坡时延优选,新加坡手动策略,美国时延优选,美国手动策略,韩国时延优选,韩国手动策略,全球手动策略
🎮 游戏平台 = select,DIRECT,游戏手动策略,兜底后备策略,香港时延优选,香港手动策略,台湾时延优选,台湾手动策略,日本时延优选,日本手动策略,新加坡时延优选,新加坡手动策略,美国时延优选,美国手动策略,韩国时延优选,韩国手动策略,全球手动策略
🌐 国外网站 = select,兜底后备策略,全球手动策略,香港时延优选,香港手动策略,台湾时延优选,台湾手动策略,日本时延优选,日本手动策略,新加坡时延优选,新加坡手动策略,美国时延优选,美国手动策略,韩国时延优选,韩国手动策略,DIRECT

[Rule]
GEOIP,CN,DIRECT
FINAL,兜底后备策略

[Remote Rule]
{{REMOTE_RULES}}

[Host]

[Rewrite]

[Script]
# Loon 无法在运行时删除策略组选项；此守卫会自动检测空地区，并把误选/失效地区回退到兜底。
network-changed script-path=https://raw.githubusercontent.com/pickarm/loon/release/runtime/region_guard.js,tag=地区节点可用性检查,timeout=10,enable=true
cron "*/10 * * * *" script-path=https://raw.githubusercontent.com/pickarm/loon/release/runtime/region_guard.js,tag=地区节点定时检查,timeout=10,enable=true

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

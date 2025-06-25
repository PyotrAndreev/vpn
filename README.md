connect to USA VPN:
sudo openvpn --config vpngate_vpn823672641.opengw.net_udp_1207.ovpn

# Sources:
notes: 
1. the could be dangerouse as I did research the risks so well. Strictly recommended use only https to visit websites as it has TLS cryptographic protocol
2. the web-sites could be banned in your country, you can visit it via proxy:
    - [spys.me](https://spys.me/proxy.txt)
    - [proxyium](https://proxyium.com)
3. Any source could be cheaked by hands, example:
- ping www.vpngate.net -- проверяет сетевую доступность сайта по IP-адресу через DNS (ICMP Echo request)
- dig www.vpngate.net -- проверяет, разрешается ли домен в IP
- curl -I https://www.vpngate.net -- посылает HTTP HEAD запрос: получает только заголовки, без тела страницы; DNS → TCP → TLS → HTTP

## Safty:
To try cheaking the safty IP source the [Scamalytics](https://scamalytics.com/) could be used  
Also try use TOR and masure the dellay in comparison with VPN

## Used:
- API: https://www.vpngate.net/api/iphone/
- [vpngate.net](www.vpngate.net) and [emailing](https://www.vpngate.net/en/mail.aspx) mirrors, some mirrors:
    - Mirror location: Ukraine
        - http://193.218.118.161:45583/en/
        - http://193.218.118.87:22225/en/
    - Mirror location: Japan
        - http://133.175.99.151:65021/en/
    - Mirror location: Viet Nam
        - http://222.254.18.58:48535/en/
    - Mirror location: Korea Republic of
        - http://210.100.229.165:54104/en/
    - Mirror location: Japan
        - http://KD113150098073.ppp-bb.dion.ne.jp:24486/en/

## Have not used:
- [vpnbook.com](https://www.vpnbook.com/freevpn)
- [geonode.com](https://geonode.com/free-proxy-list)
- [proxyscrape.com](https://proxyscrape.com/free-proxy-list)
- [free-proxy-list.net](https://free-proxy-list.net/)
- GitHub:
    - seems doesn't works [free-proxy-list](https://github.com/proxifly/free-proxy-list)
    - [PROXY-List](https://github.com/TheSpeedX/PROXY-List/blob/master/http.txt)
    - [copy-vpngate-by-a-person](https://github.com/fdciabdul/Vpngate-Scraper-API)
- more proxies with API: [here](https://chatgpt.com/share/6854328e-dd48-8012-9966-230d61378caf)

# Commands:
- curl https://ifconfig.co/json
- curl ifconfig.me
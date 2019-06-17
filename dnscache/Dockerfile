FROM alpine:edge

RUN apk update && apk --no-cache add dnsmasq

# prepare our revolf file
RUN echo -e "# CloudFlare\nnameserver 1.1.1.1\n# Google DNS\nnameserver 8.8.8.8\nnameserver 2001:4860:4860::8888\n# OpenDNS\n# nameserver 208.67.222.222\n# nameserver 208.67.220.220" > /etc/resolv.dnsmasq

# --no-daemon and --keep-in-foreground are similar
# but no-deamon has debug enabled (and thus starts with useful output)

ENTRYPOINT ["dnsmasq", \
			"--no-daemon", \
			"--user=root", \
			"--conf-file=/etc/dnsmasq.conf", \
			"--resolv-file=/etc/resolv.dnsmasq", \
			"--domain-needed", \
			"--bogus-priv", \
			"--no-hosts", \
			"--min-cache-ttl=86400", \
			"--cache-size=1000", \
			"--neg-ttl=3600", \
			"--no-poll"]

FROM alpine:edge
LABEL zimfarm=true
LABEL org.opencontainers.image.source https://github.com/openzim/zimfarm

RUN apk update && apk --no-cache add dnsmasq

RUN printf "# CloudFlare\nnameserver 1.1.1.1\n# Google DNS\nnameserver 8.8.8.8\n# OpenDNS\n# nameserver 208.67.222.222\n# nameserver 208.67.220.220" > /etc/resolv.dnsmasq.public
RUN ln -sf /etc/resolv.conf /etc/resolv.dnsmasq

COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

# --no-daemon and --keep-in-foreground are similar
# but no-deamon has debug enabled (and thus starts with useful output)

ENTRYPOINT ["entrypoint.sh"]

CMD ["dnsmasq", "--no-daemon", "--user=root", "--conf-file=/etc/dnsmasq.conf", "--resolv-file=/etc/resolv.dnsmasq", "--domain-needed", "--bogus-priv", "--no-hosts", "--cache-size=1500", "--neg-ttl=600", "--no-poll"]

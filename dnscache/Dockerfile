FROM alpine:edge

RUN apk update && apk --no-cache add dnsmasq

# --no-daemon and --keep-in-foreground are similar
# but no-deamon has debug enabled (and thus starts with useful output)

ENTRYPOINT ["dnsmasq", \
			"--no-daemon", \
			"--user=root", \
			"--conf-file=/etc/dnsmasq.conf", \
			"--domain-needed", \
			"--bogus-priv", \
			"--no-hosts", \
			"--min-cache-ttl=86400", \
			"--cache-size=1000", \
			"--neg-ttl=3600", \
			"--no-poll"]

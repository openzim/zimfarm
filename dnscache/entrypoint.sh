#!/bin/sh

if [ "$USE_PUBLIC_DNS" = "yes" ]; then
	echo "starting dnscache with Public DNS"
	ln -sf /etc/resolv.dnsmasq.public /etc/resolv.dnsmasq
else
	echo "starting dnscache with inherited DNS"
	ln -sf /etc/resolv.conf /etc/resolv.dnsmasq
fi

exec "$@"

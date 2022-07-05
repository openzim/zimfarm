FROM netdata/netdata:edge
LABEL zimfarm=true
LABEL org.opencontainers.image.source https://github.com/openzim/zimfarm

ENV DO_NOT_TRACK 1
ENV SCRAPER_CONTAINER localhost
ENV MONITORING_DEST monitoring.openzim.org:30099
ENV MONITORING_KEY 7DC0DDB8-8EAA-4391-AF5D-BE017EECF0EE

COPY netdata.conf /etc/netdata/netdata.conf
COPY python.d.conf /etc/netdata/python.d.conf
COPY go.d.conf /etc/netdata/go.d.conf
COPY node.d.conf /etc/netdata/node.d.conf
COPY apps_groups.conf /etc/netdata/apps_groups.conf

COPY entrypoint.sh /usr/local/bin/entrypoint
RUN chmod a+x /usr/local/bin/entrypoint

ENTRYPOINT ["entrypoint"]

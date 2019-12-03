FROM node:alpine as builder

RUN apk add yarn
WORKDIR /app
ADD package.json yarn.lock /app/
RUN yarn install
ADD . /app
RUN NODE_ENV=production yarn build

FROM library/nginx:mainline
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN { \
    echo "gzip on;" ; \
    echo "gzip_proxied any;" ; \
    echo "gzip_types text/plain text/css application/json application/x-javascript application/javascript text/xml application/xml application/rss+xml text/javascript image/svg+xml application/vnd.ms-fontobject application/x-font-ttf font/opentype application/atom+xml text/yaml;" ; \
} > /etc/nginx/conf.d/05gzip.conf

COPY --from=builder /app/dist /usr/share/nginx/html

ENV ZIMFARM_WEBAPI https://api.farm.openzim.org/v1

ENTRYPOINT ["entrypoint.sh"]
CMD ["nginx", "-g", "daemon off;"]

FROM node:24-alpine3.22 AS builder

RUN apk --no-cache add yarn
WORKDIR /app
COPY package.json yarn.lock /app/
RUN yarn install
COPY *.ts /app/
COPY *.json /app/
COPY *.html /app/
COPY public /app/public
COPY src /app/src
RUN NODE_ENV=production yarn build

FROM nginx:1.28-alpine3.21
LABEL zimfarm=true
LABEL org.opencontainers.image.source https://github.com/openzim/zimfarm

RUN apk --no-cache add python3

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx-default.conf /etc/nginx/conf.d/default.conf

ENV ZIMFARM_WEBAPI https://api.farm.openzim.org/v2
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]

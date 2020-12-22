FROM node:14-alpine as builder

RUN apk --no-cache add yarn
WORKDIR /app
COPY package.json yarn.lock /app/
RUN yarn install
COPY *.js /app/
COPY public /app/public
COPY src /app/src
RUN NODE_ENV=production yarn build

FROM library/nginx:mainline-alpine
LABEL zimfarm=true
LABEL org.opencontainers.image.source https://github.com/openzim/zimfarm

RUN apk --no-cache add python3

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx-default.conf /etc/nginx/conf.d/default.conf
COPY entrypoint.sh /usr/local/bin/entrypoint.sh

ENV ZIMFARM_WEBAPI https://api.farm.openzim.org/v1
EXPOSE 80

ENTRYPOINT ["entrypoint.sh"]
CMD ["nginx", "-g", "daemon off;"]

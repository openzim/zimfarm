FROM node:24-alpine AS builder

RUN apk --no-cache add yarn python3
WORKDIR /app
COPY package.json yarn.lock /app/
RUN yarn install && yarn cache clean
COPY *.ts /app/
COPY *.json /app/
COPY *.html /app/
COPY public /app/public
COPY src /app/src
CMD ["yarn", "dev", "--host", "0.0.0.0", "--port", "80"]

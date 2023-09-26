FROM node:14-alpine as builder

RUN apk --no-cache add yarn python3
WORKDIR /app
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
COPY package.json yarn.lock /app/
RUN yarn install && yarn cache clean
COPY *.js /app/
COPY public /app/public
COPY src /app/src
#CMD ["sleep", "infinity"]
ENV ENVIRON_PATH /app/public/environ.json
ENTRYPOINT [ "entrypoint.sh" ]
CMD ["yarn", "serve", "--host", "0.0.0.0", "--port", "80"]
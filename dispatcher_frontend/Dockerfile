FROM node:7.10

COPY . /app
WORKDIR /app
RUN npm install -g typescript@latest
RUN npm install
ENTRYPOINT npm start
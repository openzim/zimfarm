# Zimfarm backend

## How to run:

1. install `pwgen`
2. Set up SYSTEM_PASSWORD ``export SYSTEM_PASSWORD=`pwgen -Bs1 12` ``
3. Run using `docker-compose up --build -d`

Don't forget the second step, because if you do, the `SYSTEM_PASSWORD` will be empty string, and everyone could login using empty string.

## More about `SYSTEM_PASSWORD`

`SYSTEM_PASSWORD` is used internally by dispatcher to coordinate between multiple sub-systems. Specifically:

- backend: interact with RabbitMQ when processing a request
- monitor: listen to RabbitMQ events


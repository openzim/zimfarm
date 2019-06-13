DNS Cache
===

Simple `dnsmasq` container to cache DNS requests for openzim's scrappers.

## Usage

At the moment, this container has a static config of **caching every domain for 1day** (86400s).

``` sh
docker run --name dnscache openzim/dnscache
```

To use your DNS cache container, you need to run your scrapper(s) with the `--dns=` option. This option **only accepts** IPv4 and IPv6 values (no alias).

### Find out the IP of your `dnscache` container:

```sh
docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' dnscache
```

### Start a scrapper without knowing the IP

You can save the extra step and set the `--dns` to output of the previous command:

``` sh
docker run --dns=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' dnscache) openzim/mwoffliner
```

You can also retrieve the first IPaddress (what you want unless you're using networks) in python:

``` py
client.inspect_container("dnscache")["NetworkSettings"]["IPAddress"]
```

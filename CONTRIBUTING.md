# Contributing Guidelines

## Contributions

Before contributing, make sure you mention you'll be working on it in the associated ticket. Open a new ticket if there's none about it.

We have a very limited number of contributors so rules are quite limited:

- Submit your changes over a Pull Request
- Make sure all your python code is black formatted.
- Make sure Codefactor reports no issue.
- API code (backend) must be tested. Make sure your PR doesn't decrease code coverage.

## Local setup

Setting up the zimfarm locally is a bit complicated due to the number of moving parts.
The recommended way is to use a fully docker-based stack. See [dev](dev/README.md) folder for details on how to create offliners, offliner definitions, a test worker and
importing recipes into the database.

Depending on what you are working on, you don't need all the components and can use the
various [docker profiles](https://docs.docker.com/compose/how-tos/profiles/)
to select which component you need. For example, to run with the worker manager, you can
activate it via:

```sh
docker compose -p zimfarm --profile worker up --build -d
```

### receiver

Given the very nature of the receiver (an SSHD server), it is only tested through its container.

- Create placeholder folders

```sh
# get list of folders from http://download.kiwix.org/zim/
mkdir -p $(pwd)/{mnt,jail}/zim/{gutenberg,other,phet,psiram,stack_exchange,ted,vikidia,wikibooks,wikinews,wikipedia,wikiquote,wikisource,wikispecies,wikiversity,wikivoyage,wiktionary}
```

- Test your changes via:

```sh
docker build receiver -f receiver/Dockerfile -t receiver
# use a local IP that docker can reach so not 127.0.0.1
docker -v $(pwd)/jail:/jail -v $(pwd)/mnt:/mnt run -e ZIMFARM_WEBAPI="http://192.168.5.80/v1 receiver"
```

### worker

It is recommended to read the [workers README](./worker/README.md) to understand all the configuration variables available.

While it is possible to test the task-worker individually, we recommend to always test via a scheduled task using a manager, and always via docker.

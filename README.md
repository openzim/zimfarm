# ZIM Farm

[![Build Status](https://github.com/openzim/zimfarm/workflows/CI/badge.svg?query=branch%3Amaster)](https://github.com/openzim/zimfarm/actions?query=branch%3Amaster)
[![CodeFactor](https://www.codefactor.io/repository/github/openzim/zimfarm/badge)](https://www.codefactor.io/repository/github/openzim/zimfarm)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![codecov](https://codecov.io/gh/openzim/zimfarm/branch/master/graph/badge.svg)](https://codecov.io/gh/openzim/zimfarm)

The ZIM farm (zimfarm) is a semi-decentralised software solution to
build [ZIM files](http://www.openzim.org/) efficiently. This means scrapping Web content,
packaging them into a ZIM file and uploading the result to an online
ZIM files repository.

## How does it work?

The Zimfarm platform is a combination of different tools:

### dispatcher

The [dispatcher](http://hub.docker.com/r/openzim/zimfarm-dispatcher) is a central database and [API](https://api.farm.openzim.org/v1) that records *recipes* (metadata of ZIM to produce) and *tasks*. It includes a scheduler that decides when a ZIM file should be recreated (based on recipe) and a dispatcher that creates and assigns *tasks* to *workers*.

### frontend

The [frontend](https://hub.docker.com/r/openzim/zimfarm-ui), available at [farm.openzim.org](https://farm.openzim.org/) is a simple consumer of the API.

It is used to create, clone and edit recipes, but also to monitor the evolution of tasks and *workers*.

Anybody can use it in read-only mode.

### workers

Workers are always-running computers which gets assigned ZIM creation tasks by the dispatcher. If you are interested in providing us worker resources, please [read these instructions](https://github.com/openzim/zimfarm/blob/master/workers/README.md).

A worker is made of two software components:

#### worker-manager

The [manager](http://hub.docker.com/r/openzim/zimfarm-worker-manager) is responsible for declaring its available resources and configuration and receives tasks assigned to it by the dispatcher. It's a very-low resources container which job is to spawn `task-worker` ones.

#### task-worker

The [task-worker](http://hub.docker.com/r/openzim/zimfarm-task-worker) is responsible for running a specific task. It's also a very-low resources container but contrary to the manager, one is spawned for each task assigned to the worker (the manager defines the concurrency based on resources).

The task-worker's role is to start and monitor the scraper's container for the task and to spawn uploader containers for both created ZIM files and logs.

#### uploader

The [uploader](https://hub.docker.com/r/openzim/uploader) is instantiated by the task-worker to upload, individually, each created ZIM files, as well as the scraper's container log.

The uploader supports both SCP and SFTP. We are currently using SFTP for all uploads due to a slight speed gain.

Uploader is very fast and convenient (can watch and resumes files) but works only off files at the moment.

### receiver

The [receiver](https://hub.docker.com/r/openzim/zimfarm-receiver) is a jailed OpenSSH-server that receives scraper logs and ZIM files and pass the latter through a quarantine via the [zimcheck](https://github.com/openzim/zim-tools) tool which eventually either put them aside (invalid ZIM) or move those to the [public download server](download.kiwix.org/zim/).

### scrapers

Scrapers are the tools used to actually convert a *scraping request* (recorded in a Zimfarm recipe) into one or several ZIM files.

The most important one is the Mediawiki scraper, called [mwoffliner](https://hub.docker.com/r/openzim/mwoffliner/) but there are many of them for Stack-Exchange, Project Gutenberg, PhET and others.

Scrapers are not part of the Zimfarm. Those are completely independent projects for which the requirements to integrate into the Zimfarm are minimal:

* Works completely off a docker image
* Arguments should be set on the command line
* ZIM output folder should be settable via an argument

# How do I request a ZIM file?

ZIM file requests are handled on [zim-requests](https://github.com/openzim/zim-requests/issues/new/choose) repository.

If there's already a scraper for he website you want to convert to ZIM, someone with editor access to the Zimfarm will create the recipe and in a few days, a ZIM file should be available.

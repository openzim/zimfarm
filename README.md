# ZIM Farm

[![Build Status](https://github.com/openzim/zimfarm/workflows/CI/badge.svg?query=branch%3Amain)](https://github.com/openzim/zimfarm/actions?query=branch%3Amain)
[![CodeFactor](https://www.codefactor.io/repository/github/openzim/zimfarm/badge)](https://www.codefactor.io/repository/github/openzim/zimfarm)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![codecov](https://codecov.io/gh/openzim/zimfarm/branch/main/graph/badge.svg)](https://codecov.io/gh/openzim/zimfarm)

The ZIM farm (zimfarm) is a semi-decentralised software solution to
build [ZIM files](http://www.openzim.org/) efficiently. This means scraping Web contents,
packaging them into a ZIM file and uploading the result to an online
ZIM files repository.

## How does it work?

The Zimfarm platform is a combination of different tools:

### backend

The [backend](https://ghcr.io/openzim/zimfarm-backend) is a central database and [API](https://api.farm.openzim.org/v2) that records _recipes_ (metadata of ZIM to produce) and _tasks_. It decides when a ZIM file should be recreated (based on the recipe), creates and assigns _tasks_ to _workers_.

### frontend

The [frontend](https://ghcr.io/openzim/zimfarm-ui), available at [farm.openzim.org](https://farm.openzim.org/) is a simple consumer of the backend API.

It is used to create, clone and edit recipes, but also to monitor the evolution of tasks and _workers_.

Anybody can use it in read-only mode.

### workers

Workers are always-running computers which gets assigned ZIM creation tasks by the dispatcher. If you are interested in providing us worker resources, please [read these instructions](https://github.com/openzim/zimfarm/blob/main/workers/README.md).

A worker is made of two software components:

#### worker-manager

The [manager](https://ghcr.io/openzim/zimfarm-worker-manager) is responsible for declaring its available resources and configuration and receives tasks assigned to it by the dispatcher. It's a very-low resources container whose job is to spawn `task-worker` ones.

#### task-worker

The [task-worker](https://ghcr.io/openzim/zimfarm-task-worker) is responsible for running a specific task. It's also a very-low resources container but contrary to the manager, one is spawned for each task assigned to the worker (the manager defines the concurrency based on resources).

The task-worker's role is to start and monitor the scraper's container for the task and to spawn uploader containers for both created ZIM files and logs.

#### uploader

The [uploader](https://ghcr.io/openzim/zimfarm-uploader) is instantiated by the task-worker to upload, individually, each created ZIM files, as well as the scraper's container log.

The uploader supports both SCP and SFTP. We are currently using SFTP for all uploads due to a slight speed gain.

Uploader is very fast and convenient (can watch and resumes files) but works only off files at the moment.

#### dnscache

The [dnscache](https://ghcr.io/openzim/zimfarm-dnscache) is a dnsmasq server instantiated by the task-worker that ensures specific nameservers are used and caching of DNS results. This ensures that, if DNS becomes unstable, running tasks will not be affected

### receiver

The [receiver](https://ghcr.io/openzim/zimfarm-receiver) is a jailed OpenSSH-server that receives scraper logs and ZIM files and either put them aside (if file is not at root of source directory) or move them to the [public download server](https://download.kiwix.org/zim/).

### scrapers

Scrapers are the tools used to actually convert a _scraping request_ (recorded in a Zimfarm recipe) into one or several ZIM files.

The most important one is the Mediawiki scraper, called [mwoffliner](https://ghcr.io/openzim/mwoffliner/) but there are many of them for Stack-Exchange, Project Gutenberg, PhET and others.

Scrapers are not part of the Zimfarm. Those are completely independent projects for which the requirements to integrate into the Zimfarm are minimal:

- Works completely off a docker image
- Arguments should be set on the command line
- ZIM output folder should be settable via an argument

# How do I request a ZIM file?

ZIM file requests are handled on [zim-requests](https://github.com/openzim/zim-requests/issues/new/choose) repository.

If there's already a scraper for the website you want to convert to ZIM, someone with editor access to the Zimfarm will create the recipe and in a few days, a ZIM file should be available.

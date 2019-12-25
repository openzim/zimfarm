# ZIM Farm

[![Build Status](https://travis-ci.com/openzim/zimfarm.svg?branch=master)](https://travis-ci.com/openzim/zimfarm)
[![CodeFactor](https://www.codefactor.io/repository/github/openzim/zimfarm/badge)](https://www.codefactor.io/repository/github/openzim/zimfarm)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![codecov](https://codecov.io/gh/openzim/zimfarm/branch/master/graph/badge.svg)](https://codecov.io/gh/openzim/zimfarm)

The ZIM farm (zimfarm) is a half-decentralised software solution to
build [ZIM files](http://www.openzim.org/) efficiently. This means scrapping Web contents,
packaging them into a ZIM file and uploading the result to an online
ZIM files repository.

## Principle

The whole zimfarm system works as a task scheduler and is made of two components:

* The [**dispatcher**](http://hub.docker.com/r/openzim/zimfarm-dispatcher), the central node, which takes and dispatches zim file generation
  tasks. It is managed by the openZIM project admin and
  hosted somewhere on the Internet.

* The [**workers**](http://hub.docker.com/r/openzim/zimfarm-worker-manager), task executers, which are hosted by
  openZIM volunteers in different places around the world through Internet.

To get a new ZIM file the typical workflow is:

1. User submits a new task (to get a specific ZIM file made).
2. Dispatcher enqueues the task.
3. A worker pulls the task.
4. Worker generates the ZIM file and upload it.


Refer to [workers](https://github.com/openzim/zimfarm/tree/master/workers) to run a worker.

## Architecture

The whole system is built by reusing the best of free software
libraries components. The whole ZIM farm solution itself is made
available using Docker images.

Actually, we use even more Docker images, as the ZIM file are produced
in dedicated custom Docker images the worker has to "invoke" depending
of the properties of the task he has to accomplish.

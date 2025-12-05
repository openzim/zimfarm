# zimfarm-monitor-child

A [netdata](https://github.com/netdata/netdata/) container that monitors Zimfarm workers and streams metrics to the parent monitoring server.

## Overview

The child monitor is a lightweight Netdata agent that runs on each Zimfarm worker. It collects comprehensive metrics from the host and all containers, then streams this data to the central parent monitoring server at https://monitoring.openzim.org/.

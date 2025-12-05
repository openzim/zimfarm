zimfarm-monitor
===============

[![Docker](https://ghcr-badge.deta.dev/openzim/zimfarm-monitor/latest_tag?label=docker)](https://ghcr.io/openzim/zimfarm-monitor)

A [netdata](https://github.com/netdata/netdata) monitoring setup for the Zimfarm infrastructure, consisting of parent and child components that work together to provide comprehensive monitoring.

## Architecture

This repository contains both components of a Netdata streaming setup:

### Parent (Central Monitoring Server)

The **parent** component is a Netdata instance that acts as the central monitoring hub. It:

- Receives streamed metrics from Zimfarm workers (child nodes) over port `:19999`
- Monitors the server it's running on
- Stores historical data from all child nodes
- Provides a unified dashboard to view metrics from all workers
- Available at https://monitoring.openzim.org/

See the [parent/README.md](parent/README.md) for detailed documentation on the parent setup.

### Child (Worker Monitoring Agent)

The **child** component runs on Zimfarm workers and is a preconfigured Netdata image that streams host-level statistics to the parent monitoring server. It does not retain any data collected as everything is sent to the parent.

The child monitors **all activity on the host**, which means it captures:
- Host system metrics (overall CPU, RAM, disk I/O, network traffic, etc.)
- Statistics for every container running on the host
- Any other services or processes running on the worker

This allows the parent dashboard to show both host-level performance and individual task/container performance, making it possible to identify resource contention between concurrent tasks.

## Use Cases

- **Monitor Zimfarm tasks**: View real-time and historical metrics for scraper tasks running on workers
- **Analyze task performance**: Identify bottlenecks in CPU, memory, disk, or network usage
- **Debug issues**: Investigate problems by examining metrics during and after task execution
- **Multi-task analysis**: See how concurrent tasks on the same host affect each other

## Configuration

Both parent and child instances are configured through their respective directories:

- `parent/` - Configuration for the central monitoring server
- `child/` - Configuration for worker monitoring agents

The child image is designed to be easily deployed via environment variables, making it simple to integrate into the Zimfarm worker deployment process.

# zimfarm-monitor-parent

A [netdata](https://github.com/netdata/netdata/) container to monitor zimfarm tasks.

The objective is twofold:

- receive directly-streamed _netdata_ metrics from zimfarm workers which have monitoring enabled
- monitor the server it's running on.

Latter was not an initial objective but it's handy to have it since we don't monitor the other services.

## Specifics

- Available at https://monitoring.openzim.org/
- Opens an external port `:19999` to receive data stream from workers (non-http traffic)
- Uses a unique `[stream]` config for all workers with a single Key.
- Blocks streaming from IPs not in the zimfarm workers pool.
- `reset-netdata` script to clear all tasks' data.
- Is expected to store data on behalf of zimfarm monitors which only stream it there.

## Usage

netdata is user-friendly but has quite many features. Check out [the dashboard docs](https://learn.netdata.cloud/guides/step-by-step/step-02) if you want to know more.

### Monitoring Kiwix server

To monitor the main Kiwix server, select the node with the same name as the `NETDATA_HOSTNAME` from the `Nodes` Tab located at the top of the UI. Default `NETDATA_HOSTNAME` is `monitoring.openzim.org`. All the metrics you see are for the main server.

To monitor a Zimfarm task, you must select it from the _Nodes_ Tab at the top of the UI. If you are looking at it while it's running, a **live** indicator should be visible. After selecting it, you should click on the **Containers & VMs** section on the right sidebar. This is because the other metrics are related to the host and not necessarily the zimtask itself. In the **Containers & VMs** section, for each metric you want to view, the metrics will be aggregated across all containers running on the host itself. So, to filter out for the specific container you want e.g scraper, dnscache, etc, you will need to select `Group by instance` on the metric chart. The default is `Group by dimension`. After selecting `Group by instance`, select the specific container you want from the dropdown that lists the cgroups. For example, if you wanted to select zimscraper container, you would see in the dropdown `cgroup_zimcraper....` (The dot would be composed of the offliner type and task id).

You can check whether there were other tasks running during your monitored-task by looking at the list of containers. If there are multiple `zimscraper` ones, be careful. If there is only a single scraper in your data, you can safely look at any metric.

If there are multiple ones, you should click on the `zimscraper` one that interests you (check its ID) and look at the `cpu`, `mem` and `disk` stats available.

If you are looking at the charts later-on, keep in mind that our data retention is based on storage usage and not time, so there is no expectable delay before eviction.

You can download data from the dashboard though and import it back later or on a different netdata instance.

_**Important**_: _Zimfarm monitors_ **report metrics for their whole host** (the complete Zimfarm worker).

#### Redis

If the scraper you are monitoring is using redis and exposed it on the standard port (`sotoki` for instance), you can access _task-specific_, _redis-specific_ metrics by looking at the _Redis scraper_ section of the right sidebar (after the containers). Those are very detailed.

Unlike other non-container stats, this data is grabbed directly from the scraper container of that very task so it's not host-level compiled data.

## Configuration

https://learn.netdata.cloud/docs/configure/nodes

Data retention can be set in `netdata.conf`. It is set in MiB .

```yaml
[global]
 page size cache = 64  # uses 64MiB of RAM for cache
 # uses 4GiB of storage space.
 # ths is used as default for each stream receiver
 # if not customized in stream.conf
 dbengine disk space = 4096
 # uses 4GiB os storage for all hosts
 # that's our global limit
 dbengine multihost disk space = 4096
 # update all metrics every n seconds (1s is default)
 update every = 1
```

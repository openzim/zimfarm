# Zimfarm Workers

# Resources & load expectations

When setting-up a worker, you'll be joining the
[Zimfarm](https://farm.openzim.org) workers pool and thus receive
_tasks_ (zim creation requests) from our publishing pipe.

The [workers dashboard](https://farm.openzim.org/workers) displays a
live list of running workers and their assigned tasks.

Creating ZIM files is resources intensive and we have more than a
thousand of those to recreate each month. Some take a few minutes but
other takes weeks.

In any case, the worker will try to get as much resources as it can to
perform its task in the smallest amount of time.

You can set some resources usage _limits_ to avoid overloading your
host:

- `ZIMFARM_MAX_RAM` sets the max amount of RAM the worker will assign
  to its tasks.

- `ZIMFARM_DISK` sets the amount of disk you want to dedicate to the worker.
  It is used to decide whether you can run tasks or not but _is
  not enforced_: if a [Zimfarm](https://farm.openzim.org/recipes)
  recipe indicates that a task uses `2GB` of disk but actually uses
  `10GB`, it will try to use those `10GB` on your disk.

- `ZIMFARM_CPU` incidentally restricts the number of concurrent task
  your worker would execute. Each task usually takes `3` slots so set
  it to `3` for running a single task at once and `6` for running
  `2`. Note that this is not the number of cores to use.

Another option is to set `ZIMFARM_SELFISH="true"` so your worker is
excluded from the general pool and only receive tasks assigned
specifically to it. If you are interested in helping the creation of a
particular ZIM only, that's a way to do it (or to test your worker).

_Note_: All tasks consists of downloading content, processing it and
uploading the resulting ZIM files to our
[warehouse](https://download.kiwix.org) ; therefore it also uses the
network intensively.

# Run a worker

If you are willing to run a Zimfarm worker, the first step is to understand wether you machine matches requirements below.

## Requirements

- A reliable GNU/Linux host (works on macOS) with at least:
- 2GB of RAM and 3 cores available.
- [Docker CE server](https://docs.docker.com/engine/install/) running.
- Fast and reliable internet connexion (both downstream and upstream, biggest Zimfarm recipes handles about 100G first in download then in upload ; the fastest, the best).
- A fixed public IP (we do not mind about NAT, this is what most of our workers are doing, it is transparent for us ; we do not mind about IPs changing few times per year ; more regular IP changes are going to be a problem).
- The clock must be synchronized, e.g. using ntp.
- The machine should be available for significant amount of time (at least 6 months)

SSH access to your host for our developers is handy but not required. We do use bastion(s) to connect to our machines, so you could open SSH only to these few machines (only 2 ATM).

Reliable internet means that we do expect your Internet connection to not drop every now and then. We do not mind about very small interuption of few seconds, but anything in the range of 1 minute or more will be cause most scrapers to fail, becoming an issue.

Reliable machine means that we do expect your machine to be reasonably "always-on". We do not mind about regular scheduled downtime once a month or so, but we need you let ongoing tasks complete before doing such maintenance. We do understand that you need to bring the machine down for OS updates, and our system will allow to do this in a planned and organized manner.

We do not mind about one or two unexpected Internet or machine downtimes per year but anything happening more often is a pain for us. We mostly do not mind at all about the duration of the downtimes, especially if planned in advance.

## Setup

### Docker configuration

Default docker configuration stores its internal data into `/var/lib/docker` (Linux). While the data produced by the Zimfarm are not stored in this folder (but in the `ZIMFARM_ROOT` you'll define later), it's important to note that docker container logs are stored there.

Logs are kept only for the duration of the task/container so you should not worry about those piling up.

Still, under certain circumstances, we enable verbose mode on scrapers and that can lead to logs files up to **20GB+** large.

Keep this information in mind when you configure the disk space you want zimfarm to use as those are not managed by the zimfarm and thus not accounted for.

Additionally, if your partition scheme isn't compatible with such sizes on `/var/lib`, change the data folder of the docker daemon in `/etc/docker/daemon.json` (you'll probably have to create it) and restart docker.

```json
{
  "data-root": "/not/var/lib/docker"
}
```

### Create a Zimfarm folder

Most of the (temporary) Zimfarm-related data will be put in there
(build files, zim files, etc). Create it for example in your `$HOME`

```bash
mkdir ~/zimfarm
```

... and move to it.

```bash
cd ~/zimfarm
```

### Create a public key for your worker

This is for reference only, you'd probably want to send your public
RSA key file to us when requesting a worker account (Admins can upload it via UI)

```bash
# Generate an SSH key pair (use empty passphrase)
ssh-keygen -t ed25519 -f id_ed25519
```

If you are using a legacy system that doesn't support the Ed25519 algorithm, use:

```bash
ssh-keygen -t rsa -b 2048 -f id_rsa
```

```bash
# Display your public key (you'll share this part with Zimfarm admins)
# The public key is typically of the form <algorithm> <key> <name>
# You can change the <name> part of the key to whatever you want to different a key
# from another
cat id_ed25519.pub
```

We do recommend to rotate this SSH key once a year. Zimfarm allows to have multiple SSH keys per worker, allowing a transition without downtime (you generate the key somewhere, we add this new key, you reconfigure Zimfarm worker to use the new key, wait for ongoing tasks to complete (they use the old key), we delete the old key).

### Create worker account on the Zimfarm

Send your worker information to to Zimfarm Admins via mail [contact+zimfarm@kiwix.org](mailto:contact+zimfarm@kiwix.org) or on Slack:
- worker name (only lowercase letter, see already in-use worker names at https://farm.openzim.org/workers, avoid generic names like "cloud-vm", "zimfarm-worker", ...) 
- your email (should we need to contact you, send goodies, ...) 
- the SSH public key

Zimfarm Admin will create and configure your worker account.

### Management script

A Zimfarm worker is just a Docker container spawning other containers.

If you like to control everything, you can run it manually setting the
appropriate options. Otherwise, use our handy bash script.

```bash
sudo wget -O /usr/local/bin/zimfarm \
  https://raw.githubusercontent.com/openzim/zimfarm/master/worker/contrib/zimfarm.sh && \
  sudo chmod +x /usr/local/bin/zimfarm && \
  sudo wget -O /etc/zimfarm.config \
  https://raw.githubusercontent.com/openzim/zimfarm/master/worker/contrib/zimfarm.config.example
```

Now read and edit `/etc/zimfarm.config`. The **bare-minimal** is setting:

- `ZIMFARM_USERNAME`: your worker account username
- `ZIMFARM_ROOT`: path of your Zimfarm folder

Then, **make sure** you place your private key at `$ZIMFARM_ROOT/id_ed25519`. Permission should be `rw` for root (600).

If private key is stored somewhere else, you can modify corresponding volume mount in `/usr/local/bin/zimfarm` script.

### Validating behavior

Once you've edited the config file, you'll have to start your worker.

```bash
zimfarm start
zimfarm logs manager
```

If the output of the manager logs says `polling...` then the worker
started properly and is looking for tasks.

**Allow a minute** for the initial request to trigger the IP whitelist update on the S3 cache.

You can now request a short task (we recommend `wikipedia_fr_test`) to
your worker specifically on the Zimfarm and wait for it to pick-it up,
run it and upload it. It should only take a few minutes.

Once this is cleared, you can edit the config file and remove the
selfishness (`ZIMFARM_SELFISH=`) then restart your worker.

```bash
zimfarm restart
```

That's it!

### Youtube offliner

Youtube offliner is a bit special because it does require manual IP whitelisting by Zimfarm admins. It is hence not enabled by default. And we really want to avoid having to fix this manual configuration too often if your IP changes every year for instance.

We also do recommend to avoid running Youtube tasks on Internet connections also used by regular "browsing" users since we cannot guarantee it will not have some adverse effects on the rest of the Youtube usage.

If you feel like you want to meet these expectations, feel free to tell Zimfarm Admins about this, we will appreciate.

## Worker commands

- **`zimfarm restart`**: (re)start pulls a new version of the Docker image and also reapplies the configuration.
- **`zimfarm ps`**: displays a list of running containers with Zimfarm labels

--

- **`zimfarm stop manager`**: stops the manager without stopping the currently running workers. A stopped manager doesn't receive new task to do.
- **`zimfarm stop <task-name>`**: stops a task and its dependencies (scraper, dnscache). Marks it as canceled. Can take a minute.
- **`zimfarm shutdown`**: stops the manager and all the running tasks. Use this to stop the worker completely. Running tasks will be marked as canceled. Can take a couple minutes.

--

- **`zimfarm logs manager [n]`**: displays logs for the manager. `n` is an optionnal lines number (100 otherwise).
- **`zimfarm logs <task-name> [n]`**: displays logs for that task worker. `n` is an optionnal lines number (100 otherwise).

--

- **`zimfarm prune`**: removes unused containers and volumes to save space. you can put that in a cron task daily. ⚠️ it removes all unused images and containers.
- **`zimfarm update`**: displays a command you could use update this very script.
- **`zimfarm update do`**: attempt to tun the `zimfarm update` command.

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

If you are willing to run a Zimfarm worker, the first step is to get a
worker account on the Zimfarm. Please contact one of the developers on
Github or [send an email to
contact+zimfarm@kiwix.org](mailto:contact+zimfarm@kiwix.org).

## Requirements

- A GNU/Linux host (works on macOS) with at least:
- 2GB of RAM and 3 cores available.
- [Docker CE server](https://docs.docker.com/engine/install/) running.
- Fast internet connexion (downstream and upstream).
- A Zimfarm user account (with appropriate `worker` role).
- An SSH private key with its public key uploaded to the user account (we now recommend an `ed25519` key).
- The clock must be synchronized, e.g. using ntp.

**Note**: SSH access to your host for our developers is handy but not required.

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

### Uploading your public key

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
# Display your public key (you'll upload this part)
# The public key is typically of the form <algorithm> <key> <name>
# You can change the <name> part of the key to whatever you want to different a key
# from another
cat id_ed25519.pub

# Upload the public key. Token can be copied from
# the Zimfarm user interface (top right corner on the profile button).
curl -X POST https://api.farm.openzim.org/v2/users/<username>/keys \
    -H 'Authorization: Bearer <token>' \
    -H 'Content-Type: application/json; charset=utf-8' \
    -d $'{"key": "<key-content>"}'
```

## Setup

A Zimfarm worker is just a Docker container spawning other containers.

If you like to control everything, you can run it manually setting the
appropriate options. Otherwise, use our handy bash script.

```bash
sudo wget -O /usr/local/bin/zimfarm \
  https://raw.githubusercontent.com/openzim/zimfarm/master/workers/contrib/zimfarm.sh && \
  sudo chmod +x /usr/local/bin/zimfarm && \
  sudo wget -O /etc/zimfarm.config \
  https://raw.githubusercontent.com/openzim/zimfarm/master/workers/contrib/zimfarm.config.example
```

Now read and edit `/etc/zimfarm.config`. The **bare-minimal** is setting:

- `ZIMFARM_USERNAME`: your worker account username
- `ZIMFARM_ROOT`: path of your Zimfarm folder

Then, **make sure** you place your RSA private key at `$ZIMFARM_ROOT/id_rsa`. Permission should be `rw` for root (600).

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

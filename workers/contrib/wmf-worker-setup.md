# Setup disk

This is based on a `xlarge-xtradisk` with 300GB disk.

``` sh
# check physical volumes
sudo pvdisplay
# check volume groups
sudo vgdisplay
# check logical volumes (should be none)
sudo lvdisplay
# create logical volume
sudo lvcreate -n second-local-disk -L280G vd
# format volume
sudo mkfs.ext4 /dev/vd/second-local-disk
sudo vim /etc/fstab
```

Add the following line

```
/dev/vd/second-local-disk			/srv	ext4	defaults	0	0
```

``` sh
# mount newly created mount-point
sudo mount -a
# check mount point and disk size
df -h /srv/
```

# Install docker

``` sh
sudo apt update && sudo apt upgrade
sudo apt install apt-transport-https     ca-certificates     curl     gnupg-agent     software-properties-common
curl -fsSL https://download.docker.com/linux/debian/gpg | sudo apt-key add -
sudo add-apt-repository    "deb [arch=amd64] https://download.docker.com/linux/debian \
   $(lsb_release -cs) \
   stable"
sudo apt update && sudo apt install docker-ce docker-ce-cli containerd.io
sudo usermod -aG docker reg
sudo usermod -aG docker kelson
```

# Change docker folder location

``` sh
sudo systemctl stop docker
sudo vim /etc/docker/daemon.json
```

``` json
{
    "data-root": "/srv/docker"
}
```

``` sh
sudo rm -rf /var/lib/docker/
sudo systemctl start docker
```

# Install zimfarm

``` sh
cd /srv/
sudo mkdir -p zimfarm
cd zimfarm/
# install worker RSA key
sudo mv /home/reg/id_rsa .
sudo chown root:root id_rsa
sudo chmod 0600 id_rsa
sudo wget -O /usr/local/bin/zimfarm   https://raw.githubusercontent.com/openzim/zimfarm/master/workers/contrib/zimfarm.sh &&   sudo chmod +x /usr/local/bin/zimfarm &&   sudo wget -O /etc/zimfarm.config   https://raw.githubusercontent.com/openzim/zimfarm/master/workers/contrib/zimfarm.config
sudo vim /etc/zimfarm.config
```

``` sh
#!/bin/bash

### MANDATORY

# Zimfarm username
ZIMFARM_USERNAME="wmf-worker"

# Zimfarm folder. You have to create it. Put your `id_rsa` private key
# directly at its root. Will be used as well for other Zimfarm
# temporary data.
ZIMFARM_ROOT=/srv/zimfarm

### OPTIONAL

# Worker name (your choice, can be different from the username)
ZIMFARM_WORKER_NAME="mwoffliner1"

# Set to `"y"` if you need `sudo` for `docker` command (`""` otherwise)
SUDO_DOCKER="y"

# Whether to display debug-level logs (`"y"` or `""`)
ZIMFARM_DEBUG="y"

# Maximum amount of RAM you want your worker to use
ZIMFARM_MAX_RAM="15GiB"

# Disk space you are dedicating to the worker. worker needs this space avail to work
# /!\ disk usage is not enforced (might exceed this limit)
ZIMFARM_DISK="220GiB"

# Artificial number to configure the level of CPU load you want to
# allocate. Put `"3"` if you want to have around one task at a time,
# `"6"` if you want to have around two task in parallel, etc.
ZIMFARM_CPU="6"

# Comma-separated list of offliners to run or `""` for all of them. If
# you want to run `youtube` tasks, you need to be whitelisted, contact
# us.
ZIMFARM_OFFLINERS="mwoffliner"

# Set to `"y"` to only run task specifically assigned to this worker
# (`""` otherwise)
ZIMFARM_SELFISH=""

# Set to `"y"` to use a public (Cloudfare, Google) DNS instead of your
# system (Internet provider) one. `""` otherwise.
USE_PUBLIC_DNS=""

# change default maximum nb of tasks for your worker over a specific platform
PLATFORM_wikimedia_MAX_TASKS=3
# PLATFORM_youtube_MAX_TASKS=2
```


``` sh
zimfarm start
# check that the initial auth and all is OK and that it is polling
zimfarm logs manager
```

## Add auto-prune

``` sh
sudo vim /etc/cron.daily/zimfarm-prune
```

```sh
#!/bin/bash
/usr/local/bin/zimfarm prune
```

``` s
sudo chmod +x /etc/cron.daily/zimfarm-prune
/etc/cron.daily/zimfarm-prune
```
#!/bin/sh
# checks GID of docker socket on host then change container's docker gid to match it
# checks UID of SSH key on host then change user's uid to match it
# check GID of /zim_files folder on host then change zim group gid to match it
# ensure /zim_files is writable (or die)
# once done, replace pid with worker app

set -x

# configure script to call original entrypoint
set python app/main.py "$@"

# get gid of docker socket file
SOCK_DOCKER_GID=`ls -ng /var/run/docker.sock | cut -f3 -d' '`

# get gid of docker group inside container
CUR_DOCKER_GID=`getent group docker | cut -f3 -d: || true`

# if they don't match, adjust
if [ ! -z "$SOCK_DOCKER_GID" -a "$SOCK_DOCKER_GID" != "$CUR_DOCKER_GID" ]; then
    sudo groupmod -g ${SOCK_DOCKER_GID} -o docker
fi

# if docker socket not writable, fail.
if [ ! -w /var/run/docker.sock ] ; then
	echo "docker socket (/var/run/docker.sock in container) is not writable."
	exit 1
fi


# get uid of ssh key
SSH_KEY_UID=`ls -n /usr/src/.ssh/id_rsa | cut -f4 -d' '`
# get uid of celery_runner user inside container
CUR_CELERY_UID=`id -u celery_runner`

# if they don't match, adjust
if [ ! -z "$SSH_KEY_UID" -a "$SSH_KEY_UID" != "$CUR_CELERY_UID" ]; then
    sudo usermod -u ${SSH_KEY_UID} -o celery_runner
fi

# if ssh key not readable, fail.
if [ ! -r /usr/src/.ssh/id_rsa ] ; then
	echo "ssh key (/usr/src/.ssh/id_rsa in container) is not readable."
	exit 1
fi

# get gid of output folder
ZIM_FOLDER_GID=`ls -ndg /zim_files | cut -f3 -d' '`

# get gid of zim group inside container
CUR_FOLDER_GID=`getent group zim | cut -f3 -d: || true`

# if they don't match, adjust
if [ ! -z "$ZIM_FOLDER_GID" -a "$ZIM_FOLDER_GID" != "$CUR_FOLDER_GID" ]; then
    sudo groupmod -g ${ZIM_FOLDER_GID} -o zim
fi

# if zim folder not group-writable, fail.
if [ ! -w /zim_files ] ; then
	echo "zim output folder (/zim_files in container) is not writable."
	exit 1
fi

# replace the current pid 1 with original entrypoint
exec "$@"

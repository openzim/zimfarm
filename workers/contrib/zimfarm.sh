#!/bin/bash

# Zimfarm worker manager script
#
# README at https://github.com/openzim/zimfarm/blob/master/workers/README.md
#
# this script is provided for your comfort only.
# DONT RUN IT unless you've read it and understood its behavior.

######## DEFAULT VALUES #
# change them in your zimfarm.config file
SUDO_DOCKER=
ZIMFARM_USERNAME="unknown"
ZIMFARM_WORKER_NAME="unknown"
ZIMFARM_DEBUG=
ZIMFARM_MAX_RAM="2G"
ZIMFARM_DISK="10G"
ZIMFARM_CPU="3"
ZIMFARM_ROOT=/tmp
ZIMFARM_OFFLINERS=
ZIMFARM_SELFISH=
USE_PUBLIC_DNS=
MANAGER_IMAGE="openzim/zimfarm-worker-manager"
MANAGER_TAG="latest"
WORKER_IMAGE="openzim/zimfarm-task-worker"
WORKER_TAG="latest"
SOCKET_URI="tcp://tcp.farm.openzim.org:32029" \
WEB_API_URI="https://api.farm.openzim.org/v1" \
UPLOAD_URI="sftp://uploader@warehouse.farm.openzim.org:1522" \
#########################
SOURCE_URL="https://raw.githubusercontent.com/openzim/zimfarm/master/workers/contrib/zimfarm.sh"
WORKER_MANAGER_NAME="zimfarm_worker-manager"

function die() {
    echo $1
    exit 1
}

# find this script's path
if [[ $(uname -s) == "Darwin" ]]; then
    parentdir=$(dirname "$(greadlink -f "$0")")
    scriptname=$(basename "$(greadlink -f "$0")")
else
    parentdir=$(dirname "$(readlink -f "$0")") 
    scriptname=$(basename "$(readlink -f "$0")")
fi

# select and read config file
configfname="zimfarm.config"
search_paths=( "${parentdir}/${configfname}" "${HOME}/.${configfname}" "${HOME}/${configfname}" "/etc/${configfname}" )
function display_search_paths() {
    echo ""
    echo "Search paths:"
    for path in "${search_paths[@]}"
    do
       :
       echo "  - ${path}"
    done
}
configpath=
for path in "${search_paths[@]}"
do
   :
   if [ -f $path ] ; then
    configpath=$path
    break
   fi
done

# fail if we have no config file
if [[ "$configpath" == "" ]]; then
    echo "unable to find ${configfname} in known locations"
    display_search_paths
    die
fi 

# load config variables
source $configpath || die "failed to source ${configpath}"
datadir=$ZIMFARM_ROOT/data

# display config file path
function config() {
    echo "Using: ${configpath}"
    display_search_paths
}

# display options list
function usage() {
    echo "Usage: $0 [help|config|ps|prune|restart|stop|shutdown|update]"
    echo ""
    echo "  config          show the config file path in use"
    echo ""
    echo "  restart         start or restart the manager. reloads config."
    echo "  logs <name> [n] display logs of task or 'manager' using its name"
    echo "  stop <name>     stop a task or the 'manager' using its name"
    echo "  shutdown        stops the manager and all running tasks"
    echo ""
    echo "  ps              list of running containers with zimfarm labels"
    echo "  prune           remove all docker containers/images/volums"
    echo "  update          display commands to update this script (apply with 'update do')"
    echo ""
}

# run docker commands directly or via sudo if SUDO_DOCKER is set
function run() {
    if [ ! -z $SUDO_DOCKER ]; then
        sudo "$@"
    else
        "$@"
    fi
}

# display a list of running containers with some zimfarm labels
function ps() {
    run docker ps --format 'table {{.ID}}\t{{.Label "tid"}}\t{{.Label "schedule_name"}}\t{{.Label "task_id"}}\t{{.RunningFor}}\t{{.Names}}'
}

# cleanup disk usage (to be run in cron)
function prune() {
    run docker system prune --volumes -af
}

# stop container, extending timeout so task can stop scrapers and dnscache
function stop() {
    target=$1
    if [[ "$target" == "manager" ]]; then
        target=$WORKER_MANAGER_NAME
    fi
    echo "stopping container ${target}..."
    run docker stop -t 120 $target
}

# start or restart the manager using config values
function restart() {
    echo "(re)starting zimfarm worker manager..."
    echo ":: stopping ${WORKER_MANAGER_NAME}"
    run docker stop $WORKER_MANAGER_NAME || true
    run docker rm $WORKER_MANAGER_NAME || true

    echo ":: starting ${WORKER_MANAGER_NAME}"
    manager_image_string="$MANAGER_IMAGE:${MANAGER_TAG}"
    worker_image_string="$WORKER_IMAGE:${WORKER_TAG}"
    run docker pull $manager_image_string
    run docker run \
        --name $WORKER_MANAGER_NAME \
        --restart=always \
        --detach \
        --log-driver json-file \
        --log-opt max-size="100m" \
        -v $datadir:/data \
        -v /var/run/docker.sock:/var/run/docker.sock:ro \
        -v $ZIMFARM_ROOT/id_rsa:/etc/ssh/keys/zimfarm:ro \
        --env ZIMFARM_MEMORY=$ZIMFARM_MAX_RAM \
        --env ZIMFARM_DISK=$ZIMFARM_DISK \
        --env ZIMFARM_CPUS=$ZIMFARM_CPU \
        --env USERNAME=$ZIMFARM_USERNAME \
        --env DEBUG=$ZIMFARM_DEBUG \
        --env WORKER_NAME=$ZIMFARM_WORKER_NAME \
        --env SOCKET_URI=$SOCKET_URI \
        --env WEB_API_URI=$WEB_API_URI \
        --env UPLOAD_URI=$UPLOAD_URI \
        --env USE_PUBLIC_DNS=$USE_PUBLIC_DNS \
        --env OFFLINERS=$ZIMFARM_OFFLINERS \
        --env TASK_WORKER_IMAGE=$worker_image_string \
    $manager_image_string worker-manager
}

# stop the manager and all the workers
function shutdown() {
    echo "shutting down manager and all the workers..."
    run docker kill -s SIGQUIT $WORKER_MANAGER_NAME
}

# display logs of a container or the manager, using --tail and -f
function logs() {
    target=$1
    tail=$2
    if [[ "$target" == "manager" ]]; then
        target=$WORKER_MANAGER_NAME
    fi
    if [[ "${tail}" == "" ]]; then
        tail="100"
    fi
    run docker logs --tail $tail -f $target
}

# display the command needed to update this script from the repo
# add 'do' parameter to attempt to run it
function update() {
    echo "updating $1..."
    dest="${parentdir}/${scriptname}"
    update_cmd="sudo wget -O ${dest} ${SOURCE_URL} && chmod +x ${dest}"
    if [[ "$2" == "do" ]]; then
        bash -c "${update_cmd}"
    else
        echo $update_cmd
    fi
}

function usage_if_missing() {
    if [ -z $1 ]; then
        usage
        exit 1
    fi
}

# script entrypoint
function main() {
    action=$1
    target=$2

    case $action in
      "config")
        config
        ;;

      "ps")
        ps
        ;;

      "prune")
        prune
        ;;

      "restart")
        restart
        ;;

      "start")
        restart
        ;;

      "stop")
        usage_if_missing $target
        stop $target
        ;;

      "logs")
        usage_if_missing $target
        logs $target $3
        ;;

      "shutdown")
        shutdown
        ;;

      "update")
        update $0 $2
        ;;

      *)
        usage $0
        ;;
    esac


}


main "$@"

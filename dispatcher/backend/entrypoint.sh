#!/bin/sh

die() {
	echo "unable to run database initializations. exiting"
	exit 1
}

cd /usr/src/ && python -c "from utils.database import Initializer; Initializer.create_initial_user()" || die

exec "$@"

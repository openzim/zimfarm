#!/bin/sh

die() {
	echo "unable to run database initializations. exiting"
	exit 1
}

python -c "from utils.database import Initializer; Initializer.create_initial_user()" || die

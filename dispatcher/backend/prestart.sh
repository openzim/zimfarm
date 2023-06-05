#!/bin/sh

die() {
	echo "unable to run database initializations. exiting"
	exit 1
}

if [ ! -z "$ALEMBIC_UPGRADE_HEAD_ON_START" ]; then
    echo "Running alembic upgrade"
    alembic check
    alembic history
    alembic upgrade head
fi
python -c "from utils.database import Initializer; Initializer.create_initial_user()" || die

#!/bin/sh

die() {
	echo "unable to run database initializations. exiting"
	exit 1
}

if [ ! -z "$ALEMBIC_UPGRADE_HEAD_ON_START" ]; then
    echo "Running alembic upgrade"
    alembic check || true
    alembic history
    alembic upgrade head
fi
create-initial-user

#!/bin/bash
#
# Author : Emmanuel Engelhart
#
# Usage : check_zims <nbJobs> <zimSrcDir> <zimDstDir> <zimQuarantineDir> <logDir> <zimCheckOptions> [NO_QUARANTINE|NO_CHECK]
#

ZIMCHECK_PARALLEL_JOBS=$1
ZIM_SRC_DIR=$2
ZIM_DST_DIR=$3
ZIM_QUAR_DIR=$4
VALIDATION_LOG_DIR=$5
ZIMCHECK_OPTION=$6
VALIDATION_OPTION=$7

PARALLEL="parallel -j${ZIMCHECK_PARALLEL_JOBS}"
ZIMCHECK='/usr/local/bin/check_zim.sh'

find $ZIM_SRC_DIR -iname '*.zim' |
    $PARALLEL "$ZIMCHECK {} $ZIM_SRC_DIR $ZIM_DST_DIR $ZIM_QUAR_DIR $VALIDATION_LOG_DIR \"$ZIMCHECK_OPTION\" $VALIDATION_OPTION"

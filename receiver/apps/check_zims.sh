#!/bin/bash
#
# Author : Emmanuel Engelhart
#
# Usage : check_zims <zimSrcDir> <zimDstDir> <zimQuarantineDir> <logDir> <zimCheckOptions> [NO_QUARANTINE|NO_CHECK]
#

ZIM_SRC_DIR=$1
ZIM_DST_DIR=$2
ZIM_QUAR_DIR=$3
ZIM_CHECK_LOG_DIR=$4
ZIMCHECK_OPTION=$5
VALIDATION_OPTION=$6

PARALLEL='parallel -j2'
ZIMCHECK='/usr/local/bin/check_zim.sh'

find $ZIM_SRC_DIR -iname '*.zim' |
    $PARALLEL "$ZIMCHECK {} $ZIM_SRC_DIR $ZIM_DST_DIR $ZIM_QUAR_DIR $VALIDATION_LOG_DIR \"$ZIMCHECK_OPTION\" $VALIDATION_OPTION"

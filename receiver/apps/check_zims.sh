#!/bin/bash
#
# Author : Emmanuel Engelhart
#
# Usage : check_zims <nbJobs> <zimSrcDir> <zimDstDir> <zimQuarantineDir>
#

ZIMCHECK_PARALLEL_JOBS=$1
ZIM_SRC_DIR=$2
ZIM_DST_DIR=$3
ZIM_QUAR_DIR=$4

PARALLEL="parallel -j${ZIMCHECK_PARALLEL_JOBS}"
ZIMCHECK='/usr/local/bin/check_zim.sh'

find "$ZIM_SRC_DIR" -iname '*.zim' |
    $PARALLEL "$ZIMCHECK {} $ZIM_SRC_DIR $ZIM_DST_DIR $ZIM_QUAR_DIR"

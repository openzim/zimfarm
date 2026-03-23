#!/bin/bash
#
# Author : Emmanuel Engelhart
#
# Usage : move_zims <nbJobs> <zimSrcDir> <zimDstDir> <zimQuarantineDir>
#

ZIM_MOVE_PARALLEL_JOBS=$1
ZIM_SRC_DIR=$2
ZIM_DST_DIR=$3
ZIM_QUAR_DIR=$4

PARALLEL="parallel -j${ZIM_MOVE_PARALLEL_JOBS}"
ZIM_MOVE='/usr/local/bin/move_zim.sh'

find "$ZIM_SRC_DIR" -iname '*.zim' |
    $PARALLEL "$ZIM_MOVE {} $ZIM_SRC_DIR $ZIM_DST_DIR $ZIM_QUAR_DIR"

#!/bin/bash
#
# Author : Florent Kaisser
#
# Usage : check_zim.sh <zimFilePath> <zimSrcDir> <zimDstDir> <zimQuarantineDir> [NO_QUARANTINE|NO_CHECK]
#

ZIMFILE=$1
ZIMSRCDIR=$2
OPTION=$5


ZIMPATH=$(echo $ZIMFILE | sed "s:$ZIMSRCDIR::")

DESTFILE=$3$ZIMPATH
DESTDIR=$(dirname "$DESTFILE")

if [ "$OPTION" = "NO_QUARANTINE" ]
then
 QUARDIR=$DESTDIR
 QUARFILE=$DESTFILE
else
 QUARFILE=$4$ZIMPATH
 QUARDIR=$(dirname "$QUARFILE")
fi


function moveZim () {
   mkdir -p $1
   mv -f $ZIMFILE $2
}

# prevent zim from being uploaded to root of zimDstDir
if [ $(dirname $ZIMPATH) = "." ] ; then
  echo "Zim outside subfolder. moving to quarantine"
  QUARFILE=$4$ZIMPATH
  QUARDIR=$(dirname $QUARFILE)
  moveZim $QUARDIR $QUARFILE
  exit 0
fi

echo "move $ZIMFILE to $DESTFILE"
moveZim $DESTDIR $DESTFILE

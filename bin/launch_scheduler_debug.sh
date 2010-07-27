#!/bin/bash

DIR=$(cd $(dirname "$0"); pwd)
BIN=$DIR"/../src"
ETC=$DIR"/../src/etc"
DEBUG_PATH="/tmp/scheduler.debug"

echo "Launching Scheduler (that do scheduling only) in debug mode to the file $DEBUG_PATH"
$BIN/shinken-scheduler.py -d -c $ETC/schedulerd.cfg --debug $DEBUG_PATH

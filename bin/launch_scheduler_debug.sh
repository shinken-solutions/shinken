#!/bin/bash

DIR=$(cd $(dirname "$0"); pwd)
BIN=$DIR"/../bin"
ETC=$DIR"/../etc"
DEBUG_PATH="/tmp/scheduler.debug"

echo "Launching Scheduler (that is only in charge of the scheduling) in debug mode to the file $DEBUG_PATH"
$BIN/shinken-scheduler -d -c $ETC/schedulerd.ini --debug $DEBUG_PATH

#!/bin/bash

DIR=$(cd $(dirname "$0"); pwd)
BIN=$DIR"/../../../bin"
ETC=$DIR"/../../../test/etc/test_stack2"
DEBUG_PATH="/tmp/scheduler-2.debug"

echo "Launching Scheduler (that do scheduling only) in debug mode to the file $DEBUG_PATH"
$BIN/shinken-scheduler -d -c $ETC/schedulerd-2.ini --debug $DEBUG_PATH

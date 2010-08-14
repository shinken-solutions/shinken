#!/bin/bash

DIR=$(cd $(dirname "$0"); pwd)
BIN=$DIR"/../bin"
ETC=$DIR"/../etc"
DEBUG_PATH="/tmp/reactionner.debug"

echo "Launching Reactionner (that do notification send) in debug mode to the file $DEBUG_PATH"
$BIN/shinken-reactionner.py -d -c $ETC/reactionnerd-for-test.ini --debug $DEBUG_PATH

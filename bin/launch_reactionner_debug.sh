#!/bin/bash

DIR=$(cd $(dirname "$0"); pwd)
BIN=$DIR"/../bin"
ETC=$DIR"/../etc"
DEBUG_PATH="/tmp/reactionner.debug"

echo "Launching Reactionner (that sends the notifications) in debug mode to the file $DEBUG_PATH"
$BIN/shinken-reactionner -d -c $ETC/reactionnerd.ini --debug $DEBUG_PATH

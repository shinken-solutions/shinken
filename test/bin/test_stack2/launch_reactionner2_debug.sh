#!/bin/bash

DIR=$(cd $(dirname "$0"); pwd)
BIN=$DIR"/../../../bin"
ETC=$DIR"/../../../test/etc/test_stack2"
DEBUG_PATH="/tmp/reactionner-2.debug"

echo "Launching Reactionner (that do notification send) in debug mode to the file $DEBUG_PATH"
$BIN/shinken-reactionner -d -c $ETC/reactionnerd-2.ini --debug $DEBUG_PATH

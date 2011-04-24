#!/bin/bash

DIR=$(cd $(dirname "$0"); pwd)
BIN=$DIR"/../bin"
ETC=$DIR"/../etc"
DEBUG_PATH="/tmp/arbiter.debug"

# needed because arbiter doesn't have a default 'workdir' "properties" attribute:
cd "$DIR/../var"
echo "Launching Arbiter (that reads the configuration and dispatches it) in debug mode to the file $DEBUG_PATH"
$BIN/shinken-arbiter -d -c $ETC/nagios.cfg -c $ETC/shinken-specific.cfg --debug $DEBUG_PATH



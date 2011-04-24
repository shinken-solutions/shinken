#!/bin/bash

DIR=$(cd $(dirname "$0"); pwd)
BIN=$DIR"/../bin"
ETC=$DIR"/../etc"

# needed because arbiter doesn't have a default 'workdir' "properties" attribute:
cd "$DIR/../var"
echo "Launching Arbiter (that reads the configuration and dispatches it)"
$BIN/shinken-arbiter -d -c $ETC/nagios.cfg -c $ETC/shinken-specific.cfg

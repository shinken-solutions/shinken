#!/bin/bash

DIR=$(cd $(dirname "$0"); pwd)
BIN=$DIR"/../../../bin"
ETC=$DIR"/../../../test/etc/test_stack2"
DEBUG_PATH="/tmp/poller-2.debug"

echo "Launching Poller (that launch checks) in debug mode to the file $DEBUG_PATH"
$BIN/shinken-poller -d -c $ETC/pollerd-2.ini --debug $DEBUG_PATH

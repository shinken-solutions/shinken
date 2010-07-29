#!/bin/bash

DIR=$(cd $(dirname "$0"); pwd)
BIN=$DIR"/../bin"
ETC=$DIR"/../etc"
DEBUG_PATH="/tmp/poller.debug"

echo "Launching Poller (that launch checks) in debug mode to the file $DEBUG_PATH"
$BIN/shinken-poller.py -d -c $ETC/pollerd.cfg --debug $DEBUG_PATH

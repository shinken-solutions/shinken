#!/bin/bash

DIR=$(cd $(dirname "$0"); pwd)
BIN=$DIR"/../bin"
ETC=$DIR"/../etc"
DEBUG_PATH="/tmp/receiver.debug"

echo "Launching receiver (that manage passive data) in debug mode to the file $DEBUG_PATH"
$BIN/shinken-receiver -d -c $ETC/receiverd.ini --debug $DEBUG_PATH

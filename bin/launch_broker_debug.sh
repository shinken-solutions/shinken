#!/bin/bash

DIR=$(cd $(dirname "$0"); pwd)
BIN=$DIR"/../src"
ETC=$DIR"/../src/etc"
DEBUG_PATH="/tmp/broker.debug"

echo "Launching Broker (that export all data) in debug mode to the file $DEBUG_PATH"
$BIN/shinken-broker.py -d -c $ETC/brokerd.cfg --debug $DEBUG_PATH

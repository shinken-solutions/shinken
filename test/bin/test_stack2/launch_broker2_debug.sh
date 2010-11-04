#!/bin/bash

DIR=$(cd $(dirname "$0"); pwd)
BIN=$DIR"/../../../bin"
ETC=$DIR"/../../../test/etc/test_stack2"
DEBUG_PATH="/tmp/broker-2.debug"

echo "Launching Broker (that export all data) in debug mode to the file $DEBUG_PATH"
$BIN/shinken-broker -d -c $ETC/brokerd-2.ini --debug $DEBUG_PATH

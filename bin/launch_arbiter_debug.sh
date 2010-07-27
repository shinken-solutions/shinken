#!/bin/bash

DIR=$(cd $(dirname "$0"); pwd)
BIN=$DIR"/../src"
ETC=$DIR"/../src/etc"
DEBUG_PATH="/tmp/arbiter.debug"


echo "Launching Arbiter (that read configuration and dispatch it) in debug mode to the file $DEBUG_PATH"
$BIN/shinken-arbiter.py -d -c $ETC/nagios.cfg -c $ETC/shinken-specific.cfg --debug $DEBUG_PATH

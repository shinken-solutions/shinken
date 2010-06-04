#!/bin/bash

DIR=$(cd $(dirname "$0"); pwd)
BIN=$DIR"/../src"
ETC=$DIR"/../src/etc"

echo "Launching Arbiter (that read configuration and dispatch it)"
$BIN/shinken-arbiter.py -d -c $ETC/nagios.cfg -c $ETC/shinken-specific.cfg
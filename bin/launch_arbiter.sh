#!/bin/bash

DIR=$(cd $(dirname "$0"); pwd)
BIN=$DIR"/../bin"
ETC=$DIR"/../etc"

echo "Launching Arbiter (that read configuration and dispatch it)"
$BIN/shinken-arbiter -d -c $ETC/nagios.cfg -c $ETC/shinken-specific.cfg

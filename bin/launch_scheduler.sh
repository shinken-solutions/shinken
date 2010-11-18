#!/bin/bash

DIR=$(cd $(dirname "$0"); pwd)
BIN=$DIR"/../bin"
ETC=$DIR"/../etc"

echo "Launching Scheduler (that do scheduling only)"
$BIN/shinken-scheduler.py -d -c $ETC/schedulerd.ini

#!/bin/bash

DIR=$(cd $(dirname "$0"); pwd)
BIN=$DIR"/../bin"
ETC=$DIR"/../etc"

echo "Launching Scheduler (that is only in charge of the scheduling)"
$BIN/shinken-scheduler -d -c $ETC/schedulerd.ini

#!/bin/bash

DIR=$(cd $(dirname "$0"); pwd)
BIN=$DIR"/../bin"
ETC=$DIR"/../etc"

echo "Launching Broker (that exports all data)"
$BIN/shinken-broker -d -c $ETC/brokerd.ini

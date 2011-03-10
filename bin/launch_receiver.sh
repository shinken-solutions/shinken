#!/bin/bash

DIR=$(cd $(dirname "$0"); pwd)
BIN=$DIR"/../bin"
ETC=$DIR"/../etc"

echo "Launching Receiver (that manage passive data)"
$BIN/shinken-receiver -d -c $ETC/receiverd.ini

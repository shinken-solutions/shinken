#!/bin/bash

DIR=$(cd $(dirname "$0"); pwd)
BIN=$DIR"/../bin"
ETC=$DIR"/../etc"

echo "Launching Poller (that launch checks)"
$BIN/shinken-poller -d -c $ETC/pollerd.ini

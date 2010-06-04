#!/bin/bash

DIR=$(cd $(dirname "$0"); pwd)
BIN=$DIR"/../src"
ETC=$DIR"/../src/etc"

echo "Launching Poller (that launch checks)"
$BIN/shinken-poller.py -d -c $ETC/pollerd.cfg
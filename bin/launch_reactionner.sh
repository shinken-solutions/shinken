#!/bin/bash

DIR=$(cd $(dirname "$0"); pwd)
BIN=$DIR"/../bin"
ETC=$DIR"/../etc"

echo "Launching Reactionner (that sends the notifications)"
$BIN/shinken-reactionner -d -c $ETC/reactionnerd.ini

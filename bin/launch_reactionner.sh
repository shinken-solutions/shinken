#!/bin/bash

DIR=$(cd $(dirname "$0"); pwd)
BIN=$DIR"/../bin"
ETC=$DIR"/../etc"

echo "Launching Reactionner (that do notification send)"
$BIN/shinken-reactionner.py -d -c $ETC/reactionnerd.cfg
#!/bin/bash

DIR=$(cd $(dirname "$0"); pwd)
BIN=$DIR"/../bin"
ETC=$DIR"/../etc"

echo "Stopping reactionner"
kill `cat $DIR/../var/reactionnerd.pid`

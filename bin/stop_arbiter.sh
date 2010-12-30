#!/bin/bash

DIR=$(cd $(dirname "$0"); pwd)
BIN=$DIR"/../bin"
ETC=$DIR"/../etc"

echo "Stopping arbiter"
kill `cat $DIR/../var/arbiterd.pid`

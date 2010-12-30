#!/bin/bash

DIR=$(cd $(dirname "$0"); pwd)
BIN=$DIR"/../bin"
ETC=$DIR"/../etc"

echo "Stopping poller"
kill `cat $DIR/../var/pollerd.pid`

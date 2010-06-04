#!/bin/bash

DIR=$(cd $(dirname "$0"); pwd)
BIN=$DIR"/../src"
ETC=$DIR"/../src/etc"

echo "Stopping poller"
kill `cat $DIR/../src/var/pollerd.pid`
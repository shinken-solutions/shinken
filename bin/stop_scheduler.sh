#!/bin/bash

DIR=$(cd $(dirname "$0"); pwd)
BIN=$DIR"/../bin"
ETC=$DIR"/../etc"

echo "Stopping scheduler"
kill `cat $DIR/../var/schedulerd.pid`
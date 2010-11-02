#!/bin/bash

DIR=$(cd $(dirname "$0"); pwd)
BIN=$DIR"/../../bin"
ETC=$DIR"/../../etc/test_stack2"

echo "Stopping poller"
kill `cat $DIR/../../var/pollerd-2.pid`

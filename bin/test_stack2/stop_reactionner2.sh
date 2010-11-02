#!/bin/bash

DIR=$(cd $(dirname "$0"); pwd)
BIN=$DIR"/../../bin"
ETC=$DIR"/../../etc/test_stack2"

echo "Stopping reactionner"
kill `cat $DIR/../../var/reactionnerd-2.pid`

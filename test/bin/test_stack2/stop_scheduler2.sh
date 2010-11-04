#!/bin/bash

DIR=$(cd $(dirname "$0"); pwd)
BIN=$DIR"/../../bin"
ETC=$DIR"/../../etc/test_stack2"

echo "Stopping scheduler"
kill `cat $DIR/../../var/schedulerd-2.pid`

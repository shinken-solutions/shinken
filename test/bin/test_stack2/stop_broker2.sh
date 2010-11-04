#!/bin/bash

DIR=$(cd $(dirname "$0"); pwd)
BIN=$DIR"/../../bin"
ETC=$DIR"/../../etc/test_stack2"

echo "Stopping broker"

parent=`cat $DIR/../../var/brokerd-2.pid`

# kill parent and childs broker processes
for brokerpid in $(ps -aef | grep $parent | grep "shinken-broker" | awk '{print $2}')
do
	kill $brokerpid
done


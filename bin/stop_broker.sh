#!/bin/bash

DIR=$(cd $(dirname "$0"); pwd)
BIN=$DIR"/../bin"
ETC=$DIR"/../etc"

echo "Stopping broker"

parent=`cat $DIR/../var/brokerd.pid`

# kill parent and childs broker processes
for brokerpid in $(ps -aef | grep $parent | grep "shinken-broker.py" | awk '{print $2}')
do
	kill $brokerpid
done


#!/bin/sh

DIR=$(readlink -f $(dirname "$0")/..)

if [ "$DIR" == "" ]; then
    echo "DIR MUST NOT BE EMPTY. I WONT TRY TO REMOVE /TMP"
    exit 2
fi

if [ "$1" == "start" ]; then
    if [ ! -d "$DIR/tmp/mongodb" ]; then
        mkdir "$DIR/tmp/mongodb"
    fi
    mongod --dbpath $DIR/tmp/mongodb --smallfiles --pidfilepath $DIR/tmp/pid.txt --fork --logpath $DIR/tmp/log.txt & 
elif [ "$1" == "stop" ]; then
    kill $(cat $DIR/tmp/pid.txt)
    rm -rf $DIR/tmp/mongodb/* $DIR/tmp/pid.txt $DIR/tmp/log.txt
else
    echo "Option $1 not recognized"
fi

sleep 3

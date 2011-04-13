#!/bin/bash

DIR=$(cd $(dirname "$0"); pwd)
echo "Going to dir" $DIR

cd $DIR/..

export LANG=us_US.UTF-8

$DIR/launch_scheduler.sh
$DIR/launch_poller.sh
$DIR/launch_reactionner.sh
$DIR/launch_broker.sh
$DIR/launch_receiver.sh
$DIR/launch_arbiter.sh

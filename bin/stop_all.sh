#!/bin/bash

DIR=$(cd $(dirname "$0"); pwd)
echo $DIR


$DIR/stop_scheduler.sh
$DIR/stop_poller.sh
$DIR/stop_reactionner.sh
$DIR/stop_broker.sh
$DIR/stop_arbiter.sh



#!/bin/bash

DIR=$(cd $(dirname "$0"); pwd)
echo $DIR


$DIR/launch_scheduler_debug.sh
$DIR/launch_poller_debug.sh
$DIR/launch_reactionner_debug.sh
$DIR/launch_broker_debug.sh
$DIR/launch_arbiter_debug.sh



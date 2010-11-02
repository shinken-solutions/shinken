#!/bin/bash

DIR=$(cd $(dirname "$0"); pwd)
echo $DIR

#Schedulers
$DIR/launch_scheduler_debug.sh
$DIR/test_stack2/launch_scheduler2_debug.sh

#pollers
$DIR/launch_poller_debug.sh
$DIR/test_stack2/launch_poller2_debug.sh

#reactionners
$DIR/launch_reactionner_debug.sh
$DIR/test_stack2/launch_reactionner2_debug.sh

#brokers
$DIR/launch_broker_debug.sh
$DIR/test_stack2/launch_broker2_debug.sh


#From now only one arbtier
$DIR/launch_arbiter2_debug.sh



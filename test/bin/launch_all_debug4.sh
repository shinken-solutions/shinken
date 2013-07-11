#!/bin/bash

DIR=$(cd $(dirname "$0"); pwd)
echo $DIR

# Prepare the launch by cleaning var/log directories
. $DIR/../../bin/preparedev


# Schedulers
$DIR/../../bin/launch_scheduler_debug.sh
$DIR/test_stack2/launch_scheduler2_debug.sh

# pollers
$DIR/../../bin/launch_poller_debug.sh
$DIR/test_stack2/launch_poller2_debug.sh

# reactionners
$DIR/../../bin/launch_reactionner_debug.sh
$DIR/test_stack2/launch_reactionner2_debug.sh

# brokers
$DIR/../../bin/launch_broker_debug.sh
$DIR/test_stack2/launch_broker2_debug.sh

# One receiver
$DIR/../../bin/launch_receiver_debug.sh

# From now only one arbtier
$DIR/launch_arbiter4_debug.sh



#!/bin/bash

DIR=$(cd $(dirname "$0"); pwd)
echo $DIR

$DIR/stop_all.sh
$DIR/test_stack2/stop_scheduler2.sh
$DIR/test_stack2/stop_poller2.sh
$DIR/test_stack2/stop_reactionner2.sh
$DIR/test_stack2/stop_broker2.sh
# We do not have an arbiter in the stack2 from now :(
#$DIR/stop_arbiter2.sh



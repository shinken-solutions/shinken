#!/bin/sh
if [ -n "$1" ]; then
  SLEEP=$1
else
  SLEEP=10
fi
sleep $SLEEP
echo "I awoke after sleeping $SLEEP seconds | sleep=$SLEEP"
exit 0

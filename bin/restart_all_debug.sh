#!/bin/sh

DIR="$(cd $(dirname "$0"); pwd)"
"$DIR"/stop_all.sh
sleep 3
"$DIR"/launch_all_debug.sh

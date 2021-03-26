#!/bin/sh

DIR=$(cd $(dirname "$0"); pwd)
cd $DIR
echo "$PWD"

for ii in $(ls -1 test_*py) ; do
    echo "Launching Test $ii"
    python2 $ii
done

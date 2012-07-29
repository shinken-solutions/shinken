#!/bin/sh

DIR=$(cd $(dirname "$0"); pwd)
cd $DIR
echo "$PWD"
#python test_problem_impact.py
for ii in `ls -1 test_*py`; do echo "Launching Test $ii" && python $ii; done

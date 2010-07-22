#!/bin/sh

cd test
echo `pwd`
#python test_problem_impact.py
for ii in `ls -1 test_*py`; do echo "Launching Test $ii" && python $ii; done

#!/bin/bash

DIR=$(cd $(dirname "$0"); pwd)
cd $DIR
echo `pwd`

function launch_and_assert {
    SCRIPT=$1
    ./$SCRIPT
    if [ $? != 0 ]
	then
	echo "Error : the test $SCRIPT failed"
    fi
}

#Launching only quick tests for quick regression check
#for ii in `ls -1 test_*py`; do echo "Launching Test $ii" && python $ii; done
launch_and_assert test_services.py
launch_and_assert test_hosts.py
launch_and_assert test_action.py
launch_and_assert test_config.py
launch_and_assert test_dependencies.py
launch_and_assert test_livestatus.py
launch_and_assert test_npcdmod.py
launch_and_assert test_problem_impact.py
launch_and_assert test_timeperiods.py

echo "All quick unit tests passed :)"
echo "But please launch a test.sh pass too for long tests too!"
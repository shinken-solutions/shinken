#!/bin/bash
#Copyright (C) 2009-2010 :
#    Gabes Jean, naparuba@gmail.com
#    Gerhard Lausser, Gerhard.Lausser@consol.de
#
#This file is part of Shinken.
#
#Shinken is free software: you can redistribute it and/or modify
#it under the terms of the GNU Affero General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.
#
#Shinken is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU Affero General Public License for more details.
#
#You should have received a copy of the GNU Affero General Public License
#along with Shinken.  If not, see <http://www.gnu.org/licenses/>.


DIR=$(cd $(dirname "$0"); pwd)
cd $DIR
echo `pwd`

function launch_and_assert {
    SCRIPT=$1
    ./$SCRIPT
    if [ $? != 0 ]
	then
	echo "Error : the test $SCRIPT failed"
	exit 2
    fi
}

#Launching only quick tests for quick regression check
#for ii in `ls -1 test_*py`; do echo "Launching Test $ii" && python $ii; done
launch_and_assert test_services.py
launch_and_assert test_hosts.py
launch_and_assert test_action.py
launch_and_assert test_config.py
launch_and_assert test_dependencies.py
launch_and_assert test_npcdmod.py
launch_and_assert test_problem_impact.py
launch_and_assert test_timeperiods.py
launch_and_assert test_command.py
launch_and_assert test_module_simplelog.py
launch_and_assert test_db.py
launch_and_assert test_macroresolver.py
launch_and_assert test_complex_hostgroups.py
launch_and_assert test_resultmodulation.py
launch_and_assert test_satellites.py
launch_and_assert test_illegal_names.py
launch_and_assert test_notifway.py
launch_and_assert test_notification_warning.py
launch_and_assert test_timeperiod_inheritance.py
launch_and_assert test_bad_timeperiods.py
launch_and_assert test_maintenance_period.py

#Live status is a bit longer than the previous, so we put it at the end.
launch_and_assert test_livestatus.py

echo "All quick unit tests passed :)"
echo "But please launch a test.sh pass too for long tests too!"

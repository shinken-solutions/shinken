#!/bin/bash
# Copyright (C) 2009-2014:
#     Gabes Jean, naparuba@gmail.com
#     Gerhard Lausser, Gerhard.Lausser@consol.de
#
# This file is part of Shinken.
#
# Shinken is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Shinken is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with Shinken.  If not, see <http://www.gnu.org/licenses/>.


DIR=$(cd $(dirname "$0"); pwd)
cd $DIR
echo "$PWD"

# delete the result of nosetest, for coverage
rm -f nosetests.xml
rm -f coverage.xml
rm -f .coverage

function launch_and_assert {
    SCRIPT=$1
    #nosetests -v -s --with-xunit --with-coverage ./$SCRIPT
    python ./$SCRIPT
    if [ $? != 0 ] ; then
	echo "Error: the test $SCRIPT failed"
	exit 2
    fi
}

for ii in `ls -1 test_*py`; do launch_and_assert $ii; done
# And create the coverage file
python-coverage xml --omit=/usr/lib

echo "All quick unit tests passed :)"
echo "But please launch a test.sh pass too for long tests too!"

exit 0

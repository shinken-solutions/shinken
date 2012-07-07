#!/bin/bash

# Copyright (C) 2009-2011:
#    Gabes Jean, naparuba@gmail.com
#    Gerhard Lausser, Gerhard.Lausser@consol.de
#    Gregory Starck, g.starck@gmail.com
#    Hartmut Goebel, h.goebel@goebel-consult.de
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
# along with Shinken.  If not, see <http://www.gnu.org/licenses/>.ses/>.

#####################################
# BELOW DETAILS ABOUT SKIPPED RULES #
#####################################

## E303 ##
# Number of blank lines between two methods

DIR=$(cd $(dirname "$0"); pwd)
cd $DIR
echo "Working dir is $PWD"

echo "Launching pep8 stat pass"
cd ..

pep8  --max-line-length=100 --ignore=E303 shinken/ > $DIR/pep8.txt
echo "Pep8 pass done, you can find the result in $DIR/pep8.txt"

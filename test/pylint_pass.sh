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

echo "Launching pylint stat pass"
cd ..
pylint -f parseable --disable-msg=C0111,C0103,W0201,E1101 --max-line-length 90 shinken/ shinken/modules/*/*py > $DIR/pylint.txt
cd $DIR
echo "Pylint pass done, congrats or not? ;) "


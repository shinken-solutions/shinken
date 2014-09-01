#!/bin/bash

# Copyright (C) 2009-2014:
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

## C0111: *Missing docstring*
# Used when a module, function, class or method has no docstring. Some special
# methods like __init__ doesn't necessary require a docstring.

## C0103: *Invalid name "%s" (should match %s)*
# Used when the name doesn't match the regular expression associated to its type
# (constant, variable, class...)..

## W0201: *Attribute %r defined outside __init__*
# Used when an instance attribute is defined outside the __init__ method.

## C0302: *Too many lines in module (%s)*
# Used when a module has too much lines, reducing its readability.

## R0904: *Too many public methods (%s/%s)*
# Used when class has too many public methods, try to reduce this to get a more
# simple (and so easier to use) class.

## R0902: *Too many instance attributes (%s/%s)*
# Used when class has too many instance attributes, try to reduce this to get a
# more simple (and so easier to use) class.

## W0511:
# Used when a warning note as FIXME or XXX is detected.

DIR=$(cd $(dirname "$0"); pwd)
cd $DIR
echo "Working dir is $PWD"

echo "Launching pylint stat pass"
cd ..
pylint -f parseable --disable-msg=C0111,C0103,W0201,C0302,R0904,R0902,W0511 --max-line-length 100 shinken/ shinken/modules/*/*py > $DIR/pylint.txt
echo "Pylint pass done, you can find the result in $DIR/pylint.txt"

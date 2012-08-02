#!/bin/bash
#
# Copyright (C) 2009-2012:
#    Gabes Jean, naparuba@gmail.com
#    Gerhard Lausser, Gerhard.Lausser@consol.de
#    David GUENAULT, dguenault@monitoring-fr.org
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

# environement
export myscripts=$(readlink -f $(dirname $0))

export plugins="nagios-plugins
check_mysql_health check_wmi_plus check_mongodb check_emc_clariion
check_nwc_health capture_plugin"
export addons="pnp4nagios multisite"

cd $myscripts
./shinken.sh -i

if [ $? -ne 0 ]
then
    exit 2
fi

for p in $plugins
do
    ./shinken.sh -p $p
    if [ $? -ne 0 ]
    then
        exit 2
    fi
done

for m in $modules
do
    ./shinken.sh -p $p
    if [ $? -ne 0 ]
    then
        exit 2
    fi
done

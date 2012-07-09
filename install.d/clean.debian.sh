#!/bin/bash
#set -x
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

if [ -f /tmp/shinken.install.log ]
then
    rm -f /tmp/shinken.install.log
fi

#####################
### ENVIRONNEMENT ###
#####################

export myscripts=$(readlink -f $(dirname $0))
src=$(readlink -f "$myscripts/../../..")
. $myscripts/shinken.conf

cecho "###########################################################" red
cecho "# CAUTION THIS SCRIPT IS USED ONLY IN DEVELOPMENT PROCESS  " red
cecho "# IT COULD BREAK YOUR SYSTEM! PRESS CTRL+C TO ABORT        " red
cecho "###########################################################" red
read taste
path="/usr/local/lib/$(pythonver)/dist-packages"
pyver=$(pythonvershort)
pth="eeasy-install.pth"
for p in $PYLIBSDEB
do
    module=$(echo $p | awk -F\: '{print $1}')
    cecho " > going to remove python module: $module" yellow
    echo $path/$module
    if [ ! -z "$(ls -1 $path/$module*)" ]
    then
        cecho " > Found $path/$module" yellow
        res=$(easy_install-$pyver -m $module | grep "^Using" | awk '{print $2}')
        if [ ! -z "$res" ]
        then
            rm -Rf $res
        fi
    fi

done
APTLIST="$APTPKGS $VSPHERESDKAPTPKGS $NAGPLUGAPTPK $CHECKORACLEHEALTHAPTPKG $CHECKMONGOAPTPKG $CHECKEMCAPTPKG $CHECKNWCAPTPKG $PNPAPTPKG $MKAPTPKG $WMICAPTPKG $CHECKHPASMAPTPKGS"
for l in $APTLIST
do
    for p in $l
    do
        cecho " > remove $p" yellow
        apt-get purge $p
    done
done
apt-get autoremove

rm -Rf $PNPPREFIX
rm -Rf $MKPREFIX

rm -f /etc/apache2/conf.d/zzz_check_mk.conf
rm -f /etc/apache2/conf.d/pnp4nagios.conf

/etc/init.d/apache2 restart

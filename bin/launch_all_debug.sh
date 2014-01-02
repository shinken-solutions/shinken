#!/bin/sh
#
# Copyright (C) 2009-2012:
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
# along with Shinken.  If not, see <http://www.gnu.org/licenses/>.


DIR="$(cd $(dirname "$0"); pwd)"
echo "$DIR"

# Prepare the launch by cleaning var/log directories
. $DIR/preparedev

cd "$DIR/.."

export LANG=us_US.UTF-8
# Protect against proxy variable for dev
unset http_proxy
unset https_proxy


"$DIR"/launch_scheduler_debug.sh
"$DIR"/launch_poller_debug.sh
"$DIR"/launch_reactionner_debug.sh
"$DIR"/launch_broker_debug.sh
"$DIR"/launch_receiver_debug.sh
"$DIR"/launch_arbiter_debug.sh

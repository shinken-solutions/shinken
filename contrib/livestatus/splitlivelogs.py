#!/usr/bin/env python2
# Copyright (C) 2009-2014:
#    Gabes Jean, naparuba@gmail.com
#    Gerhard Lausser, Gerhard.Lausser@consol.de
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

"""
This script will take the sqlite database of the livestatus module and
split up the contents in single datafiles (1 for each day of data found).
"""

import sys
import optparse
import os

sys.path.append("..")
sys.path.append("../shinken")
sys.path.append("../../shinken")
sys.path.append("../../../shinken")
#sys.path.append("../bin")
#sys.path.append(os.path.abspath("bin"))


#import shinken
from shinken.modules.livestatus_broker.livestatus_db import LiveStatusDb

parser = optparse.OptionParser(
    "%prog [options] -d database [-a archive]")
parser.add_option('-d', '--database', action='store',
                  dest="database",
                  help="The sqlite datafile of your livestatus module")
parser.add_option('-a', '--archive', action='store',
                  dest="archive_path",
                  help="(optional) path to the archive directory")

opts, args = parser.parse_args()

if not opts.database:
    parser.error("Requires at least the database file (option -d/--database")
if not opts.archive_path:
    opts.archive_path = os.path.join(os.path.dirname(opts.database), 'archives')
    pass

# Protect for windows multiprocessing that will RELAUNCH all
if __name__ == '__main__':
    if os.path.exists(opts.database):
        try:
            os.stat(opts.archive_path)
        except Exception:
            os.mkdir(opts.archive_path)
        dbh = LiveStatusDb(opts.database, opts.archive_path, 3600)
        dbh.log_db_do_archive()
        dbh.close()
    else:
        print "database %s does not exist" % opts.database


# For perf tuning:

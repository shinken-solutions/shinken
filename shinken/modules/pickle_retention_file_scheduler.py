#!/usr/bin/python
# -*- coding: utf-8 -*-
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

# This Class is an example of an Scheduler module
# Here for the configuration phase AND running one

import cPickle
import shutil

from shinken.basemodule import BaseModule
from shinken.log import logger

# Hack for making 0.5 retetnion file load in a 0.6 version
# because the commandCall class was moved
import shinken
from shinken.commandcall import CommandCall
shinken.objects.command.CommandCall = CommandCall

properties = {
    'daemons': ['scheduler'],
    'type': 'pickle_retention_file',
    'external': False,
    }


def get_instance(plugin):
    """
    Called by the plugin manager to get a broker
    """
    print "Get a pickle retention scheduler module for plugin %s" % plugin.get_name()
    path = plugin.path
    instance = Pickle_retention_scheduler(plugin, path)
    return instance


class Pickle_retention_scheduler(BaseModule):
    def __init__(self, modconf, path):
        BaseModule.__init__(self, modconf)
        self.path = path

    def hook_save_retention(self, daemon):
        """
        main function that is called in the retention creation pass
        """
        self.update_retention_objects(daemon, logger)

    # The real function, this wall module will be soonly removed
    def update_retention_objects(self, sched, log_mgr):
        print "[PickleRetention] asking me to update the retention objects"
        # Now the flat file method
        try:
            # Open a file near the path, with .tmp extension
            # so in case of a problem, we do not lose the old one
            f = open(self.path + '.tmp', 'wb')
            # Just put hosts/services becauses checks and notifications
            # are already link into
            # all_data = {'hosts': sched.hosts, 'services': sched.services}

            # We create a all_data dict with lsit of dict of retention useful
            # data of our hosts and services
            all_data = sched.get_retention_data()

            #s = cPickle.dumps(all_data)
            #s_compress = zlib.compress(s)
            cPickle.dump(all_data, f, protocol=cPickle.HIGHEST_PROTOCOL)
            #f.write(s_compress)
            f.close()
            # Now move the .tmp file to the real path
            shutil.move(self.path + '.tmp', self.path)
        except IOError, exp:
            log_mgr.log("Error: retention file creation failed, %s" % str(exp))
            return
        log_mgr.log("Updating retention_file %s" % self.path)

    def hook_load_retention(self, daemon):
        return self.load_retention_objects(daemon, logger)

    # Should return if it succeed in the retention load or not
    def load_retention_objects(self, sched, log_mgr):
        print "[PickleRetention] asking me to load the retention objects"

        # Now the old flat file way :(
        log_mgr.log("[PickleRetention]Reading from retention_file %s" % self.path)
        try:
            f = open(self.path, 'rb')
            all_data = cPickle.load(f)
            f.close()
        except EOFError, exp:
            print exp
            return False
        except ValueError, exp:
            print exp
            return False
        except IOError, exp:
            print exp
            return False
        except IndexError, exp:
            s = "WARNING: Sorry, the ressource file is not compatible"
            log_mgr.log(s)
            return False
        except TypeError, exp:
            s = "WARNING: Sorry, the ressource file is not compatible"
            log_mgr.log(s)
            return False

        # call the scheduler helper function for restoring values
        sched.restore_retention_data(all_data)

        log_mgr.log("[PickleRetention] OK we've load data from retention file")

        return True

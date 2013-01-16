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
import traceback

from shinken.basemodule import BaseModule
from shinken.log import logger

# Hack for making 0.5 retention file load in a 0.6 version
# because the commandCall class was moved
import shinken
from shinken.commandcall import CommandCall
shinken.objects.command.CommandCall = CommandCall

properties = {
    'daemons': ['broker', 'arbiter', 'scheduler'],
    'type': 'pickle_retention_file_generic',
    'external': False,
    }


def get_instance(plugin):
    """
    Called by the plugin manager to get a broker
    """
    logger.debug("Get a pickle retention generic module for plugin %s" % plugin.get_name())
    path = plugin.path
    instance = Pickle_retention_generic(plugin, path)
    return instance


class Pickle_retention_generic(BaseModule):
    def __init__(self, modconf, path):
        BaseModule.__init__(self, modconf)
        self.path = path

    def hook_save_retention(self, daemon):
        """
        main function that is called in the retention creation pass
        """
        logger.debug("[PickleRetentionGeneric] asking me to update the retention objects")

        # Now the flat file method
        try:
            # Open a file near the path, with .tmp extension
            # so in case of a problem, we do not lost the old one
            f = open(self.path + '.tmp', 'wb')

            # We get interesting retention data from the daemon it self
            all_data = daemon.get_retention_data()

            # And we save it on file :)
            cPickle.dump(all_data, f, protocol=cPickle.HIGHEST_PROTOCOL)
            f.close()

            # Now move the .tmp file to the real path
            shutil.move(self.path + '.tmp', self.path)
        except IOError, exp:
            logger.error("Creating retention file failed %s" % str(exp))
            return
        logger.info("Updating retention_file %s" % self.path)

    # Should return if it succeed in the retention load or not
    def hook_load_retention(self, daemon):

        logger.debug("[PickleRetentionGeneric]Reading from retention_file %s" % self.path)
        # Now the old flat file way :(
        try:
            f = open(self.path, 'rb')
            all_data = cPickle.load(f)
            f.close()
        except (EOFError, ValueError, IOError), exp:
            logger.warning(repr(exp))
            return False
        except (IndexError, TypeError), exp:
            logger.warning("Sorry, the resource file is not compatible")
            return False

        # Ok, we send back the data to the daemon
        daemon.restore_retention_data(all_data)

        logger.info("[PickleRetentionGeneric] Retention objects loaded successfully.")

        return True

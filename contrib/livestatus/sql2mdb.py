#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (C) 2009-2014:
#    Gabes Jean, naparuba@gmail.com
#    Gerhard Lausser, Gerhard.Lausser@consol.de
#    Olivier Hanesse, olivier.hanesse@gmail.com
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

from __future__ import absolute_import, division, print_function, unicode_literals

import sys
import time
import os

try:
    import shinken
except ImportError:
    # If importing shinken fails, try to load from current directory
    # or parent directory to support running without installation.
    # Submodules will then be loaded from there, too.
    import imp
    imp.load_module('shinken', *imp.find_module('shinken', [os.path.realpath("."), os.path.realpath(".."), os.path.join(os.path.abspath(os.path.dirname(sys.argv[0])), "..")]))

from shinken.objects.config import Config
from shinken.log import logger
from shinken.modules.logstore_sqlite import get_instance as get_instance_sqlite
from shinken.modules.logstore_mongodb import get_instance as get_instance_mongodb
from shinken.modules.logstore_sqlite import LiveStatusLogStoreError
from shinken.modules.livestatus_broker.log_line import Logline

class Dummy:
    def add(self, o):
        pass

def row_factory(cursor, row):
    """Handler for the sqlite fetch method."""
    return Logline(sqlite_cursor=cursor.description, sqlite_row=row)


class Converter(object):
    def __init__(self, file):

        logger.load_obj(Dummy())
        self.conf = Config()
        buf = self.conf.read_config([file])
        raw_objects = self.conf.read_config_buf(buf)
        self.conf.create_objects_for_type(raw_objects, 'arbiter')
        self.conf.create_objects_for_type(raw_objects, 'module')
        self.conf.early_arbiter_linking()
        self.conf.create_objects(raw_objects)
        for mod in self.conf.modules:
            if mod.module_type == 'logstore_sqlite':
                self.mod_sqlite = get_instance_sqlite(mod)
                self.mod_sqlite.init()
            if mod.module_type == 'logstore_mongodb':
                self.mod_mongodb = get_instance_mongodb(mod)


if __name__ == '__main__':
    if (len(sys.argv) < 2):
        print("usage: sql2mdb shinken-specifig.cfg")
        sys.exit(1)
    conv = Converter(sys.argv[1])
    print(conv.mod_mongodb)
    print(conv.mod_sqlite)
    print(conv.mod_sqlite.archive_path)
    conv.mod_sqlite.use_aggressie_sql = False

    try:
        conv.mod_sqlite.open()
    except Exception as e:
        print("problem opening the sqlite db", e)
        sys.exit(1)
    try:
        conv.mod_mongodb.open()
    except Exception as e:
        conv.mod_sqlite.close()
        print("problem opening the mongodb", e)
        sys.exit(1)

    for dateobj, handle, archive, fromtime, totime in conv.mod_sqlite.log_db_relevant_files(0, time.time()):
        try:
            if handle == "main":
                print("attach %s" % archive)
                dbresult = conv.mod_sqlite.execute('SELECT * FROM logs', [], row_factory)
            else:
                conv.mod_sqlite.commit()
                print("attach %s" % archive)
                conv.mod_sqlite.execute_attach("ATTACH DATABASE '%s' AS %s" % (archive, handle))
                dbresult = conv.mod_sqlite.execute('SELECT * FROM %s.logs' % (handle,), [], row_factory)
                conv.mod_sqlite.execute("DETACH DATABASE %s" % handle)
            # now we have the data of one day
            for res in dbresult:
                values = res.as_dict()
                try:
                    conv.mod_mongodb.db[conv.mod_mongodb.collection].insert(values)
                except Exception as e:
                    print("problem opening the mongodb", e)
                    time.sleep(5)
                    conv.mod_mongodb.db[conv.mod_mongodb.collection].insert(values)
            print("wrote %d records" % len(dbresult))

        except LiveStatusLogStoreError as e:
            print("An error occurred:", e.args[0])
    conv.mod_sqlite.close()
    conv.mod_mongodb.close()


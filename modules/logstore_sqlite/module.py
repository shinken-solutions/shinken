#!/usr/bin/python

# -*- coding: utf-8 -*-

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

# import von modules/livestatus_logstore

"""
This class is for attaching a sqlite database to a livestatus broker module.
It is one possibility for an exchangeable storage for log broks
"""

import os
import sys
import time
import datetime
import re
from shinken.objects.service import Service
from shinken.log import logger
from shinken.modulesctx import modulesctx


livestatus_broker = modulesctx.get_module('livestatus')

# Import a class from the livestatus module, should be already loaded!
#from shinken.modules.livestatus import module as livestatus_broker
LiveStatusStack = livestatus_broker.LiveStatusStack
LOGCLASS_INVALID = livestatus_broker.LOGCLASS_INVALID
Logline = livestatus_broker.Logline


old_implementation = False
try:
    import sqlite3
except ImportError:  # python 2.4 do not have it
    try:
        import pysqlite2.dbapi2 as sqlite3  # but need the pysqlite2 install from http://code.google.com/p/pysqlite/downloads/list
    except ImportError:  # python 2.4 do not have it
        import sqlite as sqlite3  # one last try
        old_implementation = True

from shinken.basemodule import BaseModule
from shinken.objects.module import Module

properties = {
    'daemons': ['livestatus'],
    'type': 'logstore_sqlite',
    'external': False,
    'phases': ['running'],
    }


# called by the plugin manager
def get_instance(plugin):
    logger.info("[Logstore SQLite] Get an LogStore Sqlite module for plugin %s" % plugin.get_name())
    instance = LiveStatusLogStoreSqlite(plugin)
    return instance


def row_factory(cursor, row):
    """Handler for the sqlite fetch method."""
    return Logline(sqlite_cursor=cursor.description, sqlite_row=row)


class LiveStatusLogStoreError(Exception):
    pass


class LiveStatusLogStoreSqlite(BaseModule):

    def __init__(self, modconf):
        BaseModule.__init__(self, modconf)
        self.plugins = []
        # Change. The var folder is not defined based upon '.', but upon ../var from the process name (shinken-broker)
        # When the database_file variable, the default variable was calculated from '.'... Depending on where you were 
        # when you ran the command the behavior changed.
        self.database_file = getattr(modconf, 'database_file', os.path.join(os.path.abspath('.'), 'livestatus.db'))
        self.archive_path = getattr(modconf, 'archive_path', os.path.join(os.path.dirname(self.database_file), 'archives'))
        try:
            os.stat(self.archive_path)
        except:
            os.mkdir(self.archive_path)
        max_logs_age = getattr(modconf, 'max_logs_age', '365')
        maxmatch = re.match(r'^(\d+)([dwmy]*)$', max_logs_age)
        if maxmatch is None:
            logger.warning("[Logstore SQLite] Warning: wrong format for max_logs_age. Must be <number>[d|w|m|y] or <number> and not %s" % max_logs_age)
            return None
        else:
            if not maxmatch.group(2):
                self.max_logs_age = int(maxmatch.group(1))
            elif maxmatch.group(2) == 'd':
                self.max_logs_age = int(maxmatch.group(1))
            elif maxmatch.group(2) == 'w':
                self.max_logs_age = int(maxmatch.group(1)) * 7
            elif maxmatch.group(2) == 'm':
                self.max_logs_age = int(maxmatch.group(1)) * 31
            elif maxmatch.group(2) == 'y':
                self.max_logs_age = int(maxmatch.group(1)) * 365
        self.use_aggressive_sql = (getattr(modconf, 'use_aggressive_sql', '0') == '1')
        self.read_only = (getattr(modconf, 'read_only', '0') == '1')

        # This stack is used to create a full-blown select-statement
        self.sql_filter_stack = LiveStatusSqlStack()
        # This stack is used to create a minimal select-statement which
        # selects only by time >= and time <=
        self.sql_time_filter_stack = LiveStatusSqlStack()

        # Now sleep one second, so that won't get lineno collisions with the last second
        time.sleep(1)
        Logline.lineno = 0

    def load(self, app):
        self.app = app

    def init(self):
        self.old_implementation = old_implementation

    def open(self):
        logger.info("[Logstore SQLite] Open LiveStatusLogStoreSqlite ok : %s" % self.database_file)
        self.dbconn = sqlite3.connect(self.database_file, check_same_thread=False)
        # Get no problem for utf8 insert
        self.dbconn.text_factory = str
        self.dbcursor = self.dbconn.cursor()
        #self.dbconn.row_factory = row_factory
        #self.execute("PRAGMA cache_size = 200000")
        # Create db file and tables if not existing
        self.prepare_log_db_table()
        # Start with commit and rotate immediately so the interval timers
        # get initialized properly
        now = time.time()
        self.next_log_db_commit = now
        self.next_log_db_rotate = now
        # Immediately archive data. This also splits old-style (storing logs
        # from more than one day) up into many single-day databases
        if self.max_logs_age > 0:
            # open() is also called from log_db_do_archive (with max_logs_age
            # of 0 though)
            self.log_db_do_archive()

    def close(self):
        self.dbconn.commit()
        self.dbconn.close()
        self.dbconn = None
        if self.max_logs_age == 0:
            # Again, if max_logs_age is 0, we don't care for archives.
            # If max_logs_age was manually set to 0, we know that we don't
            # want archives. If it was set by log_db_do_archive(), we don't
            # want to leave empty directories around.
            try:
                os.removedirs(self.archive_path)
            except:
                pass

    def prepare_log_db_table(self):
        if self.read_only:
            return
        # 'attempt', 'class', 'command_name', 'comment', 'contact_name', 'host_name', 'lineno', 'message',
        # 'plugin_output', 'service_description', 'state', 'state_type', 'time', 'type',
        cmd = "CREATE TABLE IF NOT EXISTS logs(logobject INT, attempt INT, class INT, command_name VARCHAR(64), comment VARCHAR(256), contact_name VARCHAR(64), host_name VARCHAR(64), lineno INT, message VARCHAR(512), options VARCHAR(512), plugin_output VARCHAR(256), service_description VARCHAR(64), state INT, state_type VARCHAR(10), time INT, type VARCHAR(64))"
        self.execute(cmd)
        cmd = "CREATE INDEX IF NOT EXISTS logs_time ON logs (time)"
        self.execute(cmd)
        cmd = "CREATE INDEX IF NOT EXISTS logs_host_name ON logs (host_name)"
        self.execute(cmd)
        cmd = "PRAGMA journal_mode=truncate"
        self.execute(cmd)
        self.commit()

    def commit_and_rotate_log_db(self):
        """Submit a commit or rotate the complete database file.

        This function is called whenever the mainloop doesn't handle a request.
        The database updates are committed every second.
        Every day at 00:05 the database contents with a timestamp of past days
        are moved to their own datafiles (one for each day). We wait until 00:05
        because in a distributed environment even after 00:00 (on the broker host)
        we might receive data from other hosts with a timestamp dating from yesterday.
        """
        if self.read_only:
            return
        now = time.time()
        if self.next_log_db_commit <= now:
            self.commit()
            logger.debug("[Logstore SQLite] commit.....")
            self.next_log_db_commit = now + 1
        if self.next_log_db_rotate <= now:
            logger.info("[Logstore SQLite] at %s we rotate the database file" % time.asctime(time.localtime(now)))
            # Take the current database file
            # Move the messages into daily files
            self.log_db_do_archive()

            today = datetime.date.today()
            today0005 = datetime.datetime(today.year, today.month, today.day, 0, 5, 0)
            if now < time.mktime(today0005.timetuple()):
                nextrotation = today0005
            else:
                nextrotation = today0005 + datetime.timedelta(days=1)

            # See you tomorrow
            self.next_log_db_rotate = time.mktime(nextrotation.timetuple())
            logger.info("[Logstore SQLite] next rotation at %s " % time.asctime(time.localtime(self.next_log_db_rotate)))

    def log_db_historic_contents(self):
        """
        Find out which time range is covered by the current datafile.
        Return a list of historic datafiles which can be used to split up
        the contents of the current datafile.
        """
        try:
            dbresult = self.execute('SELECT MIN(time),MAX(time) FROM logs')
            mintime = dbresult[0][0]
            maxtime = dbresult[0][1]
        except sqlite3.Error, e:
            logger.error("[Logstore SQLite] An error occurred: %s" % str(e.args[0]))
        except IndexError, e:
            mintime = int(time.time())
            maxtime = int(time.time())

        if mintime is None:
            mintime = int(time.time())
        if maxtime is None:
            maxtime = int(time.time())
        return self.log_db_relevant_files(mintime, maxtime, True)

    def log_db_relevant_files(self, mintime, maxtime, preview=False):
        """
        Logging data created on different days are stored in separate
        datafiles. For each day there is one of them.
        Ths function takes a time range and returns the names of the files
        where the logging data of the days covered by the time range can
        be found.
        If the preview parameter is false, only names of existing files
        are returned.
        The result is a list with one element for each day. The elements
        themselves are lists consisting of the the following items:
        - A Datetime object
        - A short string of a day's date in the form db%Y%m%d
        - The filename of a datafile which contains the loggings of this day.
        - The unix timestamp of this day's 00:00 (start)
        - The unix timestamp of the day's 00:00 (end + 1s)
        Item no.2 can be used as a handle for the ATTACH-statement of sqlite.
        If the list element describes the current day, item no.2 is "main".
        """
        #print time.asctime(time.localtime(mintime))
        #print time.asctime(time.localtime(maxtime))
        minday = datetime.datetime.fromtimestamp(mintime)
        maxday = datetime.datetime.fromtimestamp(maxtime)
        minday = datetime.datetime(minday.year, minday.month, minday.day, 0, 0, 0)
        maxday = datetime.datetime(maxday.year, maxday.month, maxday.day, 0, 0, 0)
        #print time.asctime(time.localtime(time.mktime(minday.timetuple())))
        #print time.asctime(time.localtime(time.mktime(maxday.timetuple())))
        result = []
        today = datetime.date.today()
        today = datetime.datetime(today.year, today.month, today.day, 0, 0, 0)
        if maxday >= today:
            # Only loop until yesterday
            maxday = today - datetime.timedelta(days=1)
        thisday = minday
        while thisday <= maxday:
            nextday = thisday + datetime.timedelta(days=1)
            handle = "db" + thisday.strftime("%Y%m%d")
            archive = os.path.join(self.archive_path, os.path.splitext(os.path.basename(self.database_file))[0] + "-" + thisday.strftime("%Y-%m-%d") + ".db")
            if os.path.exists(archive) or preview:
                result.append([thisday, handle, archive, int(time.mktime(thisday.timetuple())), int(time.mktime(nextday.timetuple()))])
            thisday = nextday
        if maxtime >= int(time.mktime(today.timetuple())):
            # Also today's data are relevant, so we add the current database
            result.append([today, "main", self.database_file, int(time.mktime(today.timetuple())), maxtime])
        return result

    def log_db_do_archive(self):
        """
        In order to limit the datafile's sizes we flush logs dating from
        before today/00:00 to their own datafiles.
        """
        if self.read_only:
            return
        try:
            os.stat(self.archive_path)
        except:
            os.mkdir(self.archive_path)
        for day in self.log_db_historic_contents():
            dayobj, handle, archive, starttime, stoptime = day
            if handle == "main":
                # Skip archiving of today's contents
                continue
            if not os.path.exists(archive):
                # Create an empty datafile with the logs table
                #tmpconn = LiveStatusDb(archive, None, 0)
                #tmpconn.prepare_log_db_table()
                #tmpconn.close()

                dbmodconf = Module({
                    'module_name': 'LogStore',
                    'module_type': 'logstore_sqlite',
                    'use_aggressive_sql': '0',
                    'database_file': archive,
                    'max_logs_age': '0',
                })
                tmpconn = LiveStatusLogStoreSqlite(dbmodconf)
                tmpconn.open()
                tmpconn.close()

            self.commit()
            logger.info("[Logstore SQLite] move logs from %s - %s to database %s" % (time.asctime(time.localtime(starttime)), time.asctime(time.localtime(stoptime)), archive))
            cmd = "ATTACH DATABASE '%s' AS %s" % (archive, handle)
            self.execute_attach(cmd)
            cmd = "INSERT INTO %s.logs SELECT * FROM logs WHERE time >= %d AND time < %d" % (handle, starttime, stoptime)
            self.execute(cmd)
            cmd = "DELETE FROM logs WHERE time >= %d AND time < %d" % (starttime, stoptime)
            self.execute(cmd)
            self.commit()
            cmd = "DETACH DATABASE %s" % handle
            self.execute(cmd)
            # This is necessary to shrink the database file
            try:
                self.execute('VACUUM')
            except sqlite3.DatabaseError, exp:
                logger.error("[Logstore SQLite] WARNING: it seems your database is corrupted. Please recreate it")
            self.commit()

    def execute(self, cmd, values=None, row_factory=None):
        try:
            if values == None:
                values = []
            if sqlite3.paramstyle == 'pyformat':
                matchcount = 0
                for m in re.finditer(r"\?", cmd):
                    cmd = re.sub('\\?', '%(' + str(matchcount) + ')s', cmd, 1)
                    matchcount += 1
                values = dict(zip([str(x) for x in xrange(len(values))], values))
            if cmd.startswith("SELECT"):
                already_had_row_factory = hasattr(self.dbconn, "row_factory")
                if row_factory != None:
                    self.dbcursor.close()
                    if already_had_row_factory:
                        orig_row_factory = self.dbconn.row_factory
                    self.dbconn.row_factory = row_factory
                    # We need to create a new cursor which knows how to row_factory
                    # Simply setting conn.row_factory and using the old cursor
                    # would not work
                    self.dbcursor = self.dbconn.cursor()
                self.dbcursor.execute(cmd, values)
                dbresult = self.dbcursor.fetchall()
                if row_factory != None:
                    if sqlite3.paramstyle == 'pyformat':
                        dbresult = [row_factory(self.dbcursor, d) for d in dbresult]
                    if already_had_row_factory:
                        self.dbconn.row_factory = orig_row_factory
                    else:
                        delattr(self.dbconn, "row_factory")
                    self.dbcursor.close()
                    self.dbcursor = self.dbconn.cursor()
                return [x for x in dbresult]
                return dbresult
            else:
                self.dbcursor.execute(cmd, values)
        except sqlite3.Error, e:
            logger.error("[Logstore SQLite] execute error %s" % str(e))
            raise LiveStatusLogStoreError(e)

    def execute_attach(self, cmd):
        """
        Python 2.4 and old sqlite implementations show strange behavior.
        Attaching fails with the error:
        cannot ATTACH database within transaction
        That's why the ATTACH statement must be executed in it's own context.
        """
        if self.old_implementation:
            self.commit()
            orig_autocommit = self.dbconn.autocommit
            self.dbconn.autocommit = True
            cursor = self.dbconn.cursor()
            cursor.execute(cmd)
            cursor.close()
            self.dbconn.autocommit = orig_autocommit
            self.dbconn.commit()
        else:
            self.dbcursor.execute(cmd)

    def commit(self):
        start = time.time()
        while True:
            try:
                self.dbconn.commit()
                break
            except sqlite3.OperationalError:
                # If we wait more than 60s in the loop, maybe we should exit
                # than do an endless loop
                if time.time() - start > 60:
                    raise
                time.sleep(.01)

    def manage_log_brok(self, b):
        if self.read_only:
            return
        data = b.data
        line = data['log']
        if re.match("^\[[0-9]*\] [A-Z][a-z]*.:", line):
            # Match log which NOT have to be stored
            # print "Unexpected in manage_log_brok", line
            return 
        try:
            logline = Logline(line=line)
            values = logline.as_tuple()
            if logline.logclass != LOGCLASS_INVALID:
                self.execute('INSERT INTO LOGS VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', values)
        except LiveStatusLogStoreError, exp:
            logger.error("[Logstore SQLite] An error occurred: %s", str(exp.args[0]))
            logger.error("[Logstore SQLite] DATABASE ERROR!!!!!!!!!!!!!!!!!")
        except Exception, exp:
            logger.error("[Logstore SQLite] Unexpected in manage_log_brok: %s" % str(exp))
        # FIXME need access to this #self.livestatus.count_event('log_message')

    def add_filter(self, operator, attribute, reference):
        if attribute == 'time':
            self.sql_time_filter_stack.put_stack(self.make_sql_filter(operator, attribute, reference))
        self.sql_filter_stack.put_stack(self.make_sql_filter(operator, attribute, reference))

    def add_filter_and(self, andnum):
        self.sql_filter_stack.and_elements(andnum)

    def add_filter_or(self, ornum):
        self.sql_filter_stack.or_elements(ornum)

    def add_filter_not(self):
        self.sql_filter_stack.not_elements()

    def get_live_data_log(self):
        """Like get_live_data, but for log objects"""
        # finalize the filter stacks
        self.sql_time_filter_stack.and_elements(self.sql_time_filter_stack.qsize())
        self.sql_filter_stack.and_elements(self.sql_filter_stack.qsize())
        if self.use_aggressive_sql:
            # Be aggressive, get preselected data from sqlite and do less
            # filtering in python. But: only a subset of Filter:-attributes
            # can be mapped to columns in the logs-table, for the others
            # we must use "always-true"-clauses. This can result in
            # funny and potentially ineffective sql-statements
            sql_filter_func = self.sql_filter_stack.get_stack()
        else:
            # Be conservative, get everything from the database between
            # two dates and apply the Filter:-clauses in python
            sql_filter_func = self.sql_time_filter_stack.get_stack()
        result = []
        # We can apply the filterstack here as well. we have columns and filtercolumns.
        # the only additional step is to enrich log lines with host/service-attributes
        # A timerange can be useful for a faster preselection of lines
        filter_clause, filter_values = sql_filter_func()
        full_filter_clause = filter_clause
        matchcount = 0
        for m in re.finditer(r"\?", full_filter_clause):
            full_filter_clause = re.sub('\\?', str(filter_values[matchcount]), full_filter_clause, 1)
            matchcount += 1
        fromtime = 0
        totime = int(time.time()) + 1
        gtpat = re.search(r'^(\(*time|(.*\s+time))\s+>\s+(\d+)', full_filter_clause)
        gepat = re.search(r'^(\(*time|(.*\s+time))\s+>=\s+(\d+)', full_filter_clause)
        ltpat = re.search(r'^(\(*time|(.*\s+time))\s+<\s+(\d+)', full_filter_clause)
        lepat = re.search(r'^(\(*time|(.*\s+time))\s+<=\s+(\d+)', full_filter_clause)
        if gtpat != None:
            fromtime = int(gtpat.group(3)) + 1
        if gepat != None:
            fromtime = int(gepat.group(3))
        if ltpat != None:
            totime = int(ltpat.group(3)) - 1
        if lepat != None:
            totime = int(lepat.group(3))
        # now find the list of datafiles
        dbresult = []
        for dateobj, handle, archive, fromtime, totime in self.log_db_relevant_files(fromtime, totime):
            selectresult = self.select_live_data_log(filter_clause, filter_values, handle, archive, fromtime, totime)
            dbresult.extend(selectresult)
        return dbresult

    def select_live_data_log(self, filter_clause, filter_values, handle, archive, fromtime, totime):
        dbresult = []
        try:
            if handle == "main":
                dbresult = self.execute('SELECT * FROM logs WHERE %s' % filter_clause, filter_values, row_factory)
            else:
                self.commit()
                self.execute_attach("ATTACH DATABASE '%s' AS %s" % (archive, handle))
                dbresult = self.execute('SELECT * FROM %s.logs WHERE %s' % (handle, filter_clause), filter_values, row_factory)
                self.execute("DETACH DATABASE %s" % handle)
        except LiveStatusLogStoreError, e:
            logger.error("[Logstore SQLite] An error occurred: %s" % str(e.args[0]))
        return dbresult

    def make_sql_filter(self, operator, attribute, reference):
        # The filters are text fragments which are put together to form a sql where-condition finally.
        # Add parameter Class (Host, Service), lookup datatype (default string), convert reference
        # which attributes are suitable for a sql statement
        good_attributes = ['time', 'attempt', 'class', 'command_name', 'comment', 'contact_name', 'host_name', 'plugin_output', 'service_description', 'state', 'state_type', 'type']
        good_operators = ['=', '!=']

        def eq_filter():
            if reference == '':
                return ['%s IS NULL' % attribute, ()]
            else:
                return ['%s = ?' % attribute, (reference,)]

        def match_filter():
            # sqlite matches case-insensitive by default. We make
            # no difference between case-sensitive and case-insensitive
            # here. The python filters will care for the correct
            # matching later.
            return ['%s LIKE ?' % attribute, ('%' + reference + '%',)]

        def eq_nocase_filter():
            if reference == '':
                return ['%s IS NULL' % attribute, ()]
            else:
                return ['%s = ?' % attribute.lower(), (reference.lower(),)]

        def match_nocase_filter():
            return ['%s LIKE ?' % attribute, ('%' + reference + '%',)]

        def lt_filter():
            return ['%s < ?' % attribute, (reference,)]

        def gt_filter():
            return ['%s > ?' % attribute, (reference,)]

        def le_filter():
            return ['%s <= ?' % attribute, (reference,)]

        def ge_filter():
            return ['%s >= ?' % attribute, (reference,)]

        def ne_filter():
            if reference == '':
                return ['%s IS NOT NULL' % attribute, ()]
            else:
                return ['%s != ?' % attribute, (reference,)]

        def not_match_filter():
            return ['NOT %s LIKE ?' % attribute, ('%' + reference + '%',)]

        def ne_nocase_filter():
            if reference == '':
                return ['NOT %s IS NULL' % attribute, ()]
            else:
                return ['NOT %s = ?' % attribute.lower(), (reference.lower(),)]

        def not_match_nocase_filter():
            return ['NOT %s LIKE ?' % attribute, ('%' + reference + '%',)]

        def no_filter():
            return ['1 = 1', ()]

        if attribute not in good_attributes:
            return no_filter
        if operator == '=':
            return eq_filter
        elif operator == '~':
            return match_filter
        elif operator == '=~':
            return eq_nocase_filter
        elif operator == '~~':
            return match_nocase_filter
        elif operator == '<':
            return lt_filter
        elif operator == '>':
            return gt_filter
        elif operator == '<=':
            return le_filter
        elif operator == '>=':
            return ge_filter
        elif operator == '!=':
            return ne_filter
        elif operator == '!~':
            return not_match_filter
        elif operator == '!=~':
            return ne_nocase_filter
        elif operator == '!~~':
            return not_match_nocase_filter


class LiveStatusSqlStack(LiveStatusStack):

    def __init__(self, *args, **kw):
        self.type = 'sql'
        self.__class__.__bases__[0].__init__(self, *args, **kw)

    def not_elements(self):
        top_filter = self.get_stack()
        negate_clause = '(NOT ' + top_filter()[0] + ')'
        negate_values = top_filter()[1]
        negate_filter = lambda: [negate_clause, negate_values]
        self.put_stack(negate_filter)

    def and_elements(self, num):
        """Take num filters from the stack, and them and put the result back"""
        if num > 1:
            filters = []
            for _ in range(num):
                filters.append(self.get_stack())
            # Take from the stack:
            # Make a combined anded function
            # Put it on the stack
            and_clause = '(' + (' AND ').join([x()[0] for x in filters]) + ')'
            and_values = reduce(lambda x, y: x + y, [x()[1] for x in filters])
            and_filter = lambda: [and_clause, and_values]
            logger.debug("[Logstore SQLite] and_elements %s, %s" % (and_clause, and_values))
            self.put_stack(and_filter)

    def or_elements(self, num):
        """Take num filters from the stack, or them and put the result back"""
        if num > 1:
            filters = []
            for _ in range(num):
                filters.append(self.get_stack())
            or_clause = '(' + (' OR ').join([x()[0] for x in filters]) + ')'
            or_values = reduce(lambda x, y: x + y, [x()[1] for x in filters])
            or_filter = lambda: [or_clause, or_values]
            logger.debug("[Logstore SQLite] or_elements %s" % str(or_clause))
            self.put_stack(or_filter)

    def get_stack(self):
        """Return the top element from the stack or a filter which is always true"""
        if self.qsize() == 0:
            return lambda: ["1 = ?", [1]]
        else:
            return self.get()

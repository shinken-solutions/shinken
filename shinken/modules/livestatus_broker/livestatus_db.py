#!/usr/bin/env python
#Copyright (C) 2009-2011 :
#    Gabes Jean, naparuba@gmail.com
#    Gerhard Lausser, Gerhard.Lausser@consol.de
#    Gregory Starck, g.starck@gmail.com
#    Hartmut Goebel, h.goebel@goebel-consult.de
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

import time
import datetime
import os
import re
old_implementation = False
try:
    import sqlite3
except ImportError: # python 2.4 do not have it
    try:
        import pysqlite2.dbapi2 as sqlite3 # but need the pysqlite2 install from http://code.google.com/p/pysqlite/downloads/list
    except ImportError: # python 2.4 do not have it
        import sqlite as sqlite3 # one last try
        old_implementation = True


class LiveStatusDbError(Exception):
    pass


class LiveStatusDb(object):
    """This class holds everything database-related."""

    def __init__(self, database_file, archive_path, max_logs_age):
        self.database_file = database_file
        self.archive_path = archive_path
        self.max_logs_age = max_logs_age
        self.old_implementation = old_implementation
        self.dbconn = sqlite3.connect(self.database_file)
        # Get no problem for utf8 insert
        self.dbconn.text_factory = str
        self.dbcursor = self.dbconn.cursor()
        # Create db file and tables if not existing
        self.prepare_log_db_table()
        # Start with commit and rotate immediately so the interval timers
        # get initialized properly
        now = time.time()
        self.next_log_db_commit = now
        self.next_log_db_rotate = now


    def close(self):
        self.dbconn.commit()
        self.dbconn.close()
        self.dbconn = None


    def prepare_log_db_table(self):
        # 'attempt', 'class', 'command_name', 'comment', 'contact_name', 'host_name', 'lineno', 'message',
        # 'options', 'plugin_output', 'service_description', 'state', 'state_type', 'time', 'type',
        cmd = "CREATE TABLE IF NOT EXISTS logs(logobject INT, attempt INT, class INT, command_name VARCHAR(64), comment VARCHAR(256), contact_name VARCHAR(64), host_name VARCHAR(64), lineno INT, message VARCHAR(512), options VARCHAR(512), plugin_output VARCHAR(256), service_description VARCHAR(64), state INT, state_type VARCHAR(10), time INT, type VARCHAR(64))"
        self.execute(cmd)
        cmd = "CREATE INDEX IF NOT EXISTS logs_time ON logs (time)"
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
        now = time.time()
        if self.next_log_db_commit <= now:
            self.dbconn.commit()
            print "commit....."
            self.next_log_db_commit = now + 1
        if self.next_log_db_rotate <= now:
            print "at %s we rotate the database file" % time.asctime(time.localtime(now))
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
            print "next rotation at %s " % time.asctime(time.localtime(self.next_log_db_rotate))


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
            print "An error occurred:", e.args[0]
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
                tmpconn = LiveStatusDb(archive, None, 0)
                tmpconn.prepare_log_db_table()
                tmpconn.close()
            self.commit()
            print "move logs from %s - %s to database %s" % (time.asctime(time.localtime(starttime)), time.asctime(time.localtime(stoptime)), archive)
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
                print "WARNING : it seems your database is corrupted. Please recreate it"
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
                return dbresult
            else:
                self.dbcursor.execute(cmd, values)
        except sqlite3.Error, e:
            print "execute error", e
            raise LiveStatusDbError(e)


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
        self.dbconn.commit()


    def set_row_factory(self, factory):
        self.dbconn.row_factory = factory




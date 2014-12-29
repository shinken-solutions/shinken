#!/usr/bin/env python

import os
import re
import copy
import time
import subprocess
import shutil
import datetime # not used but "sub-"imported by livestatus test.. (to be corrected..)
import sys # not here used but "sub-"imported by livestatus test.. (to be corrected..)

#
from shinken.modulesctx import modulesctx
from shinken.objects.module import Module
from shinken.modulesmanager import ModulesManager
from shinken.misc.datamanager import datamgr
from shinken.log import logger

#
from  shinken_test import (
    modules_dir,
    ShinkenTest,
    time_hacker, # not used here but "sub"-imported by lvestatus test (to be corrected)
)

modulesctx.set_modulesdir(modules_dir)


# Special Livestatus module opening since the module rename
#from shinken.modules.livestatus import module as livestatus_broker
livestatus_broker = modulesctx.get_module('livestatus')
LiveStatus_broker = livestatus_broker.LiveStatus_broker
LiveStatus = livestatus_broker.LiveStatus
LiveStatusRegenerator = livestatus_broker.LiveStatusRegenerator
LiveStatusQueryCache = livestatus_broker.LiveStatusQueryCache

Logline = livestatus_broker.Logline
LiveStatusLogStoreMongoDB = modulesctx.get_module('logstore-mongodb').LiveStatusLogStoreMongoDB
LiveStatusLogStoreSqlite = modulesctx.get_module('logstore-sqlite').LiveStatusLogStoreSqlite

livestatus_modconf = Module()
livestatus_modconf.module_name = "livestatus"
livestatus_modconf.module_type = livestatus_broker.properties['type']
livestatus_modconf.properties = livestatus_broker.properties.copy()



class ShinkenModulesTest(ShinkenTest):

    def do_load_modules(self):
        self.modules_manager.load_and_init()
        self.log.log("I correctly loaded the modules: [%s]" % (','.join([inst.get_name() for inst in self.modules_manager.instances])))



    def update_broker(self, dodeepcopy=False):
        # The brok should be manage in the good order
        ids = self.sched.brokers['Default-Broker']['broks'].keys()
        ids.sort()
        for brok_id in ids:
            brok = self.sched.brokers['Default-Broker']['broks'][brok_id]
            #print "Managing a brok type", brok.type, "of id", brok_id
            #if brok.type == 'update_service_status':
            #    print "Problem?", brok.data['is_problem']
            if dodeepcopy:
                brok = copy.deepcopy(brok)
            brok.prepare()
            self.livestatus_broker.manage_brok(brok)
        self.sched.brokers['Default-Broker']['broks'] = {}


    def init_livestatus(self, modconf=None, dbmodconf=None, needcache=False):
        self.livelogs = 'tmp/livelogs.db' + self.testid

        if modconf is None:
            modconf = Module({'module_name': 'LiveStatus',
                'module_type': 'livestatus',
                'port': str(50000 + os.getpid()),
                'pnp_path': 'tmp/pnp4nagios_test' + self.testid,
                'host': '127.0.0.1',
                'socket': 'live',
                'name': 'test', #?
            })

        if dbmodconf is None:
            dbmodconf = Module({'module_name': 'LogStore',
                'module_type': 'logstore_sqlite',
                'use_aggressive_sql': "0",
                'database_file': self.livelogs,
                'archive_path': os.path.join(os.path.dirname(self.livelogs), 'archives'),
            })

        modconf.modules = [dbmodconf]
        self.livestatus_broker = LiveStatus_broker(modconf)
        self.livestatus_broker.create_queues()

        #--- livestatus_broker.main
        self.livestatus_broker.log = logger
        # this seems to damage the logger so that the scheduler can't use it
        #self.livestatus_broker.log.load_obj(self.livestatus_broker)
        self.livestatus_broker.debug_output = []
        self.livestatus_broker.modules_manager = ModulesManager('livestatus', modules_dir, [])
        self.livestatus_broker.modules_manager.set_modules(self.livestatus_broker.modules)
        # We can now output some previouly silented debug ouput
        self.livestatus_broker.do_load_modules()
        for inst in self.livestatus_broker.modules_manager.instances:
            if inst.properties["type"].startswith('logstore'):
                f = getattr(inst, 'load', None)
                if f and callable(f):
                    f(self.livestatus_broker)  # !!! NOT self here !!!!
                break
        for s in self.livestatus_broker.debug_output:
            print "errors during load", s
        del self.livestatus_broker.debug_output
        self.livestatus_broker.rg = LiveStatusRegenerator()
        self.livestatus_broker.datamgr = datamgr
        datamgr.load(self.livestatus_broker.rg)
        self.livestatus_broker.query_cache = LiveStatusQueryCache()
        if not needcache:
            self.livestatus_broker.query_cache.disable()
        self.livestatus_broker.rg.register_cache(self.livestatus_broker.query_cache)
        #--- livestatus_broker.main

        self.livestatus_broker.init()
        self.livestatus_broker.db = self.livestatus_broker.modules_manager.instances[0]
        self.livestatus_broker.livestatus = LiveStatus(self.livestatus_broker.datamgr, self.livestatus_broker.query_cache, self.livestatus_broker.db, self.livestatus_broker.pnp_path, self.livestatus_broker.from_q)

        #--- livestatus_broker.do_main
        self.livestatus_broker.db.open()
        if hasattr(self.livestatus_broker.db, 'prepare_log_db_table'):
            self.livestatus_broker.db.prepare_log_db_table()
        #--- livestatus_broker.do_main


class TestConfig(ShinkenModulesTest):

    def tearDown(self):
        self.stop_nagios()
        self.livestatus_broker.db.close()
        if os.path.exists(self.livelogs):
            os.remove(self.livelogs)
        if os.path.exists(self.livelogs + "-journal"):
            os.remove(self.livelogs + "-journal")
        if os.path.exists(self.livestatus_broker.pnp_path):
            shutil.rmtree(self.livestatus_broker.pnp_path)
        if os.path.exists('var/shinken.log'):
            os.remove('var/shinken.log')
        if os.path.exists('var/retention.dat'):
            os.remove('var/retention.dat')
        if os.path.exists('var/status.dat'):
            os.remove('var/status.dat')
        self.livestatus_broker = None


    def contains_line(self, text, pattern):
        regex = re.compile(pattern)
        for line in text.splitlines():
            if re.search(regex, line):
                return True
        return False

    def scheduler_loop(self, count, reflist, do_sleep=False, sleep_time=61):
        super(TestConfig, self).scheduler_loop(count, reflist, do_sleep, sleep_time)
        if self.nagios_installed() and hasattr(self, 'nagios_started'):
            self.nagios_loop(1, reflist)

    def update_broker(self, dodeepcopy=False):
        # The brok should be manage in the good order
        ids = self.sched.brokers['Default-Broker']['broks'].keys()
        ids.sort()
        for brok_id in ids:
            brok = self.sched.brokers['Default-Broker']['broks'][brok_id]
            #print "Managing a brok type", brok.type, "of id", brok_id
            #if brok.type == 'update_service_status':
            #    print "Problem?", brok.data['is_problem']
            if dodeepcopy:
                brok = copy.deepcopy(brok)
            brok.prepare()
            self.livestatus_broker.manage_brok(brok)
        self.sched.brokers['Default-Broker']['broks'] = {}

    def lines_equal(self, text1, text2):
        # gets two multiline strings and compares the contents
        # lifestatus output may not be in alphabetical order, so this
        # function is used to compare unordered output with unordered
        # expected output
        # sometimes mklivestatus returns 0 or 1 on an empty result
        text1 = text1.replace("200           1", "200           0")
        text2 = text2.replace("200           1", "200           0")
        text1 = text1.rstrip()
        text2 = text2.rstrip()
        #print "text1 //%s//" % text1
        #print "text2 //%s//" % text2
        sorted1 = "\n".join(sorted(text1.split("\n")))
        sorted2 = "\n".join(sorted(text2.split("\n")))
        len1 = len(text1.split("\n"))
        len2 = len(text2.split("\n"))
        #print "%s == %s text cmp %s" % (len1, len2, sorted1 == sorted2)
        #print "text1 //%s//" % sorted(text1.split("\n"))
        #print "text2 //%s//" % sorted(text2.split("\n"))
        if sorted1 == sorted2 and len1 == len2:
            return True
        else:
            # Maybe list members are different
            # allhosts;test_host_0;test_ok_0;servicegroup_02,servicegroup_01,ok
            # allhosts;test_host_0;test_ok_0;servicegroup_02,ok,servicegroup_01
            # break it up to
            # [['allhosts'], ['test_host_0'], ['test_ok_0'],
            #     ['ok', 'servicegroup_01', 'servicegroup_02']]
            [line for line in sorted(text1.split("\n"))]
            data1 = [[sorted(c.split(',')) for c in columns] for columns in [line.split(';') for line in sorted(text1.split("\n")) if line]]
            data2 = [[sorted(c.split(',')) for c in columns] for columns in [line.split(';') for line in sorted(text2.split("\n")) if line]]
            #print "text1 //%s//" % data1
            #print "text2 //%s//" % data2
            # cmp is clever enough to handle nested arrays
            return cmp(data1, data2) == 0

    def show_broks(self, title):
        print
        print "--- ", title
        for brok in sorted(self.sched.broks.values(), lambda x, y: x.id - y.id):
            if re.compile('^service_').match(brok.type):
                pass
                #print "BROK:", brok.type
                #print "BROK   ", brok.data['in_checking']
        self.update_broker()
        request = 'GET services\nColumns: service_description is_executing\n'
        response, keepalive = self.livestatus_broker.livestatus.handle_request(request)
        print response

    def nagios_installed(self, path='/usr/local/nagios/bin/nagios', livestatus='/usr/local/nagios/lib/mk-livestatus/livestatus.o'):
        return False
        raise
        if os.path.exists(path) and os.access(path, os.X_OK) and os.path.exists(livestatus):
            self.nagios_path = path
            self.livestatus_path = livestatus
            return True
        else:
            return False

    # shinkenize_nagios_config('nagios_1r_1h_1s')
    # We assume that there is a nagios_1r_1h_1s.cfg and a nagios_1r_1h_1s directory for the objects
    def unshinkenize_config(self, configname):
        new_configname = configname + '_' + str(os.getpid())
        config = open('etc/shinken_' + configname + '.cfg')
        text = config.readlines()
        config.close()

        newconfig = open('etc/shinken_' + new_configname + '.cfg', 'w')
        for line in text:
            if re.search('^resource_file=', line):
                newconfig.write("resource_file=etc/resource.cfg\n")
            elif re.search('shinken\-specific\.cfg', line):
                pass
            elif re.search('enable_problem_impacts_states_change', line):
                pass
            elif re.search('cfg_dir=', line):
                newconfig.write(re.sub(configname, new_configname, line))
            elif re.search('cfg_file=', line):
                newconfig.write(re.sub(configname, new_configname, line))
            elif re.search('execute_host_checks=', line):
                newconfig.write("execute_host_checks=0\n")
            elif re.search('execute_service_checks=', line):
                newconfig.write("execute_service_checks=0\n")
            elif re.search('^debug_level=', line):
                newconfig.write("debug_level=0\n")
            elif re.search('^debug_verbosity=', line):
                newconfig.write("debug_verbosity=0\n")
            elif re.search('^status_update_interval=', line):
                newconfig.write("status_update_interval=30\n")
            elif re.search('^command_file=', line):
                newconfig.write("command_file=var/shinken.cmd\n")
            elif re.search('^command_check_interval=', line):
                newconfig.write("command_check_interval=1s\n")
            else:
                newconfig.write(line)
        newconfig.write('broker_module=/usr/local/nagios/lib/mk-livestatus/livestatus.o var/live' + "\n")
        newconfig.close()
        for dirfile in os.walk('etc/' + configname):
            dirpath, dirlist, filelist = dirfile
            newdirpath = re.sub(configname, new_configname, dirpath)
            os.mkdir(newdirpath)
            for file in [f for f in filelist if re.search('\.cfg$', f)]:
                config = open(dirpath + '/' + file)
                text = config.readlines()
                config.close()
                newconfig = open(newdirpath + '/' + file, 'w')
                for line in text:
                    if re.search('^\s*criticity', line):
                        pass
                    elif re.search('^\s*business_impact', line):
                        pass
                    elif re.search('enable_problem_impacts_states_change', line):
                        pass
                    else:
                        newconfig.write(line)
                newconfig.close()
        return new_configname

    def start_nagios(self, config):
        if os.path.exists('var/spool/checkresults'):
            # Cleanup leftover checkresults
            shutil.rmtree('var/spool/checkresults')
        for dir in ['tmp', 'var/tmp', 'var/spool', 'var/spool/checkresults', 'var/archives']:
            if not os.path.exists(dir):
                os.mkdir(dir)
        self.nagios_config = self.unshinkenize_config(config)
        if os.path.exists('var/shinken.log'):
            os.remove('var/shinken.log')
        if os.path.exists('var/retention.dat'):
            os.remove('var/retention.dat')
        if os.path.exists('var/status.dat'):
            os.remove('var/status.dat')
        self.nagios_proc = subprocess.Popen([self.nagios_path, 'etc/shinken_' + self.nagios_config + '.cfg'], close_fds=True)
        self.nagios_started = time.time()
        time.sleep(2)

    def stop_nagios(self):
        if self.nagios_installed():
            print "i stop nagios!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
            time.sleep(5)
            if hasattr(self, 'nagios_proc'):
                attempt = 1
                while self.nagios_proc.poll() is None and attempt < 4:
                    self.nagios_proc.terminate()
                    attempt += 1
                    time.sleep(1)
                if self.nagios_proc.poll() is None:
                    self.nagios_proc.kill()
                if os.path.exists('etc/' + self.nagios_config):
                    shutil.rmtree('etc/' + self.nagios_config)
                if os.path.exists('etc/shinken_' + self.nagios_config + '.cfg'):
                    os.remove('etc/shinken_' + self.nagios_config + '.cfg')

    def ask_nagios(self, request):
        if time.time() - self.nagios_started < 2:
            time.sleep(1)
        if not request.endswith("\n"):
            request = request + "\n"
        unixcat = subprocess.Popen([os.path.dirname(self.nagios_path) + '/' + 'unixcat', 'var/live'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        tic = time.clock()
        out, err = unixcat.communicate(request)
        tac = time.clock()
        print "mklivestatus duration %f" % (tac - tic)
        attempt = 1
        while unixcat.poll() is None and attempt < 4:
            unixcat.terminate()
            attempt += 1
            time.sleep(1)
        if unixcat.poll() is None:
            unixcat.kill()
        print "unixcat says", out
        return out

    def nagios_loop(self, count, reflist, do_sleep=False, sleep_time=61):
        now = time.time()
        buffer = open('var/pipebuffer', 'w')
        for ref in reflist:
            (obj, exit_status, output) = ref
            if obj.my_type == 'service':
                cmd = "[%lu] PROCESS_SERVICE_CHECK_RESULT;%s;%s;%d;%s\n" % (now, obj.host_name, obj.service_description, exit_status, output)
                print cmd
                buffer.write(cmd)
            else:
                cmd = "[%lu] PROCESS_HOST_CHECK_RESULT;%s;%d;%s\n" % (now, obj.host_name, exit_status, output)
                buffer.write(cmd)
        buffer.close()
        print "open pipe", self.conf.command_file
        fifo = open('var/shinken.cmd', 'w')
        cmd = "[%lu] PROCESS_FILE;%s;0\n" % (now, 'var/pipebuffer')
        fifo.write(cmd)
        fifo.flush()
        fifo.close()
        time.sleep(5)

    def nagios_extcmd(self, cmd):
        fifo = open('var/shinken.cmd', 'w')
        fifo.write(cmd)
        fifo.flush()
        fifo.close()
        time.sleep(5)

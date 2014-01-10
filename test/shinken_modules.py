#!/usr/bin/env python


#
from  shinken_test import *

#define_modules_dir("../modules")
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

from shinken.misc.datamanager import datamgr

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
        #--- livestatus_broker.do_main

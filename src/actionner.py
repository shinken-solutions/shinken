from multiprocessing import Process, Queue
#import Queue
import time
import sys
#import random
import Pyro.core
from message import Message
#from check import Check
from worker import Worker
from util import get_sequence



s = Queue() #Global Master -> Slave
m = Queue() #Slave -> Master

schedulers = {
    0 : {'url' : "PYROLOC://localhost:7768/Checks",
         'con' : None,
         'verifs' : {}
         },
    1 : {'url' : "PYROLOC://localhost:7770/Checks",
         'con' : None,
         'verifs' : {}
         }
    }

workers = {} #dict of active workers
newzombies = [] #list of fresh new zombies, will be join the next loop
zombies = [] #list of quite old zombies, will be join now

request_checks = None #Pyro.core.getProxyForURI("PYROLOC://localhost:7766/Checks")

#verifs = {}

#Seq id for workers
seq_worker = get_sequence()
#seq_verif = get_sequence()


#initialise or re-initialise connexion with pynag
def pynag_con_init(id):
    global schedulers#request_checks
    print "init de connexion avec", schedulers[id]['url']
    schedulers[id]['con'] = Pyro.core.getProxyForURI(schedulers[id]['url'])


#Manage messages from Workers
def manage_msg(msg):
    global zombie
    global workers
    global schedulers
    
    if msg.get_type() == 'IWantToDie':
        zombie = msg.get_from()
        print "Got a ding wish from ",zombie
        workers[zombie].join()
    
    if msg.get_type() == 'Result':
        id = msg.get_from()
        workers[id].reset_idle()
        chk = msg.get_data()
        sched_id = chk.sched_id
        print "[%d]Get result from worker" % sched_id, chk
        chk.set_status('waitforhomerun')

        schedulers[sched_id]['verifs'][chk.get_id()] = chk


#Return the chk to pynag and clean them
def manage_return():
    #global verifs
    global schedulers#request_checks

    #ret = {}
    for sched_id in schedulers:
        ret = []
        verifs = schedulers[sched_id]['verifs']
        #Get the id to return to pynag, so after make a big array with only them
        id_to_return = [elt for elt in verifs.keys() if verifs[elt].get_status() == 'waitforhomerun']
        #print "Check in progress:", verifs.values()
        for id in id_to_return:
            v = verifs[id]
            #sched_id = v.sched_id
            del v.sched_id
            ret.append(v)
            #del verifs[id]

        #for sched_id in schedulers:
        if ret is not []:
            try:
                con = schedulers[sched_id]['con']
                con.put_results(ret)
                #We clean ONLY if the send is OK
            except Pyro.errors.ProtocolError:
                pynag_con_init(sched_id)
                return
            except Exception,x:
                print ''.join(Pyro.util.getPyroTraceback(x))
                sys.exit(0)
        
                
        for id in id_to_return:
            del verifs[id]


if __name__ == '__main__':

    #Connexion init with PyNag server
    for sched_id in schedulers:
        pynag_con_init(sched_id)

    #Allocate Mortal Threads
    for i in xrange(1, 5):
        id = seq_worker.next()
        print "Allocate : ",id
        workers[id]=Worker(id, s, m, mortal=True)
        workers[id].start()
    
    i = 0
    timeout = 1.0
    while True:
        i = i + 1
        if not i % 50:
            print "Loop ",i
        begin_loop = time.time()

        #print "Timeout", timeout
            
        try:
            msg = m.get(timeout=timeout)
            after = time.time()
            timeout -= after-begin_loop
            
            #Manager the msg like check return
            manage_msg(msg)
            
            #We add the time pass on the workers'idle time
            for id in workers:
                workers[id].add_idletime(after-begin_loop)
            
                
        except : #Time out Part
            #print "Master: timeout "
            after = time.time()
            timeout = 1.0

            #We join (old)zombies and we move new ones in the old list
            for id in zombies:
                workers[id].join()
                del workers[id]
            zombies = newzombies
            newzombies = []

            nb_queue = 0
            for sched_id in schedulers:
                #print "Stats for Scheduler No:", sched_id
                verifs = schedulers[sched_id]['verifs']
                #We add new worker if the queue is > 80% of the worker number
                #print 'Total number of Workers : %d' % len(workers)
                tmp_nb_queue = len([elt for elt in verifs.keys() if verifs[elt].get_status() == 'queue'])
                nb_queue += tmp_nb_queue
                nb_waitforhomerun = len([elt for elt in verifs.keys() if verifs[elt].get_status() == 'waitforhomerun'])
                
                if not i % 10:
                    print '[%d]Stats : Workers:%d Check %d (Queued:%d ReturnWait:%d)' % (sched_id, len(workers), len(verifs), tmp_nb_queue, nb_waitforhomerun)
            
            while nb_queue > 0.8 * len(workers) and len(workers) < 20:
                id = seq_worker.next()
                print "Allocate New worker : ",id
                workers[id] = Worker(id, s, m, mortal=True)
                workers[id].start()
                
            new_checks = []
            #We check for new check
            for sched_id in schedulers:
                try:
                    con = schedulers[sched_id]['con']
                    tmp_verifs = con.get_checks(do_checks=True, do_actions=True)
                    for v in tmp_verifs:
                        v.sched_id = sched_id
                    new_checks.extend(tmp_verifs)
                except Pyro.errors.ProtocolError as exp:
                    print exp
                #we reinitialise the ccnnexion to pynag
                    pynag_con_init(sched_id)
                    #new_checks=[]
                except Exception,x:
                    print ''.join(Pyro.util.getPyroTraceback(x))
                    sys.exit(0)
            
            #print "********Got %d new checks*******" % len(new_checks)
            for chk in new_checks:
                chk.set_status('queue')
                id = chk.get_id()
                verifs[id] = chk
                msg = Message(id=0, type='Do', data=verifs[id])
                s.put(msg)
            
                
            #We send all finished checks
            manage_return()
            
            
            #We add the time pass on the workers
            for id in workers:
                workers[id].add_idletime(after-begin_loop)
            
            delworkers = []
            #We look for cleaning workers
            for id in workers:
                if workers[id].is_killable():
                    msg=Message(id=0, type='Die')
                    workers[id].send_message(msg)
                    workers[id].set_zombie()
                    delworkers.append(id)
            #Cleaning the workers
            for id in delworkers:
                #del workers[id]
                newzombies.append(id)


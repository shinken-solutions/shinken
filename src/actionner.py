from multiprocessing import Process, Queue
import time
import sys
import Pyro.core
import select
from message import Message
from worker import Worker
from util import get_sequence



#Interface for Arbiter, our big MASTER
#It put us our conf
class IForArbiter(Pyro.core.ObjBase):
	#We keep app link because we are just here for it
	def __init__(self, app):
		Pyro.core.ObjBase.__init__(self)
		self.app = app
		self.schedulers = app.schedulers

	#function called by arbiter for giving us our conf
	#conf must be a dict with:
	#'schedulers' : schedulers dict (by id) with address and port
	def put_conf(self, conf):
		#global have_conf
		self.app.have_conf = True
		print "Sending us ", conf
		for sched_id in conf['schedulers'] :
			s = conf['schedulers'][sched_id]
			self.schedulers[sched_id] = s
			self.schedulers[sched_id]['uri'] = "PYROLOC://%s:%d/Checks" % (s['address'], s['port'])
			#self.schedulers[sched_id] = conf['schedulers'][sched_id]
			self.schedulers[sched_id]['verifs'] = {}
			self.schedulers[sched_id]['running_id'] = 0
		
		print "We have our schedulers :", self.schedulers
		
	#Use for arbiter to know if we are alive
	def ping(self):
		print "We ask us for a ping"
		return True



#Our main APP class
class Actionner:
	def __init__(self):
		#Bool to know if we have received conf from arbiter
		self.have_conf = False
		self.s = Queue() #Global Master -> Slave
		self.m = Queue() #Slave -> Master

		#Ours schedulers
		self.schedulers = {}

		self.workers = {} #dict of active workers
		self.newzombies = [] #list of fresh new zombies, will be join the next loop
		self.zombies = [] #list of quite old zombies, will be join now
		
		#TODO : change with id in the Class
		self.seq_worker = get_sequence()

	#initialise or re-initialise connexion with scheduler
	def pynag_con_init(self, id):
		print "init de connexion avec", self.schedulers[id]['uri']
		self.schedulers[id]['con'] = Pyro.core.getProxyForURI(self.schedulers[id]['uri'])
		try:
			new_run_id = self.schedulers[id]['con'].get_running_id()
		except Pyro.errors.ProtocolError, exp:
			print exp
			return
		except Pyro.errors.NamingError, exp:
			print "Scheduler is not initilised", exp
			self.schedulers[id]['con'] = None
			return
		if self.schedulers[id]['running_id'] != 0 and new_run_id != running_id:
			self.schedulers[id]['verifs'].clear()
		self.schedulers[id]['running_id'] = new_run_id
		print "Connexion OK"


        #Manage messages from Workers
	def manage_msg(self, msg):
		#global zombie
		#global workers
		#global schedulers
    
		if msg.get_type() == 'IWantToDie':
			zombie = msg.get_from()
			print "Got a ding wish from ",zombie
			self.workers[zombie].join()
    
		if msg.get_type() == 'Result':
			id = msg.get_from()
			self.workers[id].reset_idle()
			chk = msg.get_data()
			sched_id = chk.sched_id
			print "[%d]Get result from worker" % sched_id, chk
			chk.set_status('waitforhomerun')

			self.schedulers[sched_id]['verifs'][chk.get_id()] = chk


        #Return the chk to scheduler and clean them
	def manage_return(self):
		#global schedulers#request_checks
                #ret = {}
		for sched_id in self.schedulers:
			ret = []
			verifs = self.schedulers[sched_id]['verifs']
                        #Get the id to return to pynag, so after make a big array with only them
			id_to_return = [elt for elt in verifs.keys() if verifs[elt].get_status() == 'waitforhomerun']
			for id in id_to_return:
				v = verifs[id]
				del v.sched_id
				ret.append(v)
			print "[%d] Returning %s results" % (sched_id, ret)
			if ret is not []:
				try:
					con = self.schedulers[sched_id]['con']
					if con is not None:#None = not initialized
						con.put_results(ret)
                
				except Pyro.errors.ProtocolError:
					self.pynag_con_init(sched_id)
					return
				except Exception,x:
					print ''.join(Pyro.util.getPyroTraceback(x))
					sys.exit(0)
        
			#We clean ONLY if the send is OK
			for id in id_to_return:
				del verifs[id]


	def main(self):
                #Daemon init
		Pyro.core.initServer()
		self.port = int(sys.argv[1])
		print "Port:", self.port
		self.daemon = Pyro.core.Daemon(port=self.port)
		#If the port is not free, pyro take an other. I don't like taht!
		if self.daemon.port != self.port:
			print "Sorry, the port %d was not free" % self.port
			sys.exit(1)
		self.uri2 = self.daemon.connect(IForArbiter(self),"ForArbiter")

                #We wait for conf
		
		print "Waiting for a configuration"
		timeout = 1.0
		while not self.have_conf :
			socks = self.daemon.getServerSockets()
			avant = time.time()
			ins,outs,exs = select.select(socks,[],[],timeout)   # 'foreign' event loop
			if ins != []:
				for sock in socks:
					if sock in ins:
						self.daemon.handleRequests()
						print "Apres handle : Have conf?", self.have_conf
                    #have_conf = True
						apres = time.time()
						diff = apres-avant
						timeout = timeout - diff
						break    # no need to continue with the for loop
			else: #Timeout
				print "Waiting for a configuration"
				timeout = 1.0

			if timeout < 0:
				timeout = 1.0
    

                #Connexion init with PyNag server
		for sched_id in self.schedulers:
			self.pynag_con_init(sched_id)

                #Allocate Mortal Threads
		for i in xrange(1, 5):
				id = self.seq_worker.next()
				print "Allocate : ",id
				self.workers[id] = Worker(id, self.s, self.m, mortal=True)
				self.workers[id].start()

		#Now main loop
		i = 0
		timeout = 1.0
		while True:
			i = i + 1
			if not i % 50:
				print "Loop ",i
			begin_loop = time.time()

			#print "Timeout", timeout
			
			try:
				msg = self.m.get(timeout=timeout)
				after = time.time()
				timeout -= after-begin_loop
				
                                #Manager the msg like check return
				manage_msg(msg)
            
            #We add the time pass on the workers'idle time
				for id in self.workers:
					self.workers[id].add_idletime(after-begin_loop)
					
					
			except : #Time out Part
            #print "Master: timeout "
				after = time.time()
				timeout = 1.0
				
            #We join (old)zombies and we move new ones in the old list
				for id in self.zombies:
					self.workers[id].join()
					del self.workers[id]
				self.zombies = self.newzombies
				self.newzombies = []

				nb_queue = 0
				for sched_id in self.schedulers:
                #print "Stats for Scheduler No:", sched_id
					verifs = self.schedulers[sched_id]['verifs']
                #We add new worker if the queue is > 80% of the worker number
                #print 'Total number of Workers : %d' % len(workers)
					tmp_nb_queue = len([elt for elt in verifs.keys() if verifs[elt].get_status() == 'queue'])
					nb_queue += tmp_nb_queue
					nb_waitforhomerun = len([elt for elt in verifs.keys() if verifs[elt].get_status() == 'waitforhomerun'])
					
					if not i % 10:
						print '[%d]Stats : Workers:%d Check %d (Queued:%d ReturnWait:%d)' % (sched_id, len(self.workers), len(verifs), tmp_nb_queue, nb_waitforhomerun)
            

				while nb_queue > 0.8 * len(self.workers) and len(self.workers) < 20:
					id = self.seq_worker.next()
					print "Allocate New worker : ",id
					self.workers[id] = Worker(id, self.s, self.m, mortal=True)
					self.workers[id].start()
                
				new_checks = []
				#We check for new check
				for sched_id in self.schedulers:
					try:
						con = self.schedulers[sched_id]['con']
						if con is not None: #None = not initilized
							tmp_verifs = con.get_checks(do_checks=False, do_actions=True)
							print "We've got new verifs" , tmp_verifs
							for v in tmp_verifs:
								v.sched_id = sched_id
							new_checks.extend(tmp_verifs)
					except Pyro.errors.ProtocolError as exp:
						print exp
                                                #we reinitialise the ccnnexion to pynag
						self.pynag_con_init(sched_id)
					except Exception,x:
						print ''.join(Pyro.util.getPyroTraceback(x))
						sys.exit(0)
            
				for chk in new_checks:
					chk.set_status('queue')
					verifs = self.schedulers[chk.sched_id]['verifs']
					id = chk.get_id()
					verifs[id] = chk
					msg = Message(id=0, type='Do', data=verifs[id])
					#print "S avant plantage:", s
					self.s.put(msg)
					
					
                                #We send all finished checks
				self.manage_return()
            
            
            #We add the time pass on the workers
				for id in self.workers:
					self.workers[id].add_idletime(after-begin_loop)
            
				delworkers = []
            #We look for cleaning workers
				for id in self.workers:
					if self.workers[id].is_killable():
						msg=Message(id=0, type='Die')
						self.workers[id].send_message(msg)
						self.workers[id].set_zombie()
						delworkers.append(id)
                                        #Cleaning the workers
				for id in delworkers:
					self.newzombies.append(id)


if __name__ == '__main__':
	actionner = Actionner()
	actionner.main()

from multiprocessing import Process, Queue
from message import Message

class Worker:
    """The Worker class """
    _id = None
    _process = None
    _mortal = None
    _idletime = None
    _timeout = None
    _c = None
    def __init__(self, id, s, m, mortal=True, timeout=30):
        self._id = id
        self._mortal = mortal
        self._idletime = 0
        self._timeout = timeout
        self._c = Queue() # Private Control queue for the Worker
        self._process = Process(target=self.work, args=(s, m, self._c))

    def is_mortal(self):
        return self._mortal

    def start(self):
        self._process.start()

    def join(self):
        self._process.join()

    def is_killable(self):
        #print "M[%d]Is killable? %s %s %s" % (self._id, self._mortal , self._idletime , self._timeout)
        return self._mortal and self._idletime > self._timeout

    def add_idletime(self, time):
        self._idletime = self._idletime + time

    def reset_idle(self):
        self._idletime = 0
    
    def send_message(self, msg):
        self._c.put(msg)
        
    #A zombie is immortal, so kill not be kill anymore
    def set_zombie(self):
        self._mortal = False
        

    #id = id of the worker
    #s = Global Queue Master->Slave
    #m = Queue Slave->Master
    #c = Control Queue for the worker
    def work(self, s,m,c):
        while True:
            msg=None
            cmsg=None
            
            try:
                msg=s.get(timeout=1.0)
            except:
                #print "Empty Queue", self._id
                msg=None
                #print "[%d] idle up %s" % (self._id, self._idletime)
                self._idletime = self._idletime + 1
            
            #print "[%d] got %s" % (self._id, msg)
            #Here we work on the elt
            if msg is not None:
                #print msg.str()
                chk = msg.get_data()
                self._idletime = 0
                
                chk.execute()
                chk.set_status('executed')
                
                #We answer to the master
                msg=Message(id=self._id, type='Result',data=chk)
                m.put(msg)
                
            try:
                cmsg=c.get(block=False)
                if cmsg.get_type() == 'Die':
                    print "[%d]Dad say we are diing..." % self._id
                    break
            except :
                pass
                
            if self._mortal == True and self._idletime > 2 * self._timeout:
                print "[%d]Timeout, Arakiri" % self._id
                #The master must be dead and we are loonely, we must die
                break

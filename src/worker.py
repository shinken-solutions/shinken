#!/usr/bin/python
#Copyright (C) 2009 Gabes Jean, naparuba@gmail.com
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


#This class is used for poller and reactionner to work.
#The worker is a process launch by theses process and read Message in a Queue
#(self.s) (slave)
#They launch the Check and then send the result in the Queue self.m (master)
#they can die if they do not do anything (param timeout)
from multiprocessing import Process, Queue
from message import Message

import threading

#Worker class
class Worker:
    """The Worker class """
    id = 0#None
    _process = None
    _mortal = None
    _idletime = None
    _timeout = None
    _c = None
    def __init__(self, id, s, m, mortal=True, timeout=10):
        self.id = self.__class__.id
        self.__class__.id += 1

        self._mortal = mortal
        self._idletime = 0
        self._timeout = timeout
        self._c = Queue() # Private Control queue for the Worker
        self._process = Process(target=self.work, args=(s, m, self._c))
	#Thread version : not good in cpython :(
        #self._process = threading.Thread(target=self.work, args=(s, m, self._c))


    def is_mortal(self):
        return self._mortal


    def start(self):
        self._process.start()


    def join(self, timeout=None):
        self._process.join(timeout)


    def is_alive(self):
        self._process.is_alive()

    def is_killable(self):
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
    def work(self, s, m, c):
        while True:
            msg = None
            cmsg = None
            
            try:
                #print "I", self.id, "wait for a message"
                msg = s.get(timeout=1.0)
                #print "I", self.id, "I've got a message!"
            except:
                #print "Empty Queue", self._id
                msg = None
                #print "[%d] idle up %s" % (self._id, self._idletime)
                self._idletime = self._idletime + 1
            
            #print "[%d] got %s" % (self._id, msg)
            #Here we work on the elt
            if msg is not None:
                chk = msg.get_data()
                self._idletime = 0
                
                chk.execute()
                chk.set_status('executed')
                
                #We answer to the master
                msg = Message(id=self.id, type='Result', data=chk)
                m.put(msg)
                
            try:
                cmsg = c.get(block=False)
                if cmsg.get_type() == 'Die':
                    print "[%d]Dad say we are diing..." % self.id
                    break
            except :
                pass
                
            if self._mortal == True and self._idletime > 2 * self._timeout:
                print "[%d]Timeout, Arakiri" % self.id
                #The master must be dead and we are loonely, we must die
                break

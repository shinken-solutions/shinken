#!/usr/bin/env python2.6
"""
This is a multiprocessing wrapper for Net-SNMP.
This makes a synchronous API asynchronous by combining
it with Python2.6
"""

import netsnmp
from multiprocessing import Process, Queue, current_process

class HostRecord():
    """This creates a host record"""
    def __init__(self,
                 hostname = None,
                 query = None):
        self.hostname = hostname
        self.query = query

class SnmpSession():
    """A SNMP Session"""
    def __init__(self,
                oid = "sysDescr",
                Version = 2,
                DestHost = "localhost",
                Community = "public",
                Verbose = True,
                ):
        self.oid = oid
        self.Version = Version
        self.DestHost = DestHost
        self.Community = Community
        self.Verbose = Verbose
        self.var = netsnmp.Varbind(oid, 0)
        self.hostrec = HostRecord()
        self.hostrec.hostname = self.DestHost

    def query(self):
        """Creates SNMP query

        Fills out a Host Object and returns result
        """
        try:
            result = netsnmp.snmpget(self.var,
                                Version = self.Version,
                                DestHost = self.DestHost,
                                Community = self.Community)
            self.hostrec.query = result
        except Exception, err:
            if self.Verbose:
                print err
            self.hostrec.query = None
        finally:
            return self.hostrec

def make_query(host):
    """This does the actual snmp query

    This is a bit fancy as it accepts both instances
    of SnmpSession and host/ip addresses.  This
    allows a user to customize mass queries with
    subsets of different hostnames and community strings
    """
    if isinstance(host,SnmpSession):
        return host.query()
    else:
        s = SnmpSession(DestHost=host)
        return s.query()

# Function run by worker processes
def worker(input, output):
    for func in iter(input.get, 'STOP'):
        result = make_query(func)
        output.put(result)

def main():
    """Runs everything"""

    #clients
    hosts = ["localhost", "localhost"]
    NUMBER_OF_PROCESSES = len(hosts)

    # Create queues
    task_queue = Queue()
    done_queue = Queue()

    #submit tasks
    for host in hosts:
        task_queue.put(host)

    #Start worker processes
    for i in range(NUMBER_OF_PROCESSES):
        Process(target=worker, args=(task_queue, done_queue)).start()

     # Get and print results
    print 'Unordered results:'
    for i in range(len(hosts)):
        print '\t', done_queue.get().query

    # Tell child processes to stop
    for i in range(NUMBER_OF_PROCESSES):
        task_queue.put('STOP')
        print "Stopping Process #%s" % i

if __name__ == "__main__":
    main()


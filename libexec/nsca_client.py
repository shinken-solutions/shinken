### This is a very quick and dirty code for David so he can work on its sikuli agent
# and report as nsca the results.
# This need to be clean a lot, it's still a server and should be a client class :)
# I can do it after my "new baby holidays" are finished ;)
# J.Gabes



import time
import select
import socket
import struct
import sys
import random


def decrypt_xor(data, key):
    keylen = len(key)
    crypted = [chr(ord(data[i]) ^ ord(key[i % keylen])) for i in xrange(len(data))]
    return ''.join(crypted)



#Just print some stuff
class NSCA_client():
    def __init__(self, host, port, encryption_method, password):
        self.host = host
        self.port = port
        self.encryption_method = encryption_method
        self.password = password
        self.rng = random.Random(password)


    #Ok, main function that is called in the CONFIGURATION phase
    def get_objects(self):
        print "[Dummy] ask me for objects to return"
        r = {'hosts' : []}
        h = {'name' : 'dummy host from dummy arbiter module',
             'register' : '0',
             }

        r['hosts'].append(h)
        print "[Dummy] Returning to Arbiter the hosts:", r
        return r

    def send_init_packet(self, socket):
        '''
        Build an init packet
         00-127  : IV
         128-131 : unix timestamp
        '''
        iv = ''.join([chr(self.rng.randrange(256)) for i in xrange(128)])
        init_packet = struct.pack("!128sI", iv, int(time.mktime(time.gmtime())))
        socket.send(init_packet)
        return iv

    def read_check_result(self, data, iv):
        '''
        Read the check result
         00-01 : Version
         02-05 : CRC32
         06-09 : Timestamp
         10-11 : Return code
         12-75 : hostname
         76-203 : service
         204-715 : output of the plugin
         716-720 : padding
        '''
        if len(data) != 720:
            return None

        if self.encryption_method == 1:
            data = decrypt_xor(data,self.password)
            data = decrypt_xor(data,iv)

        (version, pad1, crc32, timestamp, rc, hostname_dirty, service_dirty, output_dirty, pad2) = struct.unpack("!hhIIh64s128s512sh",data)
        hostname =  hostname_dirty.partition("\0", 1)[0]
        service = service_dirty.partition("\0", 1)[0]
        output = output_dirty.partition("\0", 1)[0]
        return (timestamp, rc, hostname, service, output)

    def post_command(self, timestamp, rc, hostname, service, output):
        '''
        Send a check result command to the arbiter
        '''
        if len(service) == 0:
            extcmd = "[%lu] PROCESS_HOST_CHECK_RESULT;%s;%d;%s\n" % (timestamp,hostname,rc,output)
        else:
            extcmd = "[%lu] PROCESS_SERVICE_CHECK_RESULT;%s;%s;%d;%s\n" % (timestamp,hostname,service,rc,output)

        print "want to send", extcmd
        
        #e = ExternalCommand(extcmd)
        #self.from_q.put(e)


    # When you are in "external" mode, that is the main loop of your process
    def main(self):
        #self.set_exit_handler()
        self.interrupted = False
        backlog = 5
        size = 8192
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #server.setblocking(0)
        server.connect((self.host, self.port))
        #server.listen(backlog)
        input = [server]
        databuffer = {}
        IVs = {}

        init = server.recv(size)
        print "got init", init
        
        #init_packet = struct.pack("!128sI",iv,int(time.mktime(time.gmtime())))
        (iv, t) = struct.unpack("!128sI",init)
        print "IV", iv
        print "T", t

        version = 0
        pad1 = 0
        crc32= 0
        timestamp = int(time.time())
        rc = 2
        hostname_dirty = "moncul"
        service_dirty = "fonctionnne"
        output_dirty = "blablalba"
        pad2=0
        '''
        Read the check result
         00-01 : Version
         02-05 : CRC32
         06-09 : Timestamp
         10-11 : Return code
         12-75 : hostname
         76-203 : service
         204-715 : output of the plugin
         716-720 : padding
        '''
        init_packet = struct.pack("!hhIIh64s128s512sh", version, pad1, crc32, timestamp, rc, hostname_dirty, service_dirty, output_dirty, pad2)
        print "Create packent len", len(init_packet)
        #(version, pad1, crc32, timestamp, rc, hostname_dirty, service_dirty, output_dirty, pad2) = struct.unpack("!hhIIh64s128s512sh",data)

        data = decrypt_xor(init_packet,iv)        
        data = decrypt_xor(data,self.password)


        server.send(data)
        sys.exit(0)

        while not self.interrupted:
            print "Loop"
            inputready,outputready,exceptready = select.select(input,[],[], 1)

            for s in inputready:
                if s == server:
                    # handle the server socket
                    #client, address = server.accept()
                    iv = self.send_init_packet(client)
                    IVs[client] = iv
                    input.append(client)
                else:
                    # handle all other sockets
                    data = s.recv(size)
                    if s in databuffer:
                        databuffer[s] += data
                    else:
                        databuffer[s] = data
                    if len(databuffer[s]) == 720:
                        # end-of-transmission or an empty line was received
                        (timestamp, rc, hostname, service, output)=self.read_check_result(databuffer[s],IVs[s])
                        del databuffer[s]
                        del IVs[s]
                        self.post_command(timestamp,rc,hostname,service,output)
                        try:
                            s.shutdown(2)
                        except Exception , exp:
                            print exp
                        s.close()
                        input.remove(s)



nsca = NSCA_client('localhost', 5667, 1, 'toto')
nsca.main()

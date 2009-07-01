import Pyro.core, time

temps=time.time()

class JokeGen(Pyro.core.ObjBase):
        def __init__(self):
                Pyro.core.ObjBase.__init__(self)
        def joke(self, name):
		global temps
		tmp=time.time()
		print "diff=",tmp-temps
		temps=tmp
		#time.sleep(5)	
                return "Sorry "+name+", I don't know any jokes."

Pyro.core.initServer()
daemon=Pyro.core.Daemon()
uri=daemon.connect(JokeGen(),"jokegen")

print "The daemon runs on port:",daemon.port
print "The object's uri is:",uri

daemon.requestLoop()


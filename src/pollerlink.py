import Pyro.core

from item import Item, Items
from util import to_int, to_char, to_split, to_bool

class PollerLink(Item):
    id = 0
    properties={'name' : {'required' : True },
                'scheduler_name' : {'required' : True},
                'address' : {'required' : True},
                'port' : {'required':  True, 'pythonize': to_int}
                }
 
    running_properties = {'is_active' : False,
                          'con' : None
                          #self.is_alive = False
                          }
    macros = {}


    def clean(self):
        pass


    def create_connexion(self):
        self.uri = "PYROLOC://"+self.address+":"+str(self.port)+"/ForArbiter"
        self.con = Pyro.core.getProxyForURI(self.uri)


    def put_conf(self, conf):
        if self.con == None:
            self.create_connexion()
        print "Connexion is OK, now we put conf", conf
            
        try:
            self.con.put_conf(conf)
        except Exception,x:
            print ''.join(Pyro.util.getPyroTraceback(x))
            #sys.exit(0)



    def is_alive(self):
        print "Trying to see if ", self.address+":"+str(self.port), "is alive"
        try:
            if self.con == None:
                self.create_connexion()
            self.con.ping()
            return True
        except Pyro.errors.URIError as exp:
            print exp
            return False
        except Pyro.errors.ProtocolError as exp:
            print exp
            return False


class PollerLinks(Items):
    name_property = "name"
    inner_class = PollerLink

#    def find_spare
#    def sort(self, f):
#        self.items.sort(f)

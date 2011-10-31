import os
import cmd 
import sys 
import time
import datetime
import copy

# vim editor shortcuts
# z+o unfold
# z+c fold
# shift+ctrl+6 show file explorer

try:
    from shinken.bin import VERSION
    import shinken
except ImportError:
    # If importing shinken fails, try to load from current directory
    # or parent directory to support running without installation.
    # Submodules will then be loaded from there, too.
    import imp
    imp.load_module('shinken', *imp.find_module('shinken', [os.path.realpath("."), os.path.realpath(".."), os.path.join(os.path.abspath(os.path.dirname(sys.argv[0])), "..")]))


from shinken.bin import VERSION
from shinken.objects.config import Config

class skonf:

    def __init__(self,configfile):
        self.configfile = configfile

    def loadconfig(self):
        try:
            c=Config()
            c.read_config_silent=1
            r=c.read_config(self.configfile)
            self.config=c.read_config_buf(r)
        except:
            raise Exception('skonf','ConfigRead')

    def setparam(self,objectype,directive,value,filters):
        dfilters={}
        if len(filters) > 0:
            t=filters.split(',')
            for i in range(len(t)):
                (k,v)=t[i].split('=')
                dfilters[k]=v

        if self.config.has_key(objectype):
            max=len(self.config[objectype])
            filterok=0
            for i in range(max):
                filterok=0
                for (d,v) in dfilters.items():
                    filterok=filterok+1    
                    if self.config[objectype][i].has_key(d):
                        if self.config[objectype][i][d] != v:
                            filterok=filterok-1    
                    else:
                        filterok=filterok-1    
                if filterok == len(dfilters):
                    self.config[objectype][i][directive]=value
                    if len(dfilters)>0:
                        message="updated configuration of %s[%d] %s=%s where %s" % (objectype,i,directive,value,filters)
                    else:
                        message="updated configuration of %s[%d] %s=%s" % (objectype,i,directive,value)
                    return (True,message)
        else:
            return (False,"Unknown object type %s" % (o))

    def getdirective(self,objectype,directive,filters):
        dfilters={}
        value=""
        if len(filters) > 0:
            t=filters.split(',')
            for i in range(len(t)):
                (k,v)=t[i].split('=')
                dfilters[k]=v

        if self.config.has_key(objectype):
            max=len(self.config[objectype])
            filterok=0
            if max > 1 or max == 0:
                return (False,"Two many values. Refine your filter")
            filterok=0
            for (d,v) in dfilters.items():
                filterok=filterok+1    
                if self.config[objectype][0].has_key(d):
                    if self.config[objectype][0][d] != v:
                        filterok=filterok-1    
                else:
                    filterok=filterok-1    
            if filterok == len(dfilters):
                if not self.config[objectype][0].has_key(directive):
                    value=""
                else:
                    value=self.config[objectype][0][directive]
        else:
            return (False,"%s not found" % (objectype))
        if value == "": 
            return (False,"Not found")
        else:
            return (True,value)

    def dumpconfig(self,type,allowed):
        for (k,oc) in self.config.items():
            if k in allowed:
                if type != "" and type == k:
                    display=1
                else:
                    display=0

                if display==1:
                    print "".center(100,"=")
                    print "| "+k.center(97," ")+"|"
                    print "".center(100,"=")
                    for o in oc:
                        print "+".ljust(99,"-")+"+"
                        for (d,v) in o.items():
                            if d != "imported_from":
                                if len(v) > 48:
                                    vp = self.splitCount(v,47)
                                    col1 = "| "+d.ljust(47," ")+"| "
                                    col2 = vp[0].ljust(48," ")+"|"
                                    print col1+col2
                                    vp.pop(0)
                                    for vpe in vp:
                                        col1 = "| "+" ".ljust(47," ")+"| "
                                        col2 = vpe.ljust(48," ")+"|"
                                        print col1+col2 
                                else:
                                    col1 = "| "+d.ljust(47," ")+"| "
                                    col2 = v.ljust(48," ")+"|"
                                    print col1+col2 
                        print "+".ljust(99,"-")+"+"
        return True                                  

    def splitCount(self,s, count):
        return [s[i:i+count] for i in range(0, len(s), count)]

    def cloneobject(self,objectype,directive,filter):
        directives={}
        filters={}
        newobj={}
        # extract directives to be modified 
        for pair in directive.split(','):
            (d,v)=pair.split('=')
            directives[d]=v
        # extract filters
        for pair in filter.split(','):
            (d,v)=pair.split('=')
            filters[d]=v
        filterok=0
        # find the matching object
        for o in self.config[objectype]:
            for (d,v) in filters.items():
                if o.has_key(d) and o[d] == v:
                    filterok=filterok+1
            if filterok == len(filters):
                newobj=copy.deepcopy(o)
                filterok=0
        if len(newobj) == 0:
            return (False,"I was unable to find the object to be cloned")
        # create the new object
        for (d,v) in directives.items():
            newobj[d]=v
        # verify the unicity of the object
        for o in self.config[objectype]:
            if o[objectype+"_name"] == newobj[objectype+"_name"]:
                return (False,"An object of type %s with the name %s allready exist" % (objectype,newobj[objectype+"_name"]))
        self.config[objectype].append(newobj)
        return (True,"Success")

    def delobject(self,objectype,filters):
        dfilters={}
        configparts=[]
        if len(filters) > 0:
            t=filters.split(',')
            for i in range(len(t)):
                (k,v)=t[i].split('=')
                dfilters[k]=v

        if self.config.has_key(objectype):
            max=len(self.config[objectype])
            filterok=0
            for i in range(max):
                filterok=0
                for (d,v) in dfilters.items():
                    filterok=filterok+1    
                    if self.config[objectype][i].has_key(d):
                        if self.config[objectype][i][d] != v:
                            filterok=filterok-1    
                    else:
                        filterok=filterok-1    
                if filterok == len(dfilters):
                    self.config[objectype].pop(i)
        else:
            return (False,"Unknown object type %s" % (o))
        return (True,"config removed")


    def getaddresses(self):
        allowed = [ 'poller', 'arbiter', 'scheduler', 'broker', 'receiver', 'reactionner' ]
        addresses=[]
        for (ot,oc) in self.config.items():
            if ot in allowed:
                for o in oc:
                    for (d,v) in o.items():
                        if d == "address" and v != "localhost" and v != "127.0.01" :
                            if not v in addresses:
                                addresses.append(v)
                                return (True,v)
        return (False,"No items")                            



    def getconfig(self,objectype,filters=""):
        dfilters={}
        configparts=[]
        if len(filters) > 0:
            t=filters.split(',')
            for i in range(len(t)):
                (k,v)=t[i].split('=')
                dfilters[k]=v

        if self.config.has_key(objectype):
            max=len(self.config[objectype])
            filterok=0
            for i in range(max):
                filterok=0
                for (d,v) in dfilters.items():
                    filterok=filterok+1    
                    if self.config[objectype][i].has_key(d):
                        if self.config[objectype][i][d] != v:
                            filterok=filterok-1    
                    else:
                        filterok=filterok-1    
                if filterok == len(dfilters):
                    configparts.append(self.config[objectype][i])
#                print "%s[%d]" % (objectype,i)
#                for (d,v) in self.config[objectype][i].items():
#                    print "  %s = %s" % (d,v)
        else:
            return (False,"Unknown object type %s" % (o))
        return (True,configparts)

    def writeconfig(self):
        return (False,"Not implemented")

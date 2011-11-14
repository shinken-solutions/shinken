#!/usr/bin/env python
import os
import cmd 
import sys 
import time
import datetime
import copy
import getopt

from shinken.bin import VERSION
from shinken.objects.config import Config

class Skonf:

    def __init__(self,configfile):
        self.configfile = configfile
        self.loadconfig()

    def splitCount(self,s, count):
        return [s[i:i+count] for i in range(0, len(s), count)]

    def loadconfig(self):
        try:
            c=Config()
            c.read_config_silent=1
            r=c.read_config(self.configfile)
            self.config=c.read_config_buf(r)
            return (True,"Config loaded") 
        except:
            return (False,"There was an error reading the configuration file")

    def writeconfig(self):
        bck="%s.%d" % (self.configfile,time.time())
        os.rename(self.configfile,bck)

        fd = open(self.configfile,'w')
        objects=["arbiter","poller","scheduler","broker","reactionner","receiver","module","realm"]
        for (t,s) in self.config.items():
            if t in objects:
                for o in range(len(self.config[t])):
                    buff="define %s {\n" % (t)
                    fd.write(buff)
                    for (d,v) in self.config[t][o].items():
                        if d != "imported_from":
                            buff="  %s %s\n" % (d,v)
                            fd.write(buff)
                    buff="}\n\n"
                    fd.write(buff)
        fd.close()

    def delobject(self,objectype,filters):
        dfilters={}
        max=0
        if len(filters) > 0:
            t=filters.split(',')
            for i in range(len(t)):
                (k,v)=t[i].split('=')
                dfilters[k]=v
        else:
            return (False,"Filter is mandatory")

        if self.config.has_key(objectype):
            filterok=0
            max=len(self.config[objectype])
            removed=0
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
                    removed = removed+1
            if removed == 0:
                return (False,"Filter did not return any result")
            else:
                return (True,"%d objects removed" % (removed))
        else:
            return (False,"No %s objects found" % (objectype))

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
        return (True,"Clone success") 



    def addobject(self,objectype,directive):
        # allowed objects types to be added
        allowed = [ 'poller', 'arbiter', 'scheduler', 'broker', 'receiver', 'reactionner' ]

        # veritfy if object type is allowed
        if not objectype in allowed:
            return (False, "Invalid objectype")

        # get a dict of directives 
        try:
          directives={}
          for pair in directive.split(','):
              (d,v) = pair.split('=')
              directives[d]=v
        except:
            return (False, "An unrecoverable error occured while checking directives")

        # at least the directive objectype_name should exist
        if not directives.has_key(objectype+"_name"):
            return (False, "The object definition should have at least an object name directive")

        # check if an object with the same name and type allready exist
        if self.config.has_key(objectype):
            good=1
            # an object with the same type allready exist so we check it have different name
            name = directives[objectype+"_name"]
            for o in self.config[objectype]:
                if o[objectype+"_name"] == name:
                    # ouch same object allready defined
                    return (False, "%s %s allready exist" % (objectype,name))

        # so we can create the new object
        newobject= {} 
        for (d,v) in directives.items():
            if d != "imported_from":
                newobject[d]=v
        self.config[objectype].append(newobject)
        return (True, "Add object success")

    def dumpconfig(self,type,allowed):
        for (k,oc) in self.config.items():
            if k in allowed:
                if type != "" and type == k:
                    display=1
                else:
                    display=0

                if display==1:
                    self.dumpdata(k,oc)

    def getdirective(self,objectype,directive,filters):
        dfilters={}
        if len(filters) > 0:
            t=filters.split(',')
            for i in range(len(t)):
                (k,v)=t[i].split('=')
                dfilters[k]=v

        if self.config.has_key(objectype):
            max=len(self.config[objectype])
            filterok=0
            if max > 1 or max == 0:
                return (False, "Two many values. Refine your filter")
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
                    return (False, "Directive not found")
                else:
                    return (True,self.config[objectype][0][directive])
        else:
            Return (False, "%s not found" % (objectype))

    def dumpdata(self,title,data):
        print "".center(100,"=")
        print "| "+title.center(97," ")+"|"
        print "".center(100,"=")
        for o in data :
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


    def getobject(self,objectype,filters):
        dfilters={}
        objects=[]
        max=0
        if len(filters) > 0:
            t=filters.split(',')
            for i in range(len(t)):
                (k,v)=t[i].split('=')
                dfilters[k]=v
        else:
            return (False,"Filter is mandatory")

        if self.config.has_key(objectype):
            filterok=0
            max=len(self.config[objectype])
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
                    objects.append(self.config[objectype][i])
            if len(objects) > 0:
                return (True,objects)
            else:
                return (False,"No results")
        else:
            return (False,"No %s objects found" % (objectype))

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
                        message = "updated configuration of %s[%d] %s=%s where %s" % (objectype,i,directive,value,filters)
                    else:
                        message = "updated configuration of %s[%d] %s=%s" % (objectype,i,directive,value)
                    return (True,"setparam success")
        else:
            return (False, "Unknown object type %s" % (o))


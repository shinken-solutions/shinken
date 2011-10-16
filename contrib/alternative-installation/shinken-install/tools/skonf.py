#!/usr/bin/env python
import os
import cmd 
import sys 
import time
import datetime
import copy

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

import getopt, sys

def usage():
    print "skonf.py -a action -f configfile -o objecttype -d directive -v value -r directive=value,directive=value"
    print ""
    print " * actions:"
    print "   - addobject : add a shinken object to the shinken configuration file"
    print "   - delobject : remove a shinken object from the shinken configuration file"
    print "   - cloneobject : clone an object (currently only pollers are suported" 
    print "   - showconfig : display configuration of object"
    print "   - setparam : set directive value for an object"
    print "   - getdirective : get a directive value from an object"
    print "   - getaddresses : list the IP addresses involved in the shinken configuration"
    print " * configfile : full path to the shinken-specific.cfg file"
    print " * objectype : configuration object type on which the action apply"
    print " * directive : the directive name of a configuration object"
    print " * value : the directive value of a configuration object"
    print " * r : this parameter restric the application to objects matching the directive/value pair list"

def main():
    config=()
    action=""
    configfile=""
    objectype=""
    directive=""
    value=""
    filters=""
    quiet=0
    try:
        opts, args = getopt.getopt(sys.argv[1:], "qa:f:o:d:v:r:",[])
    except getopt.GetoptError, err:
        print str(err) 
        usage()
        sys.exit(2)
    for o, a in opts:
        if o == "-a":
            actions=["setparam","showconfig","addobject","getdirective","getaddresses","delobject","cloneobject"]
            if a in actions:
                action=a
            else:
                print "Invalid action"
                usage()
                sys.exit(2)
        elif o == "-f":
            configfile = a 
        elif o == "-q":
            quiet = 1 
        elif o == "-o":
            objectype = a
        elif o == "-d":
            directive = a 
        elif o == "-v":
            value = a
        elif o == "-r":
            filters= a 
        else:
            assert False, "unhandled option"
            sys.exit(2)

    config = loadconfig([configfile])

    if action == "":
        print "action is mandatory"
        usage()
        sys.exit(2)

    if configfile == "":
        print "config file is mandatory"
        usage()
        sys.exit(2)
    
    if objectype == "" and action != "getaddresses" and action != "showconfig":
        print "object type is mandatory"
        usage()
        sys.exit(2)
    if directive == "" and (action == "setparam" or action == "addobject"):
        print "directive is mandatory"
        usage()
        sys.exit(2)

    if filters == "" and action == "delobject": 
        print "filters is mandatory"
        usage()
        sys.exit(2)
    
    if value == "" and action == "setparam":
        print "value is mandatory"
        usage()
        sys.exit(2)

    allowed = [ 'poller', 'arbiter', 'scheduler', 'broker', 'receiver', 'reactionner' ]

    if action == "setparam":
        confignew=setparam(config,objectype,directive,value,filters)
        writeconfig(confignew,configfile)
        if quiet == 0 : dumpconfig(objectype,confignew,allowed)
    elif action == "showconfig":
        allowed = [ 'poller', 'arbiter', 'scheduler', 'broker', 'receiver', 'reactionner', 'module' ]
        dumpconfig(objectype,config,allowed)
    elif action == "cloneobject":
        allowed = [ 'poller', 'arbiter', 'scheduler', 'broker', 'receiver', 'reactionner', 'module' ]
        if objectype not in allowed:
            print "Clone of %s is not supported" % (objectype)
        else:
            confignew=cloneobject(config,objectype,directive,filters)
            writeconfig(confignew,configfile)
            if quiet == 0 : 
                dumpconfig(objectype,confignew,allowed)
            else:
                print "The objectype %s has been cloned with the new attributes : %s" % (objectype,filter)
    elif action == "addobject":
        confignew = addobject(config,objectype,directive)
        writeconfig(confignew,configfile)
        if quiet == 0 : 
            dumpconfig(objectype,confignew,allowed)
        else:
            print "Added %s : %s" % (objectype,directive)
    elif action == "delobject":
        confignew = delobject(config,objectype,filters)
        writeconfig(confignew,configfile)
        if quiet == 0 : dumpconfig(objectype,confignew,allowed)
    elif action == "getdirective":
        getdirective(config,objectype,directive,filters)
    elif action == "getaddresses":
        getaddresses(config)
    else:
        print "Unknown action %s" % (action)
        sys.exit(2)

def delobject(config,objectype,filters):
    print "NOT IMPLEMENTED (YET)"

def cloneobject(config,objectype,directive,filter):
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
    for o in config[objectype]:
        for (d,v) in filters.items():
            if o.has_key(d) and o[d] == v:
                filterok=filterok+1
        if filterok == len(filters):
            newobj=copy.deepcopy(o)
            filterok=0
    if len(newobj) == 0:
        print "I was unable to find the object to be cloned"
        sys.exit(2)
    # create the new object
    for (d,v) in directives.items():
        newobj[d]=v
    # verify the unicity of the object
    for o in config[objectype]:
        if o[objectype+"_name"] == newobj[objectype+"_name"]:
            print "An object of type %s with the name %s allready exist" % (objectype,newobj[objectype+"_name"])
            sys.exit(2)

    config[objectype].append(newobj)
    return config


def getaddresses(config):
    allowed = [ 'poller', 'arbiter', 'scheduler', 'broker', 'receiver', 'reactionner' ]
    addresses=[]
    for (ot,oc) in config.items():
        if ot in allowed:
            for o in oc:
                for (d,v) in o.items():
                    if d == "address" and v != "localhost" and v != "127.0.01" :
                        if not v in addresses:
                            addresses.append(v)
                            print v

def showconfig(config,objectype,filters=""):
    dfilters={}
    if len(filters) > 0:
        t=filters.split(',')
        for i in range(len(t)):
            (k,v)=t[i].split('=')
            dfilters[k]=v

    if config.has_key(objectype):
        max=len(config[objectype])
        filterok=0
        for i in range(max):
            filterok=0
            #if config[objectype][i].has_key(directive):
            for (d,v) in dfilters.items():
                filterok=filterok+1    
                if config[objectype][i].has_key(d):
                    if config[objectype][i][d] != v:
                        filterok=filterok-1    
                else:
                    filterok=filterok-1    
            if filterok == len(dfilters):
                print "%s[%d]" % (objectype,i)
                for (d,v) in config[objectype][i].items():
                    print "  %s = %s" % (d,v)
    else:
        print "Unknown object type %s" % (o)
    return config        

def writeconfig(config,configfile):
    bck="%s.%d" % (configfile,time.time())
    os.rename(configfile,bck)

    fd = open(configfile,'w')
    objects=["arbiter","poller","scheduler","broker","reactionner","receiver","module","realm"]
    for (t,s) in config.items():
        if t in objects:
            for o in range(len(config[t])):
                buff="define %s {\n" % (t)
                fd.write(buff)
                for (d,v) in config[t][o].items():
                    if d != "imported_from":
                        buff="  %s %s\n" % (d,v)
                        fd.write(buff)
                buff="}\n\n"
                fd.write(buff)
    fd.close()

def addobject(config,objectype,directive):
    # allowed objects types to be added
    allowed = [ 'poller', 'arbiter', 'scheduler', 'broker', 'receiver', 'reactionner' ]

    # veritfy if object type is allowed
    if not objectype in allowed:
        print "Invalid objectype"
        sys.exit(2)

    # get a dict of directives 
    try:
      directives={}
      for pair in directive.split(','):
          (d,v) = pair.split('=')
          directives[d]=v
    except:
        print "An unrecoverable error occured while checking directives"
        sys.exit(2)

    # at least the directive objectype_name should exist
    if not directives.has_key(objectype+"_name"):
        print "The object definition should have at least an object name directive"
        sys.exit(2)

    # check if an object with the same name and type allready exist
    if config.has_key(objectype):
        good=1
        # an object with the same type allready exist so we check it have different name
        name = directives[objectype+"_name"]
        for o in config[objectype]:
            if o[objectype+"_name"] == name:
                # ouch same object allready defined
                print "%s %s allready exist" % (objectype,name)
                sys.exit(2)


    # so we can create the new object
    newobject= {} 
    for (d,v) in directives.items():
        if d != "imported_from":
            newobject[d]=v
    config[objectype].append(newobject)
    return config

def splitCount(s, count):
    return [s[i:i+count] for i in range(0, len(s), count)]

def dumpconfig(type,config,allowed):
    for (k,oc) in config.items():
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
                                vp = splitCount(v,47)
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



def getdirective(config,objectype,directive,filters):
    dfilters={}
    if len(filters) > 0:
        t=filters.split(',')
        for i in range(len(t)):
            (k,v)=t[i].split('=')
            dfilters[k]=v

    if config.has_key(objectype):
        max=len(config[objectype])
        filterok=0
        if max > 1 or max == 0:
            print "Two many values. Refine your filter"
            sys.exit(2)
        filterok=0
        #if config[objectype][i].has_key(directive):
        for (d,v) in dfilters.items():
            filterok=filterok+1    
            if config[objectype][0].has_key(d):
                if config[objectype][0][d] != v:
                    filterok=filterok-1    
            else:
                filterok=filterok-1    
        if filterok == len(dfilters):
            if not config[objectype][0].has_key(directive):
                value=""
            else:
                value=config[objectype][0][directive]
            
            print value
            sys.exit(0)
    else:
        print "%s not found" % (objectype)
        sys.exit(2)
        
    return config        

def setparam(config,objectype,directive,value,filters):
    dfilters={}
    if len(filters) > 0:
        t=filters.split(',')
        for i in range(len(t)):
            (k,v)=t[i].split('=')
            dfilters[k]=v

    if config.has_key(objectype):
        max=len(config[objectype])
        filterok=0
        for i in range(max):
            filterok=0
            #if config[objectype][i].has_key(directive):
            for (d,v) in dfilters.items():
                filterok=filterok+1    
                if config[objectype][i].has_key(d):
                    if config[objectype][i][d] != v:
                        filterok=filterok-1    
                else:
                    filterok=filterok-1    
            if filterok == len(dfilters):
                config[objectype][i][directive]=value
                if len(dfilters)>0:
                    print "updated configuration of %s[%d] %s=%s where %s" % (objectype,i,directive,value,filters)
                else:
                    print "updated configuration of %s[%d] %s=%s" % (objectype,i,directive,value)
            #else:
            #    print "object %s has no directive %s" % (objectype,directive)    
    else:
        print "Unknown object type %s" % (o)
    return config        

def loadconfig(configfile):
    try:
        c=Config()
        c.read_config_silent=1
        r=c.read_config(configfile)
        b=c.read_config_buf(r)
        return b
    except:
        print "There was an error reading the configuration file"
        sys.exit(2)

if __name__ == "__main__":
    main()

#!/usr/bin/env python
import os
import cmd 
import sys 
import time
import datetime

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
    print "modify shinken parameter : skonf.py -a setparam -f configfile -o objecttype -d directive -v value -r directive=value,directive=value"
    print "display shinken config for a specific objecttypei : skonf.py -a showconfig -f configfile -o objectype"

def main():
    config=()
    action=""
    configfile=""
    objectype=""
    directive=""
    value=""
    filters=""
    try:
        opts, args = getopt.getopt(sys.argv[1:], "q:a:f:o:d:v:r:",[])
    except getopt.GetoptError, err:
        print str(err) 
        usage()
        sys.exit(2)
    for o, a in opts:
        if o == "-a":
            if a == "setparam" or a == "showconfig" or a == "addobject" or a == "getdirective":
                action=a
            else:
                print "Invalid action"
                usage()
                sys.exit(2)
        elif o == "-f":
            configfile = a 
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
    
    if objectype == "":
        print "object type is mandatory"
        usage()
        sys.exit(2)
    
    if directive == "" and action == "setparam":
        print "directive is mandatory"
        usage()
        sys.exit(2)
    
    if value == "" and action == "setparam":
        print "value is mandatory"
        usage()
        sys.exit(2)

    if directive == "" and action == "addobject":
        print "directive is mandatory"
        usage()
        sys.exit(2)

    if action == "setparam":
        confignew=setparam(config,objectype,directive,value,filters)
        writeconfig(confignew,configfile)
    elif action == "showconfig":
        showconfig(config,objectype,filters)
    elif action == "addobject":
        addobject(config,objectype,directive)
    elif action == "getdirective":
        getdirective(config,objectype,directive,filters)

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
    print "define %s {" % (objectype)
    for (d,v) in directives.items():
        print "    %s    %s" % (d,v)
    print "}"

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

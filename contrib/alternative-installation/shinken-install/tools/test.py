#!/usr/bin/python26
import sys
import os
import cmd 
import sys 
import time
import datetime
import copy
import getopt

from tools.skonf.libskonf import Skonf 


allowed = [ 'poller', 'arbiter', 'scheduler', 'broker', 'receiver', 'reactionner', 'module' ]
config="/opt/shinken/etc/shinken-specific.cfg"

skf = Skonf([config])

print "".center(100,"=")
print "| "+"loadconfig".center(97," ")+"|"
print "".center(100,"=")
try:
    code,result = skf.loadconfig()
    print result
except:
    print "loadconfig failed"
    sys.exit(2)

print "".center(100,"=")
print "| "+"dumpconfig".center(97," ")+"|"
print "".center(100,"=")
try:
    for o in allowed:
        skf.dumpconfig(o,allowed)
except:
    print "dumpconfig failed"

print "".center(100,"=")
print "| "+"setparam".center(97," ")+"|"
print "".center(100,"=")
try:
    (code,result)=skf.setparam("poller","poller_name","poller-main","poller_name=poller-1")
    print result
except:
    print "setparam failed"

print "".center(100,"=")
print "| "+"getdirective".center(97," ")+"|"
print "".center(100,"=")
try:
    (code,result) = skf.getdirective("poller","poller_name","poller_name=poller-main")
    print result
except:
    print "getdirective failed"

print "".center(100,"=")
print "| "+"cloneobject".center(97," ")+"|"
print "".center(100,"=")
try:
    (code,result)=skf.cloneobject("poller","poller_name=poller-sat1,address=10.10.10.10","poller_name=poller-main")
    print result
    skf.dumpconfig("poller",allowed)
except:
    print "cloneobject failed"

print "".center(100,"=")
print "| "+"getobject".center(97," ")+"|"
print "".center(100,"=")
try:
    (code,result)=skf.getobject("poller","poller_name=poller-main")
    skf.dumpdata("poller",result)
except:
    print "getobject failed"

print "".center(100,"=")
print "| "+"delobject".center(97," ")+"|"
print "".center(100,"=")
try:
    (code,result)=skf.delobject("poller","poller_name=poller-sat1")
    skf.dumpconfig("poller",allowed)
except:
    print "delobject failed"

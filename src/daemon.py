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

import os, errno, sys

if os.name != 'nt':
    from pwd import getpwnam
    from grp import getgrnam


##########################   DAEMON PART    ###############################
# The standard I/O file descriptors are redirected to /dev/null by default.
if (hasattr(os, "devnull")):
    REDIRECT_TO = os.devnull
else:
    REDIRECT_TO = "/dev/null"

UMASK = 0


def unlink(pidfile):
    print "Unlinking", pidfile
    os.unlink(pidfile)
            

def findpid(pidfile):
    f = open(pidfile)
    p = f.read()
    f.close()
    return int(p)


#Check if previous run are still launched by reading the pidfile
#if the pid exist by not the pid, we remove the pidfile
#if still exit, we can replace (kill) the other run
#or just bail out
def check_parallele_run(replace=False, pidfile=''):
    if os.path.exists(pidfile):
        p = findpid(pidfile)
        try:
            os.kill(p, 0)
        except os.error, detail:
            if detail.errno == errno.ESRCH:
                print "stale pidfile exists.  removing it."
                os.unlink(pidfile)
        else:
            #if replace, kill the old process
            if replace:
                print "Replacing",p 
                os.kill(p, 3)
            else:
                raise SystemExit, "valid pidfile exists.  Exiting."

#Make the program a daemon. It can redirect all outputs (stdout, stderr) to debug file if need
#or to devnull if no debug
def create_daemon(maxfd_conf=1024, workdir='/usr/local/nagios/var', pidfile='', debug=False, debug_file=''):
    #First we manage the file descriptor, because debug file can be
    #relative to pwd
    import resource
    maxfd = resource.getrlimit(resource.RLIMIT_NOFILE)[1]
    if (maxfd == resource.RLIM_INFINITY):
         maxfd = maxfd_conf

    # Iterate through and close all file descriptors.
    for fd in range(0, maxfd):
         try:
             os.close(fd)
         except OSError:# ERROR, fd wasn't open to begin with (ignored)
             pass
    #If debug, all will be writen to if
    if debug:
        os.open(debug_file, os.O_CREAT | os.O_WRONLY | os.O_TRUNC)
    else:#else, nowhere...
        os.open(REDIRECT_TO, os.O_RDWR)
    os.dup2(0, 1)# standard output (1)
    os.dup2(0, 2)# standard error (2)
    
    #Now the Fork/Fork
    try:
        pid = os.fork()
    except OSError, e:
        raise Exception, "%s [%d]" % (e.strerror, e.errno)
    if (pid == 0):
        os.setsid()
        try:
            pid = os.fork()
        except OSError, e:
            raise Exception, "%s [%d]" % (e.strerror, e.errno)
        if (pid == 0):
            os.chdir(workdir)
            os.umask(UMASK)
        else:
            os._exit(0)
    else:
         os._exit(0)

    #Ok, we daemonize :)
    #We writ the pid file now
    f = open(pidfile, "w")
    f.write("%d" % os.getpid())
    f.close()
    
    return(0)


#Just give the uid of a user by looking at it's name
def find_uid_from_name(name):
    try:
        return getpwnam(name)[2]
    except KeyError as exp:
        print "Error: the user", name, "is unknown"
        return None

#Just give the gid of a group by looking at it's name
def find_gid_from_name(name):
    try:
        return getgrnam(name)[2]
    except KeyError as exp:
        print "Error: the group", name, "is unknown"
        return None


#Change user of the running program. Just insult the admin
#if he wants root run (it can override). If change failed,
#it exit 2
def change_user(user, group, insane=False):
    #print "Trying to change user to", user, group
    #print "I am curently", os.getuid(), os.getgid()
    if (user == 'root' or group == 'root') and not insane:
        print "What's ??? You want the application run under the root account?"
        print "I am not agree with it. If you really whant it, put :"
        print "idontcareaboutsecurity=yes"
        print "in the config file"
        print "Exiting"
        sys.exit(2)

    uid = find_uid_from_name(user)
    gid = find_gid_from_name(group)
    if uid == None or gid == None:
        print "Exiting"
        sys.exit(2)
    try:
        #First group, then user :)
        os.setregid(gid, gid)
        os.setreuid(uid, uid)
    except OSError, e:
        print "Error : cannot change user/group to %s/%s (%s [%d])" % (user, group, e.strerror, e.errno)
        print "Exiting"
        sys.exit(2)
    

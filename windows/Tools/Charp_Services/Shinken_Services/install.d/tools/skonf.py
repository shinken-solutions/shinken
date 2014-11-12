#!/usr/bin/env python
#
# Copyright (C) 2009-2014:
#    Gabes Jean, naparuba@gmail.com
#    Gerhard Lausser, Gerhard.Lausser@consol.de
#    David GUENAULT, dguenault@monitoring-fr.org
#
# This file is part of Shinken.
#
# Shinken is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Shinken is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with Shinken.  If not, see <http://www.gnu.org/licenses/>.

import os
import cmd
import sys
import time
import datetime
import copy
import socket

#try:
#    from shinken.bin import VERSION
#    import shinken
#except ImportError:
#    # If importing shinken fails, try to load from current directory
#    # or parent directory to support running without installation.
#    # Submodules will then be loaded from there, too.
#    import imp
#    imp.load_module('shinken', *imp.find_module('shinken', [os.path.realpath("."), os.path.realpath(".."), os.path.join(os.path.abspath(os.path.dirname(sys.argv[0])), "..")]))


from shinken.bin import VERSION
from shinken.objects.config import Config

import getopt, sys


def usage():
    print "skonf.py -a action -f configfile -o objecttype -d directive -v value -r directive=value,directive=value"
    print ""
    print " * actions:"
    print "   - control (control action is specified with -d [stop|start|restart]). Apply action on all satellites"
    print "   - sync: deploy shinken-specific on all satellites"
    print "   - deploy deploy shinken on hosts defined in authfile (-f path/to/auth)"
    print "   - macros: execute macros file"
    print "   - delobject: remove a shinken object from the shinken configuration file"
    print "   - cloneobject: clone an object (currently only pollers are suported"
    print "   - showconfig: display configuration of object"
    print "   - setparam: set directive value for an object"
    print "   - delparam: remove directive for an object"
    print "   - getdirective: get a directive value from an object"
    print "   - getobjectnames: get a list of objects names (required parameters: configfile, objectype)"
    print " * configfile: full path to the shinken-specific.cfg file"
    print " * objectype: configuration object type on which the action apply"
    print " * directive: the directive name of a configuration object"
    print " * value: the directive value of a configuration object"
    print " * r: this parameter restric the application to objects matching the directive/value pair list"


def main():
    config = ()
    action = ""
    configfile = ""
    objectype = ""
    directive = ""
    value = ""
    filters = ""
    commit = True
    try:
        opts, args = getopt.getopt(sys.argv[1:], "qa:f:o:d:v:r:", [])
    except getopt.GetoptError, err:
        print str(err)
        usage()
        sys.exit(2)
    for o, a in opts:
        if o == "-a":
            actions = ["setparam", "delparam", "showconfig", "addobject", "getobjectnames", "getdirective", "getaddresses", "delobject", "cloneobject", "macros", "sync", "control", "deploy", "removemodule"]
            if a in actions:
                action = a
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
            filters = a
        else:
            assert False, "unhandled option"
            sys.exit(2)


    if action == "":
        print "action is mandatory"
        usage()
        sys.exit(2)

    if configfile == "" and action != "control":
        print "config file is mandatory"
        usage()
        sys.exit(2)

    if objectype == "" and action != "getaddresses" and action != "showconfig" and action != "macros" and action != "sync" and action != "control" and action != "deploy":
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

    if action != "macros" and action != "control" and action != "deploy":
        result, config = loadconfig([configfile])
        if not result:
            print config
            sys.exit(2)
        commit = False
    else:
        config = None

    allowed = ['poller', 'arbiter', 'scheduler', 'broker', 'receiver', 'reactionner']

    if action == "setparam":
        result, content = setparam(config, objectype, directive, value, filters)
        print content
        if not result:
            print content
            sys.exit(2)
        else:
            result, content = writeconfig(config, configfile)
            if not result:
                sys.exit(2)
            else:
                sys.exit(0)
    if action == "delparam":
        result, content = delparam(config, objectype, directive, filters)
        print content
        if not result:
            print content
            sys.exit(2)
        else:
            result, content = writeconfig(config, configfile)
            if not result:
                sys.exit(2)
            else:
                sys.exit(0)
    elif action == "macros":
        if directive != "":
            result, content = domacros(configfile, directive.split(','))
        else:
            result, content = domacros(configfile)
        if not result:
            print content
            sys.exit(2)
        else:
            sys.exit(0)
    elif action == "sync":
        if directive == "":
            print "You must specify the authentication file with -d option"
            sys.exit(2)
        result, content = sync(config, configfile, directive)
        if not result:
            print content
            sys.exit(2)
        else:
            sys.exit(0)
    elif action == "control":
        if directive == "":
            print "You must specify the authentication file with -d option"
            sys.exit(2)
        result, content = control(config, directive)
        if not result:
            print content
            sys.exit(2)
        else:
            sys.exit(0)
    elif action == "showconfig":
        allowed = ['poller', 'arbiter', 'scheduler', 'broker', 'receiver', 'reactionner', 'module']
        dumpconfig(objectype, config, allowed)
    elif action == "getobjectnames":
        allowed = ['poller', 'arbiter', 'scheduler', 'broker', 'receiver', 'reactionner', 'module']
        getobjectnames(objectype, config, allowed)
    elif action == "cloneobject":
        allowed = ['poller', 'arbiter', 'scheduler', 'broker', 'receiver', 'reactionner', 'module']
        if objectype not in allowed:
            print "Clone of %s is not supported" % (objectype)
            sys.exit(2)
        else:
            result, confignew = cloneobject(config, objectype, directive, filters)
            if not result:
                print confignew
                sys.exit(2)
            else:
                result, message = writeconfig(confignew, configfile)
                if not result:
                    print message
                    sys.exit(2)
                print "The objectype %s has been cloned with the new attributes: %s" % (objectype, filter)
    elif action == "addobject":
        print "Not implemented"
        sys.exit(2)
    elif action == "delobject":
        result, confignew = delobject(config, objectype, filters)
        if not result:
            print confignew
            sys.exit(2)
        else:
            result, message = writeconfig(confignew, configfile)
            print message
            if not result:
                sys.exit(2)
            else:
                sys.exit(0)
    elif action == "deploy":
        """ deploy shinken on remote hosts """
        result, content = deploy(configfile)
        if not result:
            print content
            sys.exit(2)
        else:
            print "Deploy ok"
    elif action == "getdirective":
        result, content = getdirective(config, objectype, directive, filters)
        if not result:
            print content
            sys.exit(2)
        else:
            print content
            sys.exit(0)
    elif action == "getaddresses":
        getaddresses(config)
    else:
        print "Unknown action %s" % (action)
        sys.exit(2)


def domacros(configfile, args=[]):
    import string
    import re
    """ load macro """
    try:
        fd = open(configfile, 'r')
        data = map(string.strip, fd.readlines())
        fd.close()
    except Exception:
        return (False, "Error while reading macros file")

    authfile = ""

    """ remove comments lines """
    index_line = 0
    cleandata = []
    for line in data:
        if re.match(r"^#", line) == None:
            cleandata.append(line)
        index_line += 1
    index_line = 0
    data = cleandata

    """ merge arguments with macro file content """
    if len(args) > 0:
        index_line = 0
        while index_line < len(data):
            index_args = 0
            tmp = data[index_line]
            while index_args < len(args):
                tmp = tmp.replace("ARG%d" % (index_args+1), args[index_args])
                data[index_line] = tmp
                index_args += 1
            index_line += 1

    allowed = ["arbiter", "scheduler", "poller", "broker", "reactionner", "receiver"]

    commands = {
            "onerror": r"(?P<action>\w+)",
            "setconfigfile": r"(?P<configfile>.*)",
            "setauthfile": r"(?P<authfile>.*)",
            "clone": r"(?P<object>\w+) set (?P<directives>.*) where (?P<clauses>.*)",
            "delete": r"(?P<object>\w+) where (?P<clauses>.*)",
            "showconfig": r"(?P<object>\w+)",
            "setparam": r"(?P<directive>\w+)=(?P<value>.*) from (?P<object>\w+) where (?P<clauses>.*)",
            "delparam": r"(?P<directive>\w+)=(?P<value>.*) from (?P<object>\w+) where (?P<clauses>.*)",
            "getdirective": r"(?P<directives>\w+) from (?P<object>\w+) where (?P<clauses>.*)",
            "removemodule": r"(?P<module>\w+) from (?P<object>\w+) where (?P<clauses>.*)",
            "control": r"(?P<action>\w+)",
            "writeconfig": r"",
            "sync": r""
            }

    """ Compile regexp """
    ccommands = {}
    for cmd, reg in commands.items():
        if reg != "":
            creg = re.compile(r"^(" + cmd + ") " + reg)
            ccommands[cmd] = creg
        else:
            ccommands[cmd] = False
    last = False
    indexline = 1

    """ macros execution """
    for line in data:
        maction = "stop"
        matched = False
        if last != False:
            line = line.replace("LAST", last)
        else:
            line = line.replace("LAST,", "")
        for command, regexp in ccommands.items():
            if re.match("^" + command, line):
                if type(regexp).__name__ == "SRE_Pattern":
                    result = regexp.match(line)
                    if result == None:
                        return (False, "There was an error with %s" % (command))
                    if command == "setconfigfile":
                        code, config = loadconfig([result.group('configfile')])
                        if not code:
                            return (code, config)
                        configfile = result.group('configfile')
                    if command == "setauthfile":
                        authfile = result.group('authfile')
                    elif command == "delete":
                        code, message = delobject(config, result.group('object'), result.group('clauses'))
                        if not code:
                            if maction == "stop": return (code, message)
                    elif command == "control":
                        code, message = control(authfile, result.group('action'))
                        if not code:
                            if maction == "stop": return (code, message)
                    elif command == "onerror":
                        if result.group('action') in ('continue', 'stop'):
                            maction = result.group('action')
                        else:
                            return  (False, "Unknown action on error %s" % (result.group('action')))
                    elif command == "clone":
                        code, message = cloneobject(config, result.group('object'), result.group('directives'), result.group('clauses'))
                        if not code:
                            if maction == "stop": return (code, message)
                    elif command == "showconfig":
                        dumpconfig(result.group('object'), config, allowed)
                    elif command == "getdirective":
                        code, last = getdirective(config, result.group('object'), result.group('directives'), result.group('clauses'))
                        if not code:
                            last = False
                            #return (code,last)
                    elif command == "setparam":
                        code, message = setparam(config, result.group('object'), result.group('directive'), result.group('value'), result.group('clauses'))
                        if not code:
                            if maction == "stop": return (code, message)
                    elif command == "delparam":
                        code, message = delparam(config, result.group('object'), result.group('directive'), result.group('clauses'))
                        if not code:
                            if maction == "stop": return (code, message)
                    elif command == "removemodule":
                        code, message = removemodule(config, result.group('module'), result.group('object'), result.group('clauses'))
                        if not code:
                            if maction == "stop": return (code, message)
                else:
                    if command == "writeconfig":
                        code, message = writeconfig(config, configfile)
                        if not code:
                            if maction == "stop": return (code, message)
                    elif command == "sync":
                        code, message = sync(config, configfile, authfile)
                        if not code:
                            if maction == "stop": return (code, message)
                matched = True
        if not matched:
            if not line == "":
                return (False, "Error Unknown command %s" % (line))
        indexline += 1
    return (True, "Macro execution success")


def delobject(config, objectype, filters):
    dfilters = {}
    max = 0
    if len(filters) > 0:
        t = filters.split(',')
        for i in range(len(t)):
            (k, v) = t[i].split('=')
            dfilters[k] = v
    else:
        return (False, "Filter is mandatory")

    if config.has_key(objectype):
        filterok = 0
        max = len(config[objectype])
        removed = 0
        for i in range(max):
            filterok = 0
            for (d, v) in dfilters.items():
                filterok = filterok + 1
                if config[objectype][i].has_key(d):
                    if config[objectype][i][d] != v:
                        filterok = filterok - 1
                else:
                    filterok = filterok - 1
            if filterok == len(dfilters):
                config[objectype].pop(i)
                removed = removed + 1
        if removed == 0:
            return (False, "Filter did not return any result")
        else:
            return (True, "%d objects removed" % (removed))
    else:
        return (False, "No %s objects found" % (objectype))


def cloneobject(config, objectype, directive, filter):
    directives = {}
    filters = {}
    newobj = {}
    # extract directives to be modified
    for pair in directive.split(','):
        (d, v) = pair.split('=')
        directives[d] = v
    # extract filters
    for pair in filter.split(','):
        (d, v) = pair.split('=')
        filters[d] = v
    filterok = 0
    # find the matching object
    for o in config[objectype]:
        for (d, v) in filters.items():
            if o.has_key(d) and o[d] == v:
                filterok = filterok + 1
        if filterok == len(filters):
            newobj = copy.deepcopy(o)
            filterok = 0
    if len(newobj) == 0:
        return (False, "I was unable to find the object to be cloned")
    # create the new object
    for (d, v) in directives.items():
        newobj[d] = v
    # verify the unicity of the object
    for o in config[objectype]:
        if o[objectype + "_name"] == newobj[objectype + "_name"]:
            return (False, "An object of type %s with the name %s allready exist" % (objectype, newobj[objectype + "_name"]))

    config[objectype].append(newobj)
    return (True, config)


def getaddresses(config):
    allowed = ['poller', 'arbiter', 'scheduler', 'broker', 'receiver', 'reactionner']
    addresses = []
    for (ot, oc) in config.items():
        if ot in allowed:
            for o in oc:
                for (d, v) in o.items():
                    if d == "address" and v != "localhost" and v != "127.0.01":
                        if not v in addresses:
                            addresses.append(v)
                            print v


def showconfig(config, objectype, filters=""):
    dfilters = {}
    if len(filters) > 0:
        t = filters.split(',')
        for i in range(len(t)):
            (k, v) = t[i].split('=')
            dfilters[k] = v

    if config.has_key(objectype):
        max = len(config[objectype])
        filterok = 0
        for i in range(max):
            filterok = 0
            #if config[objectype][i].has_key(directive):
            for (d, v) in dfilters.items():
                filterok = filterok + 1
                if config[objectype][i].has_key(d):
                    if config[objectype][i][d] != v:
                        filterok = filterok - 1
                else:
                    filterok = filterok - 1
            if filterok == len(dfilters):
                print "%s[%d]" % (objectype, i)
                for (d, v) in config[objectype][i].items():
                    print "  %s = %s" % (d, v)
    else:
        print "Unknown object type %s" % (o)
    return config


def getsatellitesaddresses(config):
    import netifaces
    import re
    allowed = ['poller', 'arbiter', 'scheduler', 'broker', 'receiver', 'reactionner']
    addresses = []
    local = []

    """ detect local adresses """
    for ifname in netifaces.interfaces():
        for t in netifaces.ifaddresses(ifname).items():
            for e in t[1]:
                if e.has_key('addr'):
                    if re.match(r"[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}", e['addr']):
                        if e['addr'] != "127.0.0.1":
                            local.append(e['addr'])

    """ get all adresses defined in configuration """
    for (ot, oc) in config.items():
        if ot in allowed:
            for o in oc:
                for (d, v) in o.items():
                    if d == "address" and v != "localhost" and v != "127.0.01":
                        if not v in local and not v in addresses:
                            addresses.append(v)

    return (True, addresses)


def getauthdata(authfile):
    import re
    import string
    """ load authentication data """
    auth = {}
    creg = re.compile(r"^(?P<address>.*):(?P<login>.*):(?P<password>.*)")
    try:
        fd = open(authfile, 'r')
        data = map(string.strip, fd.readlines())
        fd.close()

        for line in data:
            if line != "":
                result = creg.match(line)
                if result == None:
                    return "There was an error in the authentication file at line: %s" % (line)
                auth[result.group("address")] = {"login": result.group("login"), "password": result.group("password")}
        return (True, auth)
    except Exception:
        return (False, "Error while loading authentication data")


def sync(config, configfile, authfile):
    import re
    import paramiko
    import string

    code, addresses = getsatellitesaddresses(config)

    code, auth = getauthdata(authfile)
    if not code:
        return (False, auth)

    """ now push configuration to each satellite """
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        for address in addresses:
            print "Synch with: %s" % (address)
            if not auth.has_key(address):
                return (False, "Auth informations for %s does not exist in authfile" % (address))
            else:
                ssh.connect(address, username=auth[address]["login"], password=auth[address]["password"])
                ftp = ssh.open_sftp()
                ftp.put(configfile, configfile)
                ftp.close()
                ssh.close()
    except Exception:
        return (False, "There was an error trying to push configuration to %s" % (address))

    return (True, addresses)


def deploy(authfile):
    import paramiko
    import tarfile

    code, auths = getauthdata(authfile)

    if not code:
        return (False, auths)

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    """ current user """
    user = os.getlogin()

    """ define home """
    if user == "root":
        home = "/root"
    else:
        home = "/home/%s" % (user)

    """ compress shinken in tar gz format """
    print "Make archive"
    source = os.path.abspath(os.getcwd() + '/../../../../')
    tar = tarfile.open('/tmp/shinken.tar.gz', 'w:gz')
    tar.add(source)
    tar.close()

    """ upload shinken archive to remote server """
    for address, auth in auths.items():
        print "Upload archive on %s"
        ssh.connect(address, username=auth["login"], password=auth["password"])
        ftp = ssh.open_sftp()
        ftp.put('/tmp/shinken.tar.gz', os.path.abspath('/tmp/shinken.tar.gz'))
        ftp.close()
        print "Extract archive"
        stdin, stdout, stderr = ssh.exec_command('cd /tmp && tar zxvf shinken.tar.gz && rm -Rf %s/shinken && mv %s/shinken %s/' % (home, user, home))
        out = stdout.read()
        err = stderr.read()
        print "Launch installation"
        stdin, stdout, stderr = ssh.exec_command('cd %s/shinken/contrib/alternative-installation/shinken-install/ && ./shinken.sh -d && ./shinken.sh -i' % (home))
        out = stdout.read()
        err = stderr.read()
        print out
        print err
        ssh.close()

    return (True, "OK")


def control(authfile, action):
    import re
    import paramiko
    import string

    code, auth = getauthdata(authfile)
    if not code:
        return (False, auth)

    """ which command for an action """
    commands = {"stop": "service shinken stop", "start": "service shinken start", "restart": "service shinken restart"}
    if not commands.has_key(action):
        return (False, "Unknown action command")

    """ now apply control action to all elements """

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    for address, authdata in auth.items():
        try:
            ssh.connect(address, username=authdata["login"], password=authdata["password"])
            ssh.exec_command("service shinken %s" % (action))
            ssh.close()
        except socket.error:
            return (False, "socket error (%s)" % (address))
        except paramiko.BadAuthenticationType:
            return (False, "BadAuthenticationType (%s)" % (address))
        except paramiko.BadHostKeyException:
            return (False, "BadHostKeyException (%s)" % (address))
        except paramiko.ChannelException:
            return (False, "ChannelException (%s)" % (address))
        except paramiko.ChannelException:
            return (False, "ChannelException (%s)" % (address))
        except paramiko.PasswordRequiredException:
            return (False, "PasswordRequiredException (%s)" % (address))
        except paramiko.SSHException:
            return (False, "SSHException (%s)" % (address))
        except paramiko.AuthenticationException:
            return (False, "AuthenticationException (%s)" % (address))

    return (True, "Action completed")


def writeconfig(config, configfile):
    bck = "%s.%d" % (configfile, time.time())
    os.rename(configfile, bck)
    fd = open(configfile, 'w')
    objects = ["arbiter", "poller", "scheduler", "broker", "reactionner", "receiver", "module", "realm"]
    for (t, s) in config.items():
        if t in objects:
            for o in range(len(config[t])):
                buff = "define %s {\n" % (t)
                fd.write(buff)
                for (d, v) in config[t][o].items():
                    if d != "imported_from":
                        buff = "  %s %s\n" % (d, v)
                        fd.write(buff)
                buff = "}\n\n"
                fd.write(buff)
    fd.close()
    return (True, "Config saved")


def addobject(config, objectype, directive):
    # allowed objects types to be added
    allowed = ['poller', 'arbiter', 'scheduler', 'broker', 'receiver', 'reactionner']

    # veritfy if object type is allowed
    if not objectype in allowed:
        print "Invalid objectype"
        sys.exit(2)

    # get a dict of directives
    try:
        directives = {}
        for pair in directive.split(','):
            (d, v) = pair.split('=')
            directives[d] = v
    except Exception:
        print "An unrecoverable error occured while checking directives"
        sys.exit(2)

    # at least the directive objectype_name should exist
    if not directives.has_key(objectype + "_name"):
        print "The object definition should have at least an object name directive"
        sys.exit(2)

    # check if an object with the same name and type allready exist
    if config.has_key(objectype):
        good = 1
        # an object with the same type allready exist so we check it have different name
        name = directives[objectype + "_name"]
        for o in config[objectype]:
            if o[objectype + "_name"] == name:
                # ouch same object allready defined
                print "%s %s allready exist" % (objectype, name)
                sys.exit(2)

    # so we can create the new object
    newobject = {}
    for (d, v) in directives.items():
        if d != "imported_from":
            newobject[d] = v
    config[objectype].append(newobject)
    return config


def splitCount(s, count):
    return [s[i:i + count] for i in range(0, len(s), count)]


def dumpconfig(type, config, allowed):
    for (k, oc) in config.items():
        if k in allowed:
            if type != "" and type == k:
                display = 1
            else:
                display = 0

            if display == 1:
                print "".center(100, "=")
                print "| " + k.center(97, " ") + "|"
                print "".center(100, "=")
                for o in oc:
                    print "+".ljust(99, "-") + "+"
                    for (d, v) in o.items():
                        if d != "imported_from":
                            if len(v) > 48:
                                vp = splitCount(v, 47)
                                col1 = "| " + d.ljust(47, " ") + "| "
                                col2 = vp[0].ljust(48, " ") + "|"
                                print col1 + col2
                                vp.pop(0)
                                for vpe in vp:
                                    col1 = "| " + " ".ljust(47, " ") + "| "
                                    col2 = vpe.ljust(48, " ") + "|"
                                    print col1 + col2
                            else:
                                col1 = "| " + d.ljust(47, " ") + "| "
                                col2 = v.ljust(48, " ") + "|"
                                print col1 + col2
                    print "+".ljust(99, "-") + "+"


def getobjectnames(objectype, config, allowed):
    names = []
    for (k, oc) in config.items():
        if k in allowed and k == objectype:
            for o in oc:
                for (d, v) in o.items():
                    if objectype + "_name" == d:
                        names.append(v)
    print ','.join(names)
    return (True, ','.join(names))


def getdirective(config, objectype, directive, filters):
    try:
        dfilters = {}
        if len(filters) > 0:
            t = filters.split(',')
            for i in range(len(t)):
                (k, v) = t[i].split('=')
                dfilters[k] = v

        if config.has_key(objectype):
            ## max=len(config[objectype])
            ## filterok=0
            ## if max > 1 or max == 0:
            ##     return (False,"Two many values. Refine your filter")
            filterok = 0
            for (d, v) in dfilters.items():
                filterok = filterok + 1
                if config[objectype][0].has_key(d):
                    if config[objectype][0][d] != v:
                        filterok = filterok - 1
                else:
                    filterok = filterok - 1
            if filterok == len(dfilters):
                if not config[objectype][0].has_key(directive):
                    code = False
                    content = "Directive not found %s for object %s" % (directive, objectype)
                    return code, content
                else:
                    code = True
                    content = config[objectype][0][directive]
                    return code, content
            else:
                return (False, "Filters not matched")
        else:
            return (False, "%s not found" % (objectype))
    except Exception:
        return (False, "Unknown error in getdirective")


def setparam(config, objectype, directive, value, filters):
    import re
    dfilters = {}
    if len(filters) > 0:
        t = filters.split(',')
        for i in range(len(t)):
            (k, v) = t[i].split('=')
            dfilters[k] = v

    if config.has_key(objectype):
        max = len(config[objectype])
        filterok = 0
        for i in range(max):
            filterok = 0
            for (d, v) in dfilters.items():
                filterok = filterok + 1
                if config[objectype][i].has_key(d):
                    if config[objectype][i][d] != v:
                        filterok = filterok - 1
                else:
                    filterok = filterok - 1
            if filterok == len(dfilters):
                """ if directive does not exist create it! """
                if not config[objectype][i].has_key(directive):
                    config[objectype][i][directive] = value
                    message = "Added configuration %s[%d] %s=%s" % (objectype, i, directive, value)
                else:
                    """ check if directive value allready exist """
                    if re.search(value, config[objectype][i][directive]) != None:
                        message = "Directive value allready exist"
                    else:
                        config[objectype][i][directive] = value
                        message = "updated configuration of %s[%d] %s=%s" % (objectype, i, directive, value)
                print message
                return (True, message)
    else:
        return (False, "Unknown object type %s" % (o))


def removemodule(config, module, objectype, filters):
    import re
    dfilters = {}
    if len(filters) > 0:
        t = filters.split(',')
        for i in range(len(t)):
            (k, v) = t[i].split('=')
            dfilters[k.strip()] = v.strip()

    code = False
    message = "Nothing was done"


    # check wether objectype is defined or not
    if config.has_key(objectype):
        # verify each filter (directive,value)
        for (directive, value) in dfilters.items():
            for o in config[objectype]:
                if o.has_key(directive) and o[directive] == value:
                    modules = []
                    for m in o["modules"].split(','):
                        modules.append(m.strip())
                    if module in modules:
                        while module in modules:
                            modules.remove(module)
                        o["modules"] = ",".join(modules)
                    message = "removed module %s from objects of type %s" % (module, objectype)
                    code = True
                    print message
                    return (code, message)
        message = "No module %s found in object of type %s" % (module, objectype)
        code = True
        print message
        return (code, message)
    else:
        message = "no objectype %s was found in configuration" % (objectype)
        code = True
        print message
        return (code, message)


def delparam(config, objectype, directive, filters):
    import re
    dfilters = {}
    if len(filters) > 0:
        t = filters.split(',')
        for i in range(len(t)):
            (k, v) = t[i].split('=')
            dfilters[k] = v

    if config.has_key(objectype):
        max = len(config[objectype])
        filterok = 0
        for i in range(max):
            filterok = 0
            for (d, v) in dfilters.items():
                filterok = filterok + 1
                if config[objectype][i].has_key(d):
                    if config[objectype][i][d] != v:
                        filterok = filterok - 1
                else:
                    filterok = filterok - 1
            if filterok == len(dfilters):
                """ if directive exist remove it! """
                if config[objectype][i].has_key(directive):
                    """ config[objectype][i][directive]=value"""
                    config[objectype][i].pop(directive)
                    print config[objectype][i]
                    message = "Removed directive %s from %s" % (directive, objectype)
                else:
                    message = "Nothing to remove"
                return (True, message)
    else:
        return (False, "Unknown object type %s" % (o))


def loadconfig(configfile):
    try:
        c = Config()
        c.read_config_silent = 1
        r = c.read_config(configfile)
        b = c.read_config_buf(r)
        return (True, b)
    except Exception:
        return (False, "There was an error reading the configuration file")

if __name__ == "__main__":
    main()

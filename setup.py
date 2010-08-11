#!/usr/bin/env python
#Copyright (C) 2009-2010 :
#    Gabes Jean, naparuba@gmail.com
#    Gerhard Lausser, Gerhard.Lausser@consol.de
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


#first verion of this file from Maximilien Bersoult

from setuptools import setup, find_packages
from glob import glob
import os, sys, re
import ConfigParser
if os.name != 'nt':
    from pwd import getpwnam
    from grp import getgrnam


#We know that a Python 2.3 or Python3K will fail.
#We can say why and quit.
import platform
python_version = platform.python_version_tuple()

## Make sure people are using Python 2.3 or higher
if int(python_version[0]) == 2 and int(python_version[1]) < 4:
    print "Shinken require as a minimum Python 2.4.x, sorry"
    sys.exit(1)

if int(python_version[0]) == 3:
    print "Shinken is not yet compatible with Python3k, sorry"
    sys.exit(1)

def getscripts(path):
    script = os.path.basename(path)
    return script


#Set the default values for the paths
if os.name == 'nt':
    var_path="c:\\shinken\\var"
    var_owner=None
    var_group=None
    etc_path="c:\\shinken\\etc"
    etc_owner=None
    etc_group=None
else:
    etc_path="/etc/shinken"
    var_path="/var/lib/shinken/"
    var_owner='shinken'
    var_group='shinken'
    etc_owner='shinken'
    etc_group='shinken'


def generate_default_shinken_file():
    global var_path
    global etc_path
    f = open("bin/default/shinken.in")
    buf = f.read()
    f.close
    f = open("bin/default/shinken", "w")
    buf = buf.replace("$ETC$", etc_path)
    buf = buf.replace("$VAR$", var_path)
    f.write(buf)
    f.close()


def parse_config_file(config_file):
    global var_path
    global var_owner
    global var_group
    global etc_path
    global etc_owner
    global etc_group
    
    config = ConfigParser.ConfigParser()
    config.read(config_file)
    if config._sections == {}:
        print "Bad or missing config file : %s " % config_file
        sys.exit(2)
    
    etc_path = config._sections['etc']['path']
    var_path = config._sections['var']['path']
    #on nt no owner...
    if os.name != 'nt':
        var_owner=config._sections['var']['owner']
        var_group=config._sections['var']['group']
        etc_owner=config._sections['etc']['owner']
        etc_group=config._sections['etc']['group']

parse_config_file('setup_parameters.cfg')
generate_default_shinken_file()

setup(
  name = "Shinken",
  version = "0.1.99",
  packages = find_packages(),
  package_data = {'':['*.py','modules/*.py','modules/*/*.py']},
  description = "Shinken is a monitoring tool compatible with Nagios configuration and plugins",
  long_description=open('README').read(),
  author = "Gabes Jean",
  author_email = "naparuba@gmail.com",
  license = "GNU Affero General Public License",
  url = "http://www.shinken-monitoring.org",
  classifiers=['Development Status :: 4 - Beta',
               'Environment :: Console',
               'Intended Audience :: System Administrators',
               'License :: OSI Approved :: GNU Affero General Public License v3',
               'Operating System :: MacOS :: MacOS X',
               'Operating System :: Microsoft :: Windows',
               'Operating System :: POSIX',
               'Programming Language :: Python',
               'Topic :: System :: Monitoring',
               'Topic :: System :: Networking :: Monitoring',
               ],

  install_requires = [
                      'pyro',
                      ],

  scripts = [f for f in glob('bin/[!_]*.py')],
  data_files=[(etc_path, ["etc/nagios.cfg",'etc/brokerd.ini', 'etc/brokerd-windows.ini',
                                'etc/commons.cfg', 'etc/conf-windows.cfg', 'etc/host-150.cfg',
                                'etc/nagios.cfg', 'etc/nagios-windows.cfg', 'etc/pollerd.ini',
                                'etc/reactionnerd.ini', 'etc/resource.cfg', 'etc/schedulerd.ini',
                                'etc/schedulerd-windows.ini', 'etc/pollerd-windows.ini',
                                'etc/shinken-specific.cfg', 'etc/shinken-specific-high-availability.cfg',
                                'etc/shinken-specific-load-balanced-only.cfg'
                                ]),
              ('/etc/init.d', ['bin/init.d/shinken-arbiter', 'bin/init.d/shinken-broker', 'bin/init.d/shinken-poller',
                               'bin/init.d/shinken-reactionner', 'bin/init.d/shinken-scheduler']),
              ('/etc/default/', ['bin/default/shinken']),
              (var_path, ['var/void_for_git'])
              ]
  
)


#Ok now the less good part :(
#I didn't find any easy way to get it :(
#We will chown shinken:shinken for all /etc/shinken 
#and /var/lib/shinken.
def get_uid(user_name):
    try:
        return getpwnam(user_name)[2]
    except KeyError, exp:
        print "Error: the user", user_name, "is unknown"
        print "Maybe you should create this user"
        sys.exit(2)
        
def get_gid(group_name):
    try:
        return getgrnam(group_name)[2]
    except KeyError, exp:
        print "Error: the group",group_name , "is unknown"
        print "Maybe you should create this group"
        sys.exit(2)

#If there is another root, it's strange, it must be a special case...
if os.name != 'nt' and ('install' in sys.argv or 'sdist' in sys.argv) and re.search("--root", ' '.join(sys.argv)) == None:
    #First var
    var_uid = get_uid(var_owner)
    var_gui = get_gid(var_group)
    for root, dirs, files in os.walk(var_path):
        print "Changing the directory", root, "by", var_owner, ":", var_group
        os.chown(root, var_uid, var_gui)
        for fir in dirs:
            print "Change owner of the directory", root+os.sep+dir, "by", var_owner, ":", var_group
            os.chown(root+os.sep+dir,var_uid, var_gui)
        for name in files:
            print "Change owner of the file", root+os.sep+name, "by", var_owner, ":", var_group
            os.chown(root+os.sep+name,var_uid, var_gui)
        

    #Then etc
    etc_uid = get_uid(etc_owner)
    etc_gui = get_gid(etc_group)
    for root, dirs, files in os.walk(etc_path):
        print "Changing the directory", root, "by", etc_owner, ":", etc_group
        os.chown(root, etc_uid, etc_gui)
        for dir in dirs:
            print "Change owner of the directory", root+os.sep+dir, "by", etc_owner, ":", etc_group
            os.chown(root+os.sep+dir,etc_uid, etc_gui)
        for name in files:
            print "Change owner of the file", root+os.sep+name, "by", etc_owner, ":", etc_group
            os.chown(root+os.sep+name,etc_uid, etc_gui)


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
import getopt
import re
if os.name != 'nt':
    from pwd import getpwnam
    from grp import getgrnam

#Some global variables
install_scripts_path = "/usr/bin" #where to install launch scripts. Beter in PATH ;)
root_path = "/" #if the setup.py is call with root, get it

#We know that a Python 2.3 or Python3K will fail.
#We can say why and quit.
import platform
python_version = tuple((int(s) for s in platform.python_version_tuple()))

## Make sure people are using Python 2.3 or higher
if python_version < (2, 4):
    print "Shinken require as a minimum Python 2.4.x, sorry"
    sys.exit(1)

if python_version < (3):
    print "Shinken is not yet compatible with Python3k, sorry"
    sys.exit(1)

def getscripts(path):
    script = os.path.basename(path)
    return script




#Set the default values for the paths
#owners and groups
if os.name == 'nt':
    paths_and_owners = {'var' : {'path' : "c:\\shinken\\var", 'owner' : None, 'group' : None },
                        'etc' : {'path' : "c:\\shinken\\etc", 'owner'  : None, 'group' : None},
                        'libexec' : {'path' : "c:\\shinken\\libexec", 'owner'  : None, 'group' : None},
                        }
else:
    paths_and_owners = {'var' : {'path' : "/var/lib/shinken/", 'owner' : 'shinken', 'group' : 'shinken' },
                        'etc' : {'path' : "/etc/shinken", 'owner'  : 'shinken', 'group' : 'shinken'},
                        'libexec' : {'path' : "/usr/lib/shinken/plugins", 'owner'  : 'shinken', 'group' : 'shinken'},
                        }

    

#The default file must have good values for the directories:
#etc, var and where to push scripts that launch the app.
def generate_default_shinken_file():
    global paths_and_owners
    global install_scripts_path

    #Read the in file, it's our template
    f = open("bin/default/shinken.in")
    buf = f.read()
    f.close

    #then generate the new one with good values
    etc_path = paths_and_owners['etc']['path']
    var_path = paths_and_owners['var']['path']
    f = open("bin/default/shinken", "w")
    buf = buf.replace("$ETC$", etc_path)
    buf = buf.replace("$VAR$", var_path)
    buf = buf.replace("$SCRIPTS_BIN$", install_scripts_path)
    f.write(buf)
    f.close()


def parse_config_file(config_file):
    global paths_and_owners
    
    config = ConfigParser.ConfigParser()
    config.read(config_file)
    if config._sections == {}:
        print "Bad or missing config file : %s " % config_file
        sys.exit(2)

    for dir in ['var', 'etc', 'libexec']:
        paths_and_owners[dir]['path'] = config._sections[dir]['path']

    #on nt no owner...
    if os.name != 'nt':
        paths_and_owners[dir]['owner'] = config._sections[dir]['owner']
        paths_and_owners[dir]['group'] = config._sections[dir]['group']


#I search for the --install-scripts= parameter if present to modify the
#default/shinken file
for arg in sys.argv:
    print "Argument", arg
    if re.search("--install-scripts=", arg):
        elts = arg.split('=')
        if len(elts) > 1:
            install_scripts_path = elts[1]
            print "Install script path", install_scripts_path
    if re.search("--root=", arg):
        elts = arg.split('=')
        if len(elts) > 1:
            root_path = elts[1]
            print "New root path", root_path


#Get the paths and ownsers form the parameter file
#and the generate the default/shinken file so the init.d
#scripts will have the good values for directories
parse_config_file('setup_parameters.cfg')
generate_default_shinken_file()

etc_path = paths_and_owners['etc']['path']
var_path = paths_and_owners['var']['path']
libexec_path = paths_and_owners['libexec']['path']

required_pkgs = []
if python_version < (2, 5):
    required_pkgs.append('pyro<4')
else:
    required_pkgs.append('pyro')
if python_version < (2, 6):
    required_pkgs.append('multiprocessing')

setup(
  name = "Shinken",
  version = "0.2",
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
                      required_pkgs
                      ],

  scripts = [f for f in glob('bin/[!_]*.py')],
  data_files=[(etc_path, ["etc/nagios.cfg",'etc/brokerd.ini', 'etc/brokerd-windows.ini',
                                'etc/commons.cfg', 'etc/conf-windows.cfg', 'etc/host-150.cfg',
                                'etc/services-150h-1500srv.cfg',
                                'etc/nagios.cfg', 'etc/nagios-windows.cfg', 'etc/pollerd.ini',
                                'etc/reactionnerd.ini', 'etc/resource.cfg', 'etc/schedulerd.ini',
                                'etc/schedulerd-windows.ini', 'etc/pollerd-windows.ini',
                                'etc/shinken-specific.cfg', 'etc/shinken-specific-high-availability.cfg',
                                'etc/shinken-specific-load-balanced-only.cfg'
                                ]),
              ('/etc/init.d', ['bin/init.d/shinken-arbiter', 'bin/init.d/shinken-broker', 'bin/init.d/shinken-poller',
                               'bin/init.d/shinken-reactionner', 'bin/init.d/shinken-scheduler']),
              ('/etc/default/', ['bin/default/shinken']),
              (var_path, ['var/void_for_git']),
              (libexec_path, ['libexec/check.sh']),
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


#Open a /etc/*d.ini file and change the ../var occurence with a good value
#from the configuration file
def update_ini_file_with_var(path):
    global paths_and_owners
    var_path = paths_and_owners['var']['path']
    update_file_with_string(path, "../var", var_path)


#Replace the libexec path in common.cfg by the one in the parameter file
def update_resource_cfg_file_with_libexec(path):
    global paths_and_owners
    libexec_path = paths_and_owners['libexec']['path']
    update_file_with_string(path, "/usr/local/shinken/libexec", libexec_path)


#Replace paths in nagios.cfg file
def update_cfg_file_with_var_path(path):
    global paths_and_owners
    var_path = paths_and_owners['var']['path']
    update_file_with_string(path, "/usr/local/shinken/var", var_path)




#Replace the libexec path in common.cfg by the one in the parameter file
def update_file_with_string(path, match, new_string):
    f = open(path)
    buf = f.read()
    f.close
    f = open(path, "w")
    buf = buf.replace(match, new_string)
    f.write(buf)
    f.close()



#If there is another root, it's strange, it must be a special case...
if os.name != 'nt' and ('install' in sys.argv or 'sdist' in sys.argv) and re.search("--root", ' '.join(sys.argv)) == None:
    for g_dir in ['etc', 'var']:
        path = paths_and_owners[g_dir]['path']
        owner = paths_and_owners[g_dir]['owner']
        group = paths_and_owners[g_dir]['group']
        uid = get_uid(owner)
        gui = get_gid(group)
        for root, dirs, files in os.walk(path):
            print "Changing the directory", root, "by", owner, ":", group
            os.chown(root, uid, gui)
            for dir in dirs:
                print "Change owner of the directory", root+os.sep+dir, "by", owner, ":", group
                os.chown(root+os.sep+dir,uid, gui)
            for name in files:
                print "Change owner of the file", root+os.sep+name, "by", owner, ":", group
                os.chown(root+os.sep+name,uid, gui)



#Here, even with --root we should change the file with good values
if os.name != 'nt' and ('install' in sys.argv or 'sdist' in sys.argv):
    #then update the /etc/*d.ini files ../var value with the real var one
    print "Now updating the /etc/shinken/*d/ini files with the good value for var"
    update_ini_file_with_var(os.sep.join([root_path, etc_path, 'brokerd.ini']))
    update_ini_file_with_var(os.sep.join([root_path, etc_path, 'schedulerd.ini']))
    update_ini_file_with_var(os.sep.join([root_path, etc_path, 'pollerd.ini']))
    update_ini_file_with_var(os.sep.join([root_path, etc_path, 'reactionnerd.ini']))
    
    #And now the resource.cfg path with the value of libexec path
    print "Now updating the /etc/shinken/resource.cfg file with good libexec path"
    update_resource_cfg_file_with_libexec(os.sep.join([root_path, etc_path, 'resource.cfg']))

    #And update the nagios.cfg file for all /usr/local/shinken/var value with good one
    print "Now updating the /etc/shinken/nagios.cfg file with good var path"
    update_cfg_file_with_var_path(os.sep.join([root_path, etc_path, 'nagios.cfg']))
    update_cfg_file_with_var_path(os.sep.join([root_path, etc_path, 'shinken-specific.cfg']))

#!/usr/bin/env python
#Copyright (C) 2009-2011 :
#    Gabes Jean, naparuba@gmail.com
#    Gerhard Lausser, Gerhard.Lausser@consol.de
#    Hartmut Goebel <h.goebel@goebel-consult.de>
#First version of this file from Maximilien Bersoult
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


from setuptools import setup, find_packages
from glob import glob
import os, sys
import ConfigParser
import getopt
if os.name != 'nt':
    from pwd import getpwnam
    from grp import getgrnam

#Some global variables
install_scripts_path = "/usr/bin" #where to install launch scripts. Beter in PATH ;)
root_path = "/" #if the setup.py is call with root, get it

# Shinken requires Python 2.4, but does not support Python 3.x yet.
try:
    python_version = sys.version_info
except:
    python_version = (1,5)

## Make sure people are using Python 2.4 or higher
if python_version < (2, 4):
    sys.exit("Shinken require as a minimum Python 2.4.x, sorry")
elif python_version >= (3,):
    sys.exit("Shinken is not yet compatible with Python3k, sorry")

def getscripts(path):
    return os.path.basename(path)


#Set the default values for the paths
#owners and groups
if os.name == 'nt':
    paths_and_owners = {'var': {'path': "c:\\shinken\\var",
                                'owner': None,
                                'group': None },
                        'etc': {'path': "c:\\shinken\\etc",
                                 'owner': None,
                                'group': None},
                        'libexec': {'path': "c:\\shinken\\libexec",
                                    'owner': None,
                                    'group': None},
                        }
else:
    paths_and_owners = {'var': {'path': "/var/lib/shinken/",
                                'owner': 'shinken',
                                'group' : 'shinken' },
                        'etc': {'path': "/etc/shinken",
                                'owner': 'shinken',
                                'group' : 'shinken'},
                        'libexec': {'path': "/usr/lib/shinken/plugins",
                                    'owner': 'shinken',
                                    'group': 'shinken'},
                        }

#The default file must have good values for the directories:
#etc, var and where to push scripts that launch the app.
def generate_default_shinken_file():
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
  version = "0.5",
  packages = find_packages(),
  package_data = {'':['*.py','modules/*.py','modules/*/*.py']},
  description = "Shinken is a monitoring tool compatible with Nagios configuration and plugins",
  long_description=open('README').read(),
  author = "Gabes Jean",
  author_email = "naparuba@gmail.com",
  license = "GNU Affero General Public License",
  url = "http://www.shinken-monitoring.org",
  zip_safe=False,
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

  scripts = glob('bin/shinken-[!_]*'),
  data_files=[(etc_path,
               ["etc/nagios.cfg",
                'etc/brokerd.ini',
                'etc/brokerd-windows.ini',
                'etc/commands.cfg',
                'etc/timeperiods.cfg',
                'etc/templates.cfg',
                'etc/escalations.cfg',
                'etc/dependencies.cfg',
                'etc/hostgroups.cfg',
                'etc/servicegroups.cfg',
                'etc/contactgroups.cfg',
                'etc/nagios.cfg',
                'etc/nagios-windows.cfg',
                'etc/pollerd.ini',
                'etc/reactionnerd.ini',
                'etc/resource.cfg',
                'etc/schedulerd.ini',
                'etc/schedulerd-windows.ini',
                'etc/pollerd-windows.ini',
                'etc/shinken-specific.cfg',
                'etc/shinken-specific-high-availability.cfg',
                'etc/shinken-specific-load-balanced-only.cfg'
                ]),
              (os.path.join(etc_path, 'objects', 'hosts'),
               glob('etc/objects/hosts/[!_]*.cfg')),
              (os.path.join(etc_path, 'objects', 'services'),
               glob('etc/objects/services/[!_]*.cfg')),
              (os.path.join(etc_path, 'objects', 'contacts'),
               glob('etc/objects/contacts/[!_]*.cfg')),
              (os.path.join(etc_path, 'certs') ,
               glob('etc/certs/[!_]*.pem')),
              ('/etc/init.d',
               ['bin/init.d/shinken-arbiter',
                'bin/init.d/shinken-broker',
                'bin/init.d/shinken-poller',
                'bin/init.d/shinken-reactionner',
                'bin/init.d/shinken-scheduler',
                'bin/init.d/shinken']),
              ('/etc/default/',
               ['bin/default/shinken']),
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
        sys.exit("Error: the user" + user_name + "is unknown. "
                 "Maybe you should create this user.")


def get_gid(group_name):
    try:
        return getgrnam(group_name)[2]
    except KeyError, exp:
        sys.exit("Error: the group" +group_name + "is unknown. "
                 "Maybe you should create this group.")


#Open a /etc/*d.ini file and change the ../var occurence with a good value
#from the configuration file
def update_ini_file_with_var(path):
    var_path = paths_and_owners['var']['path']
    update_file_with_string(path, "../var", var_path)


#Replace the libexec path in common.cfg by the one in the parameter file
def update_resource_cfg_file_with_libexec(path):
    libexec_path = paths_and_owners['libexec']['path']
    update_file_with_string(path, "/usr/local/shinken/libexec", libexec_path)


#Replace paths in nagios.cfg file
def update_cfg_file_with_var_path(path):
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


if '-h' in sys.argv or '--help' in sys.argv:
    sys.exit(0)

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
                dir = os.path.join(root, dir)
                print "Change owner of the directory", dir, "to", owner, ":", group
                os.chown(dir,uid, gui)
            for name in files:
                name = os.path.join(root, name)
                print "Change owner of the file", name, "to", owner, ":", group
                os.chown(name,uid, gui)



#Here, even with --root we should change the file with good values
if os.name != 'nt' and ('install' in sys.argv or 'sdist' in sys.argv):
    #then update the /etc/*d.ini files ../var value with the real var one
    print "Now updating the /etc/shinken/*d.ini files with the good value for var"
    for name in ('brokerd.ini', 'schedulerd.ini', 'pollerd.ini',
                 'reactionnerd.ini'):
        update_ini_file_with_var(os.path.join(root_path, etc_path, name))

    #And now the resource.cfg path with the value of libexec path
    print "Now updating the /etc/shinken/resource.cfg file with good libexec path"
    for name in ('resource.cfg'):
        update_resource_cfg_file_with_libexec(os.path.join(root_path, etc_path, name))

    #And update the nagios.cfg file for all /usr/local/shinken/var value with good one
    print "Now updating the /etc/shinken/nagios.cfg file with good var path"
    for name in ('nagios.cfg', 'shinken-specific.cfg'):
        update_cfg_file_with_var_path(os.path.join(root_path, etc_path, name))

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
try:
    import pwd
    import grp
except ImportError:
    # assume non-unix platform
    pass

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


from distutils import log
from distutils.core import Command
from distutils.command.build import build as _build
from distutils.command.install import install as _install
from distutils.util import change_root
from distutils.errors import DistutilsOptionError

class build(_build):
    sub_commands = _build.sub_commands + [
        ('build_config', None),
        ]
    user_options = _build.user_options + [
        ('build-config', None, 'directory to build the configfiles to'),
        ]
    def initialize_options(self):
        _build.initialize_options(self)
        self.build_config = None

    def finalize_options (self):
        _build.finalize_options(self)
        if self.build_config is None:
            self.build_config = os.path.join(self.build_base, 'etc')
    
class install(_install):
    sub_commands = _install.sub_commands + [
        ('install_config', None),
        ]
    user_options = _install.user_options + [
        ('etc-path=', None, 'read-only single-machine data'),
        ('var-path=', None, 'modifiable single-machine data'),
        ('plugins-path=', None, 'program executables'),
        ]
    
    def initialize_options(self):
        _install.initialize_options(self)
        self.etc_path = None
        self.var_path = None
        self.var_owner = None
        self.var_group = None
        self.plugins_path = None

    def finalize_options(self):
        _install.finalize_options(self)
        if self.etc_path is None:
            self.etc_path = paths_and_owners['etc']['path']
        if self.var_path is None:
            self.var_path = paths_and_owners['var']['path']
            self.var_owner = paths_and_owners['var']['owner']
            self.var_group = paths_and_owners['var']['group']
        if self.plugins_path is None:
            self.plugins_path = paths_and_owners['libexec']['path']
        if self.root:
            for attr in ('etc_path', 'var_path', 'plugins_path'):
                setattr(self, attr, change_root(self.root, getattr(self, attr)))
            

class build_config(Command):
    description = "build the shinken config files"

    user_options = [
        ('build-dir=', None, "directory to build the configfiles to"),
        ]
    
    def initialize_options (self):
        self.build_dir = None
        self.build_base = None
        self.etc_path = None
        self.var_path = None
        self.var_owner = None
        self.var_group = None
        self.plugins_path = None

        self._install_scripts = None
        
    def finalize_options (self):
        self.set_undefined_options('build',
                                   ('build_base', 'build_base'),
                                   ('build_config', 'build_dir'),
                                   )
        self.set_undefined_options('install',
                                   ('install_scripts', '_install_scripts'),
                                   )
        self.set_undefined_options('install_config',
                                   ('etc_path', 'etc_path'),
                                   ('var_path', 'var_path'),
                                   ('plugins_path', 'plugins_path'),
                                   ('var_owner', 'var_owner'),
                                   ('var_group', 'var_group'),
                                   )
        if self.build_dir is None:
            self.build_dir = os.path.join(self.build_base, 'etc')
        #self.etc_path = os.path.join(self.etc_path, 'shinken')
        #self.var_path = os.path.join(self.var_path, 'lib', 'shinken')
        print "TOTO"*100
        print self.etc_path, self.var_path
        

    def run(self):
        if not self.dry_run:
            self.mkpath(self.build_dir)
        self.generate_default_shinken_file()
        self.update_configfiles()
        
    def generate_default_shinken_file(self):
        # The default file must have good values for the directories:
        # etc, var and where to push scripts that launch the app.
        templatefile = "bin/default/shinken.in"
        outfile = os.path.join(self.build_base, "bin/default/shinken")

        log.info('generating %s from %s', outfile, templatefile)
        if not self.dry_run:
            self.mkpath(os.path.dirname(outfile))
            # Read the template file
            f = open(templatefile)
            buf = f.read()
            f.close
            # substitute
            buf = buf.replace("$ETC$", self.etc_path)
            buf = buf.replace("$VAR$", self.var_path)
            buf = buf.replace("$SCRIPTS_BIN$", self._install_scripts)
            # write out the new file
            f = open(outfile, "w")
            f.write(buf)
            f.close()

    def update_configfiles(self):
        # Here, even with --root we should change the file with good values
        # then update the /etc/*d.ini files ../var value with the real var one

        # Open a /etc/*d.ini file and change the ../var occurence with a
        # good value from the configuration file
        for name in ('brokerd.ini',
                     'schedulerd.ini',
                     'pollerd.ini',
                     'reactionnerd.ini'):
            inname = os.path.join('etc', name)
            outname = os.path.join(self.build_dir, name)
            log.info('updating path in %s', outname)
            update_file_with_string(inname, outname,
                                    "../var", self.var_path)

        # And now the resource.cfg path with the value of libexec path
        # Replace the libexec path by the one in the parameter file
        for name in ('resource.cfg', ):
            inname = os.path.join('etc', name)
            outname = os.path.join(self.build_dir, name)
            log.info('updating path in %s', outname)
            update_file_with_string(inname, outname,
                                    "/usr/local/shinken/libexec",
                                    self.plugins_path)

        # And update the nagios.cfg file for all /usr/local/shinken/var
        # value with good one
        for name in ('nagios.cfg',
                     'shinken-specific.cfg',
                     'shinken-specific-high-availability.cfg',
                     'shinken-specific-load-balanced-only.cfg',
                     ):
            inname = os.path.join('etc', name)
            outname = os.path.join(self.build_dir, name)
            log.info('updating path in %s', outname)
            update_file_with_string(inname, outname,
                                    "/usr/local/shinken/var",
                                    self.var_path)


class install_config(Command):
    description = "install the shinken config files"

    user_options = [
        ('install-dir=', 'd', "directory to install config files to"),
        ('build-dir=','b', "build directory (where to install from)"),
        ('force', 'f', "force installation (overwrite existing files)"),
        ('skip-build', None, "skip the build steps"),
    ]

    boolean_options = ['force', 'skip-build']

    def initialize_options(self):
        self.build_dir = None
        self.force = None
        self.skip_build = None
        self.owner = None
        self.group = None

        self.root = None
        self.etc_path = None  # typically /etc on Posix systems 
        self.var_path = None # typically /var on Posix systems 
        self.var_owner = None  # typically shinken
        self.var_group = None  # typically shinken too
        self.plugins_path = None    # typically /libexec on Posix systems

    def finalize_options(self):
        self.set_undefined_options('build',
                                   ('build_config', 'build_dir'))
        self.set_undefined_options('install',
                                   ('root', 'root'),
                                   ('etc_path', 'etc_path'),
                                   ('var_path', 'var_path'),
                                   ('var_owner', 'var_owner'),
                                   ('var_group', 'var_group'),
                                   ('plugins_path', 'plugins_path'))
        if self.owner is None and pwd:
            self.owner = pwd.getpwuid(os.getuid())[0]
        if self.group is None and grp:
            self.group = grp.getgrgid(os.getgid())[0]

            
    def run(self):
        #log.warn('>>> %s', self.lib)
        log.warn('>>> %s', self.etc_path)
        if not self.skip_build:
            self.run_command('build_config')
        self.outfiles = self.copy_tree(self.build_dir, self.etc_path)


        if pwd:
            # assume a posix system
            uid = self.get_uid(self.owner)
            gid = self.get_gid(self.group)
            for file in self.get_outputs():
                log.info("Changing owner of %s to %s:%s", file, self.owner, self.group)
                if not self.dry_run:
                    os.chown(file, uid, gid)
            # And set the /var/lib/shinken in correct owner too
            # TODO : (j gabes) I can't access to self.var_owner (None) and
            # I don't know how to change it o I use the global variables
            var_uid = self.get_uid(var_owner)
            var_gid = self.get_uid(var_group)
            if not self.dry_run:
                os.chown(self.var_path, var_uid, var_gid)


    def get_inputs (self):
        return self.distribution.configs or []

    def get_outputs(self):
        return self.outfiles or []

    @staticmethod
    def _chown(path, owner, group):
        log.info("Changing owner of %s to %s:%s", path, owner, group)
        if not self.dry_run:
            os.chown(path, uid, gid)
        for root, dirs, files in os.walk(path):
            for path in itertools.chain(dirs, files):
                path = os.path.join(root, path)



    @staticmethod
    def get_uid(user_name):
        try:
            return pwd.getpwnam(user_name)[2]
        except KeyError, exp:
            raise DistutilsOptionError("The user %s is unknown. "
                                       "Maybe you should create this user"
                                       % user_name)

    @staticmethod
    def get_gid(group_name):
        try:
            return grp.getgrnam(group_name)[2]
        except KeyError, exp:
            raise DistutilsOptionError("The group %s is unknown. "
                                       "Maybe you should create this group"
                                       % group_name)


def update_file_with_string(infilename, outfilename, match, new_string):
    f = open(infilename)
    buf = f.read()
    f.close()
    buf = buf.replace(match, new_string)
    f = open(outfilename, "w")
    f.write(buf)
    f.close()


#Set the default values for the paths
#owners and groups
if os.name == 'nt':
    paths_and_owners = {'var':{'path': "c:\\shinken\\var",
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
                                'owner' : 'shinken',
                                'group' : 'shinken' },
                        'etc': {'path': "/etc/shinken",
                                'owner': 'shinken',
                                'group': 'shinken'},
                        'libexec': {'path': "/usr/lib/shinken/plugins",
                                    'owner': 'shinken',
                                    'group': 'shinken'},
                        }

required_pkgs = []
if sys.version_info < (2, 5):
    required_pkgs.append('pyro<4')
else:
    required_pkgs.append('pyro')
if sys.version_info < (2, 6):
    required_pkgs.append('multiprocessing')

etc_path = paths_and_owners['etc']['path']
etc_root = os.sep.join(etc_path.split(os.sep)[:-1])
libexec_path = paths_and_owners['libexec']['path']
var_path = paths_and_owners['var']['path']
var_owner = paths_and_owners['var']['owner']
var_group = paths_and_owners['var']['group']

setup(
  cmdclass = {'build': build,
              'install': install,
              'build_config': build_config,
              'install_config': install_config},
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
  classifiers=['Development Status :: 5 - Production/Stable',
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
               [# nagios/shinken global config
                #"etc/nagios.cfg",
                'etc/nagios-windows.cfg',
                #'etc/shinken-specific.cfg',
                #'etc/shinken-specific-high-availability.cfg',
                #'etc/shinken-specific-load-balanced-only.cfg',

                # daemon configs
                #'etc/brokerd.ini',
                'etc/brokerd-windows.ini',
                #'etc/pollerd.ini',
                'etc/pollerd-windows.ini',
                #'etc/reactionnerd.ini',
                #'etc/schedulerd.ini',
                'etc/schedulerd-windows.ini',

                # other configs
                'etc/commands.cfg',
                'etc/contactgroups.cfg',
                'etc/dependencies.cfg',
                'etc/escalations.cfg',
                'etc/hostgroups.cfg',
                'etc/resource.cfg',
                'etc/servicegroups.cfg',
                'etc/templates.cfg',
                'etc/timeperiods.cfg',
                ]),
              (os.path.join(etc_path, 'objects', 'hosts'),
               glob('etc/objects/hosts/[!_]*.cfg')),
              (os.path.join(etc_path, 'objects', 'services'),
               glob('etc/objects/services/[!_]*.cfg')),
              (os.path.join(etc_path, 'objects', 'contacts'),
               glob('etc/objects/contacts/[!_]*.cfg')),
              (os.path.join(etc_path, 'certs') ,
               glob('etc/certs/[!_]*.pem')),
              (os.path.join('/etc', 'init.d'),
               ['bin/init.d/shinken',
                'bin/init.d/shinken-arbiter',
                'bin/init.d/shinken-broker',
                'bin/init.d/shinken-poller',
                'bin/init.d/shinken-reactionner',
                'bin/init.d/shinken-scheduler']),
              (os.path.join(etc_root, 'default',),
               ['bin/default/shinken']),
              (var_path, ['var/void_for_git']),
              (libexec_path, ['libexec/check.sh']),
              ]
)


# We will chown shinken:shinken for all /etc/shinken
# and /var/lib/shinken.


#if os.name != 'nt' and ('install' in sys.argv or 'sdist' in sys.argv):
#    for dir in ['etc', 'var']:
#        _chown(paths_and_owners[dir]['path'],
#               paths_and_owners[dir]['owner'],
#               paths_and_owners[dir]['owner'])

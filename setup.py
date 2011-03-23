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


# Shinken requires Python 2.4, but does not support Python 3.x yet.
import sys
try:
    python_version = sys.version_info
except:
    python_version = (1,5)
if python_version < (2, 4):
    sys.exit("Shinken require as a minimum Python 2.4.x, sorry")
elif python_version >= (3,):
    sys.exit("Shinken is not yet compatible with Python3k, sorry")

from setuptools import setup, find_packages
from glob import glob
import os
import itertools
import ConfigParser
try:
    import pwd
    import grp
except ImportError:
    # assume non-unix platform
    pass

DEFAULT_OWNER = 'shinken'
DEFAULT_GROUP = 'shinken'

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
        ('build-config', None, 'directory to build the config files to'),
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
        ('owner=', None, ('change owner for etc/* and var '
                          '(default: %s)' % DEFAULT_OWNER)),
        ('group=', None, ('change group for etc/* and var '
                          '(default: %s)' % DEFAULT_GROUP)),
        ]
    
    def initialize_options(self):
        _install.initialize_options(self)
        self.etc_path = None
        self.var_path = None
        self.plugins_path = None
        self.owner = None
        self.group = None

    def finalize_options(self):
        _install.finalize_options(self)
        if self.etc_path is None:
            self.etc_path = default_paths['etc']
        if self.var_path is None:
            self.var_path = default_paths['var']
        if self.plugins_path is None:
            self.plugins_path = default_paths['libexec']
        if self.owner is None:
            self.owner = DEFAULT_OWNER
        if self.group is None:
            self.group = DEFAULT_GROUP

        if self.root:
            for attr in ('etc_path', 'var_path', 'plugins_path'):
                setattr(self, attr, change_root(self.root, getattr(self, attr)))
            

class build_config(Command):
    description = "build the shinken config files"

    user_options = [
        ('build-dir=', None, "directory to build the config files to"),
        ]
    
    def initialize_options (self):
        self.build_dir = None
        self.build_base = None
        self.etc_path = None
        self.var_path = None
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
                                   )
        if self.build_dir is None:
            self.build_dir = os.path.join(self.build_base, 'etc')
        

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
        for name in daemon_ini_files:
            inname = os.path.join('etc', name)
            outname = os.path.join(self.build_dir, name)
            log.info('updating path in %s', outname)
            update_file_with_string(inname, outname,
                                    "../var", self.var_path)

        # And now the resource.cfg path with the value of libexec path
        # Replace the libexec path by the one in the parameter file
        for name in resource_cfg_files:
            inname = os.path.join('etc', name)
            outname = os.path.join(self.build_dir, name)
            log.info('updating path in %s', outname)
            update_file_with_string(inname, outname,
                                    "/usr/local/shinken/libexec",
                                    self.plugins_path)

        # And update the nagios.cfg file for all /usr/local/shinken/var
        # value with good one
        for name in main_config_files:
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
        self.plugins_path = None    # typically /libexec on Posix systems

    def finalize_options(self):
        self.set_undefined_options('build',
                                   ('build_config', 'build_dir'))
        self.set_undefined_options('install',
                                   ('root', 'root'),
                                   ('etc_path', 'etc_path'),
                                   ('var_path', 'var_path'),
                                   ('plugins_path', 'plugins_path'),
                                   ('owner', 'owner'),
                                   ('group', 'group'))

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
            # recursivly changing permissions for etc/shinken and var/lib/shinken
            self.recursive_chown(self.etc_path, uid, gid, self.owner, self.group)
            self.recursive_chown(self.var_path, uid, gid, self.owner, self.group)


    def get_inputs (self):
        return self.distribution.configs or []

    def get_outputs(self):
        return self.outfiles or []

    def recursive_chown(self, path, uid, gid, owner, group):
        log.info("Changing owner of %s to %s:%s", path, owner, group)
        if not self.dry_run:
            os.chown(path, uid, gid)
        for dirname, dirs, files in os.walk(path):
            for path in itertools.chain(dirs, files):
                path = os.path.join(dirname, path)
                os.chown(path, uid, gid)

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


# Set the default values for the paths
if 'win' in sys.platform:
    default_paths = {'var':      "c:\\shinken\\var",
                     'etc':      "c:\\shinken\\etc",
                     'libexec':  "c:\\shinken\\libexec",
                     }
elif 'linux' in sys.platform:
    default_paths = {'var': "/var/lib/shinken/",
                     'etc': "/etc/shinken",
                     'libexec': "/usr/lib/shinken/plugins",
                     }
elif 'bsd' in sys.platform or 'dragonfly' in sys.platform:
    default_paths = {'var': "/var/lib/shinken",
                     'etc': "/usr/local/etc/shinken",
                     'libexec': "/usr/local/libexec/shinken",
                     }
else:
    raise "Unsupported platform, sorry"

required_pkgs = []
if sys.version_info < (2, 5):
    required_pkgs.append('pyro<4')
else:
    required_pkgs.append('pyro')
if sys.version_info < (2, 6):
    required_pkgs.append('multiprocessing')

etc_root = os.path.dirname(default_paths['etc'])

# nagios/shinken global config
main_config_files = ('nagios.cfg',
                     'nagios-windows.cfg',
                     'shinken-specific.cfg',
                     'shinken-specific-high-availability.cfg',
                     'shinken-specific-load-balanced-only.cfg',
                     )

# daemon configs
daemon_ini_files = ('brokerd.ini',
                    'brokerd-windows.ini',
                    'receiverd.ini',
                    'receiverd-windows.ini',
                    'pollerd.ini',
                    'pollerd-windows.ini',
                    'reactionnerd.ini',
                    'schedulerd.ini',
                    'schedulerd-windows.ini',
                    )

resource_cfg_files = ('resource.cfg', )



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
  data_files=[(default_paths['etc'],
               [# other configs
                'etc/commands.cfg',
                'etc/contactgroups.cfg',
                'etc/dependencies.cfg',
                'etc/escalations.cfg',
                'etc/hostgroups.cfg',
                #'etc/resource.cfg', # see above
                'etc/servicegroups.cfg',
                'etc/templates.cfg',
                'etc/timeperiods.cfg',
                ]),
              (os.path.join(default_paths['etc'], 'objects', 'hosts'),
               glob('etc/objects/hosts/[!_]*.cfg')),
              (os.path.join(default_paths['etc'], 'objects', 'services'),
               glob('etc/objects/services/[!_]*.cfg')),
              (os.path.join(default_paths['etc'], 'objects', 'contacts'),
               glob('etc/objects/contacts/[!_]*.cfg')),
              (os.path.join(default_paths['etc'], 'objects', 'discovery'), tuple() ), 
              (os.path.join(default_paths['etc'], 'certs') ,
               glob('etc/certs/[!_]*.pem')),
              (os.path.join('/etc', 'init.d'),
               ['bin/init.d/shinken',
                'bin/init.d/shinken-arbiter',
                'bin/init.d/shinken-broker',
                'bin/init.d/shinken-receiver',
                'bin/init.d/shinken-poller',
                'bin/init.d/shinken-reactionner',
                'bin/init.d/shinken-scheduler']),
              (os.path.join(etc_root, 'default',),
               ['build/bin/default/shinken']),
              (default_paths['var'], ['var/void_for_git']),
              (default_paths['libexec'], ['libexec/check.sh']),
              ]
)

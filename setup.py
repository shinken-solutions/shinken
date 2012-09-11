#!/usr/bin/python

# -*- coding: utf-8 -*-

# Copyright (C) 2009-2012:
#    Gabes Jean, naparuba@gmail.com
#    Gerhard Lausser, Gerhard.Lausser@consol.de
#    Gregory Starck, g.starck@gmail.com
#    Hartmut Goebel, h.goebel@goebel-consult.de
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

# Shinken requires Python 2.4, but does not support Python 3.x yet.
import sys
try:
    python_version = sys.version_info
except:
    python_version = (1, 5)
if python_version < (2, 4):
    sys.exit("Shinken require as a minimum Python 2.4.x, sorry")
elif python_version >= (3,):
    sys.exit("Shinken is not yet compatible with Python3k, sorry")

from setuptools import setup, find_packages
from glob import glob
import os
import os.path
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

# We try to see if we are in a full install or an update process
is_update = False
if 'update' in sys.argv:
    print "Shinken Lib Updating process only"
    sys.argv.remove('update')
    sys.argv.insert(1, 'install')
    is_update = True

# If we install/update, for the force option to always overwrite the
# shinken lib and scripts
if 'install' in sys.argv and not '-f' in sys.argv:
    sys.argv.append('-f')

is_install = 'install' in sys.argv


# Utility function to read the README file. This was directly taken from:
# http://packages.python.org/an_example_pypi_project/setuptools.html
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


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
        ('run-path=', None, 'PID files'),
        ('log-path=', None, 'LOG files'),
        ('plugins-path=', None, 'program executables'),
        ('owner=', None, (
                'change owner for etc/*, var, run and log folders (default: %s)' % DEFAULT_OWNER
            )
        ),
        ('group=', None, (
                'change group for etc/*, var, run and log folders (default: %s)' % DEFAULT_GROUP
            )
        ),
    ]

    boolean_options = _install.boolean_options + [
        'relocatable'
    ]
    
    def initialize_options(self):
        _install.initialize_options(self)
        self.etc_path = None
        self.var_path = None
        self.run_path = None
        self.log_path = None
        self.plugins_path = None
        self.owner = None
        self.group = None
        self.relocatable = None

    def finalize_options(self):
        _install.finalize_options(self)
        if self.etc_path is None:
            self.etc_path = default_paths['etc']
        if self.var_path is None:
            self.var_path = default_paths['var']
        if self.run_path is None:
            self.run_path = default_paths['run']
        if self.log_path is None:
            self.log_path = default_paths['log']
        if self.plugins_path is None:
            self.plugins_path = default_paths['libexec']
        if self.owner is None:
            self.owner = DEFAULT_OWNER
        if self.group is None:
            self.group = DEFAULT_GROUP
        if self.relocatable is None:
            self.relocatable = False

        if self.root:
            for attr in ('etc_path', 'var_path', 'plugins_path', 'run_path', 'log_path'):
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
        self.run_path = None
        self.log_path = None
        self.plugins_path = None
        self.root = None
        self._install_scripts = None
        self.relocatable = None

        self.owner = None
        self.group = None

    def finalize_options (self):
        self.set_undefined_options('build',
                                   ('build_base', 'build_base'),
                                   ('build_config', 'build_dir'),
        )
        self.set_undefined_options('install',
                                   ('install_scripts', '_install_scripts'),
                                   ('relocatable', 'relocatable'),
                                   ('root', 'root'),
        )
        self.set_undefined_options('install_config',
                                   ('etc_path', 'etc_path'),
                                   ('var_path', 'var_path'),
                                   ('run_path', 'run_path'),
                                   ('log_path', 'log_path'),
                                   ('plugins_path', 'plugins_path'),
                                   ('owner', 'owner'),
                                   ('group', 'group')
        )
        if self.build_dir is None:
            self.build_dir = os.path.join(self.build_base, 'etc')

    def run(self):
        if not self.dry_run:
            self.mkpath(self.build_dir)
        # We generate the conf files only for a full install
        if not is_update:
            self.generate_default_shinken_file()
            self.update_configfiles()
            self.copy_objects_file()

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
            buf = buf.replace("$ETC$", relative_path_if_relocatable(self.relocatable, self.root, self.etc_path))
            buf = buf.replace("$VAR$", relative_path_if_relocatable(self.relocatable, self.root, self.var_path))
            buf = buf.replace("$RUN$", relative_path_if_relocatable(self.relocatable, self.root, self.run_path))
            buf = buf.replace("$LOG$", relative_path_if_relocatable(self.relocatable, self.root, self.log_path))
            buf = buf.replace("$SCRIPTS_BIN$", relative_path_if_relocatable(self.relocatable, self.root, self._install_scripts))
            # write out the new file
            f = open(outfile, "w")
            f.write(buf)
            f.close()

    def copy_objects_file(self):
        for name in config_objects_file:
            inname = os.path.join('etc', name)
            outname = os.path.join(self.build_dir, name)
            log.info('Copying data files in: %s out: %s' % (inname, outname))
            append_file_with(inname, outname, "")
        # Creating some needed directories
        discovery_dir = os.path.join(self.build_dir + "/objects/discovery")
        if not os.path.exists(discovery_dir):
            os.makedirs(discovery_dir)
        for dirname in [self.var_path, self.run_path, self.log_path, discovery_dir]:
            if self.build_base:
                if not is_install:
                    dirname = os.path.join(self.build_base, os.path.relpath(dirname, '/')) #dirname)
                else:
                    dirname = os.path.join(self.build_base, dirname)
            if not os.path.exists(dirname):
                os.makedirs(dirname)

    def update_configfiles(self):
        # Here, even with --root we should change the file with good values
        # then update the /etc/*d.ini files ../var value with the real var one

        # Open a /etc/*d.ini file and change the ../var occurence with a
        # good value from the configuration file

        for (dname, name) in daemon_ini_files:
            inname = os.path.join('etc', name)
            outname = os.path.join(self.build_dir, name)
            log.info('updating path in %s: to "%s"' % (outname, self.var_path))

            # but we have to force the user/group & workdir values still:
            append_file_with(inname, outname, """
user=%s
group=%s
workdir=%s
pidfile=%s/%sd.pid
""" % (self.owner,
       self.group,
       relative_path_if_relocatable(self.relocatable, self.root, self.var_path),
       relative_path_if_relocatable(self.relocatable, self.root, self.run_path),
       dname))

        # And now the resource.cfg path with the value of libexec path
        # Replace the libexec path by the one in the parameter file
        for name in resource_cfg_files:
            inname = os.path.join('etc', name)
            outname = os.path.join(self.build_dir, name)
            log.info('updating path in %s', outname)
            update_file_with_string(inname, outname,
                                    "/usr/local/shinken/libexec",
                                    relative_path_if_relocatable(self.relocatable, self.root, self.plugins_path))

        # And update the nagios.cfg file for all /usr/local/shinken/var
        # value with good one
        for name in main_config_files:
            inname = os.path.join('etc', name)
            outname = os.path.join(self.build_dir, name)
            log.info('updating path in %s', outname)

            ## but we HAVE to set the shinken_user & shinken_group to thoses requested:
            append_file_with(inname, outname, """
shinken_user=%s
shinken_group=%s
lock_file=%s/arbiterd.pid
local_log=%s/arbiterd.log
""" % (self.owner,
       self.group,
       relative_path_if_relocatable(self.relocatable, self.root,self.run_path),
       relative_path_if_relocatable(self.relocatable, self.root,self.log_path))
            )

        # UPDATE Shinken-specific.cfg files too
        for name in additionnal_config_files:
            inname = os.path.join('etc', name)
            outname = os.path.join(self.build_dir, name)

            update_file_with_string(inname, outname,
                                    "/usr/local/shinken/var",
                                    relative_path_if_relocatable(self.relocatable, self.root, self.var_path))
            # And update the default log path too
            log.info('updating log path in %s', outname)
            update_file_with_string(inname, outname,
                                    "nagios.log",
                                    "%s/nagios.log" % relative_path_if_relocatable(self.relocatable, self.root, self.log_path))


class install_config(Command):
    description = "install the shinken config files"

    user_options = [
        ('install-dir=', 'd', "directory to install config files to"),
        ('build-dir=',   'b', "build directory (where to install from)"),
        ('force',        'f', "force installation (overwrite existing files)"),
        ('skip-build',   None, "skip the build steps"),
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
        self.var_path = None  # typically /var on Posix systems
        self.run_path = None  # typically /etc on Posix systems
        self.log_path = None  # typically /var on Posix systems
        self.plugins_path = None    # typically /libexec on Posix systems

    def finalize_options(self):
        self.set_undefined_options(
            'build',
                ('build_config', 'build_dir'),
        )
        self.set_undefined_options(
            'install',
               ('root', 'root'),
               ('etc_path', 'etc_path'),
               ('var_path', 'var_path'),
               ('run_path', 'run_path'),
               ('log_path', 'log_path'),
               ('plugins_path', 'plugins_path'),
               ('owner', 'owner'),
               ('group', 'group')
        )

    def run(self):
        # If we are just doing an update, pass this
        if is_update:
            return
        #log.warn('>>> %s', self.lib)
        log.warn('>>> %s', self.etc_path)
        if not self.skip_build:
            self.run_command('build_config')
        self.outfiles = self.copy_tree(self.build_dir, self.etc_path)

        # if root is set, it's for pacakge, so NO chown
        if pwd and not self.root:
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
            self.recursive_chown(self.run_path, uid, gid, self.owner, self.group)
            self.recursive_chown(self.log_path, uid, gid, self.owner, self.group)

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

def relative_path_if_relocatable(relocatable, root, path):
    if relocatable:
        return os.path.join('/', os.path.relpath(path, root))
    return path

def ensure_dir_exist(f):
    dirname = os.path.dirname(f)
    if not os.path.exists(dirname):
        os.makedirs(dirname)


def append_file_with(infilename, outfilename, append_string):
    f = open(infilename)
    buf = f.read()
    f.close()
    ensure_dir_exist(outfilename)
    f = open(outfilename, "w")
    f.write(buf)
    f.write(append_string)
    f.close()


def gen_data_files(*dirs):
    results = []

    for src_dir in dirs:
        #print "Getting all files from", src_dir
        for root, dirs, files in os.walk(src_dir):
            for file in files:
                results.append(os.path.join(root, file))
    return results


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
                     'log':      "c:\\shinken\\var",
                     'run':      "c:\\shinken\\var",
                     'libexec':  "c:\\shinken\\libexec",
                     }
elif 'linux' in sys.platform or 'sunos5' in sys.platform:
    default_paths = {'var': "/var/lib/shinken/",
                     'etc': "/etc/shinken",
                     'run': "/var/run/shinken",
                     'log': "/var/log/shinken",
                     'libexec': "/usr/lib/shinken/plugins",
                     }
elif 'bsd' in sys.platform or 'dragonfly' in sys.platform:
    default_paths = {'var': "/var/lib/shinken",
                     'etc': "/usr/local/etc/shinken",
                     'run': "/var/run/shinken",
                     'log': "/var/log/shinken",
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
                     'nagios-windows.cfg')

additionnal_config_files = ('shinken-specific.cfg',
                            'shinken-specific-high-availability.cfg',
                            'shinken-specific-load-balanced-only.cfg',
                            'skonf.cfg',
                            )

config_objects_file = (
                        'discovery_runs.cfg',
                        'templates.cfg',
                        'dependencies.cfg',
                        'timeperiods.cfg',
                        'time_templates.cfg',
                        'contacts.cfg',
                        'discovery_rules.cfg',
                        'hosts/localhost.cfg',
                        'services/linux_local.cfg',
                        'contactgroups.cfg',
                        'escalations.cfg',
                        'commands.cfg',
                        'discovery.cfg',
                        'servicegroups.cfg',
                        'hostgroups.cfg',
                        'certs/server.pem',
                        'certs/client.pem',
                        'certs/ca.pem',
)

# Now service packs files
srv_pack_files = gen_data_files('etc/packs')
# We must remove the etc from the paths
srv_pack_files = [s.replace('etc/', '') for s in srv_pack_files]
#print "SRV PACK FILES", srv_pack_files
config_objects_file_extended = list(config_objects_file)
config_objects_file_extended.extend(srv_pack_files)
config_objects_file = tuple(config_objects_file_extended)
print config_objects_file

# daemon configs
daemon_ini_files = (('broker', 'brokerd.ini'),
                    ('broker', 'brokerd-windows.ini'),
                    ('receiver', 'receiverd.ini'),
                    ('receiver', 'receiverd-windows.ini'),
                    ('poller', 'pollerd.ini'),
                    ('poller', 'pollerd-windows.ini'),
                    ('reactionner', 'reactionnerd.ini'),
                    ('reactionner', 'reactionnerd-windows.ini'),
                    ('scheduler', 'schedulerd.ini'),
                    ('scheduler', 'schedulerd-windows.ini'),
                    )

resource_cfg_files = ('resource.cfg',)

# Ok, for the webui files it's a bit tricky. we need to add all of them in
#the package_data of setup(), but from a point of view of the
# module shinken, so the directory shinken... but without movingfrom pwd!
# so: sorry for the replace, really... I HATE SETUP()!
full_path_webui_files = gen_data_files('shinken/webui')
webui_files = [s.replace('shinken/webui/', 'webui/') for s in full_path_webui_files]

package_data = ['*.py', 'modules/*.py', 'modules/*/*.py']
package_data.extend(webui_files)

#By default we add all init.d scripts and some dummy files
data_files = [
    (
        os.path.join('/etc', 'init.d'),
        ['bin/init.d/shinken',
         'bin/init.d/shinken-arbiter',
         'bin/init.d/shinken-broker',
         'bin/init.d/shinken-receiver',
         'bin/init.d/shinken-poller',
         'bin/init.d/shinken-reactionner',
         'bin/init.d/shinken-scheduler',
         'bin/init.d/shinken-skonf',
         ]
        ),
    (
        default_paths['libexec'], ['libexec/check.sh']
        )
    ]


# If not update, we install configuration files too
if not is_update:

    data_files.append(
        (os.path.join(etc_root, 'default',),
         ['build/bin/default/shinken']
         ))
#print "DATA", data_files

print "All package _data"
if __name__ == "__main__":

    setup(
        cmdclass={
            'build': build,
            'install': install,
            'build_config': build_config,
            'install_config': install_config
        },

        name="Shinken",
        version="1.0.1",
        packages=find_packages(),
        package_data={'': package_data},
        description="Shinken is a monitoring tool compatible with Nagios configuration and plugins",
        long_description=read('README'),
        author="Gabes Jean",
        author_email="naparuba@gmail.com",
        license="GNU Affero General Public License",
        url="http://www.shinken-monitoring.org",
        zip_safe=False,
        classifiers=[
            'Development Status :: 5 - Production/Stable',
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

        install_requires=[
            required_pkgs
        ],
        extras_require={
            'setproctitle': ['setproctitle']
        },

        scripts=glob('bin/shinken-[!_]*'),

        data_files=data_files,
    )

print "Shinken setup done"

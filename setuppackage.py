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

# Shinken requires Python 2.6, but does not support Python 3.x yet.
import sys
import re
try:
    python_version = sys.version_info
except:
    python_version = (1, 5)
if python_version < (2, 6):
    sys.exit("Shinken require as a minimum Python 2.6.x, sorry")
elif python_version >= (3,):
    sys.exit("Shinken is not yet compatible with Python3k, sorry")

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

from setuptools import find_packages

from setuptools import setup
# For pip, use strong setuptools
if 'pip' in sys.argv or '--single-version-externally-managed' in sys.argv:
    from setuptools.command.install import install as _install
# for local, use distutils?
else:
    from distutils.command.install import install as _install

from distutils.util import change_root
from distutils.errors import DistutilsOptionError

from distutils import log
from distutils.core import Command
from distutils.command.build import build as _build


# We try to see if we are in a full install or an update process
is_update = False
if 'update' in sys.argv or '--upgrade' in sys.argv:
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


    def initialize_options(self):
        _install.initialize_options(self)
        self.etc_path = None
        self.var_path = None
        self.run_path = None
        self.log_path = None
        self.plugins_path = None
        self.owner = None
        self.group = None


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


class build_config(Command):
    description = "build the shinken config files"

    user_options = [
        ('build-dir=', None, "directory to build the config files to"),
    ]

    def initialize_options (self):
        self.build_dir = None
        self.build_base = None
        self.root = None
        self.etc_path = None
        self.var_path = None
        self.run_path = None
        self.log_path = None
        self.plugins_path = None

        self._install_scripts = None

        self.owner = None
        self.group = None

    def finalize_options (self):
        self.set_undefined_options('build',
                                   ('build_base', 'build_base'),
                                   ('build_config', 'build_dir'),
        )
        self.set_undefined_options('install',
                                   ('install_scripts', '_install_scripts'),
        )
        self.set_undefined_options('install_config',
                                   ('root', 'root'),
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

            bin_path = self._install_scripts
            if self.root:
                bin_path = bin_path.replace(self.root.rstrip(os.path.sep), '')

            # Read the template file
            f = open(templatefile)
            buf = f.read()
            f.close
            # substitute
            buf = buf.replace("$ETC$", self.etc_path)
            buf = buf.replace("$VAR$", self.var_path)
            buf = buf.replace("$RUN$", self.run_path)
            buf = buf.replace("$LOG$", self.log_path)
            buf = buf.replace("$SCRIPTS_BIN$", bin_path)
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
        for dirname in [self.var_path, self.run_path, self.log_path]:
            if self.build_base:
                if not is_install:
                    dirname = os.path.join(self.build_base, os.path.relpath(dirname, '/')) #dirname)
                else:
                    dirname = os.path.join(self.build_base, dirname)
                    if self.root:
                        dirname = change_root(self.root, dirname)
            if not os.path.exists(dirname):
                os.makedirs(dirname)


    def update_configfiles(self):
        # Here, even with --root we should change the file with good values
        # then update the /etc/*d.ini files ../var value with the real var one

        # Open a /etc/*d.ini file and change the ../var occurence with a
        # good value from the configuration file

        if not os.path.exists(os.path.join(self.build_dir, 'daemons')):
            os.makedirs(os.path.join(self.build_dir, 'daemons'))
        for (dname, name) in daemon_ini_files:
            inname = os.path.join('etc', name)
            #outname = os.path.join(self.build_dir, '%sd.ini' % dname)
            outname = os.path.join(self.build_dir, name)
            log.info('Updating path in %s->%s: to "%s"' % (inname, outname, self.var_path))

            # but we have to force the user/group & workdir values still:
            update_file_with_string(inname, outname,
                                    ["user=\w+", "group=\w+", "workdir=.+", "logdir=.+", "pidfile=.+"],
                                    ["user=%s" % self.owner,
                                     "group=%s" % self.group,
                                     "workdir=%s" % self.var_path,
                                     "logdir=%s" % self.log_path,
                                     "pidfile=%s/%sd.pid" % (self.run_path, dname)])
            # force the user setting as it's not set by default
            append_file_with(outname, outname, "user=%s\ngroup=%s\n" % (self.owner,self.group))

        # And now the resource.cfg path with the value of libexec path
        # Replace the libexec path by the one in the parameter file
        for name in resource_cfg_files:
            inname = os.path.join('etc', name)
            outname = os.path.join(self.build_dir, name)
            log.info('updating path in %s', outname)
            update_file_with_string(inname, outname,
                                    ["/var/lib/shinken/libexec"],
                                    [self.plugins_path])

        # And update the shinken.cfg file for all /usr/local/shinken/var
        # value with good one
        for name in main_config_files:
            inname = os.path.join('etc', name)
            outname = os.path.join(self.build_dir, name)
            log.info('updating path in %s', outname)

            ## but we HAVE to set the shinken_user & shinken_group to thoses requested:
            update_file_with_string(inname, outname,
                                    ["shinken_user=\w+", "shinken_group=\w+", "workdir=.+", "lock_file=.+", "local_log=.+"],
                                    ["shinken_user=%s" % self.owner,
                                     "shinken_group=%s" % self.group,
                                     "workdir=%s" % self.var_path,
                                     "lock_file=%s/arbiterd.pid" % self.run_path,
                                     "local_log=%s/arbiterd.log" % self.log_path])


        # UPDATE others cfg files too
        for name in additionnal_config_files:
            inname = os.path.join('etc', name)
            outname = os.path.join(self.build_dir, name)

            update_file_with_string(inname, outname,
                                    ["/var/lib/shinken"], [self.var_path])
            # And update the default log path too
            log.info('updating log path in %s', outname)
            update_file_with_string(inname, outname,
                                    ["shinken.log"],
                                    ["%s/shinken.log" % self.log_path])


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
        etc_path = self.etc_path
        if self.root:
            etc_path = change_root(self.root, self.etc_path)
        self.outfiles = self.copy_tree(self.build_dir, etc_path)

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
    f.write('\n')
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


def update_file_with_string(infilename, outfilename, matches, new_strings):
    f = open(infilename)
    buf = f.read()
    f.close()
    for match, new_string in zip(matches, new_strings):
        buf = re.sub(match, new_string, buf)
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
    data_files = []
elif 'linux' in sys.platform or 'sunos5' in sys.platform:
    default_paths = {'var': "/var/lib/shinken/",
                     'etc': "/etc/shinken",
                     'run': "/var/run/shinken",
                     'log': "/var/log/shinken",
                     'libexec': "/usr/lib/shinken/plugins",
                     }
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
             ]
            )
        ]
elif 'bsd' in sys.platform or 'dragonfly' in sys.platform:
    default_paths = {'var': "/usr/local/var/shinken",
                     'etc': "/usr/local/etc/shinken",
                     'run': "/var/run/shinken",
                     'log': "/var/log/shinken",
                     'libexec': "/usr/local/libexec/shinken",
                     }
    data_files = []
else:
    raise "Unsupported platform, sorry"
    data_files = []

required_pkgs = ['pycurl']

# Should be /etc, not the /etc/shinken !
etc_root = os.path.dirname(default_paths['etc'])
var_root = default_paths['var']

# nagios/shinken global config
main_config_files = ('shinken.cfg',)


additionnal_config_files = ()

config_objects_file = (
                        'discovery/discovery_runs.cfg',
                        'templates/generic-contact.cfg',
                        'templates/generic-host.cfg',
                        'templates/generic-service.cfg',
                        'templates/srv-pnp.cfg',
                        'dependencies/sample.cfg',
                        'discovery/discovery_rules.cfg',
                        'hosts/localhost.cfg',
                        'services/services.cfg',
                        'escalations/sample.cfg',
                        'discovery/discovery.cfg',
                        'servicegroups/sample.cfg',
                        'certs/server.pem',
                        'certs/client.pem',
                        'certs/ca.pem',
)


config_objects_file_extended = list(config_objects_file)


all_etc_files = []
# Do not put daemons in this list, because it will override other modification
for p in ['packs', 'arbiters', 'brokers', 'modules',
          'pollers', 'reactionners', 'realms', 'receivers', 'schedulers',
          'timeperiods', 'contacts', 'contactgroups', 'commands',
          'hostgroups', 'templates', 'notificationways', 'resource.d']:
    # Get all files in this dir
    _files = gen_data_files('etc/%s' % p)
    # We must remove the etc from the paths
    _files = [s.replace('etc/', '') for s in _files]
    # Declare them in your global lsit now
    config_objects_file_extended.extend(_files)

# Now service packs files
#srv_pack_files = gen_data_files('etc/packs')

#srv_pack_files = [s.replace('etc/', '') for s in srv_pack_files]
# Now service packs files
#srv_pack_files = gen_data_files('etc/packs')
# We must remove the etc from the paths
#srv_pack_files = [s.replace('etc/', '') for s in srv_pack_files]

#config_objects_file_extended.extend(srv_pack_files)
# Setup ins waiting for a tuple....
config_objects_file = tuple(config_objects_file_extended)


# daemon configs
daemon_ini_files = (('broker', 'daemons/brokerd.ini'),
                    ('receiver', 'daemons/receiverd.ini'),
                    ('poller', 'daemons/pollerd.ini'),
                    ('reactionner', 'daemons/reactionnerd.ini'),
                    ('scheduler', 'daemons/schedulerd.ini'),
                    )

resource_cfg_files = ()

package_data = ['*.py', 'modules/*.py', 'modules/*/*.py']

# If not update, we install configuration files too
if not is_update:

    data_files.append(
        (os.path.join(etc_root, 'default',),
         ['build/bin/default/shinken']
         ))

    for (dname, dfile) in daemon_ini_files:
        data_files.append(
        (os.path.join(default_paths['etc'], 'daemons',),
         ['build/etc/'+dfile]
         ))
    
    # Also add modules to the var directory
    for p in gen_data_files('modules'):
        _path, _file = os.path.split(p)
        data_files.append( (os.path.join(var_root, _path), [p]))

    # Also add share files to the var directory
    for p in gen_data_files('share'):
        _path, _file = os.path.split(p)
        data_files.append( (os.path.join(var_root, _path), [p]))

# Always overrides doc, inventory and cli even for update
for p in gen_data_files('doc'):
    _path, _file = os.path.split(p)
    data_files.append( (os.path.join(var_root, _path), [p]))

# Always overrides doc and cli even for update
for p in gen_data_files('inventory'):
    _path, _file = os.path.split(p)
    data_files.append( (os.path.join(var_root, _path), [p]))


# Also add cli files to the var directory
for p in gen_data_files('cli'):
    _path, _file = os.path.split(p)
    data_files.append( (os.path.join(var_root, _path), [p]))

# Now all the libexec things
for p in gen_data_files('libexec'):
    _path, _file = os.path.split(p)
    data_files.append( (os.path.join(var_root, _path), [p]))


# compute scripts
scripts = [ s for s in glob('bin/shinken*') if not s.endswith('.py')]

if __name__ == "__main__":
    setup(
        cmdclass={
            'build': build,
            'install': install,
            'build_config': build_config,
            'install_config': install_config
        },

        name="Shinken",
        version="2.0.1",
        packages=find_packages(),
        package_data={'': package_data},
        description="Shinken is a monitoring tool compatible with Nagios configuration and plugins",
        long_description=read('README.rst'),
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

        scripts=scripts,

        data_files=data_files,
    )

print "Shinken setup done"

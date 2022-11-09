#!/usr/bin/python2

# -*- coding: utf-8 -*-

# We can't use future unicode_litteral in setup.py because versions of
# setuptools <= 41.1.0 do not manage unicode values in package_data.
# See https://github.com/pypa/setuptools/pull/1769 for details.
# from __future__ import absolute_import, division, print_function, unicode_literals

try:
    import pwd
    import grp
except ImportError:
    # don't expect to have this on windows :)
    pwd = grp = None

# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...

from distutils.core import Command
from itertools import chain
from glob import glob
import sys
import os
import re

try:
    from setuptools import setup
    from setuptools import find_packages
except:
    sys.exit("Error: missing setuptools library")

try:
    python_version = sys.version_info
except:
    python_version = None
if not python_version or python_version < (2, 7):
    sys.exit("Shinken requires Python >= 2.7.x, sorry")


###############################################################################
#
# Utility functions
#

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


def update_file_with_string(infilename, outfilename, matches, new_strings):
    with open(infilename, "rb") as f:
        buf = f.read().decode("utf-8")
    for match, new_string in zip(matches, new_strings):
        buf = re.sub(match, new_string, buf)
    with open(outfilename, "wb") as f:
        f.write(buf.encode("utf-8"))


def get_uid(user_name):
    try:
        return pwd.getpwnam(user_name)[2]
    except KeyError as exp:
        return None


def get_gid(group_name):
    try:
        return grp.getgrnam(group_name)[2]
    except KeyError as exp:
        return None


def get_init_system():
    if os.name == 'nt':
        return None
    if not os.path.isfile("/proc/1/comm"):
        return "sysv"
    with open("/proc/1/comm", "r") as f:
        init = f.read().strip()
    if init == "systemd":
        return init
    else:
        return "sysv"


def get_requirements():
    req_path = os.path.join(
        os.path.dirname(__file__),
        "requirements.txt"
    )
    with open(req_path, "r") as f:
        requirements = [r.strip() for r in f if r.strip()]
    return requirements


def get_shinken_version():
    version_path = os.path.join(
        os.path.dirname(__file__),
        "shinken",
        "bin",
        "__init__.py"
    )
    with open(version_path, "r") as f:
        version = None
        for r in f:
            if "VERSION" in r:
                version = r.split("=")[1].strip().strip('"')
                break
    if version is None:
        raise Exception("Failed to read shinken version")
    return version


###############################################################################
#
# Distribution files
#
###############################################################################

# Packages definition
package_data = ['*.py', 'modules/*.py', 'modules/*/*.py']

# Compute scripts
scripts = [s for s in glob('bin/shinken*') if not s.endswith('.py')]


###############################################################################
#
# Default paths
#
###############################################################################

shinken_services = [
    'arbiter',
    'broker',
    'poller',
    'reactionner',
    'receiver',
    'scheduler'
]

# Installation files processing
if os.path.isfile('/etc/redhat-release'):
    default_paths = {
        'sysv':     "/etc/init.d",
        'default':  "/etc/sysconfig",
        'libexec':  "/usr/local/libexec/shinken/plugins",
        'modules':  "/usr/local/lib/shinken/modules",
        'share':    "/usr/local/share/shinken",
        'examples': "/usr/local/share/doc/shinken/examples",
        'doc':      "/usr/local/share/doc/shinken",
        'etc':      "/etc/shinken",
        'var':      "/var/lib/shinken",
        'run':      "/var/run/shinken",
        'log':      "/var/log/shinken",
    }
elif os.path.isfile('/etc/debian_version'):
    default_paths = {
        'sysv':     "/etc/init.d",
        'default':  "/etc/default",
        'libexec':  "/usr/local/libexec/shinken/plugins",
        'modules':  "/usr/local/lib/shinken/modules",
        'share':    "/usr/local/share/shinken",
        'examples': "/usr/local/share/doc/shinken/examples",
        'doc':      "/usr/local/share/doc/shinken",
        'etc':      "/etc/shinken",
        'var':      "/var/lib/shinken",
        'run':      "/var/run/shinken",
        'log':      "/var/log/shinken",
    }
elif 'linux' in sys.platform or 'sunos5' in sys.platform:
    default_paths = {
        'sysv':     "/etc/init.d",
        'default':  "/etc/default",
        'libexec':  "/usr/local/libexec/shinken/plugins",
        'modules':  "/usr/local/lib/shinken/modules",
        'share':    "/usr/local/share/shinken",
        'examples': "/usr/local/share/doc/shinken/examples",
        'doc':      "/usr/local/share/doc/shinken",
        'etc':      "/etc/shinken",
        'var':      "/var/lib/shinken",
        'run':      "/var/run/shinken",
        'log':      "/var/log/shinken",
    }
elif 'openbsd':
    default_paths = {
        'sysv':     "/etc/rc.d",
        'default':  "/etc/default",
        'libexec':  "/usr/local/libexec/shinken/plugins",
        'modules':  "/usr/local/lib/shinken/modules",
        'share':    "/usr/local/share/shinken",
        'examples': "/usr/local/share/examples/shinken",
        'doc':      "/usr/local/share/doc/shinken",
        'etc':      "/etc/shinken",
        'var':      "/var/lib/shinken",
        'run':      "/var/run/shinken",
        'log':      "/var/log/shinken",
    }
elif 'bsd' in sys.platform or 'dragonfly' in sys.platform:
    default_paths = {
        'sysv':     "/usr/local/etc/rc.d",
        'default':  "/etc/default",
        'libexec':  "/usr/local/libexec/shinken/plugins",
        'modules':  "/usr/local/lib/shinken/modules",
        'share':    "/usr/local/share/shinken",
        'examples': "/usr/local/share/examples/shinken",
        'doc':      "/usr/local/share/doc/shinken",
        'etc':      "/etc/shinken",
        'var':      "/var/lib/shinken",
        'run':      "/var/run/shinken",
        'log':      "/var/log/shinken",
    }
elif sys.platform.startswith('win'):
    default_paths = {
        'libexec':  "c:\\shinken\\libexec",
        'modules':  "c:\\shinken\\var\\modules",
        'var':      "c:\\shinken\\var",
        'share':    "c:\\shinken\\var\\share",
        'examples': "c:\\shinken\\var\\share\\examples",
        'doc':      "c:\\shinken\\var\\share\\doc",
        'etc':      "c:\\shinken\\etc",
        'log':      "c:\\shinken\\var",
        'run':      "c:\\shinken\\var",
    }
else:
    raise Exception("Unsupported platform, sorry")

if os.getenv("VIRTUAL_ENV"):
    root = os.getenv("VIRTUAL_ENV")
    default_paths.update({
        'default':  os.path.join(root, "etc", "default"),
        'libexec':  os.path.join(root, "libexec", "shinken", "plugins"),
        'modules':  os.path.join(root, "lib", "shinken", "modules"),
        'share':    os.path.join(root, "share", "shinken"),
        'examples': os.path.join(root, "share", "doc", "shinken", "examples"),
        'doc':      os.path.join(root, "share", "doc", "shinken"),
        'etc':      os.path.join(root, "etc", "shinken"),
        'var':      os.path.join(root, "var", "lib", "shinken"),
        'run':      os.path.join(root, "var", "run", "shinken"),
        'log':      os.path.join(root, "var", "log", "shinken"),
    })

###############################################################################
#
# Init related files
#
###############################################################################

if get_init_system() == "systemd":
    init_files = [
        'bin/systemd/shinken-%s.service.in' % service
        for service in shinken_services
    ]
    data_files = [(
        os.path.join(default_paths['examples'], 'systemd'),
        init_files
    )]
    default_files = [
        'bin/default/shinken-%s.in' % service
        for service in shinken_services
    ]
    data_files.append((
        os.path.join(default_paths['examples'], 'default'),
        default_files
    ))
elif get_init_system() == "sysv":
    init_files = ['bin/init.d/shinken.in']
    init_files.extend([
        'bin/init.d/shinken-%s' % service for service in shinken_services
    ])
    data_files = [(
        os.path.join(default_paths['examples'], 'init.d'),
        init_files
    )]
    # warning: The default file will be generated a bit later
    default_files = ['bin/default/shinken.in']
    data_files.append((
        os.path.join(default_paths['examples'], 'default'),
        default_files
    ))
else:
    data_files = []

###############################################################################
#
# Daemon and and shinken configuration files processing
#
###############################################################################

## get all files + under-files in etc/ except daemons folder
for path, subdirs, files in os.walk('etc'):
    dirname = os.path.join(default_paths['examples'], path)
    if not files:
        data_files.append((dirname, []))
        continue
    for name in files:
        data_files.append((dirname, [os.path.join(path, name)]))

###############################################################################
#
# Modules, inventory, doc, ...
#
###############################################################################

# Modules, doc, inventory and cli are always installed
paths = ('inventory', 'cli')
dist = {}
for path, subdirs, files in chain.from_iterable(os.walk(patho) for patho in paths):
    for name in files:
        dirname = os.path.join(default_paths['var'], path)
        data_files.append((
            dirname, [os.path.join(path, name)]
        ))

for path, subdirs, files in os.walk('share'):
    for name in files:
        dirname = os.path.dirname(os.path.join(
            default_paths['share'],
            re.sub(r"^(share\/|share$)", "", path)
        ))
        data_files.append((
            dirname, [os.path.join(path, name)]
        ))

for path, subdirs, files in os.walk('doc'):
    for name in files:
        dirname = os.path.dirname(os.path.join(
            default_paths['doc'],
            re.sub(r"^(doc\/|doc$)", "", path)
        ))
        data_files.append((
            dirname, [os.path.join(path, name)]
        ))

for path, subdirs, files in os.walk('modules'):
    for name in files:
        dirname = os.path.dirname(os.path.join(
            default_paths['modules'],
            re.sub(r"^(modules\/|modules$)", "", path)
        ))
        data_files.append((
            dirname, [os.path.join(path, name)]
        ))

for path, subdirs, files in os.walk('libexec'):
    for name in files:
        dirname = os.path.dirname(os.path.join(
            default_paths['libexec'],
            re.sub(r"^(libexec\/|libexec$)", "", path)
        ))
        data_files.append((
            dirname, [os.path.join(path, name)]
        ))

###############################################################################
#
# Run related files
#
###############################################################################

data_files.append((default_paths['run'], []))
data_files.append((default_paths['log'], []))

###############################################################################
#
# Post install command and actions
#
###############################################################################

class post_install(Command):
    """
    A custom command to execute post-install actions
    """

    description = 'Run shinken post-install actions, such as templates ' \
            'processing and permissions enforcement'
    user_options = [
        # The format is (long option, short option, description).
        ('install-conf', None, 'Install shinken configuration from examples'),
        ('install-default', None, 'Install shinken default files from examples'),
        ('install-init', None, 'Install shinken init files from examples'),
        (
            'confdir=',
            'c',
            'The configuration directory to alter (defaults to %s)' %
            default_paths['etc']
        ),
        (
            'defaultdir=',
            'f',
            'The environment files director for init system (defaults to %s)' %
            default_paths['default']
        ),
        ('user=', 'u', 'User to run Shinken under (defaults to shinken)'),
        ('group=', 'g', 'User to run Shinken under (defaults to shinken)'),
        (
            'modules=',
            'm',
            'Path the modules should be placed into (defaults to %s)' %
            default_paths['modules']
        ),
        (
            'workdir=',
            'w',
            'The shinken work directory (defaults to %s)' %
            default_paths['var']
        ),
        (
            'lockdir=',
            'x',
            'The shinken service lock directory (defaults to %s)' %
            default_paths['run']
        ),
        (
            'logdir=',
            'l',
            'The shinken log directory (defaults to %s)' %
            default_paths['log']
        ),
    ]
    boolean_options = ['install-conf', 'install-default', 'install-init']

    def initialize_options(self):
        """
        Set default values for options.
        """
        # Each user option must be listed here with their default value.
        self.install_dir = None
        self.install_conf = None
        self.install_default = None
        self.install_init = None
        self.user = 'shinken'
        self.group = 'shinken'
        self.confdir = default_paths['etc']
        self.defaultdir = default_paths['default']
        self.modules = default_paths['modules']
        self.workdir = default_paths['var']
        self.lockdir = default_paths['run']
        self.logdir = default_paths['log']

    def finalize_options(self):
        """
        Post-process options.
        """
        assert get_uid(self.user) is not None, ('Unknown user %s.' % self.user)
        assert get_gid(self.group) is not None, ('Unknown group %s.' % self.group)
        self.set_undefined_options(
            'install', ('install_scripts', 'install_dir'),
        )

    def generate_default_files(self):
        # The default file must have good values for the directories:
        # etc, var and where to push scripts that launch the app.
        # The `default_files` variable has been set above while genetating the
        # `data_files` list.
        default_templates = [
            os.path.join(default_paths['examples'], re.sub(r'^bin/', '', d))
            for d in default_files
        ]
        for default_template in default_templates:
            # Read the template file
            # There can be unicode characters in files
            # As setuptools does not support unicode in python2, for 2/3
            # compatibility, read files in binary and decode them in unicode
            # Do the contrary to write them.
            with open(default_template, "rb") as f:
                buf = f.read().decode("utf-8")
            # substitute
            buf = buf.replace("$ETC$", self.confdir)
            buf = buf.replace("$VAR$", self.workdir)
            buf = buf.replace("$RUN$", self.lockdir)
            buf = buf.replace("$LOG$", self.logdir)
            # write out the new file
            target = re.sub(r'\.in$', '', default_template)
            with open(target, "wb") as f:
                f.write(buf.encode("utf-8"))

    def install_default_files(self):
        for filename in [os.path.basename(i) for i in default_files]:
            default_src = re.sub(r'\.in$', '', os.path.join(
                default_paths['examples'],
                'default',
                filename))
            default_dir = self.defaultdir
            self.mkpath(default_dir)
            self.copy_file(default_src, default_dir)

    def generate_init_files(self):
        # The default file must have good values for the directories:
        # etc, var and where to push scripts that launch the app.
        # The `default_files` variable has been set above while genetating the
        # `data_files` list.
        init_templates = [
            os.path.join(default_paths['examples'], re.sub(r'^bin/', '', i))
            for i in init_files
        ]
        for init_template in init_templates:
            # Read the template file
            # There can be unicode characters in files
            # As setuptools does not support unicode in python2, for 2/3
            # compatibility, read files in binary and decode them in unicode
            # Do the contrary to write them.
            with open(init_template, "rb") as f:
                buf = f.read().decode("utf-8")
            # substitute
            buf = buf.replace("$BIN$", self.install_dir.rstrip("/"))
            buf = buf.replace("$DEFAULT$", default_paths["default"])
            # write out the new file
            target = re.sub(r'\.in$', '', init_template)
            with open(target, "wb") as f:
                f.write(buf.encode("utf-8"))

    def install_init_files(self):
        systemd_reload = False
        for filename in [os.path.basename(i) for i in init_files]:
            if get_init_system() == "systemd":
                systemd_reload = True
                init_src = re.sub(r'\.in$', '', os.path.join(
                    default_paths['examples'],
                    'systemd',
                    filename))
                init_dir = '/etc/systemd/system'
                self.mkpath(init_dir)
                self.copy_file(init_src, init_dir)
            elif get_init_system() == "sysv":
                init_src = re.sub(r'\.in$', '', os.path.join(
                    default_paths['examples'],
                    'init.d',
                    filename))
                init_dir = default_paths['sysv']
                self.mkpath(init_dir)
                init_file = re.sub(r'\.in$', '', os.path.join(
                    init_dir,
                    filename))
                self.copy_file(init_src, init_dir)
                os.chmod(init_file, 0o0755)
        if systemd_reload:
            self.spawn(["systemctl", "daemon-reload"])

    def generate_conf_files(self):
        conf_templates = []
        conf_base = os.path.join(default_paths['examples'], 'etc')
        for path, subdirs, files in os.walk(conf_base):
            for name in files:
                if name.endswith(".in"):
                    conf_template = os.path.join(path, name)
                    conf_templates.append(conf_template)

        # Processes template files expansion
        for conf_template in conf_templates:
            target = re.sub(r'\.in$', '', conf_template)
            update_file_with_string(
                conf_template,
                target,
                [
                    "modules_dir=.*",
                    "#user=.*",
                    "#group=.*",
                    "shinken_user=\w+",
                    "shinken_group=\w+",
                    "workdir=.+",
                    "lock_file=.+",
                    "local_log=.+",
                ],
                [
                    "modules_dir=%s" % self.modules,
                    "user=%s" % self.user,
                    "group=%s" % self.group,
                    "shinken_user=%s" % self.user,
                    "shinken_group=%s" % self.group,
                    "workdir=%s" % self.workdir,
                    "lock_file=%s/arbiterd.pid" % self.lockdir,
                    "local_log=%s/arbiterd.log" % self.logdir,
                ]
            )

    def install_conf_files(self):
        conf_files = []
        conf_base = os.path.join(default_paths['examples'], 'etc')
        for path, subdirs, files in os.walk(conf_base):
            for name in files:
                if name.endswith(".in"):
                    continue
                conf_file = os.path.join(path, name)
                conf_files.append(conf_file)

        for filename in conf_files:
            conf_file = filename.replace(conf_base, self.confdir)
            conf_dir = os.path.dirname(conf_file)
            self.mkpath(conf_dir)
            self.copy_file(filename, conf_file)

    def run(self):
        """
        Run command.
        """
        self.generate_conf_files()
        if os.name == 'nt':
            return
        self.generate_default_files()
        self.generate_init_files()
        if self.install_conf:
            self.install_conf_files()
        if self.install_default:
            self.install_default_files()
        if self.install_init:
            self.install_init_files()
        # Enforces files and directories ownership
        for c in ['run', 'log', 'var']:
            p = default_paths[c]
            self.spawn(["chown", "-R", "%s:%s" % (self.user, self.group), p])
        for c in ['libexec']:
            p = default_paths[c]
            self.spawn(["chmod", "-R", "+X", p])


###############################################################################
#
# Debug output
#
###############################################################################

if os.getenv("DEBUG") == "1":
    from pprint import pprint
    print("Version")
    pprint(get_shinken_version())
    print("Packages")
    pprint(find_packages(
        exclude=[
            "shinken.webui",
            "shinken.webui.bottlecole",
            "shinken.webui.bottlewebui"
        ]
    ))
    print("Requirements")
    pprint(get_requirements())
    print("Default paths")
    pprint(default_paths)
    print("Data files")
    pprint(data_files)
    print("Default files")
    pprint(default_files)
    print("Init files")
    pprint(init_files)

###############################################################################
#
# Setup
#
###############################################################################

setup(
    name="Shinken",
    version=get_shinken_version(),
    packages=find_packages(
        exclude=[
            "shinken.webui",
            "shinken.webui.bottlecole",
            "shinken.webui.bottlewebui"
        ]
    ),
    scripts=scripts,
    package_data={'': package_data},
    description="Shinken is a monitoring framework compatible with Nagios configuration and plugins",
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
    install_requires=get_requirements(),
    extras_require={
        'setproctitle': ['setproctitle']
    },
    data_files=data_files,
    cmdclass={
        'post_install': post_install,
    },
)

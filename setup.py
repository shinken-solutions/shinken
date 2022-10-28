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

try:
    from setuptools import setup
    from setuptools import find_packages
except:
    sys.exit("Error: missing setuptools library")

from distutils.dir_util import mkpath
from itertools import chain
from glob import glob
import distutils.cmd
import sys
import os
import re


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


def ensure_dir_exist(f):
    dirname = os.path.dirname(f)
    if not os.path.exists(dirname):
        os.makedirs(dirname)


def generate_default_shinken_file(in_file):
    # The default file must have good values for the directories:
    # etc, var and where to push scripts that launch the app.
    templatefile = os.path.join("bin/default", in_file)
    build_base = 'build'
    outfile = os.path.join(build_base, "bin/default", in_file.rstrip(".in"))
    mkpath(os.path.dirname(outfile))

    # Read the template file
    with open(templatefile, "r") as f:
        buf = f.read()
    # substitute
    buf = buf.replace("$ETC$", default_paths['etc'])
    buf = buf.replace("$VAR$", default_paths['var'])
    buf = buf.replace("$RUN$", default_paths['run'])
    buf = buf.replace("$LOG$", default_paths['log'])
    # write out the new file
    with open(outfile, "w") as f:
        f.write(buf)


def update_file_with_string(infilename, outfilename, matches, new_strings):
    with open(infilename, "r") as f:
        buf = f.read()
    for match, new_string in zip(matches, new_strings):
        buf = re.sub(match, new_string, buf)
    with open(outfilename, "w") as f:
        f.write(buf)


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
if os.getenv("VIRTUAL_ENV"):
    root = os.getenv("VIRTUAL_ENV")
    default_paths = {
        'libexec':  os.path.join(root, "libexec", "shinken", "plugins"),
        'modules':  os.path.join(root, "lib", "shinken", "modules"),
        'share':    os.path.join(root, "share", "shinken"),
        'examples': os.path.join(root, "share", "doc", "shinken", "examples"),
        'doc':      os.path.join(root, "share", "doc", "shinken"),
        'etc':      os.path.join(root, "etc", "shinken"),
        'var':      os.path.join(root, "var", "lib", "shinken"),
        'run':      os.path.join(root, "var", "run", "shinken"),
        'log':      os.path.join(root, "var", "log", "shinken"),
    }
elif 'linux' in sys.platform or 'sunos5' in sys.platform:
    default_paths = {
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
elif 'bsd' in sys.platform or 'dragonfly' in sys.platform:
    default_paths = {
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

###############################################################################
#
# Init related files
#
###############################################################################

if get_init_system() == "systemd":
    init_files = [
        'bin/systemd/shinken-%s.service' % service
        for service in shinken_services
    ]
    data_files = [(
        os.path.join(default_paths['examples'], 'systemd'),
        init_files
    )]
    # warning: The default file will be generated a bit later
    default_files = [
        'build/bin/default/shinken-%s' % service
        for service in shinken_services
    ]
    data_files.append((
        os.path.join(default_paths['examples'], 'default'),
        default_files
    ))
    if 'install' in sys.argv:
        for service in shinken_services:
            generate_default_shinken_file("shinken-%s.in" % service)
elif get_init_system() == "sysv":
    init_files = ['bin/init.d/shinken']
    init_files.extend([
        'bin/init.d/shinken-%s' % service for service in shinken_services
    ])
    data_files = [(
        os.path.join(default_paths['examples'], 'init.d'),
        init_files
    )]
    # warning: The default file will be generated a bit later
    default_files = ['build/bin/default/shinken']
    data_files.append((
        os.path.join(default_paths['examples'], 'default'),
        default_files
    ))
    if 'install' in sys.argv:
        generate_default_shinken_file("shinken.in")
else:
    data_files = []

###############################################################################
#
# Daemon and and shinken configuration files processing
#
###############################################################################

## get all files + under-files in etc/ except daemons folder
for path, subdirs, files in os.walk('etc'):
    if not files:
        dirname = os.path.dirname( os.path.join(
            default_paths['examples'],
            path
        ))
        data_files.append((dirname, []))
        continue
    for name in files:
        dirname = os.path.dirname(os.path.join(
            default_paths['examples'],
            path
        ))
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

class PostInstallCommand(distutils.cmd.Command):
    """
    A custom command to execute post-install actions
    """

    description = 'Run shinken post-install actions, such as templates ' \
            'processing and permissions enforcement'
    user_options = [
        # The format is (long option, short option, description).
        (
            'confdir=',
            'c',
            'The configuration directory to alter (defaults to %s)' %
            default_paths['examples']
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

    def initialize_options(self):
        """
        Set default values for options.
        """
        # Each user option must be listed here with their default value.
        self.user = 'shinken'
        self.group = 'shinken'
        self.confdir = default_paths['examples']
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

    def run(self):
        """
        Run command.
        """
        templates = []
        for path, subdirs, files in os.walk(self.confdir):
            for name in files:
                if name.endswith(".in"):
                    templates.append(os.path.join(path, name))

        # Processes template files expansion
        modules_dir = os.path.join(default_paths['var'], 'modules')
        for template in templates:
            target = template.rstrip(".in")
            update_file_with_string(
                template,
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
                    "modules_dir=%s" % modules_dir,
                    "user=%s" % self.user,
                    "group=%s" % self.group,
                    "shinken_user=%s" % self.user,
                    "shinken_group=%s" % self.group,
                    "workdir=%s" % self.workdir,
                    "lock_file=%s/arbiterd.pid" % self.lockdir,
                    "local_log=%s/arbiterd.log" % self.logdir,
                ]
            )
        if os.name == 'nt':
            return
        # Enforces files and directories ownership
        for c in ['run', 'log', 'var']:
            p = default_paths[c]
            os.system("chown -R %s:%s %s" % (self.user, self.group, p))
        for c in ['libexec']:
            p = default_paths[c]
            os.system("chmod -R +X %s" % p)


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
    print("Data files")
    pprint(data_files)

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
        'postinstall': PostInstallCommand,
    },
)

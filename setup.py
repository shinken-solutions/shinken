#!/usr/bin/python2

# -*- coding: utf-8 -*-

# We can't use future unicode_litteral in setup.py because versions of
# setuptools <= 41.1.0 do not manage unicode values in package_data.
# See https://github.com/pypa/setuptools/pull/1769 for details.
# from __future__ import absolute_import, division, print_function, unicode_literals

import os
import sys
import re

try:
    import pwd
    import grp
except ImportError:
    # don't expect to have this on windows :)
    pwd = grp = None
import stat

# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...

try:
    from setuptools import setup
    from setuptools import find_packages
except:
    sys.exit("Error: missing setuptools library")

from itertools import chain
import optparse
import itertools
from glob import glob

from distutils.dir_util import mkpath

try:
    python_version = sys.version_info
except:
    python_version = None
if not python_version or python_version < (2, 7):
    sys.exit("Shinken require as a minimum Python 2.7.x, sorry")


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


def generate_default_shinken_file():
    # The default file must have good values for the directories:
    # etc, var and where to push scripts that launch the app.
    templatefile = "bin/default/shinken.in"
    build_base = 'build'
    outfile = os.path.join(build_base, "bin/default/shinken")
    mkpath(os.path.dirname(outfile))
    bin_path = default_paths['bin']

    # Read the template file
    with open(templatefile, "r") as f:
        buf = f.read()
    # substitute
    buf = buf.replace("$ETC$", default_paths['etc'])
    buf = buf.replace("$VAR$", default_paths['var'])
    buf = buf.replace("$RUN$", default_paths['run'])
    buf = buf.replace("$LOG$", default_paths['log'])
    buf = buf.replace("$SCRIPTS_BIN$", bin_path)
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


def recursive_chown(path, uid, gid, owner, group):
    print("Changing owner of %s to %s:%s" % (path, owner, group))
    os.chown(path, uid, gid)
    if os.path.isdir(path):
        for dirname, dirs, files in os.walk(path):
            for path in itertools.chain(dirs, files):
                path = os.path.join(dirname, path)
                os.chown(path, uid, gid)


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


# Do a chmod -R +x
def _chmodplusx(d):
    if not os.path.exists(d):
        print("warn: _chmodplusx missing dir", d)
        return
    if os.path.isdir(d):
        for item in os.listdir(d):
            p = os.path.join(d, item)
            if os.path.isdir(p):
                _chmodplusx(p)
            else:
                st = os.stat(p)
                os.chmod(p, st.st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    else:
        st = os.stat(d)
        os.chmod(d, st.st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)


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


def get_cli_parser():

    parser = optparse.OptionParser("%prog [options]", version="%prog ")
    parser.add_option(
        '--root', dest="proot", metavar="ROOT",
        help='Root dir to install, usefull only for packagers'
    )
    parser.add_option(
        '--upgrade', '--update', dest="upgrade", action='store_true',
        help='Only upgrade'
    )
    parser.add_option(
        '--owner', dest="owner", metavar="OWNER", default='shinken',
        help='User to install with, default shinken'
    )
    parser.add_option(
        '--group', dest="group", metavar="GROUP", default='shinken',
        help='Group to install with, default shinken'
    )
    parser.add_option(
        '--install-scripts', dest="install_scripts",
        help='Path to install the shinken-* scripts'
    )
    parser.add_option(
        '--skip-build', dest="skip_build", action='store_true',
        help='skipping build'
    )
    parser.add_option(
        '-O', type="int", dest="optimize",
        help='skipping build'
    )
    parser.add_option(
        '--record', dest="record",
        help='File to save writing files. Used by pip install only'
    )
    parser.add_option(
        '--single-version-externally-managed', dest="single_version", action='store_true',
        help='I really dont know, this option is for pip only'
    )
    return parser


###############################################################################
#
# Command line parsing
#

parser = get_cli_parser()
opts, args = parser.parse_args()
root = opts.proot
user = opts.owner
group = opts.group
install_scripts = opts.install_scripts
is_virtualenv = os.getenv("VIRTUAL_ENV") is not None

# We try to see if we are in a full install or an update process
is_update = False

# Try to import shinekn but not the local one. If avialable, we are in
# and upgrade phase, not a classic install
try:
    if '.' in sys.path:
        sys.path.remove('.')
    if os.path.abspath('.') in sys.path:
        sys.path.remove(os.path.abspath('.'))
    if '' in sys.path:
        sys.path.remove('')
    import shinken

    is_update = True
    print("Previous Shinken lib detected (%s)" % shinken.__file__)
except ImportError:
    pass

if '--update' in args or opts.upgrade or '--upgrade' in args:
    print("Shinken Lib Updating process only")
    if 'update' in args:
        sys.argv.remove('update')
        sys.argv.insert(1, 'install')
    if '--update' in args:
        sys.argv.remove('--update')
    if '--upgrade' in args:
        sys.argv.remove('--upgrade')

    print("Shinken Lib Updating process only")
    is_update = True

is_install = False
if 'install' in args:
    is_install = True

# Last step for pip insta an install one (at least in pip 9.0.1)
is_pip_real_install_step = 'bdist_wheel' in sys.argv
if is_pip_real_install_step:
    is_update = False
    is_install = True

# Delete command line parameters not managed by setup() that we already used
# previously
deleting_args = ['--owner', '--group', '--skip-build']
largv = len(sys.argv)
for i, arg in enumerate(reversed(sys.argv)):
    if arg.split("=")[0] in deleting_args:
        sys.argv.pop(largv - i -1)
        if "=" not in arg:
            sys.argv.pop(largv - i -1)

# Note: we do not add the "scripts" entry in the setup phase because we need to generate the
# default/shinken file with the bin path before run the setup phase, and it's not so
# easy to do in a clean and easy way

not_allowed_options = ['--upgrade', '--update']
for o in not_allowed_options:
    if o in sys.argv:
        sys.argv.remove(o)


###############################################################################
#
# Distribution files
#

# Packages definition
package_data = ['*.py', 'modules/*.py', 'modules/*/*.py']

# Installation files processing
if 'linux' in sys.platform or 'sunos5' in sys.platform:
    default_paths = {
        'bin'    : install_scripts or "/usr/bin",
        'var'    : "/var/lib/shinken/",
        'share'  : "/var/lib/shinken/share",
        'etc'    : "/etc/shinken",
        'run'    : "/var/run/shinken",
        'log'    : "/var/log/shinken",
        'libexec': "/var/lib/shinken/libexec",
    }
    data_files = [
        (
            os.path.join('/etc', 'init.d'),
            [
                'bin/init.d/shinken',
                'bin/init.d/shinken-arbiter',
                'bin/init.d/shinken-broker',
                'bin/init.d/shinken-receiver',
                'bin/init.d/shinken-poller',
                'bin/init.d/shinken-reactionner',
                'bin/init.d/shinken-scheduler',
            ]
        )
    ]

    if is_install:
        # warning: The default file will be generated a bit later
        data_files.append((
            os.path.join('/etc', 'default'),
            [
                'build/bin/default/shinken'
                ]
            ))
elif 'bsd' in sys.platform or 'dragonfly' in sys.platform:
    default_paths = {
        'bin'    : install_scripts or "/usr/local/bin",
        'var'    : "/usr/local/libexec/shinken",
        'share'  : "/usr/local/share/shinken",
        'etc'    : "/usr/local/etc/shinken",
        'run'    : "/var/run/shinken",
        'log'    : "/var/log/shinken",
        'libexec': "/usr/local/libexec/shinken/plugins",
    }
    data_files = [
        (
            '/usr/local/etc/rc.d',
            [
                'bin/rc.d/shinken-arbiter',
                'bin/rc.d/shinken-broker',
                'bin/rc.d/shinken-receiver',
                'bin/rc.d/shinken-poller',
                'bin/rc.d/shinken-reactionner',
                'bin/rc.d/shinken-scheduler',
            ]
        )
        ]
elif sys.platform.startswith('win'):
    default_paths = {
        'bin'    : install_scripts or "c:\\shinken\\bin",
        'var'    : "c:\\shinken\\var",
        'share'  : "c:\\shinken\\var\\share",
        'etc'    : "c:\\shinken\\etc",
        'log'    : "c:\\shinken\\var",
        'run'    : "c:\\shinken\\var",
        'libexec': "c:\\shinken\\libexec",
    }
    data_files = []
else:
    raise Exception("Unsupported platform, sorry")


if is_virtualenv:
    # Virtualenvs only contain python libraries and script directly related to
    # the Shinken core.
    # All the configuration files and additional (init) scripts have supposed
    # to be manually managed, as it can't be part of the virtualenv.
    #
    # Install binaries and scripts in virtualenv's bin directory
    default_paths["bin"] = os.path.join(os.getenv("VIRTUAL_ENV"), "bin")
    data_files = []
else:
    # Modules, doc, inventory and cli are always installed
    paths = ('modules', 'doc', 'inventory', 'cli')
    for path, subdirs, files in chain.from_iterable(os.walk(patho) for patho in paths):
        for name in files:
            dirname = os.path.join(default_paths['var'], path)
            data_files.append((
                dirname, [os.path.join(path, name)]
                ))

    for path, subdirs, files in os.walk('share'):
        for name in files:
            dirname = os.path.join(
                    default_paths['share'],
                    re.sub(r"^(share\/|share$)", "", path)
                )
            data_files.append((
                dirname, [os.path.join(path, name)]
                ))

    for path, subdirs, files in os.walk('libexec'):
        for name in files:
            dirname = os.path.join(
                default_paths['libexec'],
                re.sub(r"^(libexec\/|libexec$)", "", path)
            )
            data_files.append((
                dirname, [os.path.join(path, name)]
                ))

    data_files.append((default_paths['run'], []))
    data_files.append((default_paths['log'], []))

# Packages definition
package_data = ['*.py', 'modules/*.py', 'modules/*/*.py']

# Compute scripts
scripts = [s for s in glob('bin/shinken*') if not s.endswith('.py')]

###############################################################################
#
# Configuration file generation
#

# Only some platform are managed by the init.d scripts
if not is_virtualenv and is_install and \
        ('linux' in sys.platform or 'sunos5' in sys.platform):
    generate_default_shinken_file()


###############################################################################
#
# Daemon and default files processing depending on the install mode
# (install/update)
#

if not is_virtualenv and not is_update:
    ## get all files + under-files in etc/ except daemons folder
    daemonsini = []
    for path, subdirs, files in os.walk('etc'):
        if not files:
            dirname =  os.path.join(
                default_paths['etc'],
                re.sub(r"^(etc\/|etc$)", "", path)
            )
            data_files.append((dirname, []))
            continue
        for name in files:
            if name == 'shinken.cfg':
                continue
            if 'daemons' in path:
                daemonsini.append(os.path.join(path, name))
            else:
                dirname = os.path.join(
                    default_paths['etc'],
                    re.sub(r"^(etc\/|etc$)", "", path)
                )
                data_files.append((dirname, [os.path.join(path, name)]))

###############################################################################
#
# Shinken configuration depending on the install mode (install/update)
#

if not is_virtualenv and os.name != 'nt' and not is_update:
    # Adds daemons ini files
    for _file in daemonsini:
        inname = _file
        outname = os.path.join('build', _file)
        modules_dir = os.path.join(default_paths['var'], 'modules')
        # force the user setting as it's not set by default
        print('updating configuration file %s', outname)
        update_file_with_string(
            inname,
            outname,
            [
                "modules_dir=.*",
                "#user=.*",
                "#group=.*",
            ],
            [
                "modules_dir=%s" % modules_dir,
                "user=%s" % user,
                "group=%s" % group,
            ]
        )
        dirname = os.path.join(default_paths['etc'], 'daemons')
        data_files.append((dirname, [outname]))

    # And update the shinken.cfg file for all /usr/local/shinken/var
    # value with good one
    for name in ['shinken.cfg']:
        inname = os.path.join('etc', name)
        outname = os.path.join('build', name)
        print('updating configuration file %s', outname)

        ## but we HAVE to set the shinken_user & shinken_group to thoses requested:
        update_file_with_string(
            inname,
            outname,
            [
                "shinken_user=\w+",
                "shinken_group=\w+",
                "workdir=.+",
                "lock_file=.+",
                "local_log=.+",
                "modules_dir=.+",
                "pack_distribution_file=.+"
            ],
            [
                "shinken_user=%s" % user,
                "shinken_group=%s" % group,
                "workdir=%s" % default_paths['var'],
                "lock_file=%s/arbiterd.pid" % default_paths['run'],
                "local_log=%s/arbiterd.log" % default_paths['log'],
                "modules_dir=%s" % os.path.join(
                    default_paths['var'],
                    'modules'
                ),
                "pack_distribution_file=%s" % os.path.join(
                    default_paths['var'],
                    'pack_distribution.dat'
                )
            ]
        )
        data_files.append((default_paths['etc'], [outname]))


if os.getenv("DEBUG") == "1":
    from pprint import pprint
    print("Argv")
    pprint(sys.argv)
    print("Version")
    pprint(get_shinken_version())
    print("Is install")
    pprint(is_install)
    print("Is update")
    pprint(is_update)
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
# Preflight checks
#
###############################################################################

# Maybe the user is unknown, but we are in a "classic" install, if so, bail out
if not is_virtualenv and is_install and not root and not is_update and pwd and not opts.skip_build:
    uid = get_uid(user)
    gid = get_gid(group)

    if uid is None or gid is None:
        print("Error: the user/group %s/%s is unknown. Please create it first 'useradd %s'" % (user, group, user))
        sys.exit(2)

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
)

###############################################################################
#
# Post install operations
#
###############################################################################

# if root is set, it's for package, so NO chown
if not is_virtualenv and pwd and not root and is_install:
    # assume a posix system
    uid = get_uid(user)
    gid = get_gid(group)

    if uid is not None and gid is not None:
        # recursivly changing permissions for etc/shinken and var/lib/shinken
        for c in ['etc', 'run', 'log', 'var', 'libexec']:
            p = default_paths[c]
            recursive_chown(p, uid, gid, user, group)
        _chmodplusx(default_paths['libexec'])

print("Shinken setup done")

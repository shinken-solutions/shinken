#!/usr/bin/python

# -*- coding: utf-8 -*-

import os
import sys
import re

try:
    import pwd
    import grp
except ImportError:
    # don't expect to have this on windows :)
    pwd = grp = None
import fileinput
import stat

# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...

try:
    from setuptools import setup
    from setuptools import find_packages
except:
    sys.exit("Error: missing python-setuptools library")

from itertools import chain
import optparse
import itertools
from glob import glob

from distutils.dir_util import mkpath

try:
    python_version = sys.version_info
except:
    python_version = (1, 5)
if python_version < (2, 6):
    sys.exit("Shinken require as a minimum Python 2.6.x, sorry")
elif python_version >= (3,):
    sys.exit("Shinken is not yet compatible with Python3k, sorry")

PACKAGE_DATA = ['*.py', 'modules/*.py', 'modules/*/*.py']


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


def ensure_dir_exist(f):
    dirname = os.path.dirname(f)
    if not os.path.exists(dirname):
        os.makedirs(dirname)


def generate_default_shinken_file(default_paths):
    # The default file must have good values for the directories:
    # etc, var and where to push scripts that launch the app.
    templatefile = "bin/default/shinken.in"
    build_base = 'build'
    outfile = os.path.join(build_base, "bin/default/shinken")

    # print('generating %s from %s', outfile, templatefile)

    mkpath(os.path.dirname(outfile))

    bin_path = default_paths['bin']

    # Read the template file
    f = open(templatefile)
    buf = f.read()
    f.close()
    # substitute
    buf = buf.replace("$ETC$", default_paths['etc'])
    buf = buf.replace("$VAR$", default_paths['var'])
    buf = buf.replace("$RUN$", default_paths['run'])
    buf = buf.replace("$LOG$", default_paths['log'])
    buf = buf.replace("$SCRIPTS_BIN$", bin_path)
    # write out the new file
    f = open(outfile, "w")
    f.write(buf)
    f.close()


def update_file_with_string(infilename, outfilename, matches, new_strings):
    f = open(infilename)
    buf = f.read()
    f.close()
    for match, new_string in zip(matches, new_strings):
        buf = re.sub(match, new_string, buf)
    f = open(outfilename, "w")
    f.write(buf)
    f.close()


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
    except KeyError, exp:
        return None


def get_gid(group_name):
    try:
        return grp.getgrnam(group_name)[2]
    except KeyError, exp:
        return None


# Do a chmod -R +x
def _chmodplusx(d):
    if not os.path.exists(d):
        print "warn: _chmodplusx missing dir", d
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


def _error(msg):
    print 'Parser error', msg


def main():
    parser = optparse.OptionParser(
        "%prog [options]", version="%prog ")
    parser.add_option('--root',
                      dest="proot", metavar="ROOT",
                      help='Root dir to install, usefull only for packagers')
    parser.add_option('--upgrade', '--update',
                      dest="upgrade", action='store_true',
                      help='Only upgrade')
    parser.add_option('--owner',
                      dest="owner", metavar="OWNER",
                      help='User to install with, default shinken')
    parser.add_option('--group',
                      dest="group", metavar="GROUP",
                      help='Group to install with, default shinken')
    parser.add_option('--install-scripts',
                      dest="install_scripts",
                      help='Path to install the shinken-* scripts')
    parser.add_option('--skip-build',
                      dest="skip_build", action='store_true',
                      help='skipping build')
    parser.add_option('-O', type="int",
                      dest="optimize",
                      help='skipping build')
    parser.add_option('--record',
                      dest="record",
                      help='File to save writing files. Used by pip install only')
    parser.add_option('--single-version-externally-managed',
                      dest="single_version", action='store_true',
                      help='I really dont know, this option is for pip only')
    parser.add_option('--package-only',
                      dest="package_only", action='store_true',
                      help="Don't setup shinken, just install the package")
    old_error = parser.error
    parser.error = _error
    opts, args = parser.parse_args()
    # reenable the errors for later use
    parser.error = old_error

    # Handle the args
    root = opts.proot or ''
    user = opts.owner or 'shinken'
    group = opts.group or 'shinken'

    is_install = 'install' in args
    install_scripts = opts.install_scripts or ''
    skip_build = opts.skip_build

    # These are commands that setup is supposed to handle
    fallthrough_commands = ['egg_info', 'pip-egg-info']
    has_fallthrough_command = any(fallthrough_command in args for fallthrough_command in fallthrough_commands)

    # Options that setup doesn't like, but that we need
    package_only = False
    if "--package-only" in args:
        package_only = True
        sys.argv.remove("--package-only")

    # We try to see if we are in a full install or an update process
    required_pkgs = []
    is_update = check_is_update(args, opts) or check_is_package_installed()
    if not has_fallthrough_command and is_update and not package_only:
        if not check_are_data_files_installed(install_scripts, is_install):
            # We may have only done a package install before
            print "Not all files are installed"
            full_install(user, group, root, required_pkgs, install_scripts, skip_build)
        else:
            # A real upgrade
            data_files, default_paths, scripts = get_default_platform_paths(install_scripts, False)
            setup_package(required_pkgs, data_files)
    elif not has_fallthrough_command and is_install and not package_only:
        full_install(user, group, root, required_pkgs, install_scripts, skip_build)
    else:
        print "Simple setup"
        data_files, default_paths, scripts = get_default_platform_paths(install_scripts, False)
        setup_package(required_pkgs, data_files)

    print "Shinken setup done"


def full_install(user, group, root, required_pkgs, install_scripts, skip_build):
    print "Full install procedure"
    data_files, default_paths, scripts = pre_install(user, group, root, install_scripts, skip_build)
    setup_package(required_pkgs, data_files)
    post_install(user, group, root, default_paths, scripts)


def pre_install(user, group, root, install_scripts, skip_build):
    print "Preparing for shinken install..."

    # Maybe the user is unknown, but we are in a "classic" install, if so, bail out
    if not root and pwd and not skip_build:
        uid = get_uid(user)
        gid = get_gid(group)

        if uid is None or gid is None:
            print "Error: the user/group %s/%s is unknown. Please create it first 'useradd %s'" % (user, group, user)
            sys.exit(2)

    # setup() will warn about unknown parameter we already managed
    # to delete them
    deleting_args = ['--owner', '--group', '--skip-build']
    to_del = []
    for a in deleting_args:
        for av in sys.argv:
            if av.startswith(a):
                idx = sys.argv.index(av)
                print "AV,", av, "IDX", idx
                to_del.append(idx)
                # We can have --owner=shinken or --owner shinken, if so del also the
                # next one
                if '=' not in av:
                    to_del.append(idx + 1)
    to_del.sort()
    to_del.reverse()
    for idx in to_del:
        sys.argv.pop(idx)

    # Define files
    data_files, default_paths, scripts = get_default_platform_paths(install_scripts, True)

    daemonsini = []
    # get all files + under-files in etc/ except daemons folder
    for path, subdirs, files in os.walk('etc'):
        if len(files) == 0:
            data_files.append((os.path.join(default_paths['etc'], re.sub(r"^(etc\/|etc$)", "", path)), []))
        for name in files:
            if name == 'shinken.cfg':
                continue
            if 'daemons' in path:
                daemonsini.append(os.path.join(path, name))
            else:
                data_files.append((os.path.join(default_paths['etc'], re.sub(r"^(etc\/|etc$)", "", path)),
                                   [os.path.join(path, name)]))
    if os.name != 'nt':
        for _file in daemonsini:
            inifile = _file
            outname = os.path.join('build', _file)
            # force the user setting as it's not set by default
            append_file_with(inifile, outname, "modules_dir=%s\nuser=%s\ngroup=%s\n" % (
                os.path.join(default_paths['var'], 'modules'),
                user, group))
            data_files.append((os.path.join(default_paths['etc'], 'daemons'),
                               [outname]))

        # And update the shinken.cfg file for all /usr/local/shinken/var
        # value with good one
        for name in ['shinken.cfg']:
            inname = os.path.join('etc', name)
            outname = os.path.join('build', name)
            print('updating path in %s' % outname)

            # but we HAVE to set the shinken_user & shinken_group to thoses requested:
            update_file_with_string(inname, outname,
                                    ["shinken_user=\w+", "shinken_group=\w+", "workdir=.+", "lock_file=.+",
                                     "local_log=.+", "modules_dir=.+", "pack_distribution_file=.+"],
                                    ["shinken_user=%s" % user,
                                     "shinken_group=%s" % group,
                                     "workdir=%s" % default_paths['var'],
                                     "lock_file=%s/arbiterd.pid" % default_paths['run'],
                                     "local_log=%s/arbiterd.log" % default_paths['log'],
                                     "modules_dir=%s" % os.path.join(default_paths['var'], 'modules'),
                                     "pack_distribution_file=%s" % os.path.join(default_paths['var'],
                                                                                'pack_distribution.dat')],
                                    )
            data_files.append((default_paths['etc'], [outname]))

    not_allowed_options = ['--upgrade', '--update']
    for o in not_allowed_options:
        if o in sys.argv:
            sys.argv.remove(o)

    return data_files, default_paths, scripts


def check_is_update(args, opts):
    is_update = False
    if '--update' in args or opts.upgrade or '--upgrade' in args:
        if 'update' in args:
            sys.argv.remove('update')
            sys.argv.insert(1, 'install')
        if '--update' in args:
            sys.argv.remove('--update')
        if '--upgrade' in args:
            sys.argv.remove('--upgrade')

        print "Shinken Lib Updating process only"
        is_update = True
    return is_update


def check_is_package_installed():
    # Try to import shinken but not the local one. If available, we are in
    # an upgrade phase, not a classic install
    is_package_installed = False
    try:
        if '.' in sys.path:
            sys.path.remove('.')
        if os.path.abspath('.') in sys.path:
            sys.path.remove(os.path.abspath('.'))
        if '' in sys.path:
            sys.path.remove('')
        import shinken
        is_package_installed = True
        print "Previous Shinken lib detected (%s)" % shinken.__file__
    except ImportError:
        pass
    return is_package_installed


def check_are_data_files_installed(install_scripts, is_install):
    data_files, _, _ = get_default_platform_paths(install_scripts, is_install)
    for sys_path, _ in data_files:
        if not os.path.exists(sys_path):
            print "%s doesn't exist"
            return False

    return True


def get_default_platform_paths(install_scripts, is_install):
    default_paths = {}
    data_files = []
    if 'win' in sys.platform:
        default_paths = {
            'bin': install_scripts or "c:\\shinken\\bin",
            'var': "c:\\shinken\\var",
            'share': "c:\\shinken\\var\\share",
            'etc': "c:\\shinken\\etc",
            'log': "c:\\shinken\\var",
            'run': "c:\\shinken\\var",
            'libexec': "c:\\shinken\\libexec",
        }
    elif 'linux' in sys.platform or 'sunos5' in sys.platform:
        default_paths = {
            'bin': install_scripts or "/usr/bin",
            'var': "/var/lib/shinken/",
            'share': "/var/lib/shinken/share",
            'etc': "/etc/shinken",
            'run': "/var/run/shinken",
            'log': "/var/log/shinken",
            'libexec': "/var/lib/shinken/libexec",
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
        generate_default_shinken_file(default_paths)
        if is_install:
            # warning: The default file will be generated a bit later
            data_files.append(
                (os.path.join('/etc', 'default', ),
                 ['build/bin/default/shinken']
                 ))
    elif 'bsd' in sys.platform or 'dragonfly' in sys.platform:
        default_paths.update({
            'bin': install_scripts or "/usr/local/bin",
            'var': "/usr/local/libexec/shinken",
            'share': "/usr/local/share/shinken",
            'etc': "/usr/local/etc/shinken",
            'run': "/var/run/shinken",
            'log': "/var/log/shinken",
            'libexec': "/usr/local/libexec/shinken/plugins",
        })
        data_files = [
            (
                '/usr/local/etc/rc.d',
                ['bin/rc.d/shinken_arbiter',
                 'bin/rc.d/shinken_broker',
                 'bin/rc.d/shinken_receiver',
                 'bin/rc.d/shinken_poller',
                 'bin/rc.d/shinken_reactionner',
                 'bin/rc.d/shinken_scheduler',
                 ]
            )
        ]
    else:
        raise Exception("Unsupported platform, sorry")

    # Common data files
    paths = ('modules', 'doc', 'inventory', 'cli')
    for path, subdirs, files in chain.from_iterable(os.walk(patho) for patho in paths):
        for name in files:
            data_files.append((os.path.join(default_paths['var'], path), [os.path.join(path, name)]))
    for path, subdirs, files in os.walk('share'):
        for name in files:
            data_files.append((os.path.join(default_paths['share'], re.sub(r"^(share\/|share$)", "", path)),
                               [os.path.join(path, name)]))
    for path, subdirs, files in os.walk('libexec'):
        for name in files:
            data_files.append((os.path.join(default_paths['libexec'], re.sub(r"^(libexec\/|libexec$)", "", path)),
                               [os.path.join(path, name)]))
    data_files.append((default_paths['run'], []))
    data_files.append((default_paths['log'], []))

    # compute scripts
    scripts = [s for s in glob('bin/shinken*') if not s.endswith('.py')]
    # Beware to install scripts in the bin dir
    data_files.append((default_paths['bin'], scripts))

    return data_files, default_paths, scripts


def setup_package(required_pkgs, data_files):
    setup(
        name="Shinken",
        version="2.0",
        packages=find_packages(),
        package_data={'': PACKAGE_DATA},
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
        install_requires=[
            required_pkgs
        ],

        extras_require={
            'setproctitle': ['setproctitle']
        },

        data_files=data_files,
    )


def post_install(user, group, root, default_paths, scripts):
    print "Post installation actions..."
    # if root is set, it's for package, so NO chown
    if pwd and not root:
        # assume a posix system
        uid = get_uid(user)
        gid = get_gid(group)

        if uid is not None and gid is not None:
            # recursivly changing permissions for etc/shinken and var/lib/shinken
            for c in ['etc', 'run', 'log', 'var', 'libexec']:
                p = default_paths[c]
                recursive_chown(p, uid, gid, user, group)
            # Also change the rights of the shinken- scripts
            for s in scripts:
                bs = os.path.basename(s)
                recursive_chown(os.path.join(default_paths['bin'], bs), uid, gid, user, group)
                _chmodplusx(os.path.join(default_paths['bin'], bs))
            _chmodplusx(default_paths['libexec'])

        # If not exists, won't raise an error there
        _chmodplusx('/etc/init.d/shinken')
        for d in ['scheduler', 'broker', 'receiver', 'reactionner', 'poller', 'arbiter']:
            _chmodplusx('/etc/init.d/shinken-' + d)

    try:
        import pycurl
    except ImportError:
        print "Warning: missing python-pycurl lib, you MUST install it before launch the shinken daemons"

    try:
        import cherrypy
    except ImportError:
        print "Notice: for better performances for the daemons communication, " \
              "you should install the python-cherrypy3 lib"


if __name__ == '__main__':
    main()

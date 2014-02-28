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

# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...

from setuptools import setup
from setuptools import find_packages
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

user = 'shinken'
group = 'shinken'

package_data = ['*.py', 'modules/*.py', 'modules/*/*.py']

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

    print('generating %s from %s', outfile, templatefile)

    mkpath(os.path.dirname(outfile))

    bin_path = '/usr/local/bin/'
    #if self.root:
    #    bin_path = bin_path.replace(self.root.rstrip(os.path.sep), '')

    # Read the template file
    f = open(templatefile)
    buf = f.read()
    f.close
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
        print("The user %s is unknown. "
              "Maybe you should create this user"
              % user_name)
        return None
    

def get_gid(group_name):
    try:
        return grp.getgrnam(group_name)[2]
    except KeyError, exp:
        print ("The group %s is unknown. "
               "Maybe you should create this group"
               % group_name)
        return None


parser = optparse.OptionParser(
    "%prog [options]", version="%prog ")
parser.add_option('--root',
                  dest="root", metavar="ROOT",
                  help='Root dir to install, usefull only for packagers')
parser.add_option('--upgrade', '--update',
                  dest="upgrade", action='store_true',
                  help='Only upgrade')

old_error = parser.error
parser.error = lambda x:1
opts, args = parser.parse_args()
# reenable the errors for later use
parser.error = old_error

print "ARGS", args
root = opts.root or ''


# We try to see if we are in a full install or an update process
is_update = False
if 'update' in args or opts.upgrade:
    print "Shinken Lib Updating process only"
    is_update = True


is_install = False
if 'install' in args:
    is_install = True



# Define files
if 'win' in sys.platform:
    default_paths = {'var':      "c:\\shinken\\var",
                     'share':    "c:\\shinken\\var\\share",
                     'etc':      "c:\\shinken\\etc",
                     'log':      "c:\\shinken\\var",
                     'run':      "c:\\shinken\\var",
                     'libexec':  "c:\\shinken\\libexec",
                     }
    data_files = []
elif 'linux' in sys.platform or 'sunos5' in sys.platform:
    default_paths = {'var':     "/var/lib/shinken/",
                     'share':   "/var/lib/shinken/share",
                     'etc':     "/etc/shinken",
                     'run':     "/var/run/shinken",
                     'log':     "/var/log/shinken",
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

    if is_install:
        generate_default_shinken_file()
        data_files.append(
            (os.path.join('/etc', 'default',),
             ['build/bin/default/shinken']
             ))
elif 'bsd' in sys.platform or 'dragonfly' in sys.platform:
    default_paths = {'var':     "/usr/local/libexec/shinken",
                     'share':   "/usr/local/share/shinken",
                     'etc':     "/usr/local/etc/shinken",
                     'run':     "/var/run/shinken",
                     'log':     "/var/log/shinken",
                     'libexec': "/usr/local/libexec/shinken/plugins",
                     }
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
    raise "Unsupported platform, sorry"
    data_files = []

if not is_update:
    ## get all files + under-files in etc/ except daemons folder
    daemonsini = []
    for path, subdirs, files in os.walk('etc'):
        for name in files:
            if name == 'shinken.cfg':
                continue
            if 'daemons' in path:
                daemonsini.append(os.path.join(path, name))
            else:
                data_files.append( (os.path.join(default_paths['etc'], re.sub(r"^(etc\/|etc$)", "", path)), 
                                    [os.path.join(path, name)]) )

if os.name != 'nt' and not is_update:
    for _file in daemonsini:
        inifile = _file
        outname = os.path.join('build', _file)
        # force the user setting as it's not set by default
        append_file_with(inifile, outname, "modules_dir=%s\nuser=%s\ngroup=%s\n" % (
                os.path.join(default_paths['var'], 'modules'),
                user, group))
        data_files.append( (os.path.join(default_paths['etc'], 'daemons'),
                            [outname]) )

    # And update the shinken.cfg file for all /usr/local/shinken/var
    # value with good one
    for name in ['shinken.cfg']:
        inname = os.path.join('etc', name)
        outname = os.path.join('build', name)
        print('updating path in %s', outname)
        
        ## but we HAVE to set the shinken_user & shinken_group to thoses requested:
        update_file_with_string(inname, outname,
                                ["shinken_user=\w+", "shinken_group=\w+", "workdir=.+", "lock_file=.+", "local_log=.+"],
                                ["shinken_user=%s" % user,
                                 "shinken_group=%s" % group,
                                 "workdir=%s" % default_paths['var'],
                                 "lock_file=%s/arbiterd.pid" % default_paths['run'],
                                 "local_log=%s/arbiterd.log" % default_paths['log']])
        data_files.append( (default_paths['etc'], [outname]) )


# Modules, doc, inventory and cli are always installed
paths = ('modules', 'doc', 'inventory', 'cli')
for path, subdirs, files in chain.from_iterable(os.walk(patho) for patho in paths):
    for name in files:
        data_files.append( (os.path.join(default_paths['var'], path), [os.path.join(path, name)]))
	
for path, subdirs, files in os.walk('share'):
    for name in files:
        data_files.append( (os.path.join(default_paths['share'], re.sub(r"^(share\/|share$)", "", path)), 
                            [os.path.join(path, name)]) )

for path, subdirs, files in os.walk('libexec'):
    for name in files:
        data_files.append( (os.path.join(default_paths['libexec'], re.sub(r"^(libexec\/|libexec$)", "", path)), 
                            [os.path.join(path, name)]) )

data_files.append( (default_paths['run'], []) )
data_files.append( (default_paths['log'], []) )

# compute scripts
scripts = [ s for s in glob('bin/shinken*') if not s.endswith('.py')]

setup(
     name="Shinken",
    version="2.0-RC8",
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
    scripts=scripts,
    data_files = data_files
)


# if root is set, it's for pacakge, so NO chown
if pwd and not root and is_install :
    # assume a posix system
    uid = get_uid(user)
    gid = get_gid(group)
    if uid and gid:
        # recursivly changing permissions for etc/shinken and var/lib/shinken
        for c in ['etc', 'run', 'log', 'var', 'libexec']:
            p = default_paths[c]
            recursive_chown(p, uid, gid, user, group)
    for s in scripts:
        bs = os.path.basename(s)
        recursive_chown(os.path.join('/usr/local/bin/', bs), uid, gid, user, group)

    
print "Shinken setup done"

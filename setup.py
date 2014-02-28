import os
import sys
import re
import pwd
import grp

# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...

from setuptools import setup
from setuptools import find_packages
from itertools import chain
from glob import glob

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

## get all files + under-files in etc/ except daemons folder
daemonsini = []
for path, subdirs, files in os.walk('etc'):
    for name in files:
        if 'daemons' in path:
    	      daemonsini.append(os.path.join(os.path.join(default_paths['etc'], re.sub(r"^(etc\/|etc$)", "", path), name)))
    	  
        data_files.append( (os.path.join(default_paths['etc'], re.sub(r"^(etc\/|etc$)", "", path)), 
                            [os.path.join(path, name)]) )
    #if 'daemons' in path:
    	  	   
    #else:
        #for name in files:
            #print os.path.join(path, name)

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

if not '/var/lib/shinken/' in default_paths['var']:
    for file in daemonsini:
        if not 'modules_dir=' in open(file).read():
            with open(file, "a") as inifile:
                inifile.write("modules_dir=" + default_paths['var'] + "/modules")

paths = (default_paths['run'], default_paths['log'])
uid = pwd.getpwnam(user).pw_uid
gid = grp.getgrnam(group).gr_gid
for path in paths:
    os.chown(path, uid, gid)    
    
print "Shinken setup done"

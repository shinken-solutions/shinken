#!/usr/bin/python
import os

# Fix for debian 7 python that raise error on at_exit at the end of setup.py (cf http://bugs.python.org/issue15881)
try:
    import multiprocessing
except ImportError:
    pass

from shinken.bin import VERSION
os.environ['PBR_VERSION'] = VERSION


###############
# UGLY AS F***
###############
import sys
import platform
import re

arglayout = "--install-layout=deb"
if arglayout not in sys.argv and re.search("debian", platform.platform()):
    sys.argv.append(arglayout)


###############
# END UGLY
###############

import setuptools


setuptools.setup(
    setup_requires=['pbr'],
    version=VERSION,
    pbr=True,
)

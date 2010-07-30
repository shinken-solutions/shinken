#!/usr/bin/env python
# -*- coding: utf-8 -*-
#Copyright (C) 2009-2010 :
#    Gabes Jean, naparuba@gmail.com
#    Gerhard Lausser, Gerhard.Lausser@consol.de
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


#first verion of this file from Maximilien Bersoult

from setuptools import setup, find_packages
from glob import glob
import os

#We know that a Python 2.5 or Python3K will fail.
#We can say why and quit.
import platform
python_version = platform.python_version_tuple()

## Make sure people are using Python 2.5 or higher
if int(python_version[0]) == 2 and int(python_version[1]) < 6:
    print "Shinken require as a minimum Python 2.6.x, sorry"
    sys.exit(1)

if int(python_version[0]) == 3:
    print "Shinken is not yet compatible with Python3k, sorry"
    sys.exit(1)

def getscripts(path):
    script = os.path.basename(path)
    print "Script", script
    return script


setup(
  name = "Shinken",
  version = "0.1.99",
  packages = find_packages(),
  description = "Shinken is a monitoring tool compatible with Nagios configuration and plugins",
  long_description=open('README').read(),
  author = "Gabès Jean",
  author_email = "naparuba@gmail.com",
  license = "GNU Affero General Public License",
  url = "http://www.shinken-monitoring.org",
  classifiers=['Development Status :: 4 - Beta',
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
                      'pyro <= 3.10',
                      ],
 
  scripts = [getscripts(f) for f in glob('bin/[!_]*.py')],
#  entry_points = {
#      'console_scripts': [
#                          'shinken-arbiter=bin.shinken_arbiter.py:main',
#                          'shinken-broker=bin.shinken_broker:main',
#                          'shinken-poller=bin.shinken_poller:main',
#                          'shinken-reactionner=bin.shinken_reactionner:main',
#                          'shinken-scheduler=bin.shinken_scheduler:main'
#                          ]
#  },

  package_data = {'shinken': ['etc/*', 'db/*' , 'var/*', 'libexec/*', 'doc/*'] }
  
)

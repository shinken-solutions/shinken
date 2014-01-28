.. _shinken_installation_requirements:



Shinken Requirements 
---------------------


Shinken provides an "install script" which tries to manage all necessary steps to install and get Shinken up and running. 
Use it if your Operating System is compatible with it, otherwise use the Fedora RPMs or the :ref:`setup.py method <gettingstarted-quickstart-gnulinux>`. 

Get me back to the :ref:`10 minute installation guide <shinken_10min_start>`.



Mandatory Requirements 
~~~~~~~~~~~~~~~~~~~~~~~


Shinken installation prefix:

**You must use the same installation prefix on ALL your Shinken hosts.**

Shinken requires on all hosts running a Shinken daemon the *SAME* versions :

  * `Python`_ 2.4 or higher

    * Python 2.6 or higher is mandatory on the server running the built-in Web interface (WebUI)
    * Python 2.6 or higher is mandatory for using the discovery engine and configuration web interface (SkonfUI)

  * `setuptools`_ or the newer`distribute`_
  * `pyro`_ Python package

    * version 3.x for Debian Squeeze
    * version < 4.14 if running Shinken 1.0.1
    * version 3.x, 4.x and if you can 4.15 for Shinken 1.2 and newer

  * `multiprocessing`_ Needed when using Python 2.4 or 2.5 (already included in Python 2.6 and higher)
  * 
  * python-dev Python package or distribution package (ex. python-dev under Ubuntu)Core, Libs and Modules
  * build-essentials 

    * sudo apt-get install build-essential python-dev  (Installation under Linux Ubuntu/Debian)

  * `pymongo`_ >= 2.1 : for WebUI



Conditional Requirements 
~~~~~~~~~~~~~~~~~~~~~~~~~


If you plan on using the :ref:`Livestatus module <enable_livestatus_module>`, or a third party web interface, you will also need at a minimum the following Python packages:

  * `simplejson`_ (Included in Python 2.6 and higher)
  * `pysqlite`_

If you plan on using SkonfUI, NPCMOD or Canopsis

  * pycurl for SkonfUI configuration pack management
  * kombu for the Canopsis broker Module
  * MySQL_python:MySQLdb >= <version> for ndomod

If you plan on developing or testing features, you will also need at a minimum the following Python packages:

  * `nose`_
  * `unittest`_
  * git-core If you want to regularly checkout the latest code and contribute to the project. Though you can also simply download the latest from the github shinken website

if you plan on using check scripts installed by install.sh

  * paramiko (only if you use installer script)
  * netifaces (only if you use installer script)



Installing/Checking Common Requirements on Linux 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~




Python 
*******

For Python itself, the version which comes with almost all distributions should be okay. Though, if you are using a distribution with Python 2.4 or 2.5, **you should use a Python version of least 2.6 in a virtualenv**. This will avoid problems for upcoming Shinken versions that will require Python 2.6 and higher. (*This is aimed right at you, RHEL 5!*)

**You must use the same version of Python on ALL your Shinken hosts.**

You can validate your Python version with:

::

  python -c 'import sys; print sys.version[:3]'
  


Pyro 
*****

You can validate your installed Python Pyro module version using:

::

  python -c 'try:; import Pyro; except ImportError:; import Pyro4 as Pyro; print Pyro.constants.VERSION'
  
**You must use the same version of Pyro on ALL your Shinken hosts.**

Under Ubuntu, you can grab the Pyro module with:

::

  sudo apt-get install pyro
  
Under other distributions, you can search for it:

::

  yum search pyro
  
If you do not find it, or need to install a specific version, you can install it from PyPI:

::

  easy_install pyro
  
If you do not find it, or need to install a specific version, you can install it from PyPI using the following Syntax:

::

  pip install pyro4-4.15

.. _simplejson: http://pypi.python.org/pypi/simplejson/
.. _Python: http://www.python.org/download/
.. _unittest: http://pypi.python.org/pypi/unittest/
.. _distribute: http://pypi.python.org/pypi/distribute/
.. _pysqlite: http://code.google.com/p/pysqlite/
.. _pyro: http://pypi.python.org/pypi/Pyro4
.. _nose: http://pypi.python.org/pypi/nose/
.. _setuptools: http://pypi.python.org/pypi/setuptools/
.. _pymongo: http://pypi.python.org/pypi/pymongo/
.. _multiprocessing: http://pypi.python.org/pypi/multiprocessing/

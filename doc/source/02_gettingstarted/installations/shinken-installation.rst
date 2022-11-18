.. _gettingstarted/installations/shinken-installation:

=====================================
10 Minutes Shinken Installation Guide
=====================================


Summary
=======

By following this tutorial, in 10 minutes you will have the core monitoring system for your network.

The very first step is to verify that your server meets the :ref:`requirements <gettingstarted/installations/shinken-installation#requirements>`, the installation script will try to meet all requirements automatically.

You can get familiar with the :ref:`Shinken Architecture <architecture/the-shinken-architecture>` now, or after the installation. This will explain the software components and how they fit together.

  * Installation : :ref:`GNU/Linux & Unix <gettingstarted/installations/shinken-installation#gnu_linux_unix>`
  * Installation : :ref:`Windows <gettingstarted/installations/shinken-installation#windows_installation>`

Ready? Let's go!


.. _gettingstarted/installations/shinken-installation#requirements:

Requirements
============

Mandatory Requirements
----------------------

* `Python`_ 2.7, 3.4 or higher
* `pycurl`_ Python package for Shinken daemon communication
* `six`_ Python 2 and 3 compatibility library
* `bottle`_ fast and simple WSGI-framework for Python
* `cherrypy3`_ enhanceddaemons communications, especially in HTTPS mode
* `setuptools`_ or `distribute` Python package for installation


Conditional Requirements
------------------------

* `Monitoring Plugins`_ (recommended) provides a set of plugins to monitor host (Shinken uses check_icmp by default install).
  Monitoring plugins are available on most linux distributions (nagios-plugins package)


.. _gettingstarted/installations/shinken-installation#gnu_linux_unix:

.. warning::  Do not mix installation methods! If you wish to change method, use the uninstaller from the chosen method THEN install using the alternate method.


GNU/Linux & Unix Installation
=============================

Method 1: Pip
-------------

Shinken 3.0 is available on Pypi : https://pypi.python.org/pypi/Shinken/3.0
You can download the tarball and execute the setup.py or just use the pip command to install it automatically.


::

  apt-get install python-pip python-six python-pycurl python-bottle python-cherrypy3
  adduser shinken
  pip install shinken


.. notice:: Depending on your distribution, you may need to explicitly tell pip where to install the executables. For example on Ubuntu you should use ``pip install shinken --install-option="--install-scripts=/usr/local/bin"``.

Method 2: Packages
-------------------

For now the 2.4 packages are not available, but the community is working hard for it! Packages are simple, easy to update and clean.
Packages should be available on Debian/Ubuntu and Fedora/RH/CentOS soon (basically  *.deb* and  *.rpm*).


Method 3: Installation from sources
------------------------------------

Download last stable `Shinken tarball`_ archive (or get the latest `git snapshot`_) and extract it somewhere:

::

  adduser shinken
  wget http://www.shinken-monitoring.org/pub/shinken-3.0.tar.gz
  tar -xvzf shinken-3.0.tar.gz
  cd shinken-3.0
  python setup.py install

To process configuration templates (for manual deployment) and various post installation tasks, use the ``post_install`` command.

::

  python setup.py post_install

Additional command line parameters can be passed to the ``post_install`` to specify alternate pathes or values when processing the configuration templates or installing the files or directories:

* ``--confdir`` Set the configuration directory
* ``--defaultdir`` Set default/environment directory containing the files configuring the init scripts
* ``--workdir`` Set the directory where the logs and retention files are located
* ``--logdir`` Set the directory where the logs files are located
* ``--lockdir`` Set the directory where the lock files are located
* ``--modules`` Set the directory where the shinken modules should be installed
* ``--user`` Set the username the shinken services run under
* ``--group`` Set the group the shinken services run under
* ``--install-conf`` Install the configuration files from the processed templates in examples
* ``--install-default`` Install the default/environment files from the processed templates in examples
* ``--install-init`` Install the init scripts/systemd unit files from the processed templates in examples


To automatically deploy the configuration files, the default files and the init scripts/systemd unit files, use the ``--install-conf``, ``--install-default`` or ``--install-init`` options to ``post_install`` respectively.

::

  python setup.py post_install --install-conf --install-default --install-init

**Caution** this will overwrite any already existing files. Take to make backups before proceeding.

It's under the admin's responsibility to ensure the desired services start automatically.

Shinken 3.X uses LSB path. If you want to stick to one directory installation you can of course.
Default paths are the following:

 * **/etc/shinken** for configuration files
 * **/usr/local/lib/shinken/modules** for shinken modules...
 * **/usr/local/share/shinken** for shinken shared files...
 * **/usr/local/libexec/shinken/plugins** for shinken check plugins...
 * **/usr/local/share/doc/shinken** for shinken documentation...
 * **/usr/local/share/doc/shinken/examples** for shinken configuration, init scripts and default files examples...
 * **/var/lib/shinken** for shinken logs, retention files...
 * **/var/log/shinken** for log files
 * **/var/run/shinken** for pid files


.. _gettingstarted/installations/shinken-installation#windows_installation:


Windows Installation
====================

For 2.X+ the executable installer may not be provided. Consequently, installing Shinken on a Windows may be manual with setup.py.
Steps are basically the same as on Linux (Python install etc.) but in windows environment it's always a bit tricky.


.. _Python: http://www.python.org/download/
.. _cherrypy3: http://www.cherrypy.org/
.. _Monitoring Plugins: https://www.monitoring-plugins.org/
.. _pycurl: http://pycurl.sourceforge.net/
.. _six: https://pypi.org/project/six/
.. _bottle: https://bottlepy.org/docs/dev/
.. _setuptools: http://pypi.python.org/pypi/setuptools/
.. _git snapshot: https://github.com/naparuba/shinken/tarball/master
.. _Shinken tarball: http://www.shinken-monitoring.org/pub/shinken-2.4.tar.gz
.. _install.d/README: https://github.com/naparuba/shinken/blob/master/install.d/README


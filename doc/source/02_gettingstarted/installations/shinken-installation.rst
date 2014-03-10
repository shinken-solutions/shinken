.. _gettingstarted/installations/shinken-installation:

=====================================
10 Minutes Shinken Installation Guide 
=====================================


Summary 
========

By following this tutorial, in 10 minutes you will have the core monitoring system for your network.

The very first step is to verify that your server meets the :ref:`requirements <gettingstarted/installations/shinken-installation#requirements>`, the installation script will try to meet all requirements automatically.
   
You can get familiar with the :ref:`Shinken Architecture <architecture/the-shinken-architecture>` now, or after the installation. This will explain the software components and how they fit together.

  * Installation : :ref:`GNU/Linux & Unix <gettingstarted/installations/shinken-installation#gnu_linux_unix>`
  * Installation : :ref:`Windows <gettingstarted/installations/shinken-installation#windows_installation>`

Ready? Let's go!


.. _gettingstarted/installations/shinken-installation#requirements:

Requirements
=============

 * Python >= 2.6
 * Pycurl


.. _gettingstarted/installations/shinken-installation#gnu_linux_unix:

.. warning::  Do not mix installation methods! If you wish to change method, use the uninstaller from the chosen method THEN install using the alternate method.


GNU/Linux & Unix Installation 
==============================

Method 1: Pip
--------------

Shinken 2.0 is available on Pypi : https://pypi.python.org/pypi/Shinken/2.0-RC
You can donwload the tarball and execute the setup.py or just use the pip command to install it automatically.


::

  apt-get install python-pip python-pycurl
  adduser shinken
  pip install shinken


Method 2: Packages 
-------------------

For now the 2.0 packages are not available, but the community is working hard for it! Packages are simple, easy to update and clean.
Packages should be available on Debian/Ubuntu and Fedora/RH/CentOS soon (basically  *.deb* and  *.rpm*)


Method 3: Installation from sources 
------------------------------------

Download last stable `Shinken tarball`_ archive (or get the latest `git snapshot`_) and extract it somewhere:

::

  adduser shinken
  wget http://www.shinken-monitoring.org/pub/shinken-2.0.tar.gz
  tar -xvzf shinken-2.0.tar.gz
  cd shinken-2.0
  python setup.py install


Shinken 2.0 introduces LSB path. If you want to stick to one directory installation you can of course. 
Default paths are the following :

 * **/etc/shinken** for configuration files
 * **/var/lib/shinken** for shinken modules, retention files...
 * **/var/log/shinken** for log files
 * **/var/run/shinken** for pid files


.. _gettingstarted/installations/shinken-installation#windows_installation:

Windows Installation 
=====================


Download the Executable installer 
----------------------------------

CHECK_WMI_PLUS configuration 
-----------------------------


By default, check_wmi_plus.pl use an user/password to access the windows WMI functions. But locally (shinken host managed itself on windows), this cannot be done. So the local template always works even if a wrong user/password is set. In the commands file, just set local to user and localhost to the computer. 

But now, how to configure shinken to manage others windows hosts using wmi. Shinken team provides a set of commands in the windows template. We will see how to set the user/password to work properly. But there is an "extra" function to use the poller's service to push its credential to check_wmi_plus.
This kind of configuration and globaly the use of check_wmi_plus under windows is described in this :ref:`link <how-to-monitor/configure-check-wmi-plus-onwindows>`.






.. _git snapshot: https://github.com/naparuba/shinken/tarball/master
.. _Shinken tarball: http://www.shinken-monitoring.org/pub/shinken-2.0.tar.gz
.. _install.d/README: https://github.com/naparuba/shinken/blob/master/install.d/README


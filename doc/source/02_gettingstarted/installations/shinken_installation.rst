.. _shinken_installation:




=====================================
10 Minute Shinken Installation Guide 
=====================================





Summary 
--------


By following this tutorial, in 10 minutes you will have the core monitoring system for your network.

The very first step is to verify that your server meets the :ref:`requirements <shinken_installation#requirements>`, the installation script will try to meet all requirements automatically.
   
You can get familiar with the :ref:`Shinken Architecture <the_shinken_architecture>` now, or after the installation. This will explain the software components and how they fit together.


  * Installation : :ref:`GNU/Linux & Unix <shinken_installation#GNU/Linux & Unix installation>`
  * Installation : :ref:`Windows <shinken_installation#Windows installation>`

Ready? Let's go!


.. _shinken_installation#requirements:

Requirements
-------------

 * Python 2.6
 * Pycurl


.. _shinken_installation#GNU/Linux & Unix installation:

.. warning::  Do not mix installation methods! If you wish to change method, use the uninstaller from the chosen method THEN install using the alternate method.


GNU/Linux & Unix Installation 
------------------------------



Method 1: Packages 
~~~~~~~~~~~~~~~~~~~

For now the 2.0 packages are not available, but the community is working hard for it! This should always be the first way to install Shinken. Packages are simple, easy to update and clean.
Packages should be available on Debian/Ubuntu and Fedora/RH/CentOS (basically  *.deb* and  *.rpm*)


Method 2: Pip / Setup.py
~~~~~~~~~~~~~~~~~~~~~~~~~

Shinken 2.0 is available on Pypi : https://pypi.python.org/pypi/Shinken/2.0-RC
You can donwload the tarball and execute the setup.py or just use the pip command to install it automatically.


::

  pip install shinken



Method 3: Installation from sources 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


Download last stable `Shinken tarball`_ archive (or get the latest `git snapshot`_) and extract it somewhere:

::

  cd ~
  wget http://www.shinken-monitoring.org/pub/shinken-2.0.tar.gz
  tar -xvzf shinken-2.0.tar.gz


Shinken 2.0 introduces LSB path. If you want to stick to one directory installation you can of course. 
Default paths are the following :

 * **/etc/shinken** for configuration files
 * **/var/lib/shinken** for shinken modules, retention files...
 * **/var/log/shinken** for log files
 * **/var/run/shinken** for pid files


.. _shinken_installation#Windows installation:

Windows Installation 
---------------------




Packaged .EXE Installer 
~~~~~~~~~~~~~~~~~~~~~~~~

.. note:: For now the 2.0 exe installer is not available. We hope to get it soon


Download the Executable installer 
**********************************


Download the `executable installer for Shinken 2.0`_.

Thanks to J-F BUTKIEWICZ for preparing the installation package.



Read the installation instructions 
***********************************


Installation instructions at http://www.veosoft.net/index.php/en/tutorials/shinken-tutorials/shinken-1-2-4-installation-on-windows-2008-r2



Run the installer 
******************


What? You don't want to read them? No problem.

Simply launch the .exe and click Next until the installation has run its course. :-)

The executable installer creates service and copies the necessary files into C:/Program Files (x86)/Shinken by default, but you can change that target folder as you want.



CHECK_WMI_PLUS configuration 
*****************************


By default, check_wmi_plus.pl use an user/password to access the windows WMI functions. But locally (shinken host managed itself on windows), this cannot be done. So the local template always works even if a wrong user/password is set. In the commands file, just set local to user and localhost to the computer. 

But now, how to configure shinken to manage others windows hosts using wmi. Shinken team provides a set of commands in the windows template. We will see how to set the user/password to work properly. But there is an "extra" function to use the poller's service to push its credential to check_wmi_plus.
This kind of configuration and globaly the use of check_wmi_plus under windows is described in this :ref:`link <Configure_check_wmi_plus_onwindows>`.






.. _git snapshot: https://github.com/naparuba/shinken/tarball/master
.. _Shinken tarball: http://www.shinken-monitoring.org/pub/shinken-2.0.tar.gz
.. _install.d/README: https://github.com/naparuba/shinken/blob/master/install.d/README
.. _executable installer for Shinken 2.0: http://www.veosoft.net/index.php/en/component/phocadownload/category/1-binary-packages?download=6:shinken-2-0

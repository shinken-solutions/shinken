.. _shinken_10min_start:




=====================================
10 Minute Shinken Installation Guide 
=====================================





Summary 
--------


By following this tutorial, in 10 minutes you will have the core monitoring system for your network.

The very first step is to verify that your server meets the :ref:`requirements <shinken installation requirements>`, the installation script will try to meet all requirements automatically.
   
You can get familiar with the :ref:`Shinken Architecture <the_shinken_architecture>` now, or after the installation. This will explain the software components and how they fit together.


  * Installation : :ref:`GNU/Linux & Unix <shinken_10min_start#GNU/Linux & Unix installation>`
  * Installation : :ref:`Windows <shinken_10min_start#Windows installation>`
  * Post-Installation : :ref:`Common <shinken_10min_start#Post installation>`

Ready? Let's go!


.. _shinken_10min_start#GNU/Linux & Unix installation:

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




Shinken Configuration
~~~~~~~~~~~~~~~~~~~~~~

Enable Shinken
***************

If you did not use the packages, you will have to manually add Shinken init script and enable them at boot. Depending on you Linux distribution (actually it's realted to the init mechanism : upstart, systemd, sysv ..) you may exec one of the following:

::

  for i in arbiter poller reactionner scheduler broker; do
  systemctl enable shinken-$i.service;
  done


::
  
  for i in arbiter poller reactionner scheduler broker; do
  chkconfig shinken-$i on
  done



.. _shinken_10min_start#Start Shinken:

Start Shinken 
**************

Depending on your OS you can start Shinken with one of the following:

::

  /etc/init.d/shinken start
  service shinken start
  systemctl start shinken  

If you did not enable shinken but still want to launch shinken you have to do it manually:

::

   ./bin/shinken-scheduler -c /etc/shinken/daemons/schedulerd.ini -d
   ./bin/shinken-poller -c /etc/shinken/daemons/pollerd.ini -d
   ./bin/shinken-broker -c /etc/shinken/daemons/brokerd.ini -d
   ./bin/shinken-reactionner -c /etc/shinken/daemons/reactionnerd.ini -d
   ./bin/shinken-arbiter -c /etc/shinken/shinken.cfg -d




.. _shinken_10min_start#Windows installation:

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




.. _shinken_10min_start#Post installation:

Post installation 
------------------




Where is the configuration? 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~


The configuration is where you put the ``etc`` directory. Usually it's ``/etc/shinken``, ``/usr/local/shinken/etc`` or ``C:/Program Files/Shinken``.
  * ``nagios.cfg`` is meant to be fully compatible with Nagios;
  * ``shinken-specific.cfg`` contains all Shinken specific objects (ie. daemons, realms, etc.).



Do I need to change my Nagios configuration? 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


No, there is no need to change your existing Nagios configuration.
You can use an existing Nagios configuration as-is, as long as you have installed the plugins expected by the configuration.

Once you are comfortable with Shinken you can start to use its unique and powerful features.



What do I need to do next 
~~~~~~~~~~~~~~~~~~~~~~~~~~


The next logical steps for a new user are as listed in the :ref:`Getting Started <start>` page: 

* Setup the web interface:

  * Use the :ref:`default WebUI <use_with_webui>` (Note: it's the mandatory interface on Windows)
  * Or set-up a :ref:`third-party web interface <use_shinken_with>` and addons.

* Did you read the :ref:`Shinken Architecture <the_shinken_architecture>` presentation?
* Complete the :ref:`Shinken basic installation <configure_shinken>`
* Start adding devices to monitor, such as:

  * :ref:`Public services <monitoring_a_network_service>` (HTTP, SMTP, IMAP, SSH, etc.)
  * :ref:`GNU/Linux <monitoring_a_linux>` clients
  * :ref:`Windows <monitoring_a_windows>` clients
  * :ref:`Routers <monitoring_a_router_or_switch>`
  * :ref:`Printers <monitoring_a_printer>`



Getting Help 
~~~~~~~~~~~~~


New and experienced users sometimes need to find documentation, troubleshooting tips, a place to chat, etc. The :ref:`Shinken community provides many resources to help you <how_to_contribute#Shinken resources for users>`. You can discuss installation documentation changes in the Shinken forums.



.. _git snapshot: https://github.com/naparuba/shinken/tarball/master
.. _Shinken tarball: http://www.shinken-monitoring.org/pub/shinken-2.0.tar.gz
.. _install.d/README: https://github.com/naparuba/shinken/blob/master/install.d/README
.. _executable installer for Shinken 2.0: http://www.veosoft.net/index.php/en/component/phocadownload/category/1-binary-packages?download=6:shinken-2-0

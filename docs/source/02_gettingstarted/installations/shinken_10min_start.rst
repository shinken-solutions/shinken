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

GNU/Linux & Unix Installation 
------------------------------



Method 1: Installation Script 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. warning::  Do not mix installation methods! If you wish to change method, use the uninstaller from the chosen method THEN install using the alternate method.

The ``install`` script is located at the root of the Shinken sources. It creates the user and group, installs all dependencies and then installs Shinken. It is compatible with Debian, Ubuntu, Centos/RedHat 5.x and 6.x. The only requirement is an internet connection for the server on which you want to install Shinken.



Basic automated installation 
*****************************

You can get the sources and launch the install script with just this command :


::

  curl -L http://install.shinken-monitoring.org | /bin/bash
  
You can then jump to the ":ref:`Start Shinken <shinken_10min_start#Start Shinken>`" section and continue from there.

If instead want to make it manually, go in the next step :)



Installation using the sources 
*******************************


Download stable `Shinken v1.4 tarball`_ archive (or get the latest `git snapshot`_) and extract it somewhere:

::

  cd ~
  wget http://www.shinken-monitoring.org/pub/shinken-1.4.tar.gz
  tar -xvzf shinken-1.4.tar.gz


By default the installation path is ``/usr/local/shinken``, but it can be specified in the configuration file (see `install.d/README`_).



Run a basic installation 
*************************

*You need to have lsb-release package installed.*

::

  cd ~/shinken-1.4
  ./install -i

Done! Shinken is installed and you can edit its configuration files in ``/usr/local/shinken/etc`` (by default).

Init.d scripts are also copied, so you just have to enable them at boot time (with ``chkconfig`` or ``update-rc.d``).



.. _shinken_10min_start#Start Shinken:

Start Shinken 
**************

To start Shinken:

::

  /etc/init.d/shinken start
  
But wait! The installation script can do much more for you, such as installing plugins, addons, upgrading and removing an installation. See the `install.d/README`_ file or :ref:`full install script doc <install_script>` to know how you can get the best out of it.



Run a full installation 
************************


To list the plugins and addons available:

::

  ./install -h
  
A common and fully featured installation is:


::

  ./install -i &&\
  ./install -p nagios-plugins &&\
  ./install -p check_mem &&\
  ./install -p manubulon &&\
  ./install -a multisite &&\
  ./install -a pnp4nagios &&\
  ./install -a nagvis &&\
  ./install -a mongodb


This will automatically install:
  * Shinken
  * Nagios plugins
  * Manubulon SNMP plugins
  * Multisite
  * PNP4Nagios
  * Nagvis
  * MongoDB  # This is used for the SkonfUI beta and WebUI

.. tip::  
     If you encounter problems installing Multisite, it may be because the latest stable version on Check_MK's website has changed. Simply change the MK version in ``install.d/shinken.conf`` to the latest stable version: ``export MKVER="1.2.0p3"``
     
  
For more information regarding the install script. See the :ref:`full install script doc <install_script>`
  


Update 
*******

  
See :ref:`update Shinken <update>`.
  
  


Method 2: On Fedora with RPM 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. warning::  Shinken is an official RPM
  


First install Python Pyro 
**************************

::

    yum install python-pyro




Then install Shinken 
*********************



::

  yum install shinken  shinken-poller\
  shinken-scheduler shinken-arbiter \
  shinken-reactionner shinken-broker shinken-receiver




Enable Shinken services 
************************


::

  for i in arbiter poller reactionner scheduler broker; do
  systemctl enable shinken-$i.service;
  done



Start Shinken services 
***********************


::

  for i in arbiter poller reactionner scheduler broker; do
  systemctl start shinken-$i.service;
  done



Stop Shinken services 
**********************


::

  for i in arbiter poller reactionner scheduler broker; do
  systemctl stop shinken-$i.service;
  done

Easy is not it?


Windows Installation 
---------------------




Method 1: Packaged .EXE Installer 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~




Download the Executable installer 
**********************************


Download the `executable installer for Shinken 1.4`_.

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
.. _Shinken v1.4 tarball: http://shinken-monitoring.org/pub/shinken-1.4.tar.gz
.. _install.d/README: https://github.com/naparuba/shinken/blob/master/install.d/README
.. _executable installer for Shinken 1.4: http://www.veosoft.net/index.php/en/component/phocadownload/category/1-binary-packages?download=6:shinken-1-4

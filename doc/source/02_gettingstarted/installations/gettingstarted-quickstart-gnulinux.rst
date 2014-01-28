.. _gettingstarted-quickstart-gnulinux:





===================================
GNU/Linux Installation from Source 
===================================




Abstract 
~~~~~~~~~

This guide is intended to provide you with simple instructions on how to install Shinken from source (code) on GNU/Linux and have it monitoring in no time. This the basic Shinken installation primarily meant for **packagers**.




Automated installation 
~~~~~~~~~~~~~~~~~~~~~~~


Installation should be done using the :ref:`Shinken 10 minute installation <shinken_10min_start>`
  * Installs Shinken
  * Installs common checks scripts
  * Installs core related optional modules
  * Uses an **installation script** that will fetch all dependancies
  * Internet access required

Find it at :ref:`Shinken 10 minute installation <shinken_10min_start>`.




Manual installation process for packagers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


If you wish to install Shinken using the standalone setup.py installation method. Read on.

Operating system used for this walk through : Ubuntu Server edition 10.04 LTS




Requirements 
*************


Check the :ref:`Shinken Requirements <shinken_installation_requirements>`.

Make sure you've installed the required packages before continuing!




Create Shinken Account 
***********************


Become the root user.

::

  linux:~ $ sudo su -
  
Create a new shinken user account and give it a password.

::

  linux:~ # /usr/sbin/useradd -m shinken
  linux:~ # passwd shinken
  
On Ubuntu server edition (9.10 and newer versions), you will also need to add a shinken group (it's not created by default). You should be able to skip this step on desktop editions of Ubuntu.

::

  linux:~ # /usr/sbin/groupadd shinken
  linux:~ # /usr/sbin/usermod -G shinken shinken
  
Add the apache user to this group to allow external commands to be send from the web interface.

::

  linux:~ # /usr/sbin/usermod -G shinken www-data
  


Download Shinken and the Plugins 
*********************************


Create a directory for storing the downloads.

::

  linux:~ # mkdir ~/downloads
  linux:~ # cd ~/downloads
  
Download the source code of Shinken and the Shinken plugins (visit http://www.nagios.org/download/ for links to the latest versions of the plugins). At the time of writing, the latest versions plugins were 1.4.13. 

::

  linux:~ # git clone git://shinken.git.sourceforge.net/gitroot/shinken/shinken
  
or
  
Get the latest official release: https://github.com/naparuba/shinken/tarball/1.0.1
  


Install Shinken 
~~~~~~~~~~~~~~~~


::

  linux:~ # cd shinken
  linux:~ # sudo python setup.py install --install-scripts=/usr/bin
  
Don't start Shinken yet - there's still more that needs to be done...



Customize the configuration 
****************************


Sample :ref:`configuration files <configuringshinken-config>` have now been installed in the "/etc/shinken/" directory. These sample files should work fine for getting started with Shinken. You'll need to make just one change before you proceed.



Install the Nagios Plugins to use with Shinken 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


You can download plugins from source, but your debian-like administrator will just will you :

::

  linux:~ # sudo apt-get install nagios-plugins
  


Start Shinken 
~~~~~~~~~~~~~~


Configure Shinken to automatically start when the system boots.

::

  linux:~ # sudo ln -s /etc/init.d/shinken-scheduler /etc/rcS.d/S98shinken-scheduler
  linux:~ # sudo ln -s /etc/init.d/shinken-poller /etc/rcS.d/S98shinken-poller
  linux:~ # sudo ln -s /etc/init.d/shinken-reactionner /etc/rcS.d/S98shinken-reactionner
  linux:~ # sudo ln -s /etc/init.d/shinken-broker /etc/rcS.d/S98shinken-broker
  linux:~ # sudo ln -s /etc/init.d/shinken-arbiter /etc/rcS.d/S98shinken-arbiter
  
Verify the sample Shinken configuration files.

::

  linux:~ # /usr/bin/shinken-arbiter -v -c /etc/shinken/nagios.cfg -c /etc/shinken/shinken-specific.cfg
  
If there are no errors, start Shinken.

::

  linux:~ # sudo /etc/init.d/shinken-scheduler start
  linux:~ # sudo /etc/init.d/shinken-poller start
  linux:~ # sudo /etc/init.d/shinken-broker start
  linux:~ # sudo /etc/init.d/shinken-reactionner start
  linux:~ # sudo /etc/init.d/shinken-arbiter start




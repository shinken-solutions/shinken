.. _alternatives_installs:



Alternatives installations 
===========================

Here you can find another way to install Shinken without using shinken.sh . If you want to understand deeply how Shinken work, it may be a better solution.


.. note::  Article under creation, it will me deeply modified before the 1.0 release ;)



Installation 
-------------




On Ubuntu or Debian 
~~~~~~~~~~~~~~~~~~~~



Save time, use the very good installation script from `Nicolargo`_! Thanks a lot to him :)

::

  cd ~
  wget https://raw.github.com/nicolargo/shinkenautoinstall/master/shinkenautoinstall-debian.sh
  chmod a+x shinkenautoinstall-debian.sh
  sudo ./shinkenautoinstall-debian.sh
  
  


On windows 
~~~~~~~~~~~

Get the http://shinken-monitoring.org/pub/shinken-0.8.1.tar.gz file in c:\shinken

During portions of the installation you'll need to have administrator access to your server.
Make sure you've installed the following packages on your Windows installation before continuing.

  * `Python 2.7 for Windows`_
  * `Pyro 4 library Windows`_
  * `Windows Resource Kit`_
  * `PyWin32`_

Take the files instsrv.exe and srvany.exe from the directory of the resource kit (typically "c:\program files\Windows Resource Kits\Tools") and put them in the directory "c:\shinken\windows" (it should already exist by decompressing the archive, or you are a directory level to deep).

To install all services, launch the installation batch file:

::

  c:\shinken\windows\install-all.bat
  
Launch services.msc to see you brand new services (Shinken-*).

But don't start them yet, you should jump up to the discovery part before starting new Shinken services.



On Fedora with RPM 
~~~~~~~~~~~~~~~~~~~

Prerequisites:

Install python Pyro: 

::

  # yum install python-pyro


Install Shinken:

Download RPM to the url http://hvad.fedorapeople.org/fedora/shinken/RPM/

::

  # yum localinstall --nogpgcheck shinken-0.8.1-1.fc15.noarch.rpm shinken-arbiter-0.8.1-1.fc15.noarch.rpm shinken-broker-0.8.1-1.fc15.noarch.rpm shinken-poller-0.8.1-1.fc15.noarch.rpm shinken-reactionner-0.8.1-1.fc15.noarch.rpm shinken-receiver-0.8.1-1.fc15.noarch.rpm shinken-scheduler-0.8.1-1.fc15.noarch.rpm


Enable Shinken services:

::

  # for i in arbiter poller reactionner scheduler broker; do systemctl enable shinken-$i.service ; done    


Start Shinken services:

::

  # for i in arbiter poller reactionner scheduler broker; do systemctl start shinken-$i.service ; done    


Stop Shinken services:

::

  # for i in arbiter poller reactionner scheduler broker; do systemctl stop shinken-$i.service ; done 




On Debian with DEB packages 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Shinken is packaged on the debian "sid":
Prerequisites:

::

  aptitude install shinken python-simplejson python-pysqlite2 python-mysqldb python-redis python-memcache


Start Shinken services:

::

  # for i in  broker poller reactionner receiver scheduler arbiter ; do /etc/init.d/shinken-$i start ;done


Stop Shinken services:

::

  for i in  broker poller reactionner receiver scheduler arbiter ; do /etc/init.d/shinken-$i stop ;done





On RedHat/Centos and other GNU/Linux box: from the sources 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


Shinken asks for few dependencies:
  * Python >= 2.4 (but Python 2.6 is preferable) 
  * Pyro, a Python module (version >= 4.5 is possible)

To know which Python version you are running, just type 

::

  python -V
  


Dependencies for Debian folks 
******************************

To get Dependencies launch:

::

  sudo apt-get install pyro nagios-plugins-extra




Dependencies for Centos5/RH5 with python 2.4
********************************************

.. important::   Python version 2.4 is the default version of python on CentOS/RH5, so this is the easiest way to install Shinken on CentOS. The problem is that some advanced Shinken functionalities need ''at least'' python 2.6

First get the dependencies  (as root or with sudo):

::

  yum install gcc nagios-plugins python-devel python-simplejson
  wget http://pypi.python.org/packages/source/P/Pyro/Pyro-3.10.tar.gz#md5=7fc6b8b939073d4adb0e8939c59aaf1e
  tar xvfz Pyro-3.10.tar.gz
  cd Pyro-3.10
  python setup.py install
  
  cd ~
  
  wget http://pypi.python.org/packages/2.4/s/setuptools/setuptools-0.6c11-py2.4.egg#md5=bd639f9b0eac4c42497034dec2ec0c2b
  sh setuptools-0.6c11-py2.4.egg
  
  cd ~
  
  wget http://pypi.python.org/packages/source/m/multiprocessing/multiprocessing-2.6.2.1.tar.gz#md5=5cc484396c040102116ccc2355379c72
  tar xvfz multiprocessing-2.6.2.1.tar.gz
  cd multiprocessing-2.6.2.1/
  python setup.py install




Dependencies for Centos5/RH5 with python 2.6
********************************************

.. important::   Python version 2.4 is the default version on CentOS5/RH5. This version of python is deeply linked to the OS (yum package manager for instance), so you can't just ''update'' python. In order to add python 2.6 on your system, you will need to add packages from at least 2 additional repositories: '''RPMForge''' and '''EPEL release'''

First, add the additional repositories

::

   wget http://apt.sw.be/redhat/el5/en/i386/rpmforge/RPMS/rpmforge-release-0.5.2-2.el5.rf.i386.rpm
   rpm -Uvh rpmforge-release-0.5.2-2.el5.rf.i386.rpm
   wget http://download.fedora.redhat.com/pub/epel/5/i386/epel-release-5-4.noarch.rpm
   rpm -Uvh epel-release-5-4.noarch.rpm
  
  
Then install the dependencies

::

   yum install gcc nagios-plugins python26-devel python26-simplejson
   wget http://pypi.python.org/packages/source/P/Pyro4/Pyro4-4.11.tar.gz#md5=8126e7049206b7b09f324750f50cee2d
   tar xvfz Pyro4-4.11.tar.gz
   cd Pyro4-4.11
   python26 setup.py install
     
   cd ~
   wget http://pypi.python.org/packages/2.6/s/setuptools/setuptools-0.6c11-py2.6.egg#md5=bfa92100bd772d5a213eedd356d64086
   sh setuptools-0.6c11-py2.6.egg
  
  


Shinken installation 
---------------------

Create the Shinken user:

::

  sudo adduser shinken
  sudo passwd shinken


.. important::   Be sure to create a valid home directory for the shinken user. If not, the daemons won't start. 

Then, get Shinken package and install it:

::

  cd ~
  wget http://www.shinken-monitoring.org/pub/shinken-0.8.1.tar.gz
  tar xfz shinken-0.8.1.tar.gz
  cd shinken-0.8.1
  sudo python setup.py install --install-scripts=/usr/bin
  sudo mkdir -p /usr/lib/nagios/plugins/
  sudo cp libexec/* /usr/lib/nagios/plugins/
  
.. important::  Replace ''python26'' instead of ''python'' in the command line "sudo python setup.py install --install-scripts=/usr/bin" if you run CentOS5/RH5 and you wish shinken to be installed with python 2.6 support
  
You will get:

::

  new binaries into /usr/bin (files shinken-*)
  some new checks and notification scripts in /usr/lib/nagios/plugins/
  some new directory (/etc/shinken and /var/lib/shinken).
  


Discover your network 
----------------------

The network discovery scans your network and sets up a standardized monitoring configuration for all your hosts and network services. To run it, ou need to install the nmap network discovery tool.

Ubuntu:

::

  sudo apt-get install nmap

RedHat/Centos:

::

  yum install nmap
  
Now, you are ready to run the network discovery tool:

::

  [ -d /etc/shinken/discovery ] && sudo mkdir /etc/shinken/discovery
  sudo shinken-discovery -o /etc/shinken/discovery -r nmap -m "NMAPTARGETS=192.168.0.1-254 localhost"
  
The important part is the NMAPTARGETS value. It's an nmap target value, so you can give the value you want, like a list of hosts or an IP range.

.. note::   The scan duration depends on the number of IP addresses to scan. If you are scanning a large network, the scan can run into the tens of minutes.
   (the scan timeout is set to one hour by default. The timeout parameter is defined in the etc/discovery.cfg)



Setup Thruk, the Web interface 
-------------------------------

This next section will use the `Nicolargo`_ installation script, thank you once again.

If you have already run the Nicolargo script for Debian, you can skip this part.

To install Thruk, launch:

::

  perl -V:version -V:archname
  browse to http://www.thruk.org/files/  and download the file that matches the archname and version 
  ( version is last number before tar.gz)
  tar zxvf *filename*
  cd Thruk-$thruk_version
  wget https://raw.github.com/nicolargo/shinkenautoinstall/master/thruk_local.conf
  cd ..
  cp -R Thruk-1.0.5 /opt/thruk
  chown -R shinken:shinken /opt/thruk
  wget -O /etc/init.d/thruk https://raw.github.com/nicolargo/shinkenautoinstall/master/thruk
  chown root:root /etc/init.d/thruk
  chmod a+rx /etc/init.d/thruk

For Ubuntu/Debian:

::

  update-rc.d thruk defaults

For RedHat/Centos:

::

  chkconfig thruk --add
  


First launch 
-------------


You are now ready to start the system, launch Shinken and Thruk.

::

  /etc/init.d/shinken start
  /etc/init.d/thruk start


You can validate that the software is running smoothly by *tailing* the main log file at:

::

  tail -f /var/lib/shinken/shinken.log


And by connecting to the web interface at `http://localhost:3000`_ (or use the IP address of your server)

Congrats, you just launched your next monitoring tool ^_^

Now you can go through the rest of the wiki to learn how to work with the configuration, and customize it as you need. There are tutorials in the getting started section for common tasks and there is an official documentation manual that provides in depth coverage of features and options.

Now are ready to learn how to configure the Shinken daemons, your gentle introduction to distributed monitoring, by reading the :ref:`configure Shinken <configure_shinken>` page.

.. _PyWin32: http://sourceforge.net/projects/pywin32/files/pywin32/
.. _Windows Resource Kit: http://www.microsoft.com/downloads/details.aspx?FamilyID=9D467A69-57FF-4AE7-96EE-B18C4790CFFD
.. _Pyro 4 library Windows: http://pypi.python.org/pypi/Pyro4/
.. _Python 2.7 for Windows: http://www.python.org/download/
.. _Nicolargo: http://blog.nicolargo.com/2011/04/script-dinstallation-automatique-de-shinkenthruk.html?utm_source=twitterfeed&utm_medium=twitter
.. _http://localhost:3000: http://localhost:3000

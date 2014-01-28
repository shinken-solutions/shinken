.. _gettingstarted-quickstart-nokia:



=====================
Nokia N900 Quickstart 
=====================


This guide is intended to provide you with simple instructions on how to install Shinken from source (code) on a Nokia N900.

A Shinken how-to provides details on a new installation method using an install.sh script.

If you were really looking to install it on a GNU/Linux platform or Windows follow the :ref:`Shinken 10 minute installation guide. <shinken_10min_start>`.

If you really wish to install Shinken on a Nokia N900, Read On!



Required Packages 
=================


- Python >= 2.4 
- Pyro (Python module for distributed objects)
- Git (If you want the latest code)



About Nokia N900 
================


The smartphone Nokia N900 runs natively under the Maemo Operating System (which includes python 2.5.4). You can find more information about it at :
http://maemo.org/intro/ and http://maemo.nokia.com/

.. tip::
   You will need an internet connection to continu, don't forget to take care of your 3G data quota!  
   It's easier to do it via ssh.
   And you will need of a tool like gainroot or rootsh to complete the following steps.

Create users :

::
 
  Nokia-N900:~$ root
  Nokia-N900:~#
  Nokia-N900:~# useradd -m shinken
  Nokia-N900:~# groupadd shinken
  Nokia-N900:~# usermod -G shinken shinken


Then add theses two new repository at the end of /etc/apt/sources.list.d/hildon-application-manager.list :

::

  deb http://repository.maemo.org/ fremantle/sdk free non-free
  deb http://repository.maemo.org/ fremantle/tools free non-free


Next, install python an pyro :

::

  Nokia-N900:~# aptitude update
  Nokia-N900:~# aptitude install python-dev python-setuptools build-essential
  Nokia-N900:~# easy_install http://www.xs4all.nl/~irmen/pyro3/download/Pyro-3.10.tar.gz


Now, we can install shinken, we use MyDocs because it's the mount point of the ssd drive :

::

  Nokia-N900:~# cd /home/user/MyDocs/ && mkdir tmp && cd tmp
  Nokia-N900:/home/user/MyDocs/tmp/# wget http://shinken-monitoring.org/pub/shinken-0.5.1.tar.gz
  Nokia-N900:/home/user/MyDocs/tmp/# tar zxf shinken-0.5.1.tar.gz
  Nokia-N900:/home/user/MyDocs/tmp/# cd shinken-0.5.1
  Nokia-N900:/home/user/MyDocs/tmp/shinken-0.5.1# python setup.py install --install-scripts=/usr/bin/
  Nokia-N900:/home/user/MyDocs/tmp/shinken-0.5.1# cp -af bin/* /usr/bin/
  Nokia-N900:/home/user/MyDocs/tmp/shinken-0.5.1# sync && cd


You can test an see what happen :

::

  Nokia-N900:~# launch_all.sh
  Nokia-N900:~# ps aux | grep python


That's all! But for installation only! You need now to configure shinken.

.. important::  And don't forget to take care of your 3G data quota!!

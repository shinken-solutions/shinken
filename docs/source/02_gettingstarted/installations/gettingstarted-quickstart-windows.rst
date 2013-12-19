.. _gettingstarted-quickstart-windows:




====================
 Windows Quickstart 
====================




Abstract 
~~~~~~~~~


This guide is intended to provide you with simple instructions on how to install Shinken on windows and have it monitoring your local machine inside of 10 minutes. No advanced installation options are discussed here - just the basics that will work for 95% of users who want to get started.

These instructions were written based on a standard Windows (tested on 2k3, 2k8, XP and Seven).



Automated installation 
~~~~~~~~~~~~~~~~~~~~~~~


Installation should be done using the :ref:`Shinken 10 minute installation <shinken_10min_start>`
  * Installs Shinken
  * Installs common checks scripts
  * Installs core related optional modules
  * Uses an **installation script** that will fetch all dependancies
  * Internet access required

Read on to find out how to install Shinken manually.



Batch file manual installation process 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


Get the https://github.com/naparuba/shinken/zipball/1.2 file to c:\shinken

During portions of the installation you will need to have administrator privileges to your server.
Make sure you have installed the following packages on your Windows installation before continuing.

  * `Python 2.7 for Windows`_
  * `easy_install`_

    * add easy_install to your windows PATH as per setup tools instructions in link above
    * ``easy_install pip``

  * `Pyro 4 library Windows`_

    * ``pip pyro4=4.14``

  * `Windows server 2003 Resource Kit`_
  * `PyWin32`_

Take the files instsrv.exe and srvany.exe from the directory of the resource kit (typically "c:\program files\Windows Resource Kits\Tools") and put them in the directory "c:\shinken\windows" (it should already exist by decompressing the archive, or you are a directory level to deep).

To install all services, launch the installation batch file:

::

  c:\shinken\windows\install-all.bat
  
Launch services.msc to see your brand new services (Shinken-*).




You're Done 
~~~~~~~~~~~~


Congratulations! You sucessfully installed Shinken. Your journey into monitoring is just beginning. You'll no doubt want to monitor more than just your local machine, so check out the following docs...

  * :ref:`Monitoring Windows machines <gettingstarted-monitoring-windows>`
  * :ref:`Monitoring Linux/Unix machines <gettingstarted-monitoring-linux>`
  * :ref:`Monitoring Netware servers <gettingstarted-monitoring-netware>`
  * :ref:`Monitoring routers/switches <gettingstarted-monitoring-routers>`
  * :ref:`Monitoring publicly available services ("HTTP", "FTP", "SSH", etc.) <gettingstarted-monitoring-publicservices>`

You can also follow the instructions on setting up the new monitoring template based method of monitoring your systems.



  

.. _easy_install: http://pypi.python.org/pypi/setuptools/#windows
.. _PyWin32: http://sourceforge.net/projects/pywin32/files/pywin32/
.. _Pyro 4 library Windows: http://pypi.python.org/pypi/Pyro4/
.. _Python 2.7 for Windows: http://www.python.org/download/
.. _Windows server 2003 Resource Kit: http://www.microsoft.com/downloads/details.aspx?FamilyID=9D467A69-57FF-4AE7-96EE-B18C4790CFFD

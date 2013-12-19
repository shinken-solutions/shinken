.. _windows:



Monitoring Windows Devices
==========================


**Abstract**

This document describes how you can monitor devices running Microsoft Windows using a predefined template. This template can address:

  * Memory usage
  * CPU load
  * Disk usage
  * Service states
  * Running processes
  * Event logs (Application or system)
  * etc.



Introduction 
-------------


Publicly available services that are provided by Windows machines ("HTTP", "FTP", "POP3", etc.) can be monitored by following the documentation on :ref:`Monitoring publicly available services (HTTP, FTP, SSH, etc.) <network_service>`.

The instructions assume that you've installed Shinken according to the :ref:`Installation tutorial <shinken 10min start >`. The sample configuration entries below reference objects that are defined in the sample config files ("commands.cfg", "templates.cfg", etc.) that were installed.



Overview 
---------


Monitoring a windows device is possible using two different methods:
  * Agent based: by installing software installed on the server, such as NSClient++
  * Agentless: by polling directly Windows via the network using the WMI protocol

This document focuses on the agentless method. The agent based method is described in :ref:`windows monitoring with nsclient++` <windows monitoring with nsclient++>.



Prerequisites 
--------------


Have a valid account on the Microsoft Windows device (local or domain account) you will monitor using WMI queries.



Steps 
------


There are several steps you'll need to follow in order to monitor a Microsoft Windows device.

  - Install check_wmi_plus plugin on the server running your poller daemons
  - Setup an account on the monitored windows server for the WMI queries
  - Declare your windows host in the configuration
  - Restart the Shinken Arbiter



What's Already Been Done For You 
---------------------------------


To make your life a bit easier, configuration templates are provided as a starting point:

  * A selection of **check_windows** based command definitions have been added to the "commands.cfg" file. This allows you to use the **check_wmi_plus** plugin.
  * A Windows host template (called "windows") is included the "templates.cfg" file. This allows you to add new Windows host definitions in a simple manner.

The above-mentioned config files can be found in the ///usr/local/shinken/etc/packs/os/windows// directory. You can modify the definitions in these and other templates to suit your needs. However, wait until you're more familiar with Shinken before doing so. For the time being, just follow the directions outlined below and you will be monitoring your Windows devices in no time.


Setup the check_wmi_plus plugin 
--------------------------------


The plugin used for windows agent less monitoring is check_wmi_plus. To install it, just launch as root on your shinken server:
  
::

  
  ./install -p check_wmi_plus

(install is an executable script in the shinken base directory, previously known as shinken.sh)




Setup a windows account for WMI queries 
----------------------------------------


TODO: write on using less than server admin

You need to configure your user account int the /etc/shinken/resources.cfg file or the c:\shinken\etc\resource.cfg file under windows with the one you just configured:
  
::

  
  $DOMAINUSER$=shinken_user
  $DOMAINPASSWORD$=superpassword



.. tip::  You can also consult the Nagios documentation which provides a very helpful write up on setting up the domain account and assigning permissions. `Monitoring_Windows_Using_WMI.pdf`_






Declare your host in Shinken 
-----------------------------


Now it's time to define some :ref:`object definitions <configuringshinken-objectdefinitions>` in your Shinken configuration files in order to monitor the new Windows device.

We will assume that your server is named *srv-win-1*. Replace this with the real hostname of your server.

You can add the new **host** definition in an existing configuration file, but it is good practice to have one file per host, it will be easier to manage in the future. So create a file with the name of your server.

Under Linux:
  
::

  
  
::

  linux:~ # vi /etc/shinken/hosts/srv-win-1.cfg
  
Or Windows:
  
::

  
  
::

  c:\ wordpad   c:\shinken\etc\hosts\srv-win-1.cfg
  
  
You need to add a new :ref:`host <configuringshinken-objectdefinitions#configuringshinken-objectdefinitions-host>` definition for the Windows device that you will monitor. Just copy/paste the above definition, change the "host_name", and "address" fields to appropriate values.
  
::

  
  
::

  define host{
      use             windows
      host_name       srv-win-1
      address         srv-win-1.mydomain.com
      }
  
  

* use windows  is the "template" line. This host will **inherit** properties from the "windows" template.
  * host_name    is the object name of your host. It must be **unique**.
  * address      is the ip address or hostname of your host (FQDN or just the host portion). 

Note: If you use a hostname be aware that you will have a DNS dependancy in your monitoring system. Either have a periodically updated local hosts file with all relevant entries, long name resolution caching on your host or use an IP address.




What is monitored by the windows template? 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


You have configured your host to be checked by the windows template. What does it means? It means that you Shinken will monitor the following :
  * host check each 5 minutes with a ping
  * check disk space
  * check if autostarting services are started
  * check CPU load (total and each CPU)
  * check memory and swap usage
  * check for a recent (less than one hour) reboot
  * critical/warnings errors in the application and system event logs
  * too many inactive RDP sessions
  * processes hogging the CPU



Restarting Shinken 
-------------------


You're done with modifying the Shinken configuration, so you'll need to :ref:`verify your configuration files <runningshinken-verifyconfig>` and :ref:`restart Shinken <runningshinken-startstop>`.

If the verification process produces any errors messages, fix your configuration file before continuing. Make sure that you don't (re)start Shinken until the verification process completes without any errors!
.. _Monitoring_Windows_Using_WMI.pdf: http://assets.nagios.com/downloads/nagiosxi/docs/Monitoring_Windows_Using_WMI.pdf

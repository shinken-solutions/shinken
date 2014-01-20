.. _linux:



Monitoring Linux Devices
========================


**Abstract**

This document describes how you can monitor "private" services and attributes of Linux devices, such as:

  * Memory usage
  * CPU load
  * Disk usage
  * Running processes
  * etc.



Introduction 
-------------


Publicly available services that are provided by Linux devices (like "HTTP", "FTP", "POP3", etc.) can be monitored easily by following the documentation on Monitoring :ref:`publicly available services (HTTP, FTP, SSH, etc.) <network_service>`.

These instructions assume that you've installed Shinken according to the :ref:`Installation tutorial <shinken 10min start >`. The sample configuration entries below reference objects that are defined in the sample config files ("commands.cfg", "templates.cfg", etc.) that are installed if you followed the quickstart.



Overview 
---------


.. note::  TODO: draw a by snmp diag 

You can monitor a Linux device with an snmp agent, with a local agent and via SSH.

  * This tutorial will focus on the SNMP based method.
  * A local agent can provide faster query interval, more flexibility, passive and active communication methods.
  * SSH based communications and checks should only be executed for infrequent checks as these have a high impact on the client and server cpu. These also are very slow to execute overall and will not scale when polling thousands of devices.



Steps 
------


Here are the steps you will need to follow in order to monitor a new Linux device:

  - Install/configure SNMPd on the Linux device
  - Create new host definition for monitoring this device
  - Restart the Shinken daemon



What's Already Been Done For You 
---------------------------------


To make your life a bit easier, a few configuration tasks have already been done for you:

  * A selection of **check_snmp_** command definitions has been added to the "commands.cfg" file.
  * A Linux host template (called "linux") has already been created in the "templates.cfg" file. This allows you to add new host definitions with a simple keyword.

The above-mentioned configuration files can be found in the ///etc/shinken///packs/os/linux directory (or *c:\shinken\etc\packs\os\linux* under windows). You can modify the definitions in these and other configuration packs to suit your needs better. However, it is recommended to wait until you're more familiar with Shinken before doing so. For the time being, just follow the directions outlined below and you'll be securely monitoring your Linux boxes in no time.

.. tip::  In the example, the linux device being monitored is named srv-lin-1. To re-use the example, make sure to update the hostname to that of your server.



Installing/setup snmpd on srv-lin-1 
------------------------------------


First connect as root under srv-lin-1 with SSH (or putty/SecureCRT under windows).

.. note::  Todo: check if shinken.sh can do this, or with a deploy command?

RedHat like:
  
::

  
   yum install snmpd
  
Debian like:
  
::

  
   apt-get install snmpd
  
  
Edit the /etc/snmp/snmpd.conf and comment the line:
  
::

  
  agentAddress  udp:127.0.0.1:161

and uncomment the line:
  
::

  
  agentAddress udp:161,udp6:[::1]:161

You can change the SNMP community (password) for your host in the line by changing the default value "public" by what you prefer:
  
::

  
  rocommunity public


Restart the snmpd daemon:
  
::

  
  sudo /etc/init.d/snmpd restart




Test the connection 
~~~~~~~~~~~~~~~~~~~~


To see if the keys are working, just launch from your Shinken server. Change the "public" community value with your one:
  
::

  
  
::

   check_snmp -H srv-lin-1 -o .1.3.6.1.2.1.1.3.0  -C public
  
It should give you the uptime of the srv-lin-1 server.



Declare your new host in Shinken 
---------------------------------


If the SNMP community value is a global one you are using on all your hosts, you can configure it in the file /etc/shinken/resource.cfg (or c:\shinken\resource.cfg under windows) in the line:
  
::

  
  $SNMPCOMMUNITYREAD$=public


Now it's time to define some :ref:`object definitions <configuringshinken-objectdefinitions>` in your Shinken configuration files in order to monitor the new Linux device.

You can add the new **host** definition in an existing configuration file, but it's a good idea to have one file per host, it will be easier to manage in the future. So create a file with the name of your server.

Under Linux:
  
::

  
  
::

  linux:~ # vi /etc/shinken/hosts/srv-lin-1.cfg
  
Or Windows:
  
::

  
  
::

  c:\ wordpad   c:\shinken\etc\hosts\srv-lin-1.cfg
  
  
You need to add a new :ref:`host <configuringshinken-objectdefinitions#configuringshinken-objectdefinitions-host>` definition for the Linux device that you're going to monitor. Just copy/paste the above definition Change the "host_name", and "address" fields to appropriate values for this device.

  
::

  
  
::

  define host{
      use             linux
      host_name       srv-lin-1
      address         srv-lin-1.mydomain.com
  }
  
  

* The use linux is the "template" line. It mean that this host will **inherits** properties from the linux template.
  * the host_name is the object name of your host. It must be **unique**.
  * the address is ... the network address of your linux server :)

If you are using a specific SNMP community for this host, you can configure it in the SNMPCOMUNITY host macro like this:
  
::

  
  
::

  define host{
      use             linux
      host_name       srv-lin-1
      address         srv-lin-1.mydomain.com
      _SNMPCOMMUNITY  password             
  }
  
  
To enable disk checking for the host, configure the :ref:`filesystem macro <multi-layer-discovery#macros_mode>`:
  
::

  
  
::

  define host{
      use             linux
      host_name       srv-lin-1
      address         srv-lin-1.mydomain.com
      _SNMPCOMMUNITY  password
      _fs             /, /var         
  }
  
  


What is checked with a linux template? 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


At this point, you configure your host to be checked with a linux template. What does it means? It means that you got some checks already configured for you:
  * host check each 5 minutes: check with a ping that the server is UP
  * check disk spaces
  * check load average
  * check the CPU usage
  * check physical memory and swap usage
  * check network interface activities


Restarting Shinken 
-------------------


You're done with modifying the Shiknen configuration, so you'll need to :ref:`verify your configuration files <runningshinken-verifyconfig>` and :ref:`restart Shinken <runningshinken-startstop>`.

If the verification process produces any errors messages, fix your configuration file before continuing. Make sure that you don't (re)start Shinken until the verification process completes without any errors!

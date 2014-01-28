.. _monitoring_a_router_or_switch:



Monitoring Network Devices
==========================


**Abstract**

This document describes how you can monitor network devices (Cisco, Nortel, Procurve,...), such as:

  * Network usage
  * CPU load
  * Memory usage
  * Port state
  * Hardware state
  * etc.



Introduction 
-------------


These instructions assume that you have installed Shinken according to the :ref:`Installation tutorial <shinken 10min start >`. The sample configuration entries below reference objects that are defined in the sample config files ("commands.cfg", "templates.cfg", etc.) that are installed if you followed the quickstart.



Overview 
---------


.. note::  TODO: draw a by snmp diag 

Network devices are typically monitored using the SNMP and ICMP (ping) protocol.



Steps 
------


Here are the steps you will need to follow in order to monitor a new device:

  - Setup check_nwc_health and try a connection with the equipment
  - Create new host definition to monitor this device
  - Restart the Shinken daemon



What's Already Been Done For You 
---------------------------------


To make your life a bit easier, a few configuration tasks have already been done for you:

  * A selection of **check_nwc_health** command definitions have been added to the "commands.cfg" file.
  * A network equipment host template (called "switch") has already been created in the "templates.cfg" file. This allows you to add new host definitions with a simple keyword.

The above-mentioned configuration files can be found in the ///etc/shinken///packs/network/switch directory (or *c:\shinken\etc\packs\network\switch* under windows). You can modify the definitions in these and other configuration packs to suit your needs better. However, it is recommended to wait until you are familiar with Shinken before doing so. For the time being, just follow the directions outlined below and you will be securely monitoring your devices in no time.

.. tip::  In the example, the switch device being monitored is named switch-1. To re-use the example, make sure to update the hostname to that of your device.



Setup check_nwc_health and try a connection switch-1 
-----------------------------------------------------


First connect as the shinken user under your shinken host.


Unix like to install check_nwc_health:
  
::

  
   install -p check_nwc_health
  
  
Now to try to check your switch, for this you need a read community for it. Consult your device vendors documentation on how to change the SNMP community. The default value is "public". The most efficient, though less secure protocol version of SNMP is version 2c. Version 3 includes encryption and user/password combinations, but is more convoluted to configure and may tax your devices CPU, it is beyond the scope of this tutorial.

Now connect as the shinken user.
  
::

  
  su - shinken


.. warning::  NEVER launch plugins like check_* under the root account, because it can work under root but will deposit temporary files that will break the plugins when executed with the shinken user.

Let's say that the switch-1 IP is 192.168.0.1.

  
::

  
  /usr/local/shinken/libexec/check_nwc_health --hostname 192.168.0.1 --timeout 60 --community "public" --mode interface-status


It should give you the state of all interfaces.




Declare your switch in Shinken 
-------------------------------

If the SNMP community value is a global one you are using on all your hosts, you can configure it in the file /etc/shinken/resource.cfg (or c:\shinken\resource.cfg under windows) in the line:
  
::

  
  $SNMPCOMMUNITYREAD$=public


Now it's time to define some :ref:`object definitions <configuringshinken-objectdefinitions>` in your Shinken configuration files in order to monitor the new Linux device.

You can add the new **host** definition in an existing configuration file, but it's a good idea to have one file per host, it will be easier to manage in the future. So create a file with the name of your server.

Under Linux:
  
::

  
  
::

  linux:~ # vi /etc/shinken/hosts/switch-1.cfg
  
Or Windows:
  
::

  
  
::

  c:\ wordpad   c:\shinken\etc\hosts\switch-1.cfg
  
  
You need to add a new :ref:`host <configuringshinken-objectdefinitions#configuringshinken-objectdefinitions-host>` definition for the switch device that you're going to monitor. Just copy/paste the above definition Change the "host_name", and "address" fields to appropriate values for this device.



  
::

  
  
::

  define host{
      use             switch
      host_name       switch-1
      address         192.168.0.1
  }
  
  

* The use switch is the "template" line. It mean that this host will **inherit** properties and checks from the switch template.
  * the host_name is the object name of your host. It must be **unique**.
  * the address is ... the network address of your switch :)

If you are using a specific SNMP community for this host, you can configure it in the SNMPCOMUNITY host macro like this:
  
::

  
  
::

  define host{
      use             switch
      host_name       switch-1
      address         192.168.0.1
      _SNMPCOMMUNITY  password             
  }
  
  


What is checked with a switch template ? 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

At this point, you configure your host to be checked with a switch template. What does it means? It means that you got some checks already configured for you:
  * host check each 5 minutes: check with a ping that the device is UP
  * interface usage
  * interface status
  * interface errors



For CPU/memory/Hardware checks? 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Not all devices are managed by check_nwc_health. To know if yours is, just launch:

  
::

  
  /usr/local/shinken/libexec/check_nwc_health --hostname 192.168.0.1 --timeout 60 --community "public" --mode hardware-health


If it's ok, you can add the "cisco" template for your hosts (even if it's not a cisco device, we are working on getting more templates configuration).

  
::

  
  
::

  define host{
      use             cisco,switch
      host_name       switch-1
      address         192.168.0.1
      _SNMPCOMMUNITY  password             
  }
  
  
If it does not work, to learn more about your device, please launch the command:
  
::

  
  snmpwalk -v2c -c public 192.168.0.1 | bzip2 > /tmp/device.bz2

And launch this this command as well:
  
::

  
  nmap -T4 -O -oX /tmp/device.xml 192.168.0.1


Once you have done that, send us the device.bz2 and device.xml files (located in /tmp directory), we will add this new device to the check_nwc_health plugin in addition to the discovery module.
With these files please also provide some general information about the device, so we will incorporate it correctly into the discovery module.




Restarting Shinken 
-------------------


You're done with modifying the Shinken configuration, you will need to :ref:`verify your configuration files <runningshinken-verifyconfig>` and :ref:`restart Shinken <runningshinken-startstop>`.

If the verification process produces any errors messages, fix your configuration file before continuing. Make sure that you don't (re)start Shinken until the verification process completes without any errors!

.. _monitoring/vmware:

====================================
Monitoring VMware hosts and machines
====================================

**Abstract**

This document describes how you can monitor "private" services and attributes of ESX and VM machines, such as:

  * Memory usage
  * CPU load
  * Disk usage
  * Network usage
  * etc.


Introduction 
=============

In a VMware server we should monitor:

  * ESX hosts
  * VM started on it

.. note::  It is a good practice to automatically create dependencies between them so if an ESX goes down, you won't get useless notifications about all VMs on it. Consult the tutorial about the :ref:`vmware arbiter module <vmware_arbiter_module>` for more information on this topic..

For theses checks you will need the check_esx3.pl plugin.
.. note::  TODO: write in the setup phase about installing it

.. note::  TODO: draw a by vSphere check 


Steps 
======

There are some steps you'll need to follow in order to monitor a new vmware esx/vm machine. They are:

  * Create an account on the vsphere console server
  * Configure your vsphere server in Shinken
  * Create new host definition for monitoring an esx server
  * Create new host definition for monitoring a vm machine
  * Restart the Shinken daemon


What's already done for you 
============================

To make your life a bit easier, a few configuration tasks have already been done for you:

  * Some **check_esx_** commands definition has been added to the "commands.cfg" file.
  * A VMware ESX host template (called "esx") has already been created in the "templates.cfg" file. This allows you to add new host definitions in a simple manner.
  * A VMware virtual machine host template (called "vm") has already been created in the templates.cfg file.

The above-mentioned config files can be found in the ///etc/shinken/// directory (or *c:\shinken\etc* under windows). You can modify the definitions in these and other definitions to suit your needs better if you'd like. However, I'd recommend waiting until you're more familiar with configuring Shinken before doing so. For the time being, just follow the directions outlined below and you'll be monitoring your VMware boxes in no time.

.. tip::  We are supposing here that the esx machine you want to monitor is named srv-esx-1 and the virtual machine is a windows vm named srv-vm-1. Please change the above lines and commands with the real name of your server of course.


Create a vSphere account for Shinken  
======================================

Please ask your VMware administrator to create a Shinken account (can be a windows domain account) and give it read credential on the vSphere environment (on the root datacenter definition with inheritance).


Setup the vSphere console server connection 
============================================

You need to configure in the "resource.cfg" file ("/etc/shinken/resource.cfg" under linux or "c:\\shinken\\etc\\resource.cfg" under windows):
  
  * the VSPHERE host connection
  * the login for the connection
  * the password  

  
::
  
  #### vSphere (ESX) part
  $VCENTER$=vcenter.mydomain.com
  $VCENTERLOGIN$=someuser
  $VCENTERPASSWORD$=somepassowrd


You can then try the connection if you already know about an esx host, like for example myesx:
  
::

  /var/lib/nagios/plugins/check_esx3.pl -D vcenter.mydomain.com -H myesx -u someuser -p somepassword -l cpu
  


Deploy the public keys on the linux host 
-----------------------------------------

When you got the public/private keys, you can deploy the public key to you linux servers.
  
::
  
   ssh-copy-id  -i /home/shinken/.ssh/id_rsa.pub shinken@srv-lin-1
  
.. tip::  Change srv-lin-1 with the name of your server.


Test the connection 
--------------------

To see if the keys are working, just launch:
  
::

   check_by_ssh -H srv-lin-1 -C uptime
  
It should give you the uptime of the srv-lin-1 machine.


Declare your new host in Shinken 
=================================

Now it's time to define some :ref:`object definitions <configuration/objectdefinitions>` in your Shinken configuration files in order to monitor the new Linux machine.

You can add the new **host** definition in an existing configuration file, but it's a good idea to have one file by host, it will be easier to manage in the future. So create a file with the name of your server.

Under Linux:
  
::

  linux:~ # vi /etc/shinken/hosts/srv-lin-1.cfg
  
Or Windows:
  
::

  c:\ wordpad   c:\shinken\etc\hosts\srv-lin-1.cfg
  
  
You need to add a new :ref:`host <configobjects/host>` definition for the Linux machine that you're going to monitor. Just copy/paste the above definition Change the "host_name", and "address" fields to appropriate values for this machine.
  
::

  define host{
      use             esx
      host_name       srv-lin-1
      address         srv-lin-1.mydomain.com
  }


  * The use linux is the "template" line. It mean that this host will **inherits** properties from the linux template.
  * the host_name is the object name of your host. It must be **unique**.
  * the address is the network address of your linux server.


What is supervised by the linux template? 
------------------------------------------

You have configured your host to the checks defined from the linux template. What does this mean? It means that you have some checks pre-configured for you:
  
  * host check each 5 minutes: check with a ping that the server is UP
  * check disk space
  * check if ntpd is started
  * check load average
  * check physical memory and swap usage
  * check for a recent (less than one hour) reboot


Restarting Shinken 
===================

You're done with modifying the configuration, so you'll need to :ref:`verify your configuration files <runningshinken/verifyconfig>` and :ref:`restart Shinken <runningshinken/startstop>`.

If the verification process produces any errors messages, fix your configuration file before continuing. Make sure that you don't (re)start Shinken until the verification process completes without any errors!

.. _dhcp:



Monitoring a DHCP server
========================


**Abstract**

This document describes how you can monitor a DHCP service.



Introduction 
-------------


These instructions assume that you've installed Shinken according to the :ref:`Installation tutorial <shinken 10min start >`. The sample configuration entries below reference objects that are defined in the sample config files ("commands.cfg", "templates.cfg", etc.) that are installed if you follow the quickstart.



Overview 
---------


.. note::  TODO: draw a dhcp diag 

Monitoring a DHCP server means ask for a DHCP query and wait for a response from this server. Don't worry, the DHCP confirmation will never be send, so you won't have a DHCP entry for this test.



Steps 
------


There are some steps you'll need to follow in order to monitor a new database machine. They are:

  - Allow check_dhcp to run
  - Update your server host definition for dhcp monitoring
  - Restart the Shinken daemon



What's Already Done For You 
----------------------------


To make your life a bit easier, a few configuration tasks have already been done for you:

  * Some **check_dhcp** commands definition has been added to the "commands.cfg" file.
  * An DHCP host template (called "dhcp") has already been created in the "templates.cfg" file.

The above-mentioned config files can be found in the ///etc/shinken/packs/network/services/dhcp* directory (or *c:\shinken\etc\packs\network\services\dhcp// under windows). You can modify the definitions in these and other definitions to suit your needs better if you'd like. However, I'd recommend waiting until you're more familiar with configuring Shinken before doing so. For the time being, just follow the directions outlined below and you'll be monitoring your DHCP boxes in no time.

.. tip::  We are supposing here that the DHCP server you want to monitor is named srv-lin-1 and is a linux. Please change the above lines and commands with the real name of your server of course.



Allow check_dhcp to run 
------------------------


The check_dhcp must be run under the root account to send a dhcp call on the network. To do this, you should launch on your shinken server:
  
::

  
  chown root:root /usr/lib/nagios/plugins/check_dhcp
  chmod u+s /usr/lib/nagios/plugins/check_dhcp




Declare your host as an dhcp server 
------------------------------------


All you need to get all the DHCP service checks is to add the *dhcp* template to this host. We suppose you already monitor the OS for this host, and so you already got the host configuration file for it.

Under Linux:
  
::

  
  
::

  linux:~ # vi /etc/shinken/hosts/srv-lin-1.cfg
  
Or Windows:
  
::

  
  
::

  c:\ wordpad   c:\shinken\etc\hosts\srv-lin-1.cfg
  
And add:
  
::

  
  
::

  define host{
      use             dhcp,linux
      host_name       srv-lin-1
      address         srv-lin-1.mydomain.com
  }
  
  


Restarting Shinken 
-------------------


You're done with modifying the Shiknen configuration, so you'll need to :ref:`verify your configuration files <runningshinken-verifyconfig>` and :ref:`restart Shinken <runningshinken-startstop>`.

If the verification process produces any errors messages, fix your configuration file before continuing. Make sure that you don't (re)start Shinken until the verification process completes without any errors!

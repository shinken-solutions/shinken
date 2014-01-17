.. _exchange:



Monitoring Microsoft Exchange 
=============================


**Abstract**

This document describes how you can monitor devices running Microsoft Exchange. This monitoring covers typically:

  * Hub transport activity
  * Hub transport queues
  * Database activities
  * Receive/send activities
  * etc ...



Introduction 
-------------


These instructions assume that you've installed Shinken according to the :ref:`Installation tutorial <shinken 10min start >`. The sample configuration entries below reference objects that are defined in the sample config files ("commands.cfg", "templates.cfg", etc.) that was installed if you followed the quickstart.



Overview 
---------


Monitoring an Exchange device is possible the agentless by polling via the network using the WMI protocol, like we proposed in the windows template.



Prerequisites 
--------------


Have a valid account on the Microsoft Windows device (local or domain account) you will monitor using WMI queries and already get the windows server monitor with the windows template.



Steps 
------


There are several steps you'll need to follow in order to monitor a Microsoft Exchange server.

  - Add the good exchange template to your windows host in the configuration
  - Restart the Shinken Arbiter



What's Already Been Done For You 
---------------------------------


To make your life a bit easier, configuration templates are provided as a starting point:

  * A selection of **check_exchange_*** based commands definitions have been added to the "commands.cfg" file. This allows you to use the **check_wmi_plus** plugin.
  * Some Exchange host templates are included the "templates.cfg" file. This allows you to add new host definitions in a simple manner.

The above-mentioned config files can be found in the ///etc/shinken/packs/microsoft/exchange// directory. You can modify the definitions in these and other templates to suit your needs. However, wait until you're more familiar with Shinken before doing so. For the time being, just follow the directions outlined below and you'll be monitoring your devices in no time.



Setup the check_wmi_plus plugin 
--------------------------------


If you already followed the :ref:`windows monitoring <monitoring_a_windows>` tutorial, you should have the check_wmi_plus plugin installed. If it's not, please do it before activating this pack.



Declare your host in Shinken 
-----------------------------


There are some templates available for the exchange monitoring, each for an exchange role.
  * Hub transport: exchange-ht template
  * Mail Box server: exchange-mb template
  * CAS server: exchange-cas template

Now it's time to define some :ref:`object definitions <configuringshinken-objectdefinitions>` in your Shinken configuration files in order to monitor the new Windows machine.

We will suppose here that your server is named *srv-win-1*. Of course change this name with the real name of your server.

Find your host definition and edit it:

Under Linux:
  
::

  
  
::

  linux:~ # vi /etc/shinken/hosts/srv-win-1.cfg
  
Or Windows:
  
::

  
  
::

  c:\ wordpad   c:\shinken\etc\hosts\srv-win-1.cfg
  
  
All you need it to add the good template for your host. For example for a Hub Transport server:
  
::

  
  
::

  define host{
      use             exchange-ht,exchange,windows
      host_name       srv-win-1
      address         srv-win-1.mydomain.com
      }
  
  

* The use exchange-ht and exchange is the "template" line. It mean that this host will **inherits** properties from theses templates.
  * the host_name is the object name of your host. It must be **unique**.
  * the address is ... the network address of your host :)

The "exchange" template do not add any specific checks, but allow to link with the exchange contacts easily.



What is checked with an exchange template? 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


At this point, you configure your host to be checked with a windows template. What does it means? In addition to the windows classic checks, it means that you got some checks already configured for you:
  * Hub transport activity
  * Hub transport queues
  * Database activities
  * Receive/send activities
The exchange-cas and exchange-mb do not have any specific checks from now.

.. note::  Any help is welcome here :)



Restarting Shinken 
-------------------


You're done with modifying the Shinken configuration, so you'll need to :ref:`verify your configuration files <runningshinken-verifyconfig>` and :ref:`restart Shinken <runningshinken-startstop>`.

If the verification process produces any errors messages, fix your configuration file before continuing. Make sure that you don't (re)start Shinken until the verification process completes without any errors!

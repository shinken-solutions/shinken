.. _iis:



Monitoring a IIS server
=======================


**Abstract**

This document describes how you can monitor a IIS server. This monitoring covers typically:

  * connections count
  * number of errors
  * number of logged users
  * etc...



Introduction 
-------------


These instructions assume that you've installed Shinken according to the :ref:`Installation tutorial <shinken 10min start >`. The sample configuration entries below reference objects that are defined in the sample config files ("commands.cfg", "templates.cfg", etc.) that was installed if you followed the quickstart.



Overview 
---------


Monitoring a domain controler is possible in an agentless way by polling via the network using the WMI protocol, like we proposed in the windows template.



Prerequisites 
--------------


Have a valid account on the Microsoft Windows device (local or domain account) you will monitor using WMI queries and already get the windows server monitor with the windows template.



Steps 
------


There are several steps you'll need to follow in order to monitor a Microsoft IIS server.

  - Add the good iis template to your windows host in the configuration
  - Restart the Shinken Arbiter




What's Already Been Done For You 
---------------------------------


To make your life a bit easier, configuration templates are provided as a starting point:

  * A selection of **check_iis_**** based commands definitions have been added to the "commands.cfg" file. This allows you to use the **check_wmi_plus** plugin.
  * A IIS host template is included the "templates.cfg" file. This allows you to add new host definitions in a simple manner.

The above-mentioned config files can be found in the ///etc/shinken/packs/microsoft/iis// directory. You can modify the definitions in these and other templates to suit your needs. However, wait until you're more familiar with Shinken before doing so. For the time being, just follow the directions outlined below and you'll be monitoring your devices in no time.



Setup the check_wmi_plus plugin 
--------------------------------


If you already follow the :ref:`windows monitoring <monitoring_a_windows>` tutorial, you should already got the check_wmi_plus plugin. If it's not done, please do it first.



Declare your host in Shinken 
-----------------------------


The IIS template name is *iis*. All you need is to add it on your windws host.

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
      use             iis,windows
      host_name       srv-win-1
      address         srv-win-1.mydomain.com
      }
  
  

* The use iis is the "template" line. It mean that this host will **inherits** properties from this template.
  * the host_name is the object name of your host. It must be **unique**.
  * the address is ... the network address of your host :)



What is checked with a IIS template? 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


At this point, you configure your host to be checked with a IIS and Windows templates. What does it means? In addition to the windows classic checks, it means that you got some checks already configured for you:

  * connections count
  * number of errors
  * number of logged users
  * etc ...



Restarting Shinken 
-------------------


You're done with modifying the Shinken configuration, so you'll need to :ref:`verify your configuration files <runningshinken-verifyconfig>` and :ref:`restart Shinken <runningshinken-startstop>`.

If the verification process produces any errors messages, fix your configuration file before continuing. Make sure that you don't (re)start Shinken until the verification process completes without any errors!

.. _windows_monitoring_with_nsclient:


Monitoring Windows witn NSClient++
==================================

Guideline 
----------


Here we will focus here on the windows monitoring with an agent, NSClient++.

It can be get at `NSClient++`_ addon on the Windows machine and using the **check_nt** plugin to communicate with the NSClient++ addon. The **check_nt** plugin should already be installed on the Shinken server if you followed the quickstart guide.

.. tip::  There are others agent like `NC_Net`_ but for the sake of simplicity, we will cover only nsclient++, the most complete and active one




Steps 
------


There are several steps you'll need to follow in order to monitor a new Windows machine. They are:

  - Install a monitoring agent on the Windows machine
  - Create new host and add it the nsclient template for monitoring the Windows machine
  - Restart the Shinken daemon




What's Already Done For You 
----------------------------


To make your life a bit easier, a few configuration tasks have already been done for you:

  * Some **check_nt** based commands definition has been added to the "commands.cfg" file. This allows you to use the **check_nt** plugin to monitor Window services.
  * A Windows host template (called "windows") has already been created in the "templates.cfg" file. This allows you to add new Windows host definitions in a simple manner.

The above-mentioned config files can be found in the "/etc/shinken/" directory. You can modify the definitions in these and other definitions to suit your needs better if you'd like. However, I'd recommend waiting until you're more familiar with configuring Shinken before doing so. For the time being, just follow the directions outlined below and you'll be monitoring your Windows boxes in no time.




Installing the Windows Agent 
-----------------------------


Before you can begin monitoring private services and attributes of Windows machines, you'll need to install an agent on those machines. I recommend using the NSClient++ addon, which can be found at http://sourceforge.net/projects/nscplus. These instructions will take you through a basic installation of the NSClient++ addon, as well as the configuration of Shinken for monitoring the Windows machine.

  - Download the latest stable version of the NSClient++ addon from http://sourceforge.net/projects/nscplus
  - Unzip the NSClient++ files into a new C:\NSClient++ directory
  - Open a command prompt and change to the C:\NSClient++ directory
  - Register the NSClient++ system service with the following command (as an administrator):

  
::

  
  
::

     cd C:\NSClient++
     nsclient++ /install
  

- You can install the NSClient++ systray with the following command ('SysTray' is case-sensitive):
  
::

  
  
::

     nsclient++ SysTray
  

- Open the services manager and make sure the NSClientpp service is allowed to interact with the desktop (see the 'Log On' tab of the services manager). If it isn't already allowed to interact with the desktop, check the box to allow it to.



.. image:: /_static/images///official/images/nscpp.png
   :scale: 90 %



  - Edit the "NSC.INI file" (located in the "C:\NSClient++" directory) and make the following changes:
    * Uncomment all the modules listed in the [modules] section, except for "CheckWMI.dll" and "RemoteConfiguration.dll"
    * Optionally require a password for clients by changing the "password" option in the [Settings] section.
    * Uncomment the "allowed_hosts" option in the [Settings] section. Add the IP address of the Shinken server (or you pollers serbers for a multi-host setup) to this line, or leave it blank to allow all hosts to connect.
    * Make sure the "port" option in the [NSClient] section is uncommented and set to '12489' (the default port).
  - Start the NSClient++ service with the following command:

  
::

  
  
::

     C:\> nsclient++ /start
  

- If installed properly, a new icon should appear in your system tray. It will be a yellow circle with a black 'M' inside.
  - Success! The Windows server can now be added to the Shinken monitoring configuration...




Declare your new host in Shinken 
---------------------------------


Now it's time to define some :ref:`object definitions <configuringshinken-objectdefinitions>` in your Shinken configuration files in order to monitor the new Windows machine.

We will suppose here that your server is named *srv-win-1*. Of course change this name with the real name of your server.

You can add the new **host** definition in an existing configuration file, but it's a good idea to have one file by host, it will be easier to manage in the future. So create a file with the name of your server.

Under Linux:
  
::

  
  
::

  linux:~ # vi /etc/shinken/hosts/srv-win-1.cfg
  
Or Windows:
  
::

  
  
::

  c:\ wordpad   c:\shinken\etc\hosts\srv-win-1.cfg
  
  
You need to add a new :ref:`host <configuringshinken-objectdefinitions#configuringshinken-objectdefinitions-host>` definition for the Windows machine that you're going to monitor. Just copy/paste the above definition Change the "host_name", and "address" fields to appropriate values for the Windows box.
  
::

  
  
::

  define host{
      use             windows,nsclient++
      host_name       srv-win-1
      address         srv-win-1.mydomain.com
      }
  
  

* The use windows and nsclient++ templates in the "use" line. It mean that this host will **inherits** properties from the windows and nsclient++ templates.
  * the host_name is the object name of your host. It must be **unique**.
  * the address is ... the network address of your host :)




What is checked with a windows template? 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


At this point, you configure your host to be checked with a windows template. What does it means? It means that you got some checks already configured for you:
  * host check each 5 minutes: check if the RDP port is open or not.
  * check disk spaces
  * check if autostarting services are started
  * check CPU load
  * check memory and swap usage
  * check for a recent (less than one hour) reboot

.. _NC_Net: http://sourceforge.net/projects/nc-net
.. _NSClient++: http://sourceforge.net/projects/nscplus

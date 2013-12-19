.. _asterisk:




Monitoring an Asterisk server 
=============================


**Abstract**

This document describes how you can monitor an Asterisk server. This monitoring covers typically:

  * overall state



Introduction 
-------------


These instructions assume that you've installed Shinken according to the :ref:`Installation tutorial <shinken 10min start >`. The sample configuration entries below reference objects that are defined in the sample config files ("commands.cfg", "templates.cfg", etc.) that was installed if you followed the quickstart.



Overview 
---------


Monitoring an asterisk server is possible with the check_sip plugin and an account on the Asterisk server.



Prerequisites 
--------------


Have a valid account on the Asterisk device.



Steps 
------


There are several steps you'll need to follow:

  - Setup the check_sip plugin
  - Add the good asterisk template to your host in the configuration
  - Restart the Shinken Arbiter




What's Already Been Done For You 
---------------------------------


To make your life a bit easier, configuration templates are provided as a starting point:

  * A selection of **check_sip** based commands definitions have been added to the "commands.cfg" file.
  * An Asterisk host template is included the "templates.cfg" file. This allows you to add new host definitions in a simple manner.

The above-mentioned config files can be found in the ///etc/shinken/packs/network/services/asterisk// directory. You can modify the definitions in these and other templates to suit your needs. However, wait until you're more familiar with Shinken before doing so. For the time being, just follow the directions outlined below and you'll be monitoring your devices in no time.



Setup the check_sip plugin 
---------------------------


As the shinken account in your shinken server run:
  
::

  
  wget "http://www.bashton.com/downloads/nagios-check_sip-1.2.tar.gz"
  tar xvfz nagios-check_sip-1.2.tar.gz
  cd nagios-check_sip-1.2/
  cp check_sip /var/lib/nagios/plugins/
  chmod a+x /var/lib/nagios/plugins/check_sip




Add tje SIP user credentials 
-----------------------------


In the file ///etc/shinken/packs/network/services/asterisk//macros you can edit the SIPUSER that you want ot use for the connection.




Declare your host in Shinken 
-----------------------------


The Asterisk template name is *asterisk*. All you need is to add it on yourhost.

Now it's time to define some :ref:`object definitions <configuringshinken-objectdefinitions>` in your Shinken configuration files in order to monitor the new Windows machine.

We will suppose here that your server is named *srv-sip-1*. Of course change this name with the real name of your server.

Find your host definition and edit it:

Under Linux:
  
::

  
  
::

  linux:~ # vi /etc/shinken/hosts/srv-sip-1.cfg
  
Or Windows:
  
::

  
  
::

  c:\ wordpad   c:\shinken\etc\hosts\srv-sip-1.cfg
  
  
All you need it to add the asterisk template for your host.
  
::

  
  
::

  define host{
      use             asterisk,windows
      host_name       srv-sip-1
      address         srv-sip-1.mydomain.com
      }
  
  

* The use sip is the "template" line. It mean that this host will **inherits** properties from this template.
  * the host_name is the object name of your host. It must be **unique**.
  * the address is ... the network address of your host :)



What is checked with an askterisk template? 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


At this point, you configure your host to be checked with an asterisk templates. What does it means? It means that you got some checks already configured for you:
  * overall state of the asterisk server



Restarting Shinken 
-------------------


You're done with modifying the Shinken configuration, so you'll need to :ref:`verify your configuration files <runningshinken-verifyconfig>` and :ref:`restart Shinken <runningshinken-startstop>`.

If the verification process produces any errors messages, fix your configuration file before continuing. Make sure that you don't (re)start Shinken until the verification process completes without any errors!

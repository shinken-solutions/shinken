.. _monitoring_a_network_service:



Monitoring Publicly Available Services
======================================


**Abstract**

This document describes how you can monitor publicly available services, applications and protocols. By “public" I mean services that are accessible across the network - either the local network or Internet. Examples of public services include "HTTP", "POP3", "IMAP", "FTP", and "SSH". There are many more public services that you probably use on a daily basis. These services and applications, as well as their underlying protocols, can usually be monitored by Shinken without any special access requirements.



Introduction 
-------------


Private services, in contrast, cannot be monitored with Shinken without an intermediary agent of some kind. Examples of private services associated with hosts are things like CPU load, memory usage, disk usage, current user count, process information, etc.

These instructions assume that you've installed Shinken according to the :ref:`Installation tutorial <shinken 10min start >`. The sample configuration entries below reference objects that are defined in the sample config files ("commands.cfg", "templates.cfg", etc.) that are installed if you followed the quickstart.



Plugins For Monitoring Services 
--------------------------------


When you find yourself needing to monitor a particular application, service, or protocol, chances are good that a :ref:`plugin <thebasics-plugins>` exists to monitor it. The official Nagios/Shinken plugins distribution comes with plugins that can be used to monitor a variety of services and protocols. There are also a large number of contributed plugins that can be found in the "contrib/" subdirectory of the plugin distribution. The `Monitoringexchange.org`_ website hosts a number of additional plugins that have been written by users, so check it out when you have a chance.

If you don't happen to find an appropriate plugin for monitoring what you need, you can always write your own. Plugins are easy to write, so don't let this thought scare you off. Read the documentation on :ref:`developing plugins <development-pluginapi>` for more information.

I'll walk you through monitoring some basic services that you'll probably use sooner or later. Each of these services can be monitored using one of the plugins that gets installed as part of the Nagios/Shinken plugins distribution. Let's get started...



The host definition 
--------------------


Before you can monitor a service, you first need to define a :ref:`host <configuringshinken-objectdefinitions#configuringshinken-objectdefinitions-host>` that is associated with the service. If you follow the windows/linux/printer monitoring tutorial, you should be familiar with the process of creating a host and linking your services to it.

For this example, lets say you want to monitor a variety of services on a remote windows host. Let's call that host *srv-win-1*. The host definition can be placed in its own file. Here's what the host definition for *remotehost* might look like if you followed the windows monitoring tutorial:

  
::

  
  
::

  define host{
      use           windows    
      host_name     srv-win-1
      address       srv-win-1.mydomain.com
  }
  
  


Classic services definition with templates 
-------------------------------------------

For classic services like HTTP(s) or FTP, there are some ready to run template that you can use. The full service definition is explained in another tutorial :ref:`Services definitions <service definition >`.

The idea here is just to *tag* your host with what it is providing as network services and automatically get some default checks like Http or Ftp ones.


Monitoring HTTP 
----------------


Chances are you're going to want to monitor web servers at some point - either yours or someone else's. The **check_http** plugin is designed to do just that. It understands the "HTTP" protocol and can monitor response time, error codes, strings in the returned HTML, server certificates, and much more.

There is already a *http* template for your host that will create for you a Http service. All you need is to add this template on your host, with a comma for separating templates.

So you host definition will now look like:
  
::

  
  
::

  define host{
      use           windows,http
      host_name     srv-win-1
      address       srv-win-1.mydomain.com
  }
  
  
  
  
.. note::  TODO: write some custom macros for other page check or timeout

It will create a Http service that will look for the "/" page running on *srv-win-1*. It will produce alerts if the web server doesn't respond within 10 seconds or if it returns "HTTP" errors codes (403, 404, etc.). That's all you need for basic monitoring. Pretty simple, huh?



Monitoring HTTPS 
-----------------


We got more an more HTTPS services. You will basically check two things: page accessibility and certificates. 

There is already a *https* template for your host that will create for you a Https and a HttpsCertificate services. The Https check is like the Http one, but on the SSL port. The HttpsCertificate will look for the expiration of the certificate, and will warn you 30 days before the end of the certificate, and raise a critical alert if its expired.

So you host definition will now look like:
  
::

  
  
::

  define host{
      use           windows,https
      host_name     srv-win-1
      address       srv-win-1.mydomain.com
  }
  
  
.. note::  TODO: write some custom macros for other page check or timeout

You can check Http AND Https in the same time, all you need is to use the two templates in the same time:
  
::

  
  
::

  define host{
      use           windows,http,https
      host_name     srv-win-1
      address       srv-win-1.mydomain.com
  }
  
  


Monitoring FTP 
---------------


When you need to monitor "FTP" servers, you can use the **check_ftp** plugin. Like for the Http case, there is already a ftp template that you can use.

  
::

  
  
::

  define host{
      use           windows,ftp
      host_name     srv-win-1
      address       srv-win-1.mydomain.com
  }
  
This service definition will monitor the "FTP" service and generate alerts if the "FTP" server doesn't respond within 10 seconds.



Monitoring SSH 
---------------


  When you need to monitor "SSH" servers, you can use the **check_ssh** plugin.
::

  
  
::

  define host{
      use           windows,ssh
      host_name     srv-win-1
      address       srv-win-1.mydomain.com
  }
  
  
.. tip::  You don't need to declare the ssh template if you already configure your host with the linux one, the Ssh service is already configured.

This definition will monitor the "Ssh" service and generate alerts if the "SSH" server doesn't respond within 10 seconds.



Monitoring SMTP 
----------------


The **check_smtp** plugin can be using for monitoring your email servers. You can use the smtp template for you host to automatically get a Smtp service check.

  
::

  
  
::

  define host{
      use           windows,smtp
      host_name     srv-win-1
      address       srv-win-1.mydomain.com
  }
  
  
This service definition will monitor the "Smtp" service and generate alerts if the "SMTP" server doesn't respond within 10 seconds.



Monitoring POP3 
----------------


The **check_pop** plugin can be using for monitoring the "POP3" service on your email servers. Use the *pop3* template for your host to get automatically a Pop3 service.
  
::

  
  
::

  define host{
      use           windows,pop3
      host_name     srv-win-1
      address       srv-win-1.mydomain.com
  }
  
  
This service definition will monitor the "POP3" service and generate alerts if the "POP3" server doesn't respond within 10 seconds.



Monitoring IMAP 
----------------


The **check_imap** plugin can be using for monitoring "IMAP4" service on your email servers. You can use the *imap* template for your host to get an Imap service check.

  
::

  
  
::

  define host{
      use           windows,imap
      host_name     srv-win-1
      address       srv-win-1.mydomain.com
  }
  
  
This service definition will monitor the "IMAP4" service and generate alerts if the "IMAP" server doesn't respond within 10 seconds.

To get smtp, pop3 and imap service checks, you can just link all theses templates to your host:

  
::

  
  
::

  define host{
      use           windows,smtp,pop3,imap
      host_name     srv-win-1
      address       srv-win-1.mydomain.com
  }
  
  
  


Restarting Shinken 
-------------------


Once you've added the new host templates to your object configuration file(s), you're ready to start monitoring them. To do this, you'll need to :ref:`verify your configuration <runningshinken-verifyconfig>` and :ref:`restart Shinken <runningshinken-startstop>`.

If the verification process produces any errors messages, fix your configuration file before continuing. Make sure that you don't (re)start Shinken until the verification process completes without any errors!

.. _Monitoringexchange.org: https://www.monitoringexchange.org/

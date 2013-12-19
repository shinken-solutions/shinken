.. _gettingstarted-monitoring-publicservices:




========================================
 Monitoring Publicly Available Services 
========================================

**Abstract**

This document describes how you can monitor publicly available services, applications and protocols. By “public" I mean services that are accessible across the network - either the local network or the greater Internet. Examples of public services include "HTTP", "POP3", "IMAP", "FTP", and "SSH". There are many more public services that you probably use on a daily basis. These services and applications, as well as their underlying protocols, can usually be monitored by Shinken without any special access requirements.



Introduction 
=============


Private services, in contrast, cannot be monitored with Shinken without an intermediary agent of some kind. Examples of private services associated with hosts are things like CPU load, memory usage, disk usage, current user count, process information, etc. These private services or attributes of hosts are not usually exposed to external clients. This situation requires that an intermediary monitoring agent be installed on any host that you need to monitor such information on. More information on monitoring private services on different types of hosts can be found in the documentation on:

  * :ref:`Monitoring Windows machines <gettingstarted-monitoring-windows>`
  * :ref:`Monitoring Netware servers <gettingstarted-monitoring-netware>`
  * :ref:`Monitoring Linux/Unix machines <gettingstarted-monitoring-linux>`

Occasionally you will find that information on private services and applications can be monitored with "SNMP". The "SNMP" agent allows you to remotely monitor otherwise private (and inaccessible) information about the host. For more information about monitoring services using "SNMP", check out the documentation on :ref:`Monitoring routers/switches <gettingstarted-monitoring-routers>`.

These instructions assume that you've installed Shinken according to the :ref:`quickstart guide <gettingstarted-quickstart>`. The sample configuration entries below reference objects that are defined in the sample "commands.cfg" and "localhost.cfg" config files.



Plugins For Monitoring Services 
================================


When you find yourself needing to monitor a particular application, service, or protocol, chances are good that a :ref:`plugin <thebasics-plugins>` exists to monitor it. The official Nagios plugins distribution comes with plugins that can be used to monitor a variety of services and protocols. There are also a large number of contributed plugins that can be found in the "contrib/" subdirectory of the plugin distribution. The `NagiosExchange.org`_ website hosts a number of additional plugins that have been written by users, so check it out when you have a chance.

If you don't happen to find an appropriate plugin for monitoring what you need, you can always write your own. Plugins are easy to write, so don't let this thought scare you off. Read the documentation on :ref:`developing plugins <development-pluginapi>` for more information.

I'll walk you through monitoring some basic services that you'll probably use sooner or later. Each of these services can be monitored using one of the plugins that gets installed as part of the Nagios plugins distribution. Let's get started...



Creating A Host Definition 
===========================


Before you can monitor a service, you first need to define a :ref:`host <host>` that is associated with the service. You can place host definitions in any object configuration file specified by a :ref:`cfg_file <configuringshinken-configmain#configuringshinken-configmain-cfg_file>` directive or placed in a directory specified by a :ref:`cfg_dir <configuringshinken-configmain#configuringshinken-configmain-cfg_dir>` directive. If you have already created a host definition, you can skip this step.

For this example, lets say you want to monitor a variety of services on a remote host. Let's call that host *remotehost*. The host definition can be placed in its own file or added to an already exiting object configuration file. Here's what the host definition for *remotehost* might look like:

::

  define host{
      use           generic-host        ; Inherit default values from a template
      host_name     remotehost          ; The name we're giving to this host
      alias         Some Remote Host    ; A longer name associated with the host
      address       192.168.1.50        ; IP address of the host
      hostgroups    allhosts            ; Host groups this host is associated with
  }
  
Now that a definition has been added for the host that will be monitored, we can start defining services that should be monitored. As with host definitions, service definitions can be placed in any object configuration file.



Creating Service Definitions 
=============================


For each service you want to monitor, you need to define a :ref:`service <configuringshinken/configobjects/service>` in Shinken that is associated with the host definition you just created. You can place service definitions in any object configuration file specified by a :ref:`cfg_file <configuringshinken-configmain#configuringshinken-configmain-cfg_file>` directive or placed in a directory specified by a :ref:`cfg_dir <configuringshinken-configmain#configuringshinken-configmain-cfg_dir>` directive.

Some example service definitions for monitoring common public service ("HTTP", "FTP", etc) are given below.



Monitoring HTTP 
================


Chances are you're going to want to monitor web servers at some point - either yours or someone else's. The **check_http** plugin is designed to do just that. It understands the "HTTP" protocol and can monitor response time, error codes, strings in the returned HTML, server certificates, and much more.

The "commands.cfg" file contains a command definition for using the **check_http** plugin. It looks like this:

  
::

  define command{
      name            check_http
      command_name    check_http
      command_line    $USER1$/check_http -I $HOSTADDRESS$ $ARG1$
      }
  
A simple service definition for monitoring the "HTTP" service on the *remotehost* machine might look like this:

  
::

  define service{
      use                 generic-service     ; Inherit default values from a template
      host_name           remotehost
      service_description HTTP
      check_command       check_http
      }
  
This simple service definition will monitor the "HTTP" service running on *remotehost*. It will produce alerts if the web server doesn't respond within 10 seconds or if it returns "HTTP" errors codes (403, 404, etc.). That's all you need for basic monitoring. Pretty simple, huh?

For more advanced monitoring, run the **check_http** plugin manually with "--help" as a command-line argument to see all the options you can give the plugin. This "--help" syntax works with all of the plugins I'll cover in this document.

A more advanced definition for monitoring the "HTTP" service is shown below. This service definition will check to see if the /download/index.php URI contains the string "latest-version.tar.gz". It will produce an error if the string isn't found, the URI isn't valid, or the web server takes longer than 5 seconds to respond.

  
::

  define service{
      use                 generic-service   ; Inherit default values from a template
      host_name           remotehost
      service_description Product Download Link
      check_command       check_http!-u /download/index.php -t 5 -s "latest-version.tar.gz"
      }
  


Monitoring FTP 
===============


When you need to monitor "FTP" servers, you can use the **check_ftp** plugin. The "commands.cfg" file contains a command definition for using the **check_ftp** plugin, which looks like this:

  
::

  define command{
      command_name    check_ftp
      command_line    $USER1$/check_ftp -H $HOSTADDRESS$ $ARG1$
      }
  
A simple service definition for monitoring the "FTP" server on *remotehost* would look like this:

  
::

  define service{
      use                   generic-service  ; Inherit default values from a template
      host_name             remotehost
      service_description   FTP
      check_command         check_ftp
      }
  
This service definition will monitor the "FTP" service and generate alerts if the "FTP" server doesn't respond within 10 seconds.

A more advanced service definition is shown below. This service will check the "FTP" server running on port 1023 on *remotehost*. It will generate an alert if the server doesn't respond within 5 seconds or if the server response doesn't contain the string “Pure-FTPd [TLS]".

  
::

  define service{
      use                   generic-service   ; Inherit default values from a template
      host_name             remotehost
      service_description   Special FTP
      check_command         check_ftp!-p 1023 -t 5 -e "Pure-FTPd [TLS]"
      }
  


Monitoring SSH 
===============


When you need to monitor "SSH" servers, you can use the **check_ssh** plugin. The "commands.cfg" file contains a command definition for using the **check_ssh** plugin, which looks like this:

  
::

  define command{
      command_name    check_ssh
      command_line    $USER1$/check_ssh $ARG1$ $HOSTADDRESS$
      }
  
A simple service definition for monitoring the "SSH" server on *remotehost* would look like this:

  
::

  define service{
      use                  generic-service  ; Inherit default values from a template
      host_name            remotehost
      service_description  SSH
      check_command        check_ssh
      }
  
This service definition will monitor the "SSH" service and generate alerts if the "SSH" server doesn't respond within 10 seconds.

A more advanced service definition is shown below. This service will check the "SSH" server and generate an alert if the server doesn't respond within 5 seconds or if the server version string string doesn't match “OpenSSH_4.2".

  
::

  define service{
      use                 generic-service   ; Inherit default values from a template
      host_name           remotehost
      service_description SSH Version Check
      check_command       check_ssh!-t 5 -r "OpenSSH_4.2"
      }
  


Monitoring SMTP 
================


The **check_smtp** plugin can be using for monitoring your email servers. The "commands.cfg" file contains a command definition for using the **check_smtp** plugin, which looks like this:

  
::

  define command{
      command_name    check_smtp
      command_line    $USER1$/check_smtp -H $HOSTADDRESS$ $ARG1$
      }
  
A simple service definition for monitoring the "SMTP" server on *remotehost* would look like this:

  
::

  define service{
      use                  generic-service  ; Inherit default values from a template
      host_name            remotehost
      service_description  SMTP
      check_command        check_smtp
      }
  
This service definition will monitor the "SMTP" service and generate alerts if the "SMTP" server doesn't respond within 10 seconds.

A more advanced service definition is shown below. This service will check the "SMTP" server and generate an alert if the server doesn't respond within 5 seconds or if the response from the server doesn't contain "mygreatmailserver.com".

  
::

  define service{
      use                  generic-service  ; Inherit default values from a template
      host_name            remotehost
      service_description  SMTP Response Check
      check_command        check_smtp!-t 5 -e "mygreatmailserver.com"
      }
  


Monitoring POP3 
================


The **check_pop** plugin can be using for monitoring the "POP3" service on your email servers. The "commands.cfg" file contains a command definition for using the **check_pop** plugin, which looks like this:

  
::

  define command{
      command_name    check_pop
      command_line    $USER1$/check_pop -H $HOSTADDRESS$ $ARG1$
      }
  
A simple service definition for monitoring the "POP3" service on *remotehost* would look like this:

  
::

  define service{
      use                  generic-service  ; Inherit default values from a template
      host_name            remotehost
      service_description  POP3
      check_command        check_pop
      }
  
This service definition will monitor the "POP3" service and generate alerts if the "POP3" server doesn't respond within 10 seconds.

A more advanced service definition is shown below. This service will check the "POP3" service and generate an alert if the server doesn't respond within 5 seconds or if the response from the server doesn't contain "mygreatmailserver.com".

  
::

  define service{
      use                  generic-service  ; Inherit default values from a template
      host_name            remotehost
      service_description  POP3 Response Check
      check_command        check_pop!-t 5 -e "mygreatmailserver.com"
      }
  


Monitoring IMAP 
================


The **check_imap** plugin can be using for monitoring "IMAP4" service on your email servers. The "commands.cfg" file contains a command definition for using the **check_imap** plugin, which looks like this:

  
::

  define command{
      command_name    check_imap
      command_line    $USER1$/check_imap -H $HOSTADDRESS$ $ARG1$
      }
  
A simple service definition for monitoring the "IMAP4" service on *remotehost* would look like this:

  
::

  define service{
      use                  generic-service  ; Inherit default values from a template
      host_name            remotehost
      service_description  IMAP
      check_command        check_imap
      }
  
This service definition will monitor the "IMAP4" service and generate alerts if the "IMAP" server doesn't respond within 10 seconds.

A more advanced service definition is shown below. This service will check the IAMP4 service and generate an alert if the server doesn't respond within 5 seconds or if the response from the server doesn't contain “mygreatmailserver.com".

  
::

  define service{
      use                  generic-service  ; Inherit default values from a template
      host_name            remotehost
      service_description  IMAP4 Response Check
      check_command        check_imap!-t 5 -e "mygreatmailserver.com"
      }
  


Restarting Shinken 
===================


Once you've added the new host and service definitions to your object configuration file(s), you're ready to start monitoring them. To do this, you'll need to :ref:`verify your configuration <runningshinken-verifyconfig>` and :ref:`restart Shinken <runningshinken-startstop>`.

If the verification process produces any errors messages, fix your configuration file before continuing. Make sure that you don't (re)start Shinken until the verification process completes without any errors!


.. _NagiosExchange.org: http://www.nagiosexchange.org

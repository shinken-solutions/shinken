.. _advancedtopics-volatileservices:




===================
 Volatile Services 
===================



Introduction 
=============


Shinken has the ability to distinguish between “normal" services and "volatile" services. The is_volatile option in each service definition allows you to specify whether a specific service is volatile or not. For most people, the majority of all monitored services will be non-volatile (i.e. “normal"). However, volatile services can be very useful when used properly...



What Are They Useful For? 
==========================


Volatile services are useful for monitoring...

  * Things that automatically reset themselves to an "OK" state each time they are checked
  * Events such as security alerts which require attention every time there is a problem (and not just the first time)



What's So Special About Volatile Services? 
===========================================


Volatile services differ from “normal" services in three important ways. Each time they are checked when they are in a :ref:`hard <thebasics-statetypes>` non-OK state, and the check returns a non-OK state (i.e. no state change has occurred)...

  * The non-OK service state is logged
  * Contacts are notified about the problem (if that's :ref:`what should be done <thebasics-notifications>`).Notification intervals are ignored for volatile services.
  * The :ref:`event handler <advancedtopics-eventhandlers>` for the service is run (if one has been defined)

These events normally only occur for services when they are in a non-OK state and a hard state change has just occurred. In other words, they only happen the first time that a service goes into a non-OK state. If future checks of the service result in the same non-OK state, no hard state change occurs and none of the events mentioned take place again.

.. tip::  If you are only interested in logging, consider using :ref:`stalking <advancedtopics-stalking>` options instead.



The Power Of Two 
=================


  * :ref:`Shinken Configuration <advancedtopics-volatileservices#shinken_configuration>`
  * :ref:`PortSentry Configuration <advancedtopics-volatileservices#portsentry_configuration>`
  * :ref:`Port Scan Script <advancedtopics-volatileservices#port_scan_script>`

If you combine the features of volatile services and :ref:`passive service checks <thebasics-passivechecks>`, you can do some very useful things. Examples of this include handling "SNMP" traps, security alerts, etc.

How about an example... Let's say you're running `PortSentry`_ to detect port scans on your machine and automatically firewall potential intruders. If you want to let Shinken know about port scans, you could do the following...



.. _advancedtopics-volatileservices#shinken_configuration:

Shinken Configuration 
----------------------


  * Create a service definition called Port Scans and associate it with the host that PortSentry is running on.
  * Set the "max_check_attempts" directive in the service definition to 1. This will tell Shinken to immediate force the service into a :ref:`hard state <thebasics-statetypes>` when a non-OK state is reported.
  * Set the "active_checks_enabled" directive in the service definition to 0. This prevents Shinken from actively checking the service.
  * Set the "passive_checks_enabled" directive in the service definition to 1. This enables passive checks for the service.
  * Set this "is_volatile" directive in the service definition to 1.



.. _advancedtopics-volatileservices#portsentry_configuration:

PortSentry Configuration 
-------------------------


Edit your PortSentry configuration file ("portsentry.conf") and define a command for the KILL_RUN_CMD directive as follows:

  
::

  KILL_RUN_CMD="/usr/local/Shinken/libexec/eventhandlers/submit_check_result *"host_name"* 'Port Scans' 2 'Port scan from host $TARGET$ on port $PORT$.  Host has been firewalled.'"
  
Make sure to replace host_name with the short name of the host that the service is associated with.



.. _advancedtopics-volatileservices#port_scan_script:

Port Scan Script 
-----------------


Create a shell script in the "/usr/local/shinken/libexec/eventhandlers" directory named **submit_check_result**. The contents of the shell script should be something similiar to the following...

  
::

  
  #!/bin/sh
  
  # Write a command to the Shinken command file to cause
  # it to process a service check result
  
  echocmd="/bin/echo"
  
  CommandFile="/usr/local/shinken/var/rw/shinken.cmd"
  
  # get the current date/time in seconds since UNIX epoch
  datetime=`date +%s`
  
  # create the command line to add to the command file
  cmdline="[$datetime] PROCESS_SERVICE_CHECK_RESULT;$1;$2;$3;$4"
  
  # append the command to the end of the command file
  `$echocmd $cmdline >> $CommandFile`


What will happen when PortSentry detects a port scan on the machine in the future?

  * PortSentry will firewall the host (this is a function of the PortSentry software)
  * PortSentry will execute the **submit_check_result** shell script and send a passive check result to Shinken
  * Shinken will read the external command file and see the passive service check submitted by PortSentry
  * Shinken will put the Port Scans service in a hard CRITICAL state and send notifications to contacts

Pretty neat, huh?


.. _PortSentry: http://sourceforge.net/projects/sentrytools/

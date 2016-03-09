.. _thebasics/passivechecks:

================
 Passive Checks 
================


Introduction 
=============

In most cases you'll use Shinken to monitor your hosts and services using regularly scheduled :ref:`active checks <thebasics/activechecks>`. Active checks can be used to "poll" a device or service for status information every so often. Shinken also supports a way to monitor hosts and services passively instead of actively. They key features of passive checks are as follows:

  * Passive checks are initiated and performed by external applications/processes
  * Passive check results are submitted to Shinken for processing

The major difference between active and passive checks is that active checks are initiated and performed by Shinken, while passive checks are performed by external applications.


Uses For Passive Checks 
========================

Passive checks are useful for monitoring services that are:

  * Asynchronous in nature, they cannot or would not be monitored effectively by polling their status on a regularly scheduled basis
  * Located behind a firewall and cannot be checked actively from the monitoring host

Examples of asynchronous services that lend themselves to being monitored passively include:

  * "SNMP" traps and security alerts. You never know how many (if any) traps or alerts you'll receive in a given time frame, so it's not feasible to just monitor their status every few minutes.
  * Aggregated checks from a host running an agent. Checks may be run at much lower intervals on hosts running an agent.
  * Submitting check results that happen directly within an application without using an intermediate log file(syslog, event log, etc.).

Passive checks are also used when configuring :ref:`distributed <advanced/distributed>` or :ref:`redundant <advanced/redundancy>` monitoring installations.


How Passive Checks Work 
========================

.. image:: /_static/images///official/images/passivechecks.png
   :scale: 90 %


DEPRECATED IMAGE - TODO REPLACE WITH MORE ACCURATE DEPICTION

Here's how passive checks work in more detail...

  * An external application checks the status of a host or service.
  * The external application writes the results of the check to the :ref:`external command named pipe <configuration/configmain-advanced#command_file>` (a named pipe is a "memory pipe", so there is no disk IO involved).
  * Shinken reads the external command file and places the results of all passive checks into a queue for processing by the appropriate process in the Shinken cloud.
  * Shinken will execute a :ref:`check result reaper event <advanced/unused-nagios-parameters/check_result_reaper_frequency>` each second and scan the check result queue. Each service check result that is found in the queue is processed in the same manner - regardless of whether the check was active or passive. Shinken may send out notifications, log alerts, etc. depending on the check result information.

The processing of active and passive check results is essentially identical. This allows for seamless integration of status information from external applications with Shinken.


Enabling Passive Checks 
========================

In order to enable passive checks in Shinken, you'll need to do the following:

  * Set :ref:`"accept_passive_service_checks" <configuration/configmain-advanced#accept_passive_service_checks>` directive is set to 1 (in nagios.cfg).
  * Set the "passive_checks_enabled" directive in your host and service definitions is set to 1.

If you want to disable processing of passive checks on a global basis, set the :ref:`"accept_passive_service_checks" <configuration/configmain-advanced#accept_passive_service_checks>` directive to 0.

If you would like to disable passive checks for just a few hosts or services, use the "passive_checks_enabled" directive in the host and/or service definitions to do so.


Submitting Passive Service Check Results 
=========================================

External applications can submit passive service check results to Shinken by writing a PROCESS_SERVICE_CHECK_RESULT :ref:`external command <advanced/extcommands>` to the external command pipe, which is essentially a file handle that you write to as you would a file.

The format of the command is as follows: "[<timestamp>] PROCESS_SERVICE_CHECK_RESULT;<configobjects/host_name>;<svc_description>;<return_code>;<plugin_output>" where...

  * timestamp is the time in time_t format (seconds since the UNIX epoch) that the service check was perfomed (or submitted). Please note the single space after the right bracket.
  * host_name is the short name of the host associated with the service in the service definition
  * svc_description is the description of the service as specified in the service definition
  * return_code is the return code of the check (0=OK, 1=WARNING, 2=CRITICAL, 3=UNKNOWN)
  * plugin_output is the text output of the service check (i.e. the plugin output)

A service must be defined in Shinken before Shinken will accept passive check results for it! Shinken will ignore all check results for services that have not been configured before it was last (re)started.

An example shell script of how to submit passive service check results to Shinken can be found in the documentation on :ref:`volatile services <advanced/volatileservices>`.


Submitting Passive Host Check Results 
======================================

External applications can submit passive host check results to Shinken by writing a PROCESS_HOST_CHECK_RESULT external command to the external command file.

The format of the command is as follows: "[<timestamp>]PROCESS_HOST_CHECK_RESULT;<configobjects/host_name>;<configobjects/host_status>;<plugin_output>" where...

  * timestamp is the time in time_t format (seconds since the UNIX epoch) that the host check was perfomed (or submitted). Please note the single space after the right bracket.
  * host_name is the short name of the host (as defined in the host definition)
  * host_status is the status of the host (0=UP, 1=DOWN, 2=UNREACHABLE)
  * plugin_output is the text output of the host check

A host must be defined in Shinken before you can submit passive check results for it! Shinken will ignore all check results for hosts that had not been configured before it was last (re)started.

Once data has been received by the Arbiter process, either directly or through a Receiver daemon, it will forward the check results to the appropriate Scheduler to apply check logic.


Passive Checks and Host States 
===============================

Unlike with active host checks, Shinken does not (by default) attempt to determine whether or host is DOWN or UNREACHABLE with passive checks. Rather, Shinken takes the passive check result to be the actual state the host is in and doesn't try to determine the hosts' actual state using the :ref:`reachability logic <thebasics/networkreachability>`. This can cause problems if you are submitting passive checks from a remote host or you have a :ref:`distributed monitoring setup <advanced/distributed>` where the parent/child host relationships are different.

You can tell Shinken to translate DOWN/UNREACHABLE passive check result states to their "proper" state by using the :ref:`"translate_passive_host_checks" <advanced/unused-nagios-parameters#translate_passive_host_checks>` variable. More information on how this works can be found :ref:`here <advanced/passivestatetranslation>`.

Passive host checks are normally treated as :ref:`HARD states <thebasics/statetypes>`, unless the :ref:`"passive_host_checks_are_soft" <configuration/configmain-advanced#passive_host_checks_are_soft>` option is enabled.


Submitting Passive Check Results From Remote Hosts 
===================================================

.. image:: /_static/images///official/images/nsca.png
   :scale: 90 %


DEPRECATED IMAGE - TODO REPLACE WITH MORE ACCURATE DEPICTION

If an application that resides on the same host as Shinken is sending passive host or service check results, it can simply write the results directly to the external command named pipe file as outlined above. However, applications on remote hosts can't do this so easily.

In order to allow remote hosts to send passive check results to the monitoring host, there a multiple modules to that can send and accept passive check results. :ref:`NSCA <nsca_daemon_module>`, TSCA, Shinken WebService and more. 

:ref:`Learn more about the different passive check result/command protocols and how to configure them. <thebasics/passivechecks>`



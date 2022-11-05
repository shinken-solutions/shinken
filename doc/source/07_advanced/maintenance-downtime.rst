.. _advanced/maintenance-downtime:

======================
 Maintenance Downtime
======================


Introduction
=============

.. image:: /_static/images///official/images/downtime.png
   :scale: 90 %

Shinken allows you to schedule periods of planned maintenance for hosts and service that you're monitoring. This is useful in the event that you actually know you're going to be taking a server down for an upgrade, etc. It also allows to dynamically define if an host or a service is under maintenance using maintenance check command calls.


Maintenance Downtime
=====================

Unlike scheduled downtimes, maintenance downtimes can't be set by an user. They behave exactly the same way (maintenance downtimes can be seen as automatically defined scheduled downtimes), but they are meant to be defined through the configuration (using a `maintenance_period`), or dynamically (using a `maintenance_check_command`). Once the downtime has expired, it is automatically deleted, and the machine returns to the normal notification state.

Maintenance period vs. Maintenance check
=========================================

As stated above, there are two different approaches to tell if a machine is under maintenance.

"Maintenance period" is a static period, defined in the host or service configuration. It defines the timeperiod during which the host or the service is to be considered as under maintenance. This approach well suits situation where you know in advance that an host or a service will be totally or partially unavailable. For instance, a recurrent backup operation on a database server.

"Maintenance check" is a dynamic approach where maintenance state is not defined statically but through a command execution, exactly the same way as an host or service state check. A plugin is run, and depending on its returncode, a sliding downtime is created. It automatically expands until another maintenance check tells the machine is back to production. This approach is well suited if you don't know when a machine or a service is unavailable, but you have an external system that can tell it. For instance, a release system, with an API endpoint telling when a release is running. A maintenance downtime can be set when the release starts, and deleted when the release ends.


Downtime duration
==================

When a downtime period starts or a maintenance state is detected by a maintenance check command, a special downtime is created. Its expiration datetime is defined following the rules below:

  - If a maintenance period is running, the downtime expires when we exit the period.
  - If no maintenance period is running, the downtime expires at **now + 3 * maintenance_check_interval**, and the downtime end is re-evaluated each time a command is executed. In other words, it is automatically extended until the host or service is no more detected as under maintenance.
  - If both a maintenance period is running and a maintenance state is detected, a single downtime is created, expiring with the maintenance period, and the maintenance period expires, the downtime continues its extension, exactly as in the previous situation.


Maintenance check command
==========================

A maintenance check command is equivalent to a state check, but it affects the maintenance state of the host or service it's bound to. It is defined through a `command_name`. The command is run by a poller, exactly as of state check, and depending on the command return code, the host or service is detected as under maintenance.

The allowed returncode are:

    * 0 = the host or service is in production
    * 2 = the host or service is under maintenance

Any other value is considered as an error and logged by the scheduler. The fallback state is PRODUCTION in such a situation, to avoid disabling an host or service by accident if the command crashes.

The *1* return code has been ignored, as it's the most used when a command is unexpectedly failing, and the *2* code is semantically closer to what we want to detect than the *3*, which traduces an unknown state.

**It is under your responsibility to ensure that a maintenance check command does never unexpectedly exit a 2 returncode !!**

Example
--------


::

    define service {
        use                           generic-service
        host_name                     lb
        service_description           Web frontend
        check_command                 check_http_frontend
        maintenance_checks_enabled    1
        maintenance_check_command     check_release
        maintenance_check_interval    1
        maintenance_retry_interval    1
        maintenance_check_period      24x7
        ...
    }

    define command {
        command_name                  check_release
        command_line                  $PLUGINSDIR$/check_release_api
    }

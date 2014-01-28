.. _configuringshinken-configmain:




=================================
 Main Configuration File Options 
=================================


When creating and/or editing configuration files, keep the following in mind:

* Lines that start with a '"#"' character are taken to be comments and are not processed
* Variable names are case-sensitive
* If you want to configure a process to use a specific module:

  * You must define the module in a **modules_xxx.cfg** file in the **shinken-specific.d** directory
  * You must reference it in the **modules** section for that process, e.g. the **broker.cfg** file


Config File Location and sample 
--------------------------------


The main configuration files are usually named "nagios.cfg" and "shinken-specific*.cfg". They are located in the "/etc/shinken/" directory.
Sample main configuration files ("/etc/shinken/nagios.cfg", "/etc/shiken/shinken-specific*.cfg") are installed for you when you follow the :ref:`Quickstart installation guide <gettingstarted-quickstart>`.



Broker Modules 
---------------


Shinken provides a lot of functionality through its interfaces with external systems. To this end, the broker daemon will load modules. The function of the modules is described in more detail in the :ref:`Broker modules page <the_broker_modules>`.

Broker modules are essential for the web frontends, the metric databases, logging state changes in log management systems.



Arbiter, Receiver, Poller, Reactionner Modules 
-----------------------------------------------


Shinken daemons can also load modules to influence what they can do and how they interface with external systems.

The sample configuration file provides succinct explanations of each module, the shinken architecture page also links to the different module configuration pages.



Path, users and log variables 
------------------------------


Below you will find descriptions of each main Shinken configuration file option.



.. _configuringshinken-configmain#configuringshinken-configmain-log_file:


Log File 
~~~~~~~~~

Defined in shinken-specific.cfg file.

Format

::

  define broker{
       modules           <logging modules>
       [...]
  }
  
  
Example for logging module named "Simple_log"

::

   define module{
       module_name      Simple-log
       module_type      simple_log
       path             /var/lib/shinken/nagios.log
       archive_path     /var/lib/shinken/archives/
   }
  
  
  
This variable specifies where Shinken should create its main log file **on the broker server**. If you have :ref:`Log Rotation Method <configuringshinken-configmain#configuringshinken-configmain-log_rotation_method>` enabled, this file will automatically be rotated every day.




Log Level 
~~~~~~~~~~

Defined in nagios.cfg file.

Format

::

  log_level=[DEBUG,INFO,WARNING,ERROR,CRITICAL]
  
Example :

::

  log_level=WARNING
  
  
This variable specifies which logs will be raised by the arbiter daemon. For others daemons, it can be defined in their local \*d.ini files.



.. _configuringshinken-configmain#configuringshinken-configmain-date_format:

Human format for log timestamp 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Say if the timespam should be a unixtime (default) or a human read one.

Format :

::

  human_timestamp_log=[0/1]
  
Example

::

  human_timestamp_log=0
  
  
This directive is used to specify if the timespam before the log entry should be in unixtime (like [1302874960]) which is the default, or a human readable one (like [Fri Apr 15 15:43:19 2011]).

Beware : if you set the human format, some automatic parsing log tools won't work!



.. _configuringshinken-configmain#configuringshinken-configmain-cfg_file:

Object Configuration File 
~~~~~~~~~~~~~~~~~~~~~~~~~~

Defined in nagios.cfg file.

Format :

::

  cfg_file=<file_name>
  
Example

::

  cfg_file=/usr/local/shinken/etc/hosts.cfg
  cfg_file=/usr/local/shinken/etc/services.cfg
  cfg_file=/usr/local/shinken/etc/commands.cfg
  
This directive is used to specify an :ref:`Object Configuration Overview <configuringshinken-configobject>` containing object definitions that Shinken should use for monitoring. Object configuration files contain definitions for hosts, host groups, contacts, contact groups, services, commands, etc. You can seperate your configuration information into several files and specify multiple "cfg_file=" statements to have each of them processed.

Remark : the *cfg_file* can be a relative path, so it can be relative from the file that is reading. For example if you set "cfg_file=hosts.cfg" in the file "cfg_file=/etc/shinken/nagios.cfg", the file that will be read is "/etc/shinken/hosts.cfg".

.. _configuringshinken-configmain#configuringshinken-configmain-cfg_dir:

Object Configuration Directory 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Defined in nagios.cfg file.

Format:

::

  cfg_dir=<directory_name>

Example:

::

  cfg_dir=/etc/shinken/commands
  cfg_dir=/etc/shinken/services
  cfg_dir=/etc/shinken/hosts
  
This directive is used to specify a directory which contains :ref:`Object Configuration Overview <configuringshinken-configobject>` that Shinken should use for monitoring. All files in the directory with a .cfg extension are processed as object config files. Additionally, it will recursively process all config files in subdirectories of the directory you specify here. You can separate your configuration files into different directories and specify multiple

::

  cfg_dir=
  
statements to have all config files in each directory processed.



.. _configuringshinken-configmain#configuringshinken-configmain-resource_file:


Resource File 
~~~~~~~~~~~~~~

Defined in nagios.cfg file.

Format:
   resource_file=<file_name>
Example:

::

  resource_file=/etc/shinken/resource.cfg
  
This is used to specify an optional resource file that can contain "$USERn$" :ref:`Understanding Macros and How They Work <thebasics-macros>` definitions. "$USERn$" macros are useful for storing usernames, passwords, and items commonly used in command definitions (like directory paths). A classical variable used is $USER1$, used to store the plugins path, "/usr/local/nagios/libexec" on a classic installation.



.. _configuringshinken-configmain#configuringshinken-configmain-nagios_user:

Arbiter Daemon User 
~~~~~~~~~~~~~~~~~~~~

Defined in brokerd.ini, brokerd-windows.ini, pollerd.ini, pollerd-windows.ini, reactionnerd.ini, schedulerd.ini and schedulerd-windows.ini.

Format:

::

  user=username

Example:

::

  user=shinken
  
This is used to set the effective user that the **Arbiter** process (main process) should run as. After initial program startup, Shinken will drop its effective privileges and run as this user.


.. _configuringshinken-configmain#configuringshinken-configmain-nagios_group:

Arbiter Daemon user Group 
~~~~~~~~~~~~~~~~~~~~~~~~~~

Defined in brokerd.ini, brokerd-windows.ini, pollerd.ini, pollerd-windows.ini, reactionnerd.ini, schedulerd.ini and schedulerd-windows.ini.

Format:

::

  group=groupname

Example:

::

  group=shinken
  
This is used to set the effective group of the user used to launch the **arbiter** daemon.




Bypass security checks for the Arbiter daemon 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Defined in brokerd.ini, brokerd-windows.ini, pollerd.ini, pollerd-windows.ini, reactionnerd.ini, schedulerd.ini and schedulerd-windows.ini.

Format:

::

  idontcareaboutsecurity=<0/1>

Example:

::

  idontcareaboutsecurity=0
  
This option determines whether or not Shinken will allow the Arbiter daemon to run under the root account. If this option is disabled, Shinken will bailout if the :ref:`nagios_user <configuringshinken-configmain#configuringshinken-configmain-nagios_user>` or the :ref:`nagios_group <configuringshinken-configmain#configuringshinken-configmain-nagios_group>` is configured with the root account.

The Shinken daemons do not need root right. Without a good reason do not run thems under this account!
  * 0 = Be a responsible administrator
  * 1 = Make crazy your security manager



.. _configuringshinken-configmain#configuringshinken-configmain-enable_notifications:

Notifications Option 
~~~~~~~~~~~~~~~~~~~~~


Format:

::

  enable_notifications=<0/1>

Example:

::

  enable_notifications=1
  
This option determines whether or not Shinken will send out :ref:`notifications <thebasics-notifications>`. If this option is disabled, Shinken will not send out notifications for any host or service.

Values are as follows:
  * 0 = Disable notifications
  * 1 = Enable notifications (default)


.. _configuringshinken-configmain#configuringshinken-configmain-log_rotation_method:

Log Rotation Method (Not fully implemented) 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


Format:

::

  log_rotation_method=<n/h/d/w/m>

Example:

::

  log_rotation_method=d
  
This is the rotation method that you would like Shinken to use for your log file on the **broker server**. Values are as follows:

  * n = None (don't rotate the log - this is the default)
  * h = Hourly (rotate the log at the top of each hour)
  * d = Daily (rotate the log at midnight each day)
  * w = Weekly (rotate the log at midnight on Saturday)
  * m = Monthly (rotate the log at midnight on the last day of the month)

.. tip::  From now, only the d (Daily) parameter is managed. 


.. _configuringshinken-configmain#configuringshinken-configmain-check_external_commands:

External Command Check Option 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


Format:

::

  check_external_commands=<0/1>

Example:

::

  check_external_commands=1
  
This option determines whether or not Shinken will check the :ref:`External Command File <configuringshinken-configmain#configuringshinken-configmain-command_file>` for commands that should be executed with the **arbiter daemon**. More information on external commands can be found :ref:`here <advancedtopics-extcommands>`.

  * 0 = Don't check external commands (default)
  * 1 = Check external commands (default)

.. note::  FIX ME : Find the real default value


.. _configuringshinken-configmain#configuringshinken-configmain-command_file:

External Command File 
~~~~~~~~~~~~~~~~~~~~~~

Defined in nagios.cfg file.

Format:

::

  command_file=<file_name>

Example:

::

  command_file=/var/lib/shinken/rw/nagios.cmd
  
This is the file that Shinken will check for external commands to process with the **arbiter daemon**. The :ref:`command CGI <thebasics-cgis#thebasics-cgis-cmd_cgi>` writes commands to this file. The external command file is implemented as a named pipe (FIFO), which is created when Nagios starts and removed when it shuts down. More information on external commands can be found :ref:`here <advancedtopics-extcommands>`.

.. FIXME: where is thebasics-cgis#thebasics-cgis-cmd_cgi ?

.. tip::  This external command file is not managed under Windows system. Please use others way to send commands like the LiveStatus module for example.




Arbiter Lock File 
~~~~~~~~~~~~~~~~~~

Defined in nagios.cfg file.

Format:  
lock_file=<file_name>
Example:  
lock_file=/var/lib/shinken/arbiterd.pid

This option specifies the location of the lock file that Shinken **arbiter daemon** should create when it runs as a daemon (when started with the "-d" command line argument). This file contains the process id (PID) number of the running **arbiter** process.


.. _configuringshinken-configmain#configuringshinken-configmain-retain_state_information:

State Retention Option (Not implemented) 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


Format:

::

  retain_state_information=<0/1>

Example:

::

  retain_state_information=1
  
This option determines whether or not Shinken will retain state information for hosts and services between program restarts. If you enable this option, you should supply a value for the :ref:`State Retention File <configuringshinken-configmain#configuringshinken-configmain-state_retention_file>` variable. When enabled, Shinken will save all state information for hosts and service before it shuts down (or restarts) and will read in previously saved state information when it starts up again.
  * 0 = Don't retain state information
  * 1 = Retain state information (default)

.. note::  Idea to approve : Mark it as Unused : `Related topic`_. A Shinken module replace it.



State Retention File 
~~~~~~~~~~~~~~~~~~~~~


Format:  

::

  state_retention_file=<file_name>

Example:  

::

  state_retention_file=/var/lib/shinken/retention.dat
  
This is the file that Shinken **scheduler daemons** will use for storing status, downtime, and comment information before they shuts down. When Shinken is restarted it will use the information stored in this file for setting the initial states of services and hosts before it starts monitoring anything. In order to make Shinken retain state information between program restarts, you must enable the :ref:`State Retention Option <configuringshinken-configmain#configuringshinken-configmain-retain_state_information>` option.

.. important::  The file format is not the same between Shinken and Nagios! The retention.dat generated with Nagios will not load into Shinken.



Automatic State Retention Update Interval 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


Format:

::

  retention_update_interval=<minutes>

Example:

::

  retention_update_interval=60
  
This setting determines how often (in minutes) that Shinken **scheduler** will automatically save retention data during normal operation. If you set this value to 0, it will not save retention data at regular intervals, but it will still save retention data before shutting down or restarting. If you have disabled state retention (with the :ref:`State Retention Option <configuringshinken-configmain#configuringshinken-configmain-retain_state_information>` option), this option has no effect.




Scheduling parameters 
----------------------




.. _configuringshinken-configmain#configuringshinken-configmain-execute_service_checks:

Service/Host Check Execution Option 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


Format:

::

  execute_service_checks=<0/1>
  execute_host_checks=<0/1>

Example:

::

  execute_service_checks=1
  execute_host_checks=1
  
This option determines whether or not Shinken will execute service/host checks. Do not change this option unless you use a old school distributed architecture. And even if you do this, please change your architecture with a cool new one far more efficient.

  * 0 = Don't execute service checks
  * 1 = Execute service checks (default)



.. _configuringshinken-configmain#configuringshinken-configmain-accept_passive_service_checks:

Passive Service/Host Check Acceptance Option 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


Format:

::

  accept_passive_service_checks=<0/1>
  accept_passive_host_checks=<0/1>

Example:

::

  accept_passive_service_checks=1
  accept_passive_host_checks=1
  
This option determines whether or not Shinken will accept :ref:`passive service/host checks <thebasics-passivechecks>`. If this option is disabled, Nagios will not accept any passive service/host checks.

  * 0 = Don't accept passive service/host checks
  * 1 = Accept passive service/host checks (default)



.. _configuringshinken-configmain#configuringshinken-configmain-enable_event_handlers:

Event Handler Option 
~~~~~~~~~~~~~~~~~~~~~


Format:

::

  enable_event_handlers=<0/1>

Example:

::

  enable_event_handlers=1
  
This option determines whether or not Shinken will run :ref:`event handlers <advancedtopics-eventhandlers>`.

  * 0 = Disable event handlers
  * 1 = Enable event handlers (default)



Event Handler during downtimes 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


Format:

::

  no_event_handlers_during_downtimes=<0/1>

Example:

::

  no_event_handlers_during_downtimes=1
  
This option determines whether or not Shinken will run :ref:`event handlers <advancedtopics-eventhandlers>` when the host or service is in a scheduled downtime.

  * 0 = Disable event handlers (Nagios behavior) (default)
  * 1 = Enable event handlers

References:

  * http://www.mail-archive.com/shinken-devel@lists.sourceforge.net/msg01394.html
  * https://github.com/naparuba/shinken/commit/9ce28d80857c137e5b915b39bbb8c1baecc821f9



Syslog Logging Option 
~~~~~~~~~~~~~~~~~~~~~~


Format:  

::

  use_syslog=<0/1>

Example:  

::

  use_syslog=1
  
This variable determines whether messages are logged to the syslog facility on your local host. Values are as follows:

  * 0 = Don't use syslog facility
  * 1 = Use syslog facility

.. tip::  This is a Unix Os only option.



Notification Logging Option 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~


Format:

::

  log_notifications=<0/1>

Example:

::

  log_notifications=1
  
This variable determines whether or not notification messages are logged. If you have a lot of contacts or regular service failures your log file will grow (let say some Mo by day for a huge configuration, so it's quite OK for nearly every one to log them). Use this option to keep contact notifications from being logged.

  * 0 = Don't log notifications
  * 1 = Log notifications



Service/Host Check Retry Logging Option (Not implemented) 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


Format:

::

  log_service_retries=<0/1>
  log_host_retries=<0/1>

Example:

::

  log_service_retries=0
  log_host_retries=0
  
This variable determines whether or not service/host check retries are logged. Service check retries occur when a service check results in a non-OK state, but you have configured Shinken to retry the service more than once before responding to the error. Services in this situation are considered to be in "soft" states. Logging service check retries is mostly useful when attempting to debug Shinken or test out service/host :ref:`event handlers <advancedtopics-eventhandlers>`.

  * 0 = Don't log service/host check retries (default)
  * 1 = Log service/host check retries



Event Handler Logging Option 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


Format:

::

  log_event_handlers=<0/1>

Example:

::

  log_event_handlers=1
  
This variable determines whether or not service and host :ref:`event handlers <advancedtopics-eventhandlers>` are logged. Event handlers are optional commands that can be run whenever a service or hosts changes state. Logging event handlers is most useful when debugging Shinken or first trying out your event handler scripts.

  * 0 = Don't log event handlers
  * 1 = Log event handlers




Initial States Logging Option (Not implemented) 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Format:  

::

  log_initial_states=<0/1>

Example:

::

  log_initial_states=1

This variable determines whether or not Shinken will force all initial host and service states to be logged, even if they result in an OK state. Initial service and host states are normally only logged when there is a problem on the first check. Enabling this option is useful if you are using an application that scans the log file to determine long-term state statistics for services and hosts.

  * 0 = Don't log initial states (default)
  * 1 = Log initial states




External Command Logging Option 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


Format:

::

  log_external_commands=<0/1>

Example:

::

  log_external_commands=1
  
This variable determines whether or not Shinken will log :ref:`external commands <advancedtopics-extcommands>` that it receives.

  * 0 = Don't log external commands
  * 1 = Log external commands (default)




Passive Check Logging Option (Not implemented)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


Format:

::

  log_passive_checks=<0/1>

Example:

::

  log_passive_checks=1
  
This variable determines whether or not Shinken will log :ref:`passive host and service checks <thebasics-passivechecks>` that it receives from the :ref:`external command file <configuringshinken-configmain#configuringshinken-configmain-command_file>`.

  * 0 = Don't log passive checks
  * 1 = Log passive checks (default)




Global Host/Service Event Handler Option (Not implemented) 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


Format:

::

  global_host_event_handler=<command>
  global_service_event_handler=<command>

Example:

::

  global_host_event_handler=log-host-event-to-db
  global_service_event_handler=log-service-event-to-db
  
This option allows you to specify a host event handler command that is to be run for every host state change. The global event handler is executed immediately prior to the event handler that you have optionally specified in each host definition. The command argument is the short name of a command that you define in your :ref:`Object Configuration Overview <configuringshinken-configobject>`. The maximum amount of time that this command can run is controlled by the :ref:`Event Handler Timeout <configuringshinken-configmain#configuringshinken-configmain-event_handler_timeout>` option. More information on event handlers can be found :ref:`here <advancedtopics-eventhandlers>`.

.. FIXME where is configuringshinken-configmain#configuringshinken-configmain-global_service_event_handler ??

Such commands should not be so useful with the new Shinken distributed architecture. If you use it, look if you can avoid it because such commands will kill your performances.



Maximum Host/Service Check Spread 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


Format:

::

  max_service_check_spread=<minutes>

Example:

::

  max_service_check_spread=30
  
This option determines the maximum number of minutes from when Shinken starts that all hosts/services (that are scheduled to be regularly checked) are checked. This option will ensure that the initial checks of all hosts/services occur within the timeframe you specify. Default value is 30 (minutes).



.. _configuringshinken-configmain#configuringshinken-configmain-interval_length:

Timing Interval Length 
~~~~~~~~~~~~~~~~~~~~~~~


Format:

::

  interval_length=<seconds>

Example:

::

  interval_length=60
  
This is the number of seconds per “unit interval" used for timing in the scheduling queue, re-notifications, etc. "Units intervals" are used in the object configuration file to determine how often to run a service check, how often to re-notify a contact, etc.

The default value for this is set to 60, which means that a "unit value" of 1 in the object configuration file will mean 60 seconds (1 minute). 

.. tip::  Set this option top 1 is not a good thing with Shinken. It's not design to be a hard real time (<5seconds) monitoring system. Nearly no one need such hard real time (maybe only the Nuclear center or a market place like the London Exchange...).



Tuning and advanced parameters 
-------------------------------

Others parameters are useful for advanced features like flapping detection or performance tuning. Please look at the 
:ref:`configuringshinken-configmain-advanced <configuringshinken-configmain-advanced>` page for them.




Old CGI related parameter 
--------------------------

If you are using the old CGI from Nagios, please migrate to a new WebUI. For historical perspective you can find information on the :ref:`specific CGI parameters <specific_cgi_parameters>`.



Unused parameters 
------------------

The below parameters are inherited from Nagios but are not used in Shinken. You can defined them but if you don't it will be the same :)

They are listed on another page :ref:`Unused Nagios parameters <unused_nagios_parameters>`.



.. _Related topic: http://www.shinken-monitoring.org/forum/index.php/topic,21.0.html

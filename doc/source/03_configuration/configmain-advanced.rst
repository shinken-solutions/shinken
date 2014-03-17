.. _configuration/configmain-advanced:

===========================
Main advanced configuration
===========================


Tuning and advanced parameters 
===============================

.. important::  If you do not know how to change the values of theses parameters, don't touch them :)
   (and ask for help on the mailing list).


Performance data parameters 	
============================

Performance Data Processor Command Timeout 
-------------------------------------------

Format:  

::

  perfdata_timeout=<seconds>

Example:  

::

  perfdata_timeout=5
  
This is the maximum number of seconds that Shinken will allow a :ref:`host performance data processor command <configuration/configmain-advanced#host_perfdata_file_processing_command>` or :ref:`service performance data processor command <configuration/configmain-advanced#service_perfdata_file_processing_command>` to be run. If a command exceeds this time limit it will be killed and a warning will be logged.


.. _configuration/configmain-advanced#process_performance_data:

Performance Data Processing Option 
-----------------------------------

Format:

::

  process_performance_data=<0/1>

Example:

::

  process_performance_data=1

This value determines whether or not Shinken will process host and service check :ref:`performance data <advanced/perfdata>`.

  * 0 = Don't process performance data 
  * 1 = Process performance data (default)

If you want to use tools like PNP, NagiosGrapher or Graphite set it to 1.


.. _configuration/configmain-advanced#host_perfdata_command:
.. _configuration/configmain-advanced#service_perfdata_command:

Host/Service Performance Data Processing Command 
-------------------------------------------------

Format:

::

  host_perfdata_command=<configobjects/command>
  service_perfdata_command=<configobjects/command>

Example:

::

  host_perfdata_command=process-host-perfdata
  services_perfdata_command=process-service-perfdata
  
This option allows you to specify a command to be run after every host/service check to process host/service :ref:`performance data <advanced/perfdata>` that may be returned from the check. The command argument is the short name of a :ref:`command definition <configobjects/command>` that you define in your object configuration file. This command is only executed if the :ref:`Performance Data Processing Option <configuration/configmain-advanced#process_performance_data>` option is enabled globally and if the "process_perf_data" directive in the :ref:`host definition <configobjects/host>` is enabled.


.. _configuration/configmain-advanced#host_perfdata_file:
.. _configuration/configmain-advanced#service_perfdata_file:

Host/Service Performance Data File 
-----------------------------------

Format:

::

  host_perfdata_file=<file_name>
  service_perfdata_file=<file_name>

Example:

::

  host_perfdata_file=/usr/local/shinken/var/host-perfdata.dat
  service_perfdata_file=/usr/local/shinken/var/service-perfdata.dat
  
This option allows you to specify a file to which host/service :ref:`performance data <advanced/perfdata>` will be written after every host check. Data will be written to the performance file as specified by the :ref:`Host Performance Data File Template <configuration/configmain-advanced#host_perfdata_file_template>` option or the service one. Performance data is only written to this file if the :ref:`Performance Data Processing Option <configuration/configmain-advanced#process_performance_data>` option is enabled globally and if the "process_perf_data" directive in the :ref:`host definition <configobjects/host>` is enabled.


.. _configuration/configmain-advanced#host_perfdata_file_template:

Host Performance Data File Template 
------------------------------------

Format:

::

  host_perfdata_file_template=<template>

Example:

::

  host_perfdata_file_template=[HOSTPERFDATA]\t$TIMET$\t$HOSTNAME$\t$HOSTEXECUTIONTIME$\t$HOSTOUTPUT$\t$HOSTPERFDATA$
  
This option determines what (and how) data is written to the :ref:`host performance data file <configuration/configmain-advanced#host_perfdata_file>`. The template may contain :ref:`macros <thebasics/macros>`, special characters (\t for tab, \r for carriage return, \n for newline) and plain text. A newline is automatically added after each write to the performance data file.


.. _configuration/configmain-advanced#service_perfdata_file_template:

Service Performance Data File Template 
---------------------------------------

Format:

::

  service_perfdata_file_template=<template>

Example:

::

  service_perfdata_file_template=[SERVICEPERFDATA]\t$TIMET$\t$HOSTNAME$\t$SERVICEDESC$\t$SERVICEEXECUTIONTIME$\t$SERVICELATENCY$\t$SERVICEOUTPUT$\t$SERVICEPERFDATA$
  
This option determines what (and how) data is written to the :ref:`service performance data file <configuration/configmain-advanced#service_perfdata_file>`. The template may contain :ref:`macros <thebasics/macros>`, special characters (\t for tab, \r for carriage return, \n for newline) and plain text. A newline is automatically added after each write to the performance data file.


.. _configuration/configmain-advanced#host_perfdata_file_mode:
.. _configuration/configmain-advanced#service_perfdata_file_mode:

Host/Service Performance Data File Mode 
----------------------------------------

Format:

::

  host_perfdata_file_mode=<mode>
  service_perfdata_file_mode=<mode>

Example:

::

  host_perfdata_file_mode=a
  service_perfdata_file_mode=a
  
This option determines how the :ref:`host performance data file <configuration/configmain-advanced#host_perfdata_file>` (or the service one) is opened. Unless the file is a named pipe you'll probably want to use the default mode of append.

  * a = Open file in append mode (default)
  * w = Open file in write mode
  * p = Open in non-blocking read/write mode (useful when writing to pipes)


.. _configuration/configmain-advanced#host_perfdata_file_processing_interval:
.. _configuration/configmain-advanced#service_perfdata_file_processing_interval:

Host/Service Performance Data File Processing Interval (Unused) 
----------------------------------------------------------------

Format:

::

  host_perfdata_file_processing_interval=<seconds>
  service_perfdata_file_processing_interval=<seconds>

Example:

::

  host_perfdata_file_processing_interval=0
  service_perfdata_file_processing_interval=0
  
<<<<<<< HEAD:doc/source/03_configuringshinken/configuringshinken-configmain-advanced.rst
This option allows you to specify the interval (in seconds) at which the :ref:`host performance data file <configuringshinken-configmain#configuringshinken-configmain-host_perfdata_file>` (or the service one) is processed using the :ref:`host performance data file processing command <configuringshinken-configmain#configuringshinken-configmain-host_perfdata_command>`. A value of 0 indicates that the performance data file should not be processed at regular intervals.
=======
This option allows you to specify the interval (in seconds) at which the :ref:`host performance data file <configuration/configmain-advanced#host_perfdata_file>` (or the service one) is processed using the :ref:`host performance data file processing command <configuration/configmain-advanced#host_perfdata_command>`. A value of 0 indicates that the performance data file should not be processed at regular intervals.
>>>>>>> upstream/master:doc/source/03_configuration/configmain-advanced.rst


.. _configuration/configmain-advanced#host_perfdata_file_processing_command:
.. _configuration/configmain-advanced#service_perfdata_file_processing_command:

Host/Service Performance Data File Processing Command (Unused) 
---------------------------------------------------------------

Format:

::

  host_perfdata_file_processing_command=<configobjects/command>
  service_perfdata_file_processing_command=<configobjects/command>

Example:

::

  host_perfdata_file_processing_command=process-host-perfdata-file
  service_perfdata_file_processing_command=process-service-perfdata-file
  
This option allows you to specify the command that should be executed to process the :ref:`host performance data file <configuration/configmain-advanced#host_perfdata_file>` (or the service one). The command argument is the short name of a :ref:`command definition <configobjects/command>` that you define in your object configuration file. The interval at which this command is executed is determined by the :ref:`host_perfdata_file_processing_interval <configuration/configmain-advanced#host_perfdata_file_processing_interval>` directive.


Advanced scheduling parameters 
===============================


.. _configuration/configmain-advanced#passive_host_checks_are_soft:

Passive Host Checks Are SOFT Option (Not implemented) 
------------------------------------------------------

Format:

::

  passive_host_checks_are_soft=<0/1>

Example:

::

  passive_host_checks_are_soft=1
  
This option determines whether or not Shinken will treat :ref:`passive host checks <thebasics/passivechecks>` as HARD states or SOFT states. By default, a passive host check result will put a host into a :ref:`HARD state type <thebasics/statetypes>`. You can change this behavior by enabling this option.

  * 0 = Passive host checks are HARD (default)
  * 1 = Passive host checks are SOFT



.. _configuration/configmain-advanced#enable_predictive_host_dependency_checks:
.. _configuration/configmain-advanced#enable_predictive_service_dependency_checks:

Predictive Host/Service Dependency Checks Option (Unused) 
----------------------------------------------------------

Format:

::

  enable_predictive_host_dependency_checks=<0/1>
  enable_predictive_service_dependency_checks=<0/1>

Example:

::

  enable_predictive_host_dependency_checks=1
  enable_predictive_service_dependency_checks=1
  
This option determines whether or not Shinken will execute predictive checks of hosts/services that are being depended upon (as defined in :ref:`host/services dependencies <advanced/dependencies>`) for a particular host/service when it changes state. Predictive checks help ensure that the dependency logic is as accurate as possible. More information on how predictive checks work can be found :ref:`here <advanced/dependencychecks>`.

  * 0 = Disable predictive checks
  * 1 = Enable predictive checks (default)


.. _configuration/configmain-advanced#check_for_orphaned_services:
.. _configuration/configmain-advanced#check_for_orphaned_hosts:

Orphaned Host/Service Check Option 
-----------------------------------

Format:

::

  check_for_orphaned_services=<0/1>
  check_for_orphaned_hosts=<0/1>

Example:

::

  check_for_orphaned_services=1
  check_for_orphaned_hosts=1
  
This option allows you to enable or disable checks for orphaned service/host checks. Orphaned checks are checks which have been launched to pollers but have not had any results reported in a long time.

Since no results have come back in for it, it is not rescheduled in the event queue. This can cause checks to stop being executed. Normally it is very rare for this to happen - it might happen if an external user or process killed off the process that was being used to execute a check.

If this option is enabled and Shinken finds that results for a particular check have not come back, it will log an error message and reschedule the check. If you start seeing checks that never seem to get rescheduled, enable this option and see if you notice any log messages about orphaned services.

  * 0 = Don't check for orphaned service checks
  * 1 = Check for orphaned service checks (default)


.. _configuration/configmain-advanced#max_plugins_output_length:

Max Plugins Output Length 
--------------------------

Format:

::

  max_plugins_output_length=<int>

Example:

::

  max_plugins_output_length=8192
  
This option is used to set the max size in bytes for the checks plugins output. So if you saw truncated output like for huge disk check when you have a lot of partitions, raise this value.


.. _configuration/configmain-advanced#enable_problem_impacts_states_change:

Enable problem/impacts states change 
-------------------------------------

Format:

::

  enable_problem_impacts_states_change=<0/1>

Example:

::

  enable_problem_impacts_states_change=0
  
This option is used to know if we apply or not the state change when an host or service is impacted by a root problem (like the service's host going down or a host's parent being down too). The state will be changed by UNKNONW for a service and UNREACHABLE for an host until their next schedule check. This state change do not count as a attempt, it's just for console so the users know that theses objects got problems and the previous states are not sure.


.. _configuration/configmain-advanced#soft_state_dependencies:

Soft State Dependencies Option (Not implemented) 
-------------------------------------------------

Format:  soft_state_dependencies=<0/1>
Example:  soft_state_dependencies=0

This option determines whether or not Shinken will use soft state information when checking :ref:`host and service dependencies <advanced/dependencies>`. Normally it will only use the latest hard host or service state when checking dependencies. If you want it to use the latest state (regardless of whether its a soft or hard :ref:`state type <thebasics/statetypes>`), enable this option.

  * 0 = Don't use soft state dependencies (default)
  * 1 = Use soft state dependencies


Performance tuning 
===================

.. _configuration/configmain-advanced#cached_host_check_horizon:
.. _configuration/configmain-advanced#cached_service_check_horizon:

Cached Host/Service Check Horizon 
----------------------------------

Format:

::

  cached_host_check_horizon=<seconds>
  cached_service_check_horizon=<seconds>

Example:

::

   cached_host_check_horizon=15
   cached_service_check_horizon=15
  
This option determines the maximum amount of time (in seconds) that the state of a previous host check is considered current. Cached host states (from host/service checks that were performed more recently than the time specified by this value) can improve host check performance immensely. Too high of a value for this option may result in (temporarily) inaccurate host/service states, while a low value may result in a performance hit for host/service checks. Use a value of 0 if you want to disable host/service check caching. More information on cached checks can be found :ref:`here <advanced/cachedchecks>`.

.. tip::  Nagios default is 15s, but it's a tweak that make checks less accurate. So Shinken use 0s as a default. If you have performances problems and you can't add a new scheduler or poller, increase this value and start to buy a new server because this won't be magical.


.. _configuration/configmain-advanced#use_large_installation_tweaks:

Large Installation Tweaks Option 
---------------------------------

Format:

::

  use_large_installation_tweaks=<0/1>

Example:

::

  use_large_installation_tweaks=0
  
This option determines whether or not the Shinken daemon will take shortcuts to improve performance. These shortcuts result in the loss of a few features, but larger installations will likely see a lot of benefit from doing so. If you can't add new satellites to manage the load (like new pollers), you can activate it. More information on what optimizations are taken when you enable this option can be found :ref:`here <tuning/largeinstalltweaks>`.

  * 0 = Don't use tweaks (default)
  * 1 = Use tweaks


.. _configuration/configmain-advanced#enable_environment_macros:

Environment Macros Option 
--------------------------

Format:

::

  enable_environment_macros=<0/1>

Example:

::

  enable_environment_macros=0
  
This option determines whether or not the Shinken daemon will make all standard :ref:`macros <thebasics/macrolist>` available as environment variables to your check, notification, event hander, etc. commands. In large installations this can be problematic because it takes additional CPU to compute the values of all macros and make them available to the environment. It also cost a increase network communication between schedulers and pollers.

  * 0 = Don't make macros available as environment variables
  * 1 = Make macros available as environment variables (default)


Flapping parameters 
====================

.. _configuration/configmain-advanced#enable_flap_detection:

Flap Detection Option 
----------------------

Format:

::

  enable_flap_detection=<0/1>

Example:

::

  enable_flap_detection=1
  
This option determines whether or not Shinken will try and detect hosts and services that are “flapping". Flapping occurs when a host or service changes between states too frequently, resulting in a barrage of notifications being sent out. When Shinken detects that a host or service is flapping, it will temporarily suppress notifications for that host/service until it stops flapping.

More information on how flap detection and handling works can be found :ref:`here <advanced/flapping>`.

  * 0 = Don't enable flap detection (default)
  * 1 = Enable flap detection


.. _configuration/configmain-advanced#low_host_flap_threshold:
.. _configuration/configmain-advanced#low_service_flap_threshold:

Low Service/Host Flap Threshold 
--------------------------------

Format:

::

  low_service_flap_threshold=<percent>
  low_host_flap_threshold=<percent>

Example:

::

  low_service_flap_threshold=25.0
  low_host_flap_threshold=25.0
  
This option is used to set the low threshold for detection of host/service flapping. For more information on how flap detection and handling works (and how this option affects things) read :ref:`this <advanced/flapping>`.


.. _configuration/configmain-advanced#high_host_flap_threshold:
.. _configuration/configmain-advanced#high_service_flap_threshold:

High Service/Host Flap Threshold 
---------------------------------

Format:

::

  high_service_flap_threshold=<percent>
  high_host_flap_threshold=<percent>

Example:

::

  high_service_flap_threshold=50.0
  high_host_flap_threshold=50.0
  
This option is used to set the high threshold for detection of host/service flapping. For more information on how flap detection and handling works (and how this option affects things) read :ref:`this <advanced/flapping>`.


.. _configuration/configmain-advanced#flap_history:

Flap History 
-------------

Format:

::

  flap_history=<int>
  
Example:

::

  flap_history=20

This option is used to set the history size of states keep by the scheduler to make the flapping calculation. By default, the value is 20 states kept.

The size in memory is for the scheduler daemon : 4Bytes * flap_history * (nb hosts + nb services). For a big environment, it costs 4 * 20 * (1000+10000) - 900Ko. So you can raise it to higher value if you want. To have more information about flapping, you can read :ref:`this <advanced/flapping>`.


Commands/checks timeout 
=======================

.. _configuration/configmain-advanced#host_check_timeout:
.. _configuration/configmain-advanced#service_check_timeout:

Service/Host Check Timeout 
---------------------------

Format:

::

  service_check_timeout=<seconds>

Example:

::

  service_check_timeout=60
  
This is the maximum number of seconds that Shinken will allow service checks to run. If checks exceed this limit, they are killed and a CRITICAL state is returned. A timeout error will also be logged.

There is often widespread confusion as to what this option really does. It is meant to be used as a last ditch mechanism to kill off plugins which are misbehaving and not exiting in a timely manner. It should be set to something high (like 60 seconds or more), so that each check normally finishes executing within this time limit. If a check runs longer than this limit, Shinken will kill it off thinking it is a runaway processes.


.. _configuration/configmain-advanced#event_handler_timeout:
.. _configuration/configmain-advanced#notification_timeout:

Various commands Timeouts 
--------------------------

Format:

::

  event_handler_timeout=<seconds>  # default: 30s
  notification_timeout=<seconds>   # default: 30s
  ocsp_timeout=<seconds>           # default: 15s
  ochp_timeout=<seconds>           # default: 15s

Example:

::

  event_handler_timeout=60
  notification_timeout=60
  ocsp_timeout=5
  ochp_timeout=5
  
This is the maximum number of seconds that Shinken will allow :ref:`event handlers <advanced/eventhandlers>`, notification, :ref:`obsessive compulsive service processor command <configuration/configmain-advanced#ocsp_command>` or a :ref:`Obsessive Compulsive Host Processor Command <configuration/configmain-advanced#ochp_command>` to be run. If an command exceeds this time limit it will be killed and a warning will be logged.

There is often widespread confusion as to what this option really does. It is meant to be used as a last ditch mechanism to kill off commands which are misbehaving and not exiting in a timely manner. It should be set to something high (like 60 seconds or more for notification, less for oc*p commands), so that each event handler command normally finishes executing within this time limit. If an event handler runs longer than this limit, Shinken will kill it off thinking it is a runaway processes.


Old Obsess Over commands 
=========================

.. _configuration/configmain-advanced#obsess_over_services:

Obsess Over Services Option 
----------------------------

Format:

::

  obsess_over_services=<0/1>

Example:

::

  obsess_over_services=1
  
This value determines whether or not Shinken will “obsess" over service checks results and run the :ref:`obsessive compulsive service processor command <configuration/configmain-advanced#ocsp_command>` you define. I know _ funny name, but it was all I could think of. This option is useful for performing :ref:`distributed monitoring <advanced/distributed>`. If you're not doing distributed monitoring, don't enable this option.

  * 0 = Don't obsess over services (default)
  * 1 = Obsess over services


.. _configuration/configmain-advanced#ocsp_command:

Obsessive Compulsive Service Processor Command 
-----------------------------------------------

Format:

::

  ocsp_command=<configobjects/command>

Example:

::

  ocsp_command=obsessive_service_handler

This option allows you to specify a command to be run after every service check, which can be useful in :ref:`distributed monitoring <advanced/distributed>`. This command is executed after any :ref:`event handler <advanced/eventhandlers>` or :ref:`notification <thebasics/notifications>` commands. The command argument is the short name of a :ref:`command definition <configobjects/command>` that you define in your object configuration file.

It's used nearly only for the old school distributed architecture. If you use it, please look at new architecture capabilities that are far efficient than the old one. More information on distributed monitoring can be found :ref:`here <advanced/distributed>`. This command is only executed if the :ref:`Obsess Over Services Option <configuration/configmain-advanced#obsess_over_services>` option is enabled globally and if the "obsess_over_service" directive in the :ref:`service definition <configobjects/service>` is enabled.


.. _configuration/configmain-advanced#obsess_over_hosts:

Obsess Over Hosts Option 
-------------------------

Format:

::

  obsess_over_hosts=<0/1>

Example:

::

  obsess_over_hosts=1
  
This value determines whether or not Shinken will “obsess" over host checks results and run the :ref:`obsessive compulsive host processor command <configuration/configmain-advanced#ochp_command>` you define. Same like the service one but for hosts :)

  * 0 = Don't obsess over hosts (default)
  * 1 = Obsess over hosts


.. _configuration/configmain-advanced#ochp_command:

Obsessive Compulsive Host Processor Command 
--------------------------------------------

Format:

::

  ochp_command=<configobjects/command>

Example:

::

  ochp_command=obsessive_host_handler
  
This option allows you to specify a command to be run after every host check, which can be useful in :ref:`distributed monitoring <advanced/distributed>`. This command is executed after any :ref:`event handler <advanced/eventhandlers>` or :ref:`notification <thebasics/notifications>` commands. The command argument is the short name of a :ref:`command definition <configobjects/command>` that you define in your object configuration file. 

This command is only executed if the :ref:`Obsess Over Hosts Option <configuration/configmain-advanced#obsess_over_hosts>` option is enabled globally and if the "obsess_over_host" directive in the :ref:`host definition <configobjects/host>` is enabled.


Freshness check 
================

.. _configuration/configmain-advanced#check_service_freshness:
.. _configuration/configmain-advanced#check_host_freshness:

Host/Service Freshness Checking Option 
---------------------------------------

Format:

::

  check_service_freshness=<0/1>
  check_host_freshness=<0/1>

Example:

::

  check_service_freshness=0
  check_host_freshness=0
  
This option determines whether or not Shinken will periodically check the “freshness" of host/service checks. Enabling this option is useful for helping to ensure that :ref:`passive service checks <thebasics/passivechecks>` are received in a timely manner. More information on freshness checking can be found :ref:`here <advanced/freshness>`.

  * 0 = Don't check host/service freshness
  * 1 = Check host/service freshness (default)


.. _configuration/configmain-advanced#service_freshness_check_interval:
.. _configuration/configmain-advanced#host_freshness_check_interval:

Host/Service Freshness Check Interval 
--------------------------------------

Format:

::

  service_freshness_check_interval=<seconds>
  host_freshness_check_interval=<seconds>

Example:

::

  service_freshness_check_interval=60
  host_freshness_check_interval=60
  
This setting determines how often (in seconds) Shinken will periodically check the “freshness" of host/service check results. If you have disabled host/service freshness checking (with the :ref:`check_service_freshness <configuration/configmain-advanced#check_service_freshness>` option), this option has no effect. More information on freshness checking can be found :ref:`here <advanced/freshness>`.


.. _configuration/configmain-advanced#additional_freshness_latency:

Additional Freshness Threshold Latency Option (Not implemented) 
----------------------------------------------------------------

Format:

::

  additional_freshness_latency=<#>

Example:

::

  additional_freshness_latency=15
  
This option determines the number of seconds Shinken will add to any host or services freshness threshold it automatically calculates (e.g. those not specified explicitly by the user). More information on freshness checking can be found :ref:`here <advanced/freshness>`.


All the others :) 
==================


.. _configuration/configmain-advanced#date_format:

Date Format (Not implemented) 
------------------------------

Format:

::

  date_format=<option>

Example:

::

  date_format=us
  
This option allows you to specify what kind of date/time format Shinken should use in date/time :ref:`macros <thebasics/macros>`. Possible options (along with example output) include:

============== =================== ===================
Option         Output Format       Sample Output      
us             MM/DD/YYYY HH:MM:SS 06/30/2002 03:15:00
euro           DD/MM/YYYY HH:MM:SS 30/06/2002 03:15:00
iso8601        YYYY-MM-DD HH:MM:SS 2002-06-30 03:15:00
strict-iso8601 YYYY-MM-DDTHH:MM:SS 2002-06-30T03:15:00
============== =================== ===================


.. _configuration/configmain-advanced#use_timezone:

Timezone Option 
----------------

Format:

::

  use_timezone=<tz>

Example:

::

  use_timezone=US/Mountain
  
This option allows you to override the default timezone that this instance of Shinken runs in. Useful if you have multiple instances of Shinken that need to run from the same server, but have different local times associated with them. If not specified, Shinken will use the system configured timezone.


.. _configuration/configmain-advanced#illegal_object_name_chars:

Illegal Object Name Characters 
-------------------------------

Format:

::

  illegal_object_name_chars=<chars...>

Example:

::

  illegal_object_name_chars=`-!$%^&*"|'<>?,()=
  
This option allows you to specify illegal characters that cannot be used in host names, service descriptions, or names of other object types. Shinken will allow you to use most characters in object definitions, but I recommend not using the characters shown in the example above. Doing may give you problems in the web interface, notification commands, etc.


.. _configuration/configmain-advanced#illegal_macro_output_chars:

Illegal Macro Output Characters 
--------------------------------

Format:

::

  illegal_macro_output_chars=<chars...>

Example:

::

  illegal_macro_output_chars=`-$^&"|'<>
  
This option allows you to specify illegal characters that should be stripped from :ref:`macros <thebasics/macros>` before being used in notifications, event handlers, and other commands. This DOES NOT affect macros used in service or host check commands. You can choose to not strip out the characters shown in the example above, but I recommend you do not do this. Some of these characters are interpreted by the shell (i.e. the backtick) and can lead to security problems. The following macros are stripped of the characters you specify:

  * "$HOSTOUTPUT$"
  * "$HOSTPERFDATA$"
  * "$HOSTACKAUTHOR$"
  * "$HOSTACKCOMMENT$"
  * "$SERVICEOUTPUT$"
  * "$SERVICEPERFDATA$"
  * "$SERVICEACKAUTHOR$"
  * "$SERVICEACKCOMMENT$"

  
.. _configuration/configmain-advanced#use_regexp_matching:

Regular Expression Matching Option (Not implemented) 
-----------------------------------------------------

Format:

::

  use_regexp_matching=<0/1>

Example:

::

  use_regexp_matching=0
  
This option determines whether or not various directives in your :ref:`Object Configuration Overview <configuration/configobject>` will be processed as regular expressions. More information on how this works can be found :ref:`here <advanced/objecttricks>`.

  * 0 = Don't use regular expression matching (default)
  * 1 = Use regular expression matching


.. _configuration/configmain-advanced#use_true_regexp_matching:

True Regular Expression Matching Option (Not implemented) 
----------------------------------------------------------

Format:

::

  use_true_regexp_matching=<0/1>

Example:

::

  use_true_regexp_matching=0
  
If you've enabled regular expression matching of various object directives using the :ref:`Regular Expression Matching Option <configuration/configmain-advanced#use_regexp_matching>` option, this option will determine when object directives are treated as regular expressions. If this option is disabled (the default), directives will only be treated as regular expressions if they contain \*, ?, +, or \.. If this option is enabled, all appropriate directives will be treated as regular expression _ be careful when enabling this! More information on how this works can be found :ref:`here <advanced/objecttricks>`.

  * 0 = Don't use true regular expression matching (default)
  * 1 = Use true regular expression matching


.. _configuration/configmain-advanced#admin_email:

Administrator Email Address (unused) 
-------------------------------------

Format:

::

  admin_email=<email_address>

Example:

::

  admin_email=root@localhost.localdomain
  
This is the email address for the administrator of the local machine (i.e. the one that Shinken is running on). This value can be used in notification commands by using the "$ADMINEMAIL$" :ref:`macro <thebasics/macros>`.


.. _configuration/configmain-advanced#admin_pager:

Administrator Pager (unused) 
-----------------------------

Format:

::

  admin_pager=<pager_number_or_pager_email_gateway>

Example:

::

  admin_pager=pageroot@localhost.localdomain
  
This is the pager number (or pager email gateway) for the administrator of the local machine (i.e. the one that Shinken is running on). The pager number/address can be used in notification commands by using the $ADMINPAGER$ :ref:`macro <thebasics/macros>`.

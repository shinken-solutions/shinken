.. _configuration/configmain:

==============================================
 Main Configuration File (shinken.cfg) Options
==============================================

When creating and/or editing configuration files, keep the following in mind:

* Lines that start with a '"#"' character are taken to be comments and are not processed
* Variable names are case-sensitive
* If you want to configure a process to use a specific module:

  * You must define the module in a **xxx.cfg** file in the **modules** directory
  * You must reference it in the **modules** section for that process, e.g. the **broker.cfg** file



The main configuration file is "shinken.cfg". It is located in the "/etc/shinken/" directory.
Sample main configuration files are installed for you when you follow the :ref:`Quickstart installation guide <gettingstarted/quickstart>`.
Below are listed parameters currently used in the file. For other parameters (not mentionned by default) see :ref:`Main Configuration File Advanced <configuration/configmain-advanced>`

Default used options
=====================

.. _configuration/configmain#cfg_dir:
.. _configuration/configmain#cfg_file:

Cfg dir and Cfg files
---------------------
Format :

::

  cfg_dir=<directory_name>
  cfg_file=<file_name>

Those are **statements and not parameters**. The arbiter considers them as order to open other(s) configuration(s) file(s)
For the cfg_dir one, the arbiter **only** reads files ending with ".cfg".
The arbiter **does** read recursively directory for files but **does not** consider lines into those files as **statements** anymore.

This means that a cfg_dir or cfg_file is considered as a **parameter** outside of shinken.cfg (or any configuration file directly given to the arbiter as parameter in a command line)
The arbiter handles main configuration files differently than any other files.

With those 2 statements, all Shinken configuration is defined : daemons, objects, resources.



.. _configuration/configmain#retention_update_interval:

Automatic State Retention Update Interval
------------------------------------------

Format:

::

  retention_update_interval=<minutes>

Default:

::

  retention_update_interval=60

This setting determines how often (in minutes) that Shinken **scheduler** will automatically save retention data during normal operation.
If you set this value to 0, it will not save retention data at regular intervals, but it will still save retention data before shutting down or restarting.
If you have disabled state retention (with the :ref:`State Retention Option <configuration/configmain-advanced#retain_state_information>` option), this option has no effect.


.. _configuration/configmain#max_service_check_spread:

Maximum Host/Service Check Spread
----------------------------------

Format:

::

  max_service_check_spread=<minutes>
  max_host_check_spread=<minutes>

Default:

::

  max_service_check_spread=30
  max_host_check_spread=30

This option determines the maximum number of minutes from when Shinken starts that all hosts/services (that are scheduled to be regularly checked) are checked. This option will ensure that the initial checks of all hosts/services occur within the timeframe you specify. Default value is 30 (minutes).


.. _configuration/configmain#host_check_timeout:
.. _configuration/configmain#service_check_timeout:

Service/Host Check Timeout
---------------------------

Format:

::

  service_check_timeout=<seconds>
  host_check_timeout=<seconds>

Default:

::

  service_check_timeout=60
  host_check_timeout=30

This is the maximum number of seconds that Shinken will allow service/host checks to run. If checks exceed this limit, they are killed and a CRITICAL state is returned. A timeout error will also be logged.

There is often widespread confusion as to what this option really does. It is meant to be used as a last ditch mechanism to kill off plugins which are misbehaving and not exiting in a timely manner. It should be set to something high (like 60 seconds or more), so that each check normally finishes executing within this time limit. If a check runs longer than this limit, Shinken will kill it off thinking it is a runaway processes.

.. _configuration/configmain#timeout_exit_status:

Timeout Exit Status
--------------------

Format:

::

   timeout_exit_status=[0,1,2,3]

Default:

::

   timeout_exit_status=2

State set by Shinken in case of timeout.


.. _configuration/configmain#flap_history:

Flap History
-------------

Format:

::

  flap_history=<int>

Default:

::

  flap_history=20

This option is used to set the history size of states keep by the scheduler to make the flapping calculation. By default, the value is 20 states kept.

The size in memory is for the scheduler daemon : 4Bytes * flap_history * (nb hosts + nb services). For a big environment, it costs 4 * 20 * (1000+10000) - 900Ko. So you can raise it to higher value if you want. To have more information about flapping, you can read :ref:`this <advanced/flapping>`.


.. _configuration/configmain#max_plugins_output_length:

Max Plugins Output Length
--------------------------

Format:

::

  max_plugins_output_length=<int>

Default:

::

  max_plugins_output_length=8192

This option is used to set the max size in bytes for the checks plugins output. So if you saw truncated output like for huge disk check when you have a lot of partitions, raise this value.


.. _configuration/configmain#enable_problem_impacts_states_change:

Enable problem/impacts states change
-------------------------------------

Format:

::

  enable_problem_impacts_states_change=<0/1>

Default:

::

  enable_problem_impacts_states_change=0

This option is used to know if we apply or not the state change when a host or service is impacted by a root problem (like the service's host going down or a host's parent being down too). The state will be changed by UNKNONW for a service and UNREACHABLE for a host until their next schedule check. This state change do not count as a attempt, it's just for console so the users know that theses objects got problems and the previous states are not sure.


.. _configuration/configmain#disable_old_nagios_parameters_whining:

Disable Old Nagios Parameters Whining
--------------------------------------

Format:

::

  disable_old_nagios_parameters_whining=<0/1>

Default:

::

  disable_old_nagios_parameters_whining=0

If 1, disable all notice and warning messages at configuration checking


.. _configuration/configmain#use_timezone:

Timezone Option
----------------

Format:

::

  use_timezone=<tz from tz database>

Default:

::

  use_timezone=''

This option allows you to override the default timezone that this instance of Shinken runs in. Useful if you have multiple instances of Shinken that need to run from the same server, but have different local times associated with them. If not specified, Shinken will use the system configured timezone.



.. _configuration/configmain#enable_environment_macros:

Environment Macros Option
--------------------------

Format:

::

  enable_environment_macros=<0/1>

Default:

::

  enable_environment_macros=1

This option determines whether or not the Shinken daemon will make all standard :ref:`macros <thebasics/macrolist>` available as environment variables to your check, notification, event hander, etc. commands. In large installations this can be problematic because it takes additional CPU to compute the values of all macros and make them available to the environment. It also cost a increase network communication between schedulers and pollers.

  * 0 = Don't make macros available as environment variables
  * 1 = Make macros available as environment variables


.. _configuration/configmain#log_initial_states:

Initial States Logging Option (Not implemented)
------------------------------------------------

Format:

::

  log_initial_states=<0/1>

Default:

::

  log_initial_states=1

This variable determines whether or not Shinken will force all initial host and service states to be logged, even if they result in an OK state. Initial service and host states are normally only logged when there is a problem on the first check. Enabling this option is useful if you are using an application that scans the log file to determine long-term state statistics for services and hosts.

  * 0 = Don't log initial states
  * 1 = Log initial states


.. _configuration/configmain#no_event_handlers_during_downtimes:

Event Handler during downtimes
-------------------------------

Format:

::

  no_event_handlers_during_downtimes=<0/1>

Default:

::

  no_event_handlers_during_downtimes=0

This option determines whether or not Shinken will run :ref:`event handlers <advanced/eventhandlers>` when the host or service is in a scheduled downtime.

  * 0 = Launch event handlers (Nagios behavior)
  * 1 = Don't launch event handlers

References:

  * http://www.mail-archive.com/shinken-devel@lists.sourceforge.net/msg01394.html
  * https://github.com/naparuba/shinken/commit/9ce28d80857c137e5b915b39bbb8c1baecc821f9



Arbiter daemon part
====================

The following parameters are common to all daemons.

.. _configuration/configmain#workdir:

Workdir
-------

Format:

::

  workdir=<directory>

Default :

::

  workdir=/var/run/shinken/

This variable specify the working directory of the daemon.
In the arbiter case, if the value is empty, the directory name of lock_file parameter. See below


.. _configuration/configmain#lock_file:

Arbiter Lock File
------------------

Defined in nagios.cfg file.

Format:

::

  lock_file=<file_name>

Example:

::

  lock_file=/var/lib/shinken/arbiterd.pid

This option specifies the location of the lock file that Shinken **arbiter daemon** should create when it runs as a daemon (when started with the "-d" command line argument). This file contains the process id (PID) number of the running **arbiter** process.


.. _configuration/configmain#local_log:

Local Log
----------

Format:

::

  local_log=<filename>

Default:

::

  local_log=/var/log/shinken/arbiterd.log'


This variable specifies the log file for the daemon.


.. _configuration/configmain#log_level:

Log Level
----------

Format:

::

  log_level=[DEBUG,INFO,WARNING,ERROR,CRITICAL]

Default:

::

  log_level=WARNING


This variable specifies which logs will be raised by the arbiter daemon. For others daemons, it can be defined in their local \*d.ini files.


.. _configuration/configmain#shinken_user:

Arbiter Daemon User
--------------------

Defined in brokerd.ini, brokerd-windows.ini, pollerd.ini, pollerd-windows.ini, reactionnerd.ini, schedulerd.ini and schedulerd-windows.ini.

Format:

::

  shinken_user=username

Default:

::

  shinken_user=<current user>

This is used to set the effective user that the **Arbiter** process (main process) should run as.
After initial program startup, Shinken will drop its effective privileges and run as this user.



.. _configuration/configmain#shinken_group:

Arbiter Daemon user Group
--------------------------

Defined in brokerd.ini, brokerd-windows.ini, pollerd.ini, pollerd-windows.ini, reactionnerd.ini, schedulerd.ini and schedulerd-windows.ini.

Format:

::

  shinken_group=groupname

Default:

::

  shinken_group=<current group>

This is used to set the effective group of the user used to launch the **arbiter** daemon.


.. _configuration/configmain#modules_dir:

Modules directory
------------------

Format:

::

  modules_dir=<direname>

Default:

::

  modules_dir=/var/lib/shinken/modules


Path to the modules directory


.. _configuration/configmain#daemon_enabled:

Daemon Enabled
---------------

Format:

::

  daemon_enabled=[0/1]

Default:

::
  daemon_enabled=1

Set to 0 if you want to make this daemon (arbiter) **NOT** to run


.. _configuration/configmain#use_ssl:

Use SSL
-------

Format:

::

  use_ssl=[0/1]

Default:

::

  use_ssl=0

Use SSL or not. You have to enable it on other daemons too.


.. _configuration/configmain#ca_cert:

Ca Cert
--------

Format:

::

  ca_cert=<filename>

Default:

::

  ca_cert=/etc/certs/ca.pem

Certification Authority (CA) certificate

.. warning::  Put full paths for certs


.. _configuration/configmain#server_cert:

Server Cert
------------

Format:

::

  server_cert=<filename>

Default:

::

  server_cert=/etc/certs/server.cert

Server certificate for SSL

.. warning::  Put full paths for certs


.. _configuration/configmain#server_key:

Server Key
-----------

Format:

::

  server_key=<filename>

Default:

::

  server_key=/etc/certs/server.key

Server key for SSL

.. warning::  Put full paths for certs


.. _configuration/configmain#hard_ssl_name_check:

Hard SSL Name Check
--------------------

Format:

::

  hard_ssl_name_check=[0/1]


Default:

::

  hard_ssl_name_check=0

Enable SSL name check.


.. _configuration/configmain#http_backend:

HTTP Backend
-------------

Format:

::

  http_backend=[auto, cherrypy, swsgiref]

Default:

::

  http_backend=auto

Specify which http_backend to use. Auto is better. If cherrypy3 is not available, it will fail back to swsgiref
.. note:: Actually, if you specify something else than cherrypy or auto, it will fall into swsgiref

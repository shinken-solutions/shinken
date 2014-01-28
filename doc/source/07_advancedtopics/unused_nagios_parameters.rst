.. _unused_nagios_parameters:


========================
Unused nagios parameters
========================


The parameters below are managed in Nagios but not in Shinken because they are useless in the architecture. If you really need one of them, please use Nagios instead or send us a patch :)

.. note::  The title is quite ambiguous : a not implemented parameter is different from an unused parameter. 
   
   The difference has been done in this page, why about creating a not_implemented_nagios_parameters? 




External Command Check Interval (Unused) 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~




======== ===============================
Format:  command_check_interval=<xxx>[s]
Example: command_check_interval=1       
======== ===============================

If you specify a number with an "s" appended to it (i.e. 30s), this is the number of seconds to wait between external command checks. If you leave off the "s", this is the number of “time units" to wait between external command checks. Unless you've changed the :ref:`Timing Interval Length <configuringshinken-configmain#configuringshinken-configmain-interval_length>` value (as defined below) from the default value of 60, this number will mean minutes.

By setting this value to **-1**, Nagios will check for external commands as often as possible. Each time Nagios checks for external commands it will read and process all commands present in the :ref:`External Command File <configuringshinken-configmain#configuringshinken-configmain-command_file>` before continuing on with its other duties. More information on external commands can be found :ref:`here <advancedtopics-extcommands>`.



External Command Buffer Slots (Not implemented) 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~




======== =================================
Format:  external_command_buffer_slots=<#>
Example: external_command_buffer_slots=512
======== =================================

This is an advanced feature.

This option determines how many buffer slots Nagios will reserve for caching external commands that have been read from the external command file by a worker thread, but have not yet been processed by the main thread of the Nagios deamon. Each slot can hold one external command, so this option essentially determines how many commands can be buffered. For installations where you process a large number of passive checks (e.g. :ref:`distributed setups <advancedtopics-distributed>`), you may need to increase this number. You should consider using MRTG to graph Nagios' usage of external command buffers. 






Use Retained Program State Option (Not implemented) 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~




======== ================================
Format:  use_retained_program_state=<0/1>
Example: use_retained_program_state=1    
======== ================================

This setting determines whether or not Nagios will set various program-wide state variables based on the values saved in the retention file. Some of these program-wide state variables that are normally saved across program restarts if state retention is enabled include the :ref:`Notifications Option <configuringshinken-configmain#configuringshinken-configmain-enable_notifications>`, :ref:`Flap Detection Option <configuringshinken-configmain-advanced#configuringshinken-configmain-enable_flap_detection>`, :ref:`Event Handler Option <configuringshinken-configmain#configuringshinken-configmain-enable_event_handlers>`, :ref:`Service Check Execution Option <configuringshinken-configmain#configuringshinken-configmain-execute_service_checks>`, and :ref:`Passive Service Check Acceptance Option <configuringshinken-configmain#configuringshinken-configmain-accept_passive_service_checks>` !!!!!!!!!! options. If you do not have :ref:`State Retention Option <configuringshinken-configmain#configuringshinken-configmain-retain_state_information>` enabled, this option has no effect.

  * 0 = Don't use retained program state
  * 1 = Use retained program state (default)



Use Retained Scheduling Info Option (Not implemented) 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~




======== ==================================
Format:  use_retained_scheduling_info=<0/1>
Example: use_retained_scheduling_info=1    
======== ==================================

This setting determines whether or not Nagios will retain scheduling info (next check times) for hosts and services when it restarts. If you are adding a large number (or percentage) of hosts and services, I would recommend disabling this option when you first restart Nagios, as it can adversely skew the spread of initial checks. Otherwise you will probably want to leave it enabled.

  * 0 = Don't use retained scheduling info
  * 1 = Use retained scheduling info (default)



Retained Host and Service Attribute Masks (Not implemented) 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~




======== =============================================================================
Format:  retained_host_attribute_mask=<number>

         retained_service_attribute_mask=<number>

Example: retained_host_attribute_mask=0

         retained_service_attribute_mask=0              
======== =============================================================================

This is an advanced feature. You'll need to read the Nagios source code to use this option effectively.

These options determine which host or service attributes are NOT retained across program restarts. The values for these options are a bitwise AND of values specified by the “MODATTR_" definitions in the "include/common.h" source code file. By default, all host and service attributes are retained.



Retained Process Attribute Masks (Not implemented) 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~




======== =============================================================================================
Format:  retained_process_host_attribute_mask=<number>

         retained_process_service_attribute_mask=<number>

Example: retained_process_host_attribute_mask=0

         retained_process_service_attribute_mask=0              
======== =============================================================================================

This is an advanced feature. You'll need to read the Nagios source code to use this option effectively.

These options determine which process attributes are NOT retained across program restarts. There are two masks because there are often separate host and service process attributes that can be changed. For example, host checks can be disabled at the program level, while service checks are still enabled. The values for these options are a bitwise AND of values specified by the “MODATTR_" definitions in the "include/common.h" source code file. By default, all process attributes are retained.



Retained Contact Attribute Masks (Not implemented) 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~




======== =============================================================================================
Format:  retained_contact_host_attribute_mask=<number>

         retained_contact_service_attribute_mask=<number>

Example: retained_contact_host_attribute_mask=0i

         retained_contact_service_attribute_mask=0              
======== =============================================================================================

This is an advanced feature. You'll need to read the Nagios source code to use this option effectively.

These options determine which contact attributes are NOT retained across program restarts. There are two masks because there are often separate host and service contact attributes that can be changed. The values for these options are a bitwise AND of values specified by the “MODATTR_" definitions in the "include/common.h" source code file. By default, all process attributes are retained.



Service Inter-Check Delay Method (Unused) 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~




======== =============================================
Format:  service_inter_check_delay_method=<n/d/s/x.xx>
Example: service_inter_check_delay_method=s           
======== =============================================

This option allows you to control how service checks are initially “spread out" in the event queue. Using a “smart" delay calculation (the default) will cause Nagios to calculate an average check interval and spread initial checks of all services out over that interval, thereby helping to eliminate CPU load spikes. Using no delay is generally not recommended, as it will cause all service checks to be scheduled for execution at the same time. This means that you will generally have large CPU spikes when the services are all executed in parallel. More information on how to estimate how the inter-check delay affects service check scheduling can be found :ref:`here <advancedtopics-checkscheduling>`. Values are as follows:

  * n = Don't use any delay - schedule all service checks to run immediately (i.e. at the same time!)
  * d = Use a "dumb" delay of 1 second between service checks
  * s = Use a “smart" delay calculation to spread service checks out evenly (default)
  * x.xx = Use a user-supplied inter-check delay of x.xx seconds




Inter-Check Sleep Time (Unused) 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~




======== ====================
Format:  sleep_time=<seconds>
Example: sleep_time=1        
======== ====================

This is the number of seconds that Nagios will sleep before checking to see if the next service or host check in the scheduling queue should be executed. Note that Nagios will only sleep after it "catches up" with queued service checks that have fallen behind.



Service Interleave Factor (Unused) 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~




======== ===============================
Format:  service_interleave_factor=<s/x>
Example: service_interleave_factor=s    
======== ===============================

This variable determines how service checks are interleaved. Interleaving allows for a more even distribution of service checks, reduced load on remote hosts, and faster overall detection of host problems. Setting this value to 1 is equivalent to not interleaving the service checks (this is how versions of Nagios previous to 0.0.5 worked). Set this value to s (smart) for automatic calculation of the interleave factor unless you have a specific reason to change it. The best way to understand how interleaving works is to watch the status CGI (detailed view) when Nagios is just starting. You should see that the service check results are spread out as they begin to appear. More information on how interleaving works can be found :ref:`here <advancedtopics-checkscheduling>`.

  * x = A number greater than or equal to 1 that specifies the interleave factor to use. An interleave factor of 1 is equivalent to not interleaving the service checks.
  * s = Use a “smart" interleave factor calculation (default)




Maximum Concurrent Service Checks (Unused) 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~




======== ==================================
Format:  max_concurrent_checks=<max_checks>
Example: max_concurrent_checks=20          
======== ==================================

This option allows you to specify the maximum number of service checks that can be run in parallel at any given time. Specifying a value of 1 for this variable essentially prevents any service checks from being run in parallel. Specifying a value of 0 (the default) does not place any restrictions on the number of concurrent checks. You'll have to modify this value based on the system resources you have available on the machine that runs Nagios, as it directly affects the maximum load that will be imposed on the system (processor utilization, memory, etc.). More information on how to estimate how many concurrent checks you should allow can be found :ref:`here <advancedtopics-checkscheduling>`.



Check Result Reaper Frequency (Unused) 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~




======== ====================================================
Format:  check_result_reaper_frequency=<frequency_in_seconds>
Example: check_result_reaper_frequency=5                     
======== ====================================================

This option allows you to control the frequency in seconds of check result "reaper" events. "Reaper" events process the results from host and service checks that have finished executing. These events consitute the core of the monitoring logic in Nagios.



Maximum Check Result Reaper Time 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


.. note::  Is it Unused or Not Implemeted?? 



======== ======================================
Format:  max_check_result_reaper_time=<seconds>
Example: max_check_result_reaper_time=30       
======== ======================================

This option allows you to control the maximum amount of time in seconds that host and service check result "reaper" events are allowed to run. "Reaper" events process the results from host and service checks that have finished executing. If there are a lot of results to process, reaper events may take a long time to finish, which might delay timely execution of new host and service checks. This variable allows you to limit the amount of time that an individual reaper event will run before it hands control back over to Nagios for other portions of the monitoring logic.



Check Result Path (Unused) 
~~~~~~~~~~~~~~~~~~~~~~~~~~~




======== ================================================
Format:  check_result_path=<path>                        
Example: check_result_path=/var/spool/nagios/checkresults
======== ================================================

This options determines which directory Nagios will use to temporarily store host and service check results before they are processed. This directory should not be used to store any other files, as Nagios will periodically clean this directory of old file (see the :ref:Max Check Result File Age option above for more information).

Make sure that only a single instance of Nagios has access to the check result path. If multiple instances of Nagios have their check result path set to the same directory, you will run into problems with check results being processed (incorrectly) by the wrong instance of Nagios!



Max Check Result File Age (Unused) 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~




======== ===================================
Format:  max_check_result_file_age=<seconds>
Example: max_check_result_file_age=3600     
======== ===================================

This options determines the maximum age in seconds that Nagios will consider check result files found in the *check_result_path* directory to be valid. Check result files that are older that this threshold will be deleted by Nagios and the check results they contain will not be processed. By using a value of zero (0) with this option, Nagios will process all check result files - even if they're older than your hardware :-).



Host Inter-Check Delay Method (Unused) 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~




======== ==========================================
Format:  host_inter_check_delay_method=<n/d/s/x.xx>
Example: host_inter_check_delay_method=s           
======== ==========================================

This option allows you to control how host checks that are scheduled to be checked on a regular basis are initially “spread out" in the event queue. Using a “smart" delay calculation (the default) will cause Nagios to calculate an average check interval and spread initial checks of all hosts out over that interval, thereby helping to eliminate CPU load spikes. Using no delay is generally not recommended. Using no delay will cause all host checks to be scheduled for execution at the same time. More information on how to estimate how the inter-check delay affects host check scheduling can be found :ref:`here <advancedtopics-checkscheduling>`. Values are as follows:

  * n = Don't use any delay - schedule all host checks to run immediately (i.e. at the same time!)
  * d = Use a "dumb" delay of 1 second between host checks
  * s = Use a “smart" delay calculation to spread host checks out evenly (default)
  * x.xx = Use a user-supplied inter-check delay of x.xx seconds
 


Auto-Rescheduling Option (Not implemented) 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~




======== ============================
Format:  auto_reschedule_checks=<0/1>
Example: auto_reschedule_checks=1    
======== ============================

This option determines whether or not Nagios will attempt to automatically reschedule active host and service checks to “smooth" them out over time. This can help to balance the load on the monitoring server, as it will attempt to keep the time between consecutive checks consistent, at the expense of executing checks on a more rigid schedule.

THIS IS AN EXPERIMENTAL FEATURE AND MAY BE REMOVED IN FUTURE VERSIONS. ENABLING THIS OPTION CAN DEGRADE PERFORMANCE - RATHER THAN INCREASE IT - IF USED IMPROPERLY!



Auto-Rescheduling Interval (Not implemented) 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~




======== ====================================
Format:  auto_rescheduling_interval=<seconds>
Example: auto_rescheduling_interval=30       
======== ====================================

This option determines how often (in seconds) Nagios will attempt to automatically reschedule checks. This option only has an effect if the *Auto-Rescheduling Option* option is enabled. Default is 30 seconds.

THIS IS AN EXPERIMENTAL FEATURE AND MAY BE REMOVED IN FUTURE VERSIONS. ENABLING THE AUTO-RESCHEDULING OPTION CAN DEGRADE PERFORMANCE - RATHER THAN INCREASE IT - IF USED IMPROPERLY!



Auto-Rescheduling Window (Not implemented) 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~




======== ==================================
Format:  auto_rescheduling_window=<seconds>
Example: auto_rescheduling_window=180      
======== ==================================

This option determines the “window" of time (in seconds) that Nagios will look at when automatically rescheduling checks. Only host and service checks that occur in the next X seconds (determined by this variable) will be rescheduled. This option only has an effect if the Auto-Rescheduling Option option is enabled. Default is 180 seconds (3 minutes).

THIS IS AN EXPERIMENTAL FEATURE AND MAY BE REMOVED IN FUTURE VERSIONS. ENABLING THE AUTO-RESCHEDULING OPTION CAN DEGRADE PERFORMANCE - RATHER THAN INCREASE IT - IF USED IMPROPERLY!





Aggressive Host Checking Option (Unused) 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~




======== ==================================
Format:  use_aggressive_host_checking=<0/1>
Example: use_aggressive_host_checking=0    
======== ==================================

Nagios tries to be smart about how and when it checks the status of hosts. In general, disabling this option will allow Nagios to make some smarter decisions and check hosts a bit faster. Enabling this option will increase the amount of time required to check hosts, but may improve reliability a bit. Unless you have problems with Nagios not recognizing that a host recovered, I would suggest not enabling this option.

  * 0 = Don't use aggressive host checking (default)
  * 1 = Use aggressive host checking



Translate Passive Host Checks Option (Not implemented) 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~




======== ===================================
Format:  translate_passive_host_checks=<0/1>
Example: translate_passive_host_checks=1    
======== ===================================

This option determines whether or not Nagios will translate DOWN/UNREACHABLE passive host check results to their “correct" state from the viewpoint of the local Nagios instance. This can be very useful in distributed and failover monitoring installations. More information on passive check state translation can be found :ref:`here <advancedtopics-passivestatetranslation>`.

  * 0 = Disable check translation (default)
  * 1 = Enable check translation




Child Process Memory Option (Unused) 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~




======== ===============================
Format:  free_child_process_memory=<0/1>
Example: free_child_process_memory=0    
======== ===============================

This option determines whether or not Nagios will free memory in child processes when they are fork()ed off from the main process. By default, Nagios frees memory. However, if the :ref:`use_large_installation_tweaks <configuringshinken-configmain#configuringshinken-configmain-use_large_installation_tweaks>` option is enabled, it will not. By defining this option in your configuration file, you are able to override things to get the behavior you want.

  * 0 = Don't free memory
  * 1 = Free memory



Child Processes Fork Twice (Unused) 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~




======== ================================
Format:  child_processes_fork_twice=<0/1>
Example: child_processes_fork_twice=0    
======== ================================

This option determines whether or not Nagios will fork() child processes twice when it executes host and service checks. By default, Nagios fork()s twice. However, if the :ref:`use_large_installation_tweaks <configuringshinken-configmain#configuringshinken-configmain-use_large_installation_tweaks>` option is enabled, it will only fork() once. By defining this option in your configuration file, you are able to override things to get the behavior you want.

  * 0 = Fork() just once
  * 1 = Fork() twice




Event Broker Options (Unused) 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~




======== ========================
Format:  event_broker_options=<#>
Example: event_broker_options=-1 
======== ========================

This option controls what (if any) data gets sent to the event broker and, in turn, to any loaded event broker modules. This is an advanced option. When in doubt, either broker nothing (if not using event broker modules) or broker everything (if using event broker modules). Possible values are shown below.

  * 0 = Broker nothing
  * -1 = Broker everything
  * # = See BROKER_* definitions in source code ("include/broker.h") for other values that can be OR'ed together



Event Broker Modules (Unused) 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~




======== ======================================================================================================
Format:  broker_module=<modulepath> [moduleargs]                                                               
Example: broker_module=/usr/local/nagios/bin/ndomod.o                 cfg_file=/usr/local/nagios/etc/ndomod.cfg
======== ======================================================================================================

This directive is used to specify an event broker module that should by loaded by Nagios at startup. Use multiple directives if you want to load more than one module. Arguments that should be passed to the module at startup are seperated from the module path by a space.

Do NOT overwrite modules while they are being used by Nagios or Nagios will crash in a fiery display of SEGFAULT glory. This is a bug/limitation either in "dlopen()", the kernel, and/or the filesystem. And maybe Nagios...

The correct/safe way of updating a module is by using one of these methods:

  * Shutdown Nagios, replace the module file, restart Nagios
  * While Nagios is running... delete the original module file, move the new module file into place, restart Nagios



Debug File (Unused) 
~~~~~~~~~~~~~~~~~~~~




======== =============================================
Format:  debug_file=<file_name>                       
Example: debug_file=/usr/local/nagios/var/nagios.debug
======== =============================================

This option determines where Nagios should write debugging information. What (if any) information is written is determined by the *Debug Level* and *Debug Verbosity* options. You can have Nagios automaticaly rotate the debug file when it reaches a certain size by using the *Maximum Debug File Size* option.



Debug Level (Unused) 
~~~~~~~~~~~~~~~~~~~~~




======== ===============
Format:  debug_level=<#>
Example: debug_level=24 
======== ===============

This option determines what type of information Nagios should write to the *Debug File*. This value is a logical OR of the values below.

  * -1 = Log everything
  * 0 = Log nothing (default)
  * 1 = Function enter/exit information
  * 2 = Config information
  * 4 = Process information
  * 8 = Scheduled event information
  * 16 = Host/service check information
  * 32 = Notification information
  * 64 = Event broker information



Debug Verbosity (Unused) 
~~~~~~~~~~~~~~~~~~~~~~~~~




======== ===================
Format:  debug_verbosity=<#>
Example: debug_verbosity=1  
======== ===================

This option determines how much debugging information Nagios should write to the *Debug File*.

  * 0 = Basic information
  * 1 = More detailed information (default)
  * 2 = Highly detailed information



Maximum Debug File Size (Unused) 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~




======== ===========================
Format:  max_debug_file_size=<#>    
Example: max_debug_file_size=1000000
======== ===========================

This option determines the maximum size (in bytes) of the *debug file*. If the file grows larger than this size, it will be renamed with a .old extension. If a file already exists with a .old extension it will automatically be deleted. This helps ensure your disk space usage doesn't get out of control when debugging Nagios.


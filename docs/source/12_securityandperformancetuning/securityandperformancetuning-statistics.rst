.. _securityandperformancetuning-statistics:




================================
 Shinken performance statistics 
================================



Introduction 
=============


Shinken provides some statistics in the log files on the health of the Shinken services. These are not currently available in the check_shinken check script. Support is planned in a future release. This will permit graphical review that Shinken :

  * Operates efficiently
  * Locate problem areas in the monitoring process
  * Observe the performance impacts of changes in your Shinken configuration


Shinken :ref:`internal metrics <internal_metrics>` are collected in the poller log and scheduler logs when :ref:`debug log level is enabled <troubleshooting_shinken>`.



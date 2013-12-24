.. _advancedtopics-perfdata:




==================
 Performance Data 
==================




Introduction 
=============


Shinken is designed to allow :ref:`plugins <thebasics-plugins>` to return optional performance data in addition to normal status data, as well as allow you to pass that performance data to external applications for processing. A description of the different types of performance data, as well as information on how to go about processing that data is described below...



Types of Performance Data 
==========================


There are two basic categories of performance data that can be obtained from Shinken:

  - Check performance data
  - Plugin performance data

Check performance data is internal data that relates to the actual execution of a host or service check. This might include things like service check latency (i.e. how "late" was the service check from its scheduled execution time) and the number of seconds a host or service check took to execute. This type of performance data is available for all checks that are performed. The :ref:`$HOSTEXECUTIONTIME$ <$HOSTEXECUTIONTIME$>` and :ref:`$SERVICEEXECUTIONTIME$ <$SERVICEEXECUTIONTIME$>` :ref:`macros <thebasics-macros>` can be used to determine the number of seconds a host or service check was running and the :ref:`$HOSTLATENCY$ <$HOSTLATENCY$>` and :ref:`$SERVICELATENCY$ <$SERVICELATENCY$>` macros can be used to determine how "late" a regularly-scheduled host or service check was.

Plugin performance data is external data specific to the plugin used to perform the host or service check. Plugin-specific data can include things like percent packet loss, free disk space, processor load, number of current users, etc. - basically any type of metric that the plugin is measuring when it executes. Plugin-specific performance data is optional and may not be supported by all plugins. Plugin-specific performance data (if available) can be obtained by using the :ref:`$HOSTPERFDATA$ <$HOSTPERFDATA$>` and :ref:`$SERVICEPERFDATA$ <$SERVICEPERFDATA$>` :ref:`macros <thebasics-macros>`. Read on for more information on how plugins can return performance data to Shinken for inclusion in the $HOSTPERFDATA$ and $SERVICEPERFDATA$ macros.



Plugin Performance Data 
========================


At a minimum, Shinken plugins must return a single line of human-readable text that indicates the status of some type of measurable data. For example, the **check_ping** plugin might return a line of text like the following:

  
::

  PING ok - Packet loss = 0%, RTA = 0.80 ms
  
With this simple type of output, the entire line of text is available in the $HOSTOUTPUT$ or $SERVICEOUTPUT$ :ref:`macros <thebasics-macros>` (depending on whether this plugin was used as a host check or service check).

Plugins can return optional performance data in their output by sending the normal, human-readable text string that they usually would, followed by a pipe character (|), and then a string containing one or more performance data metrics. Let's take the **check_ping** plugin as an example and assume that it has been enhanced to return percent packet loss and average round trip time as performance data metrics. Sample output from the plugin might look like this:

  
::

  PING ok - Packet loss = 0%, RTA = 0.80 ms | percent_packet_loss=0, rta=0.80
  
When Shinken sees this plugin output format it will split the output into two parts:

  - Everything before the pipe character is considered to be the “normal" plugin output and will be stored in either the $HOSTOUTPUT$ or $SERVICEOUTPUT$ macro
  - Everything after the pipe character is considered to be the plugin-specific performance data and will be stored in the $HOSTPERFDATA$ or $SERVICEPERFDATA$ macro

In the example above, the $HOSTOUTPUT$ or $SERVICEOUTPUT$ macro would contain *"PING ok - Packet loss = 0%, RTA = 0.80 ms"* (without quotes) and the $HOSTPERFDATA$ or $SERVICEPERFDATA$ macro would contain *"percent_packet_loss=0, rta=0.80"* (without quotes).

Multiple lines of performace data (as well as normal text output) can be obtained from plugins, as described in the :ref:`plugin API documentation <development-pluginapi>`.

The Shinken daemon doesn't directly process plugin performance data, so it doesn't really care what the performance data looks like. There aren't really any inherent limitations on the format or content of the performance data. However, if you are using an external addon to process the performance data (i.e. PerfParse), the addon may be expecting that the plugin returns performance data in a specific format. Check the documentation that comes with the addon for more information.



Processing Performance Data 
============================


If you want to process the performance data that is available from Shinken and the plugins, you'll need to do the following:

  - Enable the :ref:`process_performance_data <configuringshinken-configmain#configuringshinken-configmain-process_performance_data>` option.
  - Configure Shinken so that performance data is either written to files and/or processed by executing commands.

Read on for information on how to process performance data by writing to files or executing commands.



Processing Performance Data Using Commands 
===========================================


The most flexible way to process performance data is by having Shinken execute commands (that you specify) to process or redirect the data for later processing by external applications. The commands that Shinken executes to process host and service performance data are determined by the :ref:`host_perfdata_command <configuringshinken-configmain-advanced#configuringshinken-configmain-host_perfdata_command>` and :ref:`service_perfdata_command <configuringshinken-configmain-advanced#configuringshinken-configmain-service_perfdata_command>` options, respectively.

An example command definition that redirects service check performance data to a text file for later processing by another application is shown below:

  
::

  define command{
    command_name    store-service-perfdata
    command_line    /bin/echo -e "$LASTSERVICECHECK$\t$HOSTNAME$\t$SERVICEDESC$\t$SERVICESTATE$\t$SERVICEATTEMPT$\t$SERVICESTATETYPE$\t$SERVICEEXECUTIONTIME$\t$SERVICELATENCY$\t$SERVICEOUTPUT$\t$SERVICEPERFDATA$" >> /usr/local/shinken/var/service-perfdata.dat
  }
  
This method, while flexible, comes with a relatively high CPU overhead. If you're processing performance data for a large number of hosts and services, you'll probably want Shinken to write performance data to files instead. This method is described in the next section.



Writing Performance Data To Files 
==================================


You can have Shinken write all host and service performance data directly to text files using the :ref:`host_perfdata_file <configuringshinken-configmain#configuringshinken-configmain-host_perfdata_file>` and :ref:`service_perfdata_file <configuringshinken-configmain#configuringshinken-configmain-service_perfdata_file>` options. The format in which host and service performance data is written to those files is determined by the :ref:`host_perfdata_file_template <configuringshinken-configmain#configuringshinken-configmain-host_perfdata_file_template>` and :ref:`service_perfdata_file_template <configuringshinken-configmain#configuringshinken-configmain-service_perfdata_file_template>` options.

An example file format template for service performance data might look like this:

  
::

  service_perfdata_file_template=[SERVICEPERFDATA]\t$TIMET$\t$HOSTNAME$\t$SERVICEDESC$\t$SERVICEEXECUTIONTIME$\t$SERVICELATENCY$\t$SERVICEOUTPUT$\t$SERVICEPERFDATA$
  
By default, the text files will be opened in "append" mode. If you need to change the modes to "write" or "non-blocking read/write" (useful when writing to pipes), you can use the :ref:`host_perfdata_file_mode <configuringshinken-configmain#configuringshinken-configmain-host_perfdata_file_mode>` and :ref:`service_perfdata_file_mode <configuringshinken-configmain#configuringshinken-configmain-service_perfdata_file_mode>` options.

Additionally, you can have Shinken periodically execute commands to periocially process the performance data files (e.g. rotate them) using the :ref:`host_perfdata_file_processing_command <configuringshinken-configmain#configuringshinken-configmain-host_perfdata_file_processing_command>` and :ref:`service_perfdata_file_processing_command <configuringshinken-configmain#configuringshinken-configmain-service_perfdata_file_processing_command>` options. The interval at which these commands are executed are governed by the :ref:`host_perfdata_file_processing_interval <configuringshinken-configmain#configuringshinken-configmain-host_perfdata_file_processing_interval>` and :ref:`service_perfdata_file_processing_interval <configuringshinken-configmain#configuringshinken-configmain-service_perfdata_file_processing_interval>` options, respectively.


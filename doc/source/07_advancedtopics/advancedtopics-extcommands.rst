.. _advancedtopics-extcommands:





===================
 External Commands 
===================



Introduction 
=============


Shinken can process commands from external applications (including the CGIs and others UIs) and alter various aspects of its monitoring functions based on the commands it receives. External applications can submit commands by writing to the :ref:`command file <configuringshinken-configmain#configuringshinken-configmain-command_file>`, which is periodically processed by the Nagios daemon.



Enabling External Commands 
===========================




.. image:: /_static/images///official/images/externalcommands.png
   :scale: 90 %



In order to have Shinken process external commands, make sure you do the following:

  * Enable external command checking with the :ref:`check_external_commands <configuringshinken-configmain#configuringshinken-configmain-check_external_commands>` option.
  * Specify the location of the command file with the :ref:`command_file <configuringshinken-configmain#configuringshinken-configmain-command_file>` option.
  * Setup proper permissions on the directory containing the external command file, as described in the :ref:`quickstart guide <gettingstarted-quickstart>`.



When Does Shinken Check For External Commands? 
===============================================


In fact every loop it look at it and reap all it can have in the pipe.



Using External Commands 
========================


External commands can be used to accomplish a variety of things while Shinken is running. Example of what can be done include temporarily disabling notifications for services and hosts, temporarily disabling service checks, forcing immediate service checks, adding comments to hosts and services, etc.



Command Format 
===============


External commands that are written to the :ref:`command file <configuringshinken-configmain#configuringshinken-configmain-command_file>` have the following format...

  
::

  [time] command_id;command_arguments
  
...where time is the time (in "time_t" format) that the external application submitted the external command to the command file. The values for the "command_id" and "command_arguments" arguments will depend on what command is being submitted to Shinken.

A full listing of external commands that can be used (along with examples of how to use them) can be found online at the following URL:

http://www.nagios.org/developerinfo/externalcommands/


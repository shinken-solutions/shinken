.. _configuringshinken-config:




======================
Configuration Overview
======================



Introduction 
=============


There are several different configuration files that you're going to need to create or edit before you start monitoring anything. Be patient! Configuring Shinken can take quite a while, especially if you're first-time user. Once you figure out how things work, it'll all be well worth your time. :-)

Sample configuration files are installed in the "/usr/local/shinken/etc/" directory when you follow the :ref:`Quickstart installation guide <gettingstarted-quickstart>`.



Main Configuration File 
========================


Main Shinken configuration files are separate in two part :
  * Nagios compatible part (nagios.cfg)
  * Shinken specific part (shinken-specific.cfg)

Documentation for the main configuration file can be found :ref:`Main Configuration File Options <configuringshinken-configmain>`.



Resource File(s) 
=================




.. image:: /_static/images/official/images/configoverview-shinken.png
   :scale: 90 %



Resource files can be used to store user-defined macros. The main point of having resource files is to use them to store sensitive configuration information (like passwords), without making them available to the CGIs.

You can specify one or more optional resource files by using the :ref:`resource_file <configuringshinken-configmain#configuringshinken-configmain-resource_file>` directive in your main configuration file.
ngshinken-configmain#configuringshinken-configmain-resource_file


Object Definition Files 
========================


Object definition files are used to define hosts, services, hostgroups, contacts, contactgroups, commands, etc. This is where you define all the things you want monitor and how you want to monitor them.

You can specify one or more object definition files by using the :ref:`cfg_file <configuringshinken-configmain#configuringshinken-configmain-cfg_file>` and/or :ref:`cfg_dir <configuringshinken-configmain#configuringshinken-configmain-cfg_dir>` directives in your main configuration file.

An introduction to object definitions, and how they relate to each other, can be found :ref:`here <configuringshinken-configobject>`.


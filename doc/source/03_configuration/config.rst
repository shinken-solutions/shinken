.. _configuration/config:

======================
Configuration Overview
======================


Introduction 
=============

There are several different configuration files that you're going to need to create or edit before you start monitoring anything.
Be patient! Configuring Shinken can take quite a while, especially if you're first-time user.
Once you figure out how things work, it'll all be well worth your time. :-)

Sample configuration files are installed in the **/etc/shinken/** directory when you follow the :ref:`Quickstart installation guide <gettingstarted/quickstart>`.


Main Configuration File : shinken.cfg
=====================================

.. note:: A main configuration file is a file given to the arbiter as parameter from command_line. In Shinken 2.0, there is only shinken.cfg

The 2.0 introduces a new configuration layout. The basic configuration is now split into several small files.
Don't be afraid, it's actually a better layout for your mind because one file ~ one object definition.
This helps a lot to understand object concepts and uses in Shinken configuration.

However, one file, among others can be considered as the entry point : **shinken.cfg**. This is the main configuration file.

This configuration file is pointing to all configuration directories Shinken needs. The **cfg_dir=** statement is actually doing all the job.
It includes all the configuration files described below.

.. note:: The **cfg_dir** statement will only read files that end with **.cfg**. Any other file is skipped.

Documentation for the main configuration file can be found :ref:`Main Configuration File Options <configuration/configmain>`.

Daemons Definition Files
========================

Files for daemons definition are located in separated directories. For example pollers definitions are in the **pollers** directory.
Each directory contains one file per existing daemon.

Modules Definition Files
=========================

Files for modules definition are located in **/etc/shinken/modules**. Each module has its own configuration file.
As modules are loaded by daemons, modules files are referenced in daemons files. The statement is **module** to specify a module to load.


Resource Files
=================

.. image:: /_static/images/official/images/configoverview-shinken.png
   :scale: 90 %

Resource files can be used to store user-defined macros.
The main point of having resource files is to use them to store sensitive configuration information (like passwords), without making them available to the CGIs.

You can specify one or more optional resource files by using the :ref:`resource_file <configuration/configmain-advanced#resource_file>` directive in your main configuration file.


Object Definition Files 
========================

Object definition files are used to define hosts, services, hostgroups, contacts, contactgroups, commands, etc.
This is where you define all the things you want monitor and how you want to monitor them.

You can specify one or more object definition files by using the :ref:`cfg_file <configuration/configmain#cfg_file>` and/or :ref:`cfg_dir <configuration/configmain#cfg_dir>` directives in your main configuration file.

An introduction to object definitions, and how they relate to each other, can be found :ref:`here <configuration/configobject>`.


.. _configuration/objectdefinitions:

==================
Object Definitions 
==================


Introduction 
=============

One of the features of Shinken' object configuration format is that you can create object definitions that inherit properties from other object definitions. An explanation of how object inheritance works can be found :ref:`here <advanced/objectinheritance>`. I strongly suggest that you familiarize yourself with object inheritance once you read over the documentation presented below, as it will make the job of creating and maintaining object definitions much easier than it otherwise would be. Also, read up on the :ref:`object tricks <advanced/objecttricks>` that offer shortcuts for otherwise tedious configuration tasks.

When creating and/or editing configuration files, keep the following in mind:

  - Lines that start with a '"#"' character are taken to be comments and are not processed
  - Directive names are case-sensitive


Sample Configuration Files 
===========================

Sample object configuration files are installed in the "/etc/shinken/" directory when you follow the :ref:`quickstart installation guide <gettingstarted/quickstart>`.


Object Types 
=============

  * :ref:`Host <configobjects/host>`
  * :ref:`Host Group <configobjects/hostgroup>`
  * :ref:`Service <configobjects/service>`
  * :ref:`Service Group <configobjects/servicegroup>`
  * :ref:`Contact <configobjects/contact>`
  * :ref:`Contact Group <configobjects/contactgroup>`
  * :ref:`Time Period <configobjects/timeperiod>`
  * :ref:`Command <configobjects/command>`
  * :ref:`Service Dependency <configobjects/servicedependency>`
  * :ref:`Service Escalation <configobjects/serviceescalation>`
  * :ref:`Host Dependency <configobjects/hostdependency>`
  * :ref:`Host Escalation <configobjects/hostescalation>`
  * :ref:`Extended Host Information <configobjects/hostextinfo>`
  * :ref:`Extended Service Information <configobjects/serviceextinfo>`
  * :ref:`Realm <configobjects/realm>`
  * :ref:`Arbiter <configobjects/arbiter>`
  * :ref:`Scheduler <configobjects/scheduler>`
  * :ref:`Poller <configobjects/poller>`
  * :ref:`Reactionner <configobjects/reactionner>`
  * :ref:`Broker <configobjects/broker>`


.. _configuringshinken-objectdefinitions:




==================
Object Definitions 
==================



Introduction 
=============


One of the features of Shinken' object configuration format is that you can create object definitions that inherit properties from other object definitions. An explanation of how object inheritance works can be found :ref:`here <advancedtopics-objectinheritance>`. I strongly suggest that you familiarize yourself with object inheritance once you read over the documentation presented below, as it will make the job of creating and maintaining object definitions much easier than it otherwise would be. Also, read up on the :ref:`object tricks <advancedtopics-objecttricks>` that offer shortcuts for otherwise tedious configuration tasks.

When creating and/or editing configuration files, keep the following in mind:

  - Lines that start with a '"#"' character are taken to be comments and are not processed
  - Directive names are case-sensitive



Sample Configuration Files 
===========================


Sample object configuration files are installed in the "/etc/shinken/" directory when you follow the :ref:`quickstart installation guide <gettingstarted-quickstart>`.



Object Types 
=============


  * :ref:`Host <configuringshinken/configobjects/host>`
  * :ref:`Host Group <configuringshinken/configobjects/hostgroup>`
  * :ref:`Service <configuringshinken/configobjects/service>`
  * :ref:`Service Group <configuringshinken/configobjects/servicegroup>`
  * :ref:`Contact <configuringshinken/configobjects/contact>`
  * :ref:`Contact Group <configuringshinken/configobjects/contactgroup>`
  * :ref:`Time Period <configuringshinken/configobjects/timeperiod>`
  * :ref:`Command <configuringshinken/configobjects/command>`
  * :ref:`Service Dependency <configuringshinken/configobjects/servicedependency>`
  * :ref:`Service Escalation <configuringshinken/configobjects/serviceescalation>`
  * :ref:`Host Dependency <configuringshinken/configobjects/hostdependency>`
  * :ref:`Host Escalation <configuringshinken/configobjects/hostescalation>`
  * :ref:`Extended Host Information <configuringshinken/configobjects/hostextinfo>`
  * :ref:`Extended Service Information <configuringshinken/configobjects/serviceextinfo>`
  * :ref:`Realm <configuringshinken/configobjects/realm>`
  * :ref:`Arbiter <configuringshinken/configobjects/arbiter>`
  * :ref:`Scheduler <configuringshinken/configobjects/scheduler>`
  * :ref:`Poller <configuringshinken/configobjects/poller>`
  * :ref:`Reactionner <configuringshinken/configobjects/reactionner>`
  * :ref:`Broker <configuringshinken/configobjects/broker>`
























.. _start:



===============================
Shinken Official Documentation 
===============================


  * :ref:`Getting started <start>`
  * Shinken official documentation [You are here]
  * :ref:`How to contribute <how to contribute] >`
  * :ref:`The project vision <the_project_vision] >`
  * :ref:`Getting help! <] >`
  * :ref:`Global Discussion Page <discussion >`

.. tip::  You are welcome to improve this wiki. Simply create an account, login and ask on the forum to get activated for edition. :)


**Table of Contents**

  * :ref:`About <part-about>`
    * :ref:`About Shinken <about>`
    * :ref:`What's different between Shinken and Nagios <about-whatsnew>`
  * :ref:`Getting Started <part-gettingstarted>`
    * :ref:`Advice for Beginners <gettingstarted-beginners>`
    * :ref:`Quickstart Installation Guides <gettingstarted-quickstart>`
    * :ref:`GNU/Linux Quickstart <gettingstarted-quickstart-gnulinux>`
    * :ref:`Windows Quickstart <gettingstarted-quickstart-windows>`
    * :ref:`Upgrading Shinken <ch07>`
    * :ref:`Monitoring Windows Machines <gettingstarted-monitoring-windows>`
    * :ref:`Monitoring Linux/Unix Machines <gettingstarted-monitoring-linux>`
    * :ref:`Monitoring Network Printers <gettingstarted-monitoring-printers>`
    * :ref:`Monitoring Routers and Switches <gettingstarted-monitoring-routers>`
    * :ref:`Monitoring Publicly Available Services <gettingstarted-monitoring-publicservices>`
  * :ref:`Configuring Shinken <part-configuringshinken>`
    * :ref:`Configuration Overview <configuringshinken-config>`
    * :ref:`Main Configuration File Options <configuringshinken-configmain>`
    * :ref:`Main Configuration File - Broker modules <the_broker_modules>`.
    * :ref:`Object Configuration Overview <configuringshinken-configobject>`
    * :ref:`Object Definitions <configuringshinken-objectdefinitions>`
    * :ref:`Custom Object Variables <configuringshinken-customobjectvars>`
   * :ref:`Running Shinken <part-runningshinken>`
    * :ref:`Verifying Your Configuration <runningshinken-verifyconfig>`
    * :ref:`Starting and Stopping Shinken <runningshinken-startstop>`
  * :ref:`The Basics <part-thebasics>`
    * :ref:`Nagios/Shinken Plugins <thebasics-plugins>`
    * :ref:`Understanding Macros and How They Work <thebasics-macros>`
    * :ref:`Standard Macros in Shinken <thebasics-macrolist>`
    * :ref:`Host Checks <thebasics-hostchecks>`
    * :ref:`Service Checks <thebasics-servicechecks>`
    * :ref:`Active Checks <thebasics-activechecks>`
    * :ref:`Passive Checks <thebasics-passivechecks>`
    * :ref:`State Types <thebasics-statetypes>`
    * :ref:`Time Periods <thebasics-timeperiods>`
    * :ref:`Determining Status and Reachability of Network Hosts <thebasics-networkreachability>`
    * :ref:`Notifications <thebasics-notifications>`
  * :ref:`Advanced Topics <part-advancedtopics>`
    * :ref:`External Commands <advancedtopics-extcommands>`
    * :ref:`Event Handlers <advancedtopics-eventhandlers>`
    * :ref:`Volatile Services <advancedtopics-volatileservices>`
    * :ref:`Service and Host Freshness Checks <advancedtopics-freshness>`
    * :ref:`Distributed Monitoring <advancedtopics-distributed>`
    * :ref:`Redundant and Failover Network Monitoring <advancedtopics-redundancy>`
    * :ref:`Detection and Handling of State Flapping <advancedtopics-flapping>`
    * :ref:`Notification Escalations <advancedtopics-escalations>`
    * :ref:`On-Call Rotations <advancedtopics-oncallrotation>`
    * :ref:`Monitoring Service and Host Clusters <advancedtopics-clusters>`
    * :ref:`Host and Service Dependencies <advancedtopics-dependencies>`
    * :ref:`State Stalking <advancedtopics-stalking>`
    * :ref:`Performance Data <advancedtopics-perfdata>`
    * :ref:`Scheduled Downtime <advancedtopics-downtime>`
    * :ref:`Adaptive Monitoring <advancedtopics-adaptative>`
    * :ref:`Predictive Dependency Checks <advancedtopics-dependencychecks>`
    * :ref:`Cached Checks <advancedtopics-cachedchecks>`
    * :ref:`Passive Host State Translation <advancedtopics-passivestatetranslation>`
    * :ref:`Service and Host Check Scheduling <advancedtopics-checkscheduling>`
    * :ref:`Object Inheritance <advancedtopics-objectinheritance>`
    * :ref:`Time-Saving Tricks For Object Definitions <advancedtopics-objecttricks>`
    * :ref:`Problems and impacts correlation management <part-problemsandimpacts >`
    * :ref:`Business rules <advancedtopics-businessrules >`
    * :ref:`Migrating from Nagios to Shinken <advancedtopics-migratingfromnagios >`
  * :ref:`Security and Performance Tuning <part-securityandperformancetuning>`
    * :ref:`Security Considerations <securityandperformancetuning-security>`
    * :ref:`Tuning Shinken For Maximum Performance <securityandperformancetuning-tuning>`
    * :ref:`Scaling a Shinken Installation <securityandperformancetuning-largeinstalltweaks>`
    * :ref:`Performance statistics <securityandperformancetuning-statistics>`
  * :ref:`Integration With Other Software <part-integrationwithothersoftware>`
    * :ref:`Integration Overview <integrationwithothersoftware-integration>`
    * :ref:`SNMP Trap Integration <integrationwithothersoftware-int-snmptrap>`
    * :ref:`TCP Wrappers Integration <integrationwithothersoftware-int-tcpwrappers>`
  * :ref:`Extending Shinken <part-shinkenaddons>`
    * :ref:`Extending Shinken <shinkenaddons-addons>`
  * :ref:`Development <part-development>`
    * :ref:`Nagios/Shinken Plugin API <development-pluginapi>`
    * :ref:`Developing Shinken daemon modules <development-modules>`
    * :ref:`Hacking the Shinken Code <development-hackingcode>`




Authors 
~~~~~~~~

  * Ethan Galstad (Nagios Enterprises): first versions, 1999->2007
  * Sébastien Guilbaud: HTML to Docbook transformation 
  * Olivier Jan: HTML to Docbook transformation 
  * Jean Gabès: DocBook to xhtml, xhtml to dokuwiki, adaptation to Shinken
  * xkilian: Rewrite, reorganize, update and cleanup the documentation





Copyrights =
~~~~~~~~~~~~


__Shinken is not related with the official Nagios project nor Nagios Enterprise.__ 

Nagios, the Nagios logo, and Nagios graphics are the servicemarks, trademarks, or registered trademarks owned by Nagios Enterprises. All other servicemarks and trademarks are the property of their respective owner.·

Shinken is provided “AS IS" with “NO WARRANTY OF ANY KIND, INCLUDING THE WARRANTY OF DESIGN, MERCHANTABILITY, AND FITNESS FOR A PARTICULAR PURPOSE."

Copyright © 1999-2007 Ethan Galstad, Nagios Enterprises
Copyright © 2007-2009 Sébastien Guilbaud and Olivier Jan
Copyright © 2009->now Jean Gabès and the Shinken community
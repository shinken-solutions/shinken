.. _thebasics-servicechecks:




================
 Service Checks 
================




Introduction 
=============


The basic workings of service checks are described here...



When Are Service Checks Performed? 
===================================


Services are checked by the Shinken daemon:

  * At regular intervals, as defined by the "check_interval" and "retry_interval" options in your :ref:`service definitions <configuringshinken/configobjects/service>`.
  * On-demand as needed for :ref:`predictive service dependency checks <advancedtopics-dependencychecks>`.

On-demand checks are performed as part of the :ref:`predictive service dependency check <advancedtopics-dependencychecks>` logic. These checks help ensure that the dependency logic is as accurate as possible. If you don't make use of :ref:`service dependencies <configuringshinken/configobjects/servicedependency>`, Shinken won't perform any on-demand service checks.



Cached Service Checks 
======================


The performance of on-demand service checks can be significantly improved by implementing the use of cached checks, which allow Shinken to forgo executing a service check if it determines a relatively recent check result will do instead. Cached checks will only provide a performance increase if you are making use of :ref:`service dependencies <configuringshinken/configobjects/servicedependency>`. More information on cached checks can be found :ref:`here <advancedtopics-cachedchecks>`.



Dependencies and Checks 
========================


You can define :ref:`service execution dependencies <configuringshinken/configobjects/servicedependency>` that prevent Shinken from checking the status of a service depending on the state of one or more other services. More information on dependencies can be found :ref:`here <advancedtopics-dependencies>`.



Parallelization of Service Checks 
==================================


Scheduled service checks are run in parallel.



Service States 
===============


Services that are checked can be in one of four different states:

  * OK
  * WARNING
  * UNKNOWN
  * CRITICAL



Service State Determination 
============================


Service checks are performed by :ref:`plugins <thebasics-plugins>`, which can return a state of OK, WARNING, UNKNOWN, or CRITICAL. These plugin states directly translate to service states. For example, a plugin which returns a WARNING state will cause a service to have a WARNING state.



Services State Changes 
=======================


When Shinken checks the status of services, it will be able to detect when a service changes between OK, WARNING, UNKNOWN, and CRITICAL states and take appropriate action. These state changes result in different :ref:`state types <thebasics-statetypes>` (HARD or SOFT), which can trigger :ref:`event handlers <advancedtopics-eventhandlers>` to be run and :ref:`notifications <thebasics-notifications>` to be sent out. Service state changes can also trigger on-demand :ref:`host checks <thebasics-hostchecks>`. Detecting and dealing with state changes is what Shinken is all about.

When services change state too frequently they are considered to be “flapping". Shinken can detect when services start flapping, and can suppress notifications until flapping stops and the service's state stabilizes. More information on the flap detection logic can be found :ref:`here <advancedtopics-flapping>`.


.. _hostdependency:
.. _configuringshinken/configobjects/hostdependency:



===========================
Host Dependency Definition 
===========================




Description 
============


Host dependencies are an advanced feature of Shinken that allow you to suppress notifications for hosts based on the status of one or more other hosts. Host dependencies are optional and are mainly targeted at advanced users who have complicated monitoring setups. More information on how host dependencies work (read this!) can be found :ref:`here <advancedtopics-dependencies>`.



Definition Format 
==================


Bold directives are required, while the others are optional.



============================= ================
define hostdependency{                        
**dependent_host_name**       ***host_name*** 
dependent_hostgroup_name      *hostgroup_name*
**host_name**                 ***host_name*** 
hostgroup_name                *hostgroup_name*
inherits_parent               [0/1]           
execution_failure_criteria    [o,d,u,p,n]     
notification_failure_criteria [o,d,u,p,n]     
dependency_period             timeperiod_name 
}                                             
============================= ================



Example Definition 
===================


  
::

  	  define hostdependency{
  	  host_name                       WWW1
  	  dependent_host_name             DBASE1
  	  notification_failure_criteria   d,u
  	  }
  


Directive Descriptions 
=======================


   dependent_host_name
  
This directive is used to identify the *short name(s)* of the *dependent* :ref:`host(s) <configuringshinken/configobjects/host>`. Multiple hosts should be separated by commas.


   dependent_hostgroup_name
  
This directive is used to identify the *short name(s)* of the *dependent* :ref:`hostgroup(s) <configuringshinken/configobjects/host>`. Multiple hostgroups should be separated by commas. The dependent_hostgroup_name may be used instead of, or in addition to, the dependent_host_name directive.

   host_name
  
This directive is used to identify the *short name(s)* of the :ref:`host(s) <configuringshinken/configobjects/host>` *that is being depended upon* (also referred to as the master host). Multiple hosts should be separated by commas.

   hostgroup_name
  
This directive is used to identify the *short name(s)* of the :ref:`hostgroup(s) <configuringshinken/configobjects/host>` *that is being depended upon* (also referred to as the master host). Multiple hostgroups should be separated by commas. The hostgroup_name may be used instead of, or in addition to, the host_name directive.

   inherits_parent
  
This directive indicates whether or not the dependency inherits dependencies of the host *that is being depended upon* (also referred to as the master host). In other words, if the master host is dependent upon other hosts and any one of those dependencies fail, this dependency will also fail.

   execution_failure_criteria
  
This directive is used to specify the criteria that determine when the dependent host should *not* be actively checked. If the *master* host is in one of the failure states we specify, the *dependent* host will not be actively checked. Valid options are a combination of one or more of the following (multiple options are separated with commas):

  * **o** = fail on an UP state
  * **d** = fail on a DOWN state
  * **u** = fail on an UNREACHABLE state
  * **p** = fail on a pending state (e.g. the host has not yet been checked)
  * **n** (none) : the execution dependency will never fail and the dependent host will always be actively checked (if other conditions allow for it to be).

If you specify **u,d** in this field, the *dependent* host will not be actively checked if the *master* host is in either an UNREACHABLE or DOWN state.

   notification_failure_criteria
  
This directive is used to define the criteria that determine when notifications for the dependent host should *not* be sent out. If the *master* host is in one of the failure states we specify, notifications for the *dependent* host will not be sent to contacts. Valid options are a combination of one or more of the following:

  * **o** = fail on an UP state
  * **d** = fail on a DOWN state
  * **u** = fail on an UNREACHABLE state
  * **p** = fail on a pending state (e.g. the host has not yet been checked)
  * **n** = (none) : the notification dependency will never fail and notifications for the dependent host will always be sent out.

If you specify **d** in this field, the notifications for the *dependent* host will not be sent out if the *master* host is in a DOWN state.

   dependency_period
  
This directive is used to specify the short name of the :ref:`time period <configuringshinken/configobjects/timeperiod>` during which this dependency is valid. If this directive is not specified, the dependency is considered to be valid during all times.

.. _setup_notification_escalations:


Notifications and escalations
=============================


Escalations 
------------




.. image:: /_static/images///official/images/objects-contacts.png
   :scale: 90 %

Shinken supports optional escalation of contact notifications for hosts and services. Escalation of host and service notifications is accomplished by defining :ref:`escalations <configuringshinken-objectdefinitions#configuringshinken-objectdefinitions-escalation>` and call them from your hosts and services definitions.

.. tip::  Legacy Nagios host_escalations and service_escalations objects are still managed, but it's adviced to migrate and simplify your configuration with simple escalations objects.



Definition and sample 
----------------------


Notifications are escalated if and only if one or more escalation linked to your host/service matches the current notification that is being sent out. Look at the example below:
  
 

::

  define escalation{
    escalation_name     To_level_2
    first_notification_time    60
    last_notification_time    240
    notification_interval    60
    contact_groups    level2
  }
  
  
And then you can call it from a service (or an host):
  

::

  define service{
    use                    webservice
    host_name              webserver
    service_description    HTTP
    escalations            To_level_2
    contact_groups         level1
  }
  
  
Here, notifications sent before the fist_notification_time (60 = 60*interval_length*seconds = 60*60s = 1h) will be send to the contact_groups of the service, and between one hour and 4 hours (last_notification_time) it will be escalated to the level2 contact group.

If there is no escalations available (like after 4 hours) it fail back to the default service contact_groups, level1 here.




Lower contact groups 
---------------------


When defining notification escalations, look if it's interesting that were members of "lower" escalations (i.e. those with lower notification time ranges) should also be included in "higher" escalation definitions or not. This can be done to ensure that anyone who gets notified of a problem continues to get notified as the problem is escalated.

In our previous example it becomes:
  
 

::

  define escalation{
    escalation_name     To_level_2
    first_notification_time    60
    last_notification_time    240
    notification_interval    60
    contact_groups    level1,level2
  }
  
  
  


Multiple escalations levels 
----------------------------


It can be interesting to have more than one level for escalations. Like if problems are send to your level1, and after 1 hour it's send to your level2 and after 4 hours it's send to the level3 until it's resolved.

All you need is to define theses two escalations and link them to your host/service:
  
 

::

  define escalation{
    escalation_name     To_level_2
    first_notification_time    60
    last_notification_time    240
    notification_interval    60
    contact_groups    level2
  }
  
  define escalation{
    escalation_name     To_level_3
    first_notification_time    240
    last_notification_time    0
    notification_interval    60
    contact_groups    level3
  }
  
  
And for your service:
  

::

  define service{
    use                    webservice
    host_name              webserver
    service_description    HTTP
    escalations            To_level_2,To_level_3
    contact_groups         level1
  }
  
  
  


Overlapping Escalation Ranges 
------------------------------


Notification escalation definitions can have notification ranges that overlap. Take the following example:
  


::

  define escalation{
    escalation_name     To_level_2
    first_notification_time    60
    last_notification_time    240
    notification_interval    60
    contact_groups    level2
  }
  
  define escalation{
    escalation_name     To_level_3
    first_notification_time    120
    last_notification_time    0
    notification_interval    60
    contact_groups    level3
  }
  
  
In the example above:
  * The level2 is notified at one hour
  * level 2 and 3 are notified at 2 hours
  * Only the level 3 is notified after 4 hours




Recovery Notifications 
-----------------------


Recovery notifications are slightly different than problem notifications when it comes to escalations. If the problem was escalated, or was about to reach a new level, who notified for the recovery?

The rule is very simple: we notify about the recovery every one that was notified about the problem, and only them.



Short escalations and long notification Intervals 
--------------------------------------------------


It's also interesting to see that with escalation, if the notification interval is longer than the next escalation time, it's this last value that will be taken into account.

Let take an example where your service got:

  

::

  define service{
       notification_interval     1440
       escalations    To_level_2,To_level_3
  }
  
Then with the escalations objects:
  

::

  define escalation{
    escalation_name   To_level2
    first_notification_time    60
    last_notification_time     120
    contact_groups    level2
  }
  
  define escalation{
    escalation_name     To_level_3
    first_notification_time    120
    last_notification_time     0
    contact_groups    level3
  }
  
Here let say you have a problem HARD on the service at t=0. It will notify the level1. The next notification should be at t=1440 minutes, so tomorrow. It's okay for classic services (too much notification is DANGEROUS!) but not for escalated ones.

Here, at t=60 minutes, the escalation will raise, you will notify the level2 contact group, and then at t=120 minutes you will notify the level3, and here one a day until they solve it!

So you can put large notification_interval and still have quick escalations times, it's not a problem :)




Time Period Restrictions 
-------------------------


Under normal circumstances, escalations can be used at any time that a notification could normally be sent out for the host or service. This "notification time window" is determined by the "notification_period" directive in the :ref:`host <configuringshinken-objectdefinitions#configuringshinken-objectdefinitions-host>` or :ref:`service <configuringshinken-objectdefinitions#configuringshinken-objectdefinitions-service>` definition.

You can optionally restrict escalations so that they are only used during specific time periods by using the "escalation_period" directive in the host or service escalation definition. If you use the "escalation_period" directive to specify a :ref:`Time Period Definition <configuringshinken-objectdefinitions#configuringshinken-objectdefinitions-timeperiod>` during which the escalation can be used, the escalation will only be used during that time. If you do not specify any "escalation_period" directive, the escalation can be used at any time within the "notification time window" for the host or service.

Escalated notifications are still subject to the normal time restrictions imposed by the "notification_period" directive in a host or service definition, so the timeperiod you specify in an escalation definition should be a subset of that larger "notification time window".



State Restrictions 
-------------------


If you would like to restrict the escalation definition so that it is only used when the host or service is in a particular state, you can use the "escalation_options" directive in the host or service escalation definition. If you do not use the "escalation_options" directive, the escalation can be used when the host or service is in any state.



Legacy definitions: host_escalations and service_escalations based on notification number 
------------------------------------------------------------------------------------------


The Nagios legacy escalations definitions are still managed, but it's strongly advice to switch to escalations based on time and call by host/services because it's far more flexible.

Hera are example of theses legacy definitions:


::

  define serviceescalation{
    host_name    webserver
    service_description    HTTP
    first_notification    3
    last_notification    5
    notification_interval    45
    contact_groups    nt-admins,managers
  }
  
  define hostescalation{
    host_name    webserver
    first_notification    6
    last_notification    0
    notification_interval    60
    contact_groups    nt-admins,managers,everyone
  }
  
  
It's based on notification number to know if the escalation should be raised or not. Remember that with this form you cannot mix long notification_interval and short escalations time!

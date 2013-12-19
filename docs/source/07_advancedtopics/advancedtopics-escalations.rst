.. _advancedtopics-escalations:




==========================
 Notification Escalations 
==========================




Introduction 
=============




.. image:: /_static/images///official/images/objects-contacts.png
   :scale: 90 %

Shinken supports optional escalation of contact notifications for hosts and services. Escalation of host and service notifications is accomplished by defining :ref:`host escalations <configuringshinken/configobjects/hostescalation>` and :ref:`service escalations <configuringshinken/configobjects/serviceescalation>` in your :ref:`Object Configuration Overview <configuringshinken-configobject>`.

The examples I provide below all make use of service escalation definitions, but host escalations work the same way. Except, of course, that they're for hosts instead of services. :-)



When Are Notifications Escalated? 
==================================


Notifications are escalated if and only if one or more escalation definitions matches the current notification that is being sent out. If a host or service notification does not have any valid escalation definitions that applies to it, the contact group(s) specified in either the host group or service definition will be used for the notification. Look at the example below:

  
::

  define serviceescalation{
    host_name    webserver
    service_description    HTTP
    first_notification    3
    last_notification    5
    notification_interval    90
    contact_groups    nt-admins,managers
  }
  
  define serviceescalation{
    host_name    webserver
    service_description    HTTP
    first_notification    6
    last_notification    10
    notification_interval    60
    contact_groups    nt-admins,managers,everyone
  }
  
Notice that there are "holes" in the notification escalation definitions. In particular, notifications 1 and 2 are not handled by the escalations, nor are any notifications beyond 10. For the first and second notification, as well as all notifications beyond the tenth one, the default contact groups specified in the service definition are used. For all the examples I'll be using, I'll be assuming that the default contact groups for the service definition is called nt-admins.



Contact Groups 
===============


When defining notification escalations, it is important to keep in mind that any contact groups that were members of "lower" escalations (i.e. those with lower notification number ranges) should also be included in "higher" escalation definitions. This should be done to ensure that anyone who gets notified of a problem continues to get notified as the problem is escalated. Example:

  
::

  define serviceescalation{
    host_name    webserver
    service_description    HTTP
    first_notification    3
    last_notification    5
    notification_interval    90
    contact_groups    nt-admins,managers
  }
  
  define serviceescalation{
    host_name    webserver
    service_description    HTTP
    first_notification    6
    last_notification    0
    notification_interval    60
    contact_groups    nt-admins,managers,everyone
  }
  
The first (or "lowest") escalation level includes both the nt-admins and managers contact groups. The last (or "highest") escalation level includes the nt-admins, managers, and everyone contact groups. Notice that the nt-admins contact group is included in both escalation definitions. This is done so that they continue to get paged if there are still problems after the first two service notifications are sent out. The managers contact group first appears in the "lower" escalation definition - they are first notified when the third problem notification gets sent out. We want the managers group to continue to be notified if the problem continues past five notifications, so they are also included in the "higher" escalation definition.



Overlapping Escalation Ranges 
==============================


Notification escalation definitions can have notification ranges that overlap. Take the following example:

  
::

  define serviceescalation{
    host_name    webserver
    service_description    HTTP
    first_notification    3
    last_notification    5
    notification_interval    20
    contact_groups    nt-admins,managers
  }
  
  define serviceescalation{
    host_name    webserver
    service_description    HTTP
    first_notification    4
    last_notification    0
    notification_interval    30
    contact_groups    on-call-support
  }
  
In the example above:

  * The nt-admins and managers contact groups get notified on the third notification
  * All three contact groups get notified on the fourth and fifth notifications
  * Only the on-call-support contact group gets notified on the sixth (or higher) notification



Recovery Notifications 
=======================


Recovery notifications are slightly different than problem notifications when it comes to escalations. Take the following example:

  
::

  define serviceescalation{
    host_name    webserver
    service_description    HTTP
    first_notification    3
    last_notification    5
    notification_interval    20
    contact_groups    nt-admins,managers
  }
  
  define serviceescalation{
    host_name    webserver
    service_description    HTTP
    first_notification    4
    last_notification    0
    notification_interval    30
    contact_groups    on-call-support
  }
  
If, after three problem notifications, a recovery notification is sent out for the service, who gets notified? The recovery is actually the fourth notification that gets sent out. However, the escalation code is smart enough to realize that only those people who were notified about the problem on the third notification should be notified about the recovery. In this case, the nt-admins and managers contact groups would be notified of the recovery.



Notification Intervals 
=======================


You can change the frequency at which escalated notifications are sent out for a particular host or service by using the notification_interval option of the hostgroup or service escalation definition. Example:

  
::

  define serviceescalation{
    host_name    webserver
    service_description    HTTP
    first_notification    3
    last_notification    5
    notification_interval    45
    contact_groups    nt-admins,managers
  }
  
  define serviceescalation{
    host_name    webserver
    service_description    HTTP
    first_notification    6
    last_notification    0
    notification_interval    60
    contact_groups    nt-admins,managers,everyone
  }
  
In this example we see that the default notification interval for the services is 240 minutes (this is the value in the service definition). When the service notification is escalated on the 3rd, 4th, and 5th notifications, an interval of 45 minutes will be used between notifications. On the 6th and subsequent notifications, the notification interval will be 60 minutes, as specified in the second escalation definition.

Since it is possible to have overlapping escalation definitions for a particular hostgroup or service, and the fact that a host can be a member of multiple hostgroups, Shinken has to make a decision on what to do as far as the notification interval is concerned when escalation definitions overlap. In any case where there are multiple valid escalation definitions for a particular notification, Shinken will choose the smallest notification interval. Take the following example:

  
::

  define serviceescalation{
    host_name    webserver
    service_description    HTTP
    first_notification    3
    last_notification    5
    notification_interval    45
    contact_groups    nt-admins,managers
  }
  
  define serviceescalation{
    host_name    webserver
    service_description    HTTP
    first_notification    4
    last_notification    0
    notification_interval    60
    contact_groups    nt-admins,managers,everyone
  }
  
We see that the two escalation definitions overlap on the 4th and 5th notifications. For these notifications, Shinken will use a notification interval of 45 minutes, since it is the smallest interval present in any valid escalation definitions for those notifications.

One last note about notification intervals deals with intervals of 0. An interval of 0 means that Shinken should only sent a notification out for the first valid notification during that escalation definition. All subsequent notifications for the hostgroup or service will be suppressed. Take this example:

  
::

  define serviceescalation{
    host_name    webserver
    service_description    HTTP
    first_notification    3
    last_notification    5
    notification_interval    45
    contact_groups    nt-admins,managers
  }
  
  define serviceescalation{
    host_name    webserver
    service_description    HTTP
    first_notification    3
    last_notification    5
    notification_interval    45
    contact_groups    nt-admins,managers
  }
  
  define serviceescalation{
    host_name    webserver
    service_description    HTTP
    first_notification    7
    last_notification    0
    notification_interval    30
    contact_groups    nt-admins,managers
  }
  
In the example above, the maximum number of problem notifications that could be sent out about the service would be four. This is because the notification interval of 0 in the second escalation definition indicates that only one notification should be sent out (starting with and including the 4th notification) and all subsequent notifications should be repressed. Because of this, the third service escalation definition has no effect whatsoever, as there will never be more than four notifications.




Escalations based on time 
==========================

The escalations can also be based on time, instead of notification number. It's very easy to setup and work like for the old way but with time instead.

  
::

  define escalation{
    first_notification_time    60
    last_notification_time     120
    contact_groups    nt-admins,managers
  }
  
It will use the interval length for the value you set for first/last notification time. Here, it will escalate after 1 hour problem, and stop at 2 hours. You cannot have in the same escalation time and number escalation rules. But of course you can have escalations based on time and escalation based on notification number applied on hosts and services.




Escalations based on time short time 
=====================================

It's also interesting to see that with escalation based on time, if the notification interval is longer than the next escalation time, it's this last value that will be taken into account.

Let take an example where your service got :
  
::

  define service{
       notification_interval     1440
       escalations    ToLevel2,ToLevel3
  }
Then with the escalations objects :
  
::

  define escalation{
    first_notification_time    60
    last_notification_time     120
    contact_groups    level2
  }
  
    define escalation{
    first_notification_time    120
    last_notification_time     0
    contact_groups    level3
  }
Here let say you have a problem HARD on the service at t=0. It will notify the level1. The next notification should be at t=1440 minutes, so tomorrow. It's ok for classic services (too much notification is DANGEROUS!) but not for escalated ones.

Here, at t=60 minutes, the escalation will raise, you will notify the level2 contact group, and then at t=120 minutes you will notify the level3, and here one a day until they solve it!

So you can put large notification_interval and still have quick escalations times, it's not a problem :)



Time Period Restrictions 
=========================


Under normal circumstances, escalations can be used at any time that a notification could normally be sent out for the host or service. This "notification time window" is determined by the "notification_period" directive in the :ref:`host <configuringshinken/configobjects/host>` or :ref:`service <configuringshinken/configobjects/service>` definition.

You can optionally restrict escalations so that they are only used during specific time periods by using the "escalation_period" directive in the host or service escalation definition. If you use the "escalation_period" directive to specify a :ref:`Time Period Definition <configuringshinken/configobjects/timeperiod>` during which the escalation can be used, the escalation will only be used during that time. If you do not specify any "escalation_period" directive, the escalation can be used at any time within the "notification time window" for the host or service.

Escalated notifications are still subject to the normal time restrictions imposed by the "notification_period" directive in a host or service definition, so the timeperiod you specify in an escalation definition should be a subset of that larger "notification time window".



State Restrictions 
===================


If you would like to restrict the escalation definition so that it is only used when the host or service is in a particular state, you can use the "escalation_options" directive in the host or service escalation definition. If you do not use the "escalation_options" directive, the escalation can be used when the host or service is in any state.


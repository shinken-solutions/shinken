.. _notificationway:



============================
Notification Way Definition 
============================




Description 
============


A notificationway definition is used to define a way a contact if notified.



Definition Format 
==================


Bold directives are required, while the others are optional.



================================= ==========================
define notificationway{                                     
**notificationway_name**          ***notificationway_name***
**host_notification_period**      ***timeperiod_name***     
**service_notification_period**   ***timeperiod_name***     
**host_notification_options**     **[d,u,r,f,s,n]**         
**service_notification_options**  **[w,u,c,r,f,s,n]**       
**host_notification_commands**    ***command_name***        
**service_notification_commands** ***command_name***        
min_business_impact               [0/1/2/3/4/5]             
}                                                           
================================= ==========================



Example Definition 
===================

  
::

       # Email the whole 24x7 is okay
       define notificationway{
       notificationway_name            email_in_day
       service_notification_period     24x7
       host_notification_period        24x7
       service_notification_options    w,u,c,r,f
       host_notification_options       d,u,r,f,s
       service_notification_commands   notify-service
       host_notification_commands      notify-host
       }


Directive Descriptions 
=======================


   notificationway_name
  
This directive define the name of the notification witch be specified further in a contact definition

   host_notification_period
  
This directive is used to specify the short name of the :ref:`time period <configuringshinken/configobjects/timeperiod>` during which the contact can be notified about host problems or recoveries. You can think of this as an “on call" time for host notifications for the contact. Read the documentation on :ref:`time periods <thebasics-timeperiods>` for more information on how this works and potential problems that may result from improper use.

   service_notification_period
  
This directive is used to specify the short name of the :ref:`time period <configuringshinken/configobjects/timeperiod>` during which the contact can be notified about service problems or recoveries. You can think of this as an “on call" time for service notifications for the contact. Read the documentation on :ref:`time periods <thebasics-timeperiods>` for more information on how this works and potential problems that may result from improper use.

   host_notification_commands
  
This directive is used to define a list of the *short names* of the :ref:`commands <configuringshinken/configobjects/command>` used to notify the contact of a *host* problem or recovery. Multiple notification commands should be separated by commas. All notification commands are executed when the contact needs to be notified. The maximum amount of time that a notification command can run is controlled by the :ref:`notification_timeout <configuringshinken-configmain#configuringshinken-configmain-notification_timeout>` option.

   service_notification_commands
  
This directive is used to define a list of the *short names* of the :ref:`commands <configuringshinken-objectdefinitions#configuringshinken-objectdefinitions-command>` used to notify the contact of a *service* problem or recovery. Multiple notification commands should be separated by commas. All notification commands are executed when the contact needs to be notified. The maximum amount of time that a notification command can run is controlled by the :ref:`notification_timeout <configuringshinken-configmain#configuringshinken-configmain-notification_timeout>` option.

   host_notification_options
  
This directive is used to define the host states for which notifications can be sent out to this contact. Valid options are a combination of one or more of the following:

  * d = notify on DOWN host states
  * u = notify on UNREACHABLE host states
  * r = notify on host recoveries (UP states)
  * f = notify when the host starts and stops :ref:`flapping <advancedtopics-flapping>`,
  * s = send notifications when host or service :ref:`scheduled downtime <advancedtopics-downtime>` starts and ends. If you specify **n** (none) as an option, the contact will not receive any type of host notifications.

   service_notification_options
  
This directive is used to define the service states for which notifications can be sent out to this contact. Valid options are a combination of one or more of the following:

  * w = notify on WARNING service states
  * u = notify on UNKNOWN service states
  * c = notify on CRITICAL service states
  * r = notify on service recoveries (OK states)
  * f = notify when the service starts and stops :ref:`flapping <advancedtopics-flapping>`.
  * n = (none) : the contact will not receive any type of service notifications.

   min_business_impact
  
This directive is use to define the minimum business criticity level of a service/host the contact will be notified. Please see :ref:`root_problems_and_impacts </root_problems_and_impacts>`  for more details. 

  * 0 = less important
  * 1 = more important than 0
  * 2 = more important than 1
  * 3 = more important than 2
  * 4 = more important than 3
  * 5 = most important
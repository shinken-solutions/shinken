.. _setup_notification_ways:



The Notification Ways, AKA mail 24x7, SMS only the night for a same contact 
----------------------------------------------------------------------------


Let take a classical example: you want email notification 24x7 but SMS only the night and for critical alerts only. How do this with contacts definitions? You have to duplicate the contact. One with notification_period of 24x7 and the email command, and one other with send-by-sms for the night. Duplicate contacts can be hard to manage in services definitions afterward !

That why notification ways are useful: you defined some notification ways (that look really like contacts) and you linked them to your contact. 



Example 
~~~~~~~~


For example, you can have the below configuration:
your contact, a happy admin:

::

  
  define contact{
    contact_name                    happy_admin
    alias                           happy_admin
    email                           admin@localhost
    pager                           +33699999999
    notificationways                email_in_day,sms_the_night
  }


And now define our notification ways:

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
  
  # But SMS only at night
  define notificationway{
       notificationway_name            sms_at_night
       service_notification_period     night
       host_notification_period        night
       service_notification_options    c   ; so only CRITICAL
       host_notification_options       d   ; and DOWN
       service_notification_commands   notify-service-sms
       host_notification_commands      notify-host-sms
  }


And you can call theses ways from several contacts :)


The contact is valid because he's got valid notificationways. For each notification, we ask for all notification_ways to give us the commands to send. If their notification options or timeperiod is not good, they just do not give one.



Mix old contact with new notification says 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


Of course, you can still have "old school" contact definition, and even with the notificationways parameters. The service_notification_period parameter of the contact will just be used to create a notificationways like the others, that's all.

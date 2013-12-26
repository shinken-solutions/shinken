.. _sms_with_gateway:




===================
Send sms by gateway
===================


Shinken can be used to send sms to you and other people when you got an alert. 

I will tell you how to do it with ovh gateway. If you need for another one you need to modify a little bit the information. 



1. you need to go to your contact.cfg who is for linux in /usr/local/shinken/etc/contacts.cfg 
==============================================================================================



For each user you need to add her phone number in the pager line. (For ovh you need to do it with 0032 for example and not +32 , all phone number must be with the international prefix).

In the same file you need also to add these lines in each contact you want that I receive ams.

  
::

  
  host_notifications_enabled      1                    // This will activate the notifications for the hosts
  service_notifications_enabled   1                    // This will activate the notifications for the services
  notificationways SMS                                 // This is the name of your notifications ways ( You can write what you want but remember what you set ) 
   
  
Then you need to add this at the end of the contacts.cfg


::
  
  define notificationway{
       notificationway_name            SMS           // Here you need to put the name of the notifications ways you write up
       service_notification_period     24x7          // Here I will receive ams all the time, If you wanna receive them for only the night replace 24x7 by night. 
       host_notification_period        24x7          // Same as above
       service_notification_options    w,c,r         // It tell that I want receive a sms for the hosts who are in warning / critical / recovery
      host_notification_options         d,r          // It tell that I want receive a sms for the services who are down and recovery
       service_notification_commands   notify-service-by-ovhsms // The name of the notifications
       host_notification_commands      notify-host-by-ovhsms
  }



2. you need to go to your commands.cfg  who is in /usr/local/shinken/etc/commands.cfg 
======================================================================================



And add these line at the end. 


::

  
  # Notify Service by SMS-OVH
  define command {
    command_name        notify-service-by-ovhsms     // Should be the same as in the contacts.cfg
    command_line        $PLUGINSDIR$/ovhsms.sh  $CONTACTPAGER$ $NOTIFICATIONTYPE$ $SERVICEDESC$ $HOSTNAME$ $SE$ // Tell wich script shinken as to use to send sms. We will create it after. 
  }
  

  # Notify host by SMS-OVH
  define command {
    command_name        notify-host-by-ovhsms      * * Should be the same as in the contacts.cfg
    command_line        $PLUGINSDIR$/ovhsms.sh $CONTACTPAGER$ $NOTIFICATIONTYPE$ $SERVICEDESC$ $HOSTNAME$ $SER$ // Tell wich script shinken as to use to send sms. We will create it after.
  }





3. Add the script 
==================


First you need to be the shinken user so do a : su shinken
do a : cd /usr/local/shinken/libexec/
and then create and edit your new script with the name you set above :  nano -w ovhsms.sh


::

  
  #!/bin/bash
  
  
  date > ~/datesms
  
  NOTIFICATIONTYPE=$2
  HOSTALIAS=$3
  SERVICEDESC=$4
  SERVICESTATE=$5
  textesms="**"$NOTIFICATIONTYPE" alerte - "$HOSTALIAS"/"$SERVICEDESC" is "$SERVICESTATE" **" // This is the message who will be send. You can add something if you want. 
  wget -o ~/logenvoisms -O ~/reponse "https://www.ovh.com/cgi-bin/sms/http2sms.cgi?smsAccount=sms-XXXXXXXX-1&login=XXXXXXXX&password=XXXXXXXX&from=XXXXXXXXXXX&to=$1&contentType=text/xml&message=$textesms"     // This is the command who will send the sms. You need to adapt it with you gateway settings. 
  
  exit 0




4. Test It 
===========

   
Save your file and do : "exit" 
To exit the shinken user.
Then set down one of your host or service to test if you receive it.  

.. _sms_with_android:



Shinken and Android 
====================


Shinken can run on an android device like a phone. It can be very useful for one particular daemon: the reactionner that send alerts. With this, you can setup a "sms by phone" architecture, with high availability. We will see that you can also receive ACKs by SMS :)

All you need is one (or two if you want high availability) android phone with an internet connection and Wifi. Any version should work.

.. tip::  This is of course for fun. Unless you have a secure connection to your monitoring infrastructure. You should never open up your firewall to have in/out communications from a mobile phone directly to your monitoring systems. A serious infrastructure should use an SMS gateway in a DMZ that receives notifications from a your monitoring system. Either sourced as mails, or other message types.



Sending SMS 
------------




Install Python on your phone 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


  * enable the "Unknown sources" option in your device's "Application" settings to allow application installation from another source that the android marker.
  * Go to http://code.google.com/p/android-scripting/ and "flash" the barcode with an application like "barcode scanner", or just download http://android-scripting.googlecode.com/files/sl4a_r4.apk. Install this application.
  * Launch the sl4a application you just installed.
  * click in the menu button, click "view" and then select "interpreter"
  * click the menu button again, then add and select "Python 2.6". Then click to install.


Install the Pyro lib on your phone 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Go to http://pypi.python.org/pypi/Pyro4/ and download the same Pyro that you are using in Shinken.

  * Connect your phone to a computer, and open the sdcard disk.
  * Untar the Pyro4 tar ball, and copy the Pyro4 library directory (the one IN the Pyro4-10 directory, NOT the 4.10 directory itself) and copy/paste it in SDCARD/com.googlecode.pythonforandroid\extras\python directory. Be sure the file SDCARD\com.googlecode.pythonforandroid\extras\python\Pyro\__init__.py exists, or you put the wrong directory here.
  * Don't close your sdcard explorer



Install Shinken on your phone 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


  * Like for Pyro, copy your shinken library directory in SDCARD\com.googlecode.pythonforandroid\extras\python\. If you do not have the SDCARD\com.googlecode.pythonforandroid\extras\python\shinken\__ini__.py file, you put the bad directory.
  * Copy the bin/shinken-reactionner file in SDCARD\sl4a\scripts direcotry and rename it shinken-reactionner.py (so add the .py extension)



Time to launch the Shinken app on the phone 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


  * Unmount the phone from your computer and be sure to re-mount the sdcard on your phone (look at the notifications).
  * Launch the sl4a app
  * launch the shinken-reactionner.py app in the script list.
  * It should launch without errors



Declare this daemon in the central configuration 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


The phone(s) will be a new reactionner daemon. You should want to only launch SMS with it, not mail commands or nother notifications. So you will have to define this reactionner to manage only the SMS commands. There is an example of such SMS-reactionner in the sample etc/shinken-specific.cfg file and the module AndroidSMS need by this reactionner to send SMS with android.


::
  
  define reactionner{
       reactionner_name             reactionner-Android
       address                      WIFIIPOFYOURPHONE
       port                         7769
       spare                        0
  
       # Modules
       modules         AndroidSMS
       reactionner_tags        android_sms
  
       }
  
  
  # Reactionner can be launched under an android device
  # and can be used to send SMS with this module
  define module{
       module_name      AndroidSMS
       module_type      android_sms
  }

The important lines are:

 * address: put the Wifi address of your phone
 * modules: load the Android module to be able to manage sms sent.
 * reactionner_tags: only android_sms commands will be send to this reactionner.

In the commands.cfg, there are example of sms sending commands

::

  # For Android SMS things
  # You need both reactionner_tag and module_type in most cases!
  define command{
       command_name                    notify-host-by-android-sms
       command_line                    android_sms  $CONTACTPAGER$ Host: $HOSTNAME$\nAddress: $HOSTADDRESS$\nState: $HOSTSTATE$\nInfo: $OUTPUT$\nDate: $DATETIME$
       reactionner_tag                 android_sms
       module_type                     android_sms
  }
  

  define command{
       command_name                    notify-service-by-android-sms
       command_line                    android_sms  $CONTACTPAGER$ Service: $SERVICEDESC$\nHost: $HOSTNAME$\nAddress: $HOSTADDRESS$\nState: $SERVICESTATE$\nInfo: $OUTPUT$\nDate: $DATETIME$
       reactionner_tag                 android_sms
       module_type                     android_sms
  }


The important part are the reactionner_tag and module_type lines. With this parameter, you are sure the command will be managed by:
 * only the reactionner(s) with the tag android_sms, and in this reactionner, it will be managed by the module android_sms.



Add SMS notification ways 
~~~~~~~~~~~~~~~~~~~~~~~~~~


In order to use SMS, it is a good thing to add notification way dedicated to send SMS, separated from email notifications.
Edit templates and add theses lines to declare a new notification way using SMS (:ref:`more about notification ways <setup_notification_ways>`) :

::
  
  define notificationway{
       notificationway_name            android-sms
       service_notification_period     24x7
       host_notification_period        24x7
       service_notification_options    c,w,r
       host_notification_options       d,u,r,f,s
       service_notification_commands   notify-service-by-android-sms
       host_notification_commands      notify-host-by-android-sms
  }




Add SMS to your contacts 
~~~~~~~~~~~~~~~~~~~~~~~~~

You only need to add theses commands to your contacts (or contact templates, or notification ways) to send them SMS:

::
  
  define contact{
        name                            generic-contact         ; The name of this contact template
        [...]
        notificationways                email,android-sms       ; Use email and sms to notify the contact
  
  
That's all.




Receive SMS: acknowledge with a SMS 
------------------------------------




Pre-requite 
~~~~~~~~~~~~

You need to have a working android-reactionner with the sms module. The sms reception will be automatically enabled.



How to send ACK from SMS? 
~~~~~~~~~~~~~~~~~~~~~~~~~~


All you need is to send a SMS to the phone with the format:

For a service:

::
  
   ACK  host_name/service_description
  
For an host:

::

   ACK  host_name
  
  
And it will automatically raise an acknowledgment for this object :)

.. _setup_high_availability_shinken:



Shinken High Availability 
--------------------------


Shinken makes it easy to have a high availability architecture. Just as easily as the load balancing feature at :ref:`setup_distributed_shinken`

Shinken is business friendly when it comes to meeting availability requirements.

You learned how to add new poller satellites in the :ref:`setup_distributed_shinken`. For the HA the process is the same **You just need to add new satellites in the same way, then define them as "spares".**

You can (should) do the same for all the satellites for a complete HA architecture.



Install all spares daemons on server3 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


We keep the load balancing of the previous installation and we add a new server (if you do not need load balancing, just take the previous server). This new HA server will be server3 (server2 was for poller load balancing).

So like the previous case, you need to install the daemons but not launch them for now. Look at the 10 min start tutorial to know how to install them on server3.



Declare these spares on server1 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


Daemons on the server1 neeed to know where their spares are. Everything is done in the main configuration file shinken-specific.cfg. It should be at /etc/shinken/shinken-specific.cfg or c:\shinken\etc\shinken-specific.cfg).

Add theses lines:
 
::
  
  define scheduler{
  
       scheduler_name	scheduler-spare
       address	        server3
       port	        7768
       spare	        1
       }
  

  define poller{
  
       poller_name     poller-spare
       address         server3
       port            7771
       spare           1
  }
  

  define reactionner{

       reactionner_name	reactionner-spare
       address	        server3
       port	        7769
       spare	        1
       }
 
 
  define receiver{
  
       receiver_name    receiver-spare
       address          server3
       port             7773
       spare            1
  }

  
  define broker{
  
       broker_name     broker-spare
       address         server3
       port            7772
       spare           1
       modules         Simple-log,Livestatus
  }
  

  define arbiter{

       arbiter_name    arbiter-spare
       address         server3
       host_name       server3
       port            7770
       spare           1
  }


Ok. Configuring HA is defining new daemons on server3 as "spare 1". 

WAIT! There are 2 main pitfalls that can halt HA in its tracks:
  * Modules  - If your master daemon has modules, you must add them on the spare as well!!!!
  * Hostname - arbiter-spare has a host_name parameter: it must be the hostname of server3 (so in 99% of the cases, server3). Launch hostname to know the name of your server. If the value is incorrect, the spare arbiter won't start! 



Copy all configuration from server1 to server3 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


.. important::  It's very important that the two arbiter daemons have the same shinken-specific.cfg file. The whole configuration should also be rsync'ed or copied once a day to ensure the spare arbiter can take over in case of a massive failure of active arbiter. 

So copy it in the server3 (overwrite the old one) in the same place.

You do not need to sync all configuration files for hosts and services in the spare. When the master starts, it will synchronize with the spare. But beware, if server1 dies and you must start from fresh on server3, you will not have the full configuration! So synchronize the whole configuration once a day using rsync or other similar method, it is a requirement.



Start :) 
~~~~~~~~~


Ok, everything is ready. All you need now is to start all the daemons:
  
::

  
  $server1: sudo /etc/init.d/shinken start
  $server3: sudo /etc/init.d/shinken start


If an active daemon die, the spare will take over. This is detected in a minute or 2 (you can change it in the shinken-specific.cfg, for each daemon).

.. note::  For stateful fail-over of a scheduler, link one of the :ref:`distributed retention modules` <distributed retention modules> such as memcache or redis to your schedulers. This will avoid losing the current state of the checks handled by a failed scheduler. Without a retention module, the spare scheduler taking over will need to reschedule all checks and check states will be PENDING until this has completed.

.. note::  You now have a high availability architecture.

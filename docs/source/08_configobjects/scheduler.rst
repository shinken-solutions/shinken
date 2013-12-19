.. _scheduler:
.. _configuringshinken/configobjects/scheduler:



=====================
Scheduler Definition 
=====================




Description 
============


The Scheduler daemon is in charge of the scheduling checks, the analysis of results and follow up actions (like if a service is down, ask for a host check). They do not launch checks or notifications. They keep a queue of pending checks and notifications for other elements of the architecture (like pollers or reactionners). There can be many schedulers.

The Scheduler definition is optionnal. If no scheduler is defined, Shinken will "create" one for the user. There will be no high availability for it (no spare), and will use the default port in the server where the deamon is launched.



Definition Format 
==================


Variables in red are required, while those in black are optional. However, you need to supply at least one optional variable in each definition for it to be of much use.



================= ========================
define scheduler{                         
scheduler_name    *scheduler_name*        
address           *dns name of ip address*
port              *port*                  
spare             //[0/1]//               
realm             *realm name*            
modules           *modules*               
}                                         
================= ========================



Example Definition: 
====================


  
::

  	  define scheduler{
               scheduler_name     Europe-scheduler
               address            node1.mydomain
               port               7770
               spare              0
  	       realm              Europe
  
               ## Optional
               spare               0   ; 1 = is a spare, 0 = is not a spare
               weight              1   ; Some schedulers can manage more hosts than others
               timeout             3   ; Ping timeout
               data_timeout        120 ; Data send timeout
               max_check_attempts  3   ; If ping fails N or more, then the node is dead
               check_interval      60  ; Ping node every minutes
               modules            PickleRetention
               
               # Skip initial broks creation for faster boot time. Experimental feature
               # which is not stable.
               skip_initial_broks  0
               # In NATted environments, you declare each satellite ip[:port] as seen by
               # *this* scheduler (if port not set, the port declared by satellite itself
               # is used)
               #satellitemap    poller-1=1.2.3.4:1772, reactionner-1=1.2.3.5:1773, ...
  	  }
  
  
  
    
  
}



Variable Descriptions 
======================


   scheduler_name
  
This variable is used to identify the *short name* of the scheduler which the data is associated with.

   address
  
This directive is used to define the adress from where the main arbier can reach this scheduler. This can be a DNS name or a IP adress.

   port
  
This directive is used to define the TCP port used bu the daemon. The default value is *7768*.

   spare
  
This variable is used to define if the scheduler must be managed as a spare one (will take the conf only if a master failed). The default value is *0* (master).

   realm
  
This variable is used to define the :ref:`realm <configuringshinken/configobjects/realm>` where the scheduler will be put. If none is selected, it will be assigned to the default one.

   modules
  
This variable is used to define all modules that the scheduler will load.

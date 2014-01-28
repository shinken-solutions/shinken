.. _reactionner:
.. _configuringshinken/configobjects/reactionner:



=======================
Reactionner Definition 
=======================




Description 
============


The Reactionner daemon is in charge of notifications and launching event_handlers. There can be more than one Reactionner.



Definition Format 
==================


Variables in red are required, while those in black are optional. However, you need to supply at least one optional variable in each definition for it to be of much use.



=================== ========================
define reactionner{                         
reactionner_name    *reactionner_name*      
address             *dns name of ip address*
port                *port*                  
spare               //[0/1]//               
realm               *realm name*            
manage_sub_realms   *[0,1]*                 
modules             *modules*               
}                                           
=================== ========================



Example Definition: 
====================


  
::

  	  define reactionner{
               reactionner_name   Main-reactionner
               address            node1.mydomain
               port               7769
               spare              0
  	       realm              All
  
               ## Optionnal
               manage_sub_realms   0   ; Does it take jobs from schedulers of sub-Realms?
               min_workers         1   ; Starts with N processes (0 = 1 per CPU)
               max_workers         15  ; No more than N processes (0 = 1 per CPU)
               polling_interval    1   ; Get jobs from schedulers each 1 second
               timeout             3   ; Ping timeout
               data_timeout        120 ; Data send timeout
               max_check_attempts  3   ; If ping fails N or more, then the node is dead
               check_interval      60  ; Ping node every minutes
               reactionner_tags   tag1
               modules            module1,module2
  	  }
  


Variable Descriptions 
======================


   reactionner_name
  
This variable is used to identify the *short name* of the reactionner which the data is associated with.

   address
  
This directive is used to define the adress from where the main arbier can reach this reactionner. This can be a DNS name or a IP adress.

   port
  
This directive is used to define the TCP port used bu the daemon. The default value is *7772*.

   spare
  
This variable is used to define if the reactionner must be managed as a spare one (will take the conf only if a master failed). The default value is *0* (master).

   realm
  
This variable is used to define the :ref:`realm <configuringshinken/configobjects/realm>` where the reactionner will be put. If none is selected, it will be assigned to the default one.

   manage_sub_realms
  
This variable is used to define if the poller will take jobs from scheduler from the sub-realms of it's realm. The default value is *1*.

   modules
  
This variable is used to define all modules that the scheduler will load.

   reactionner_tags
  
This variable is used to define the checks the reactionner can take. If no reactionner_tags is defined, reactionner  will take all untagued notifications and event handlers. If at least one tag is defined, it will take only the checks that are also taggued like it.

By default, there is no reactionner_tag, so reactionner can take all untagued notification/event handlers (default).

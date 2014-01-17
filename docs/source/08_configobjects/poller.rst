.. _poller:
.. _configuringshinken/configobjects/poller:



==================
Poller Definition 
==================



Description 
============


The Poller object is a way to the Arbiter daemons to talk with a scheduler and give it hosts to manage. They are in charge of launching plugins as requested by schedulers. When the check is finished they return the result to the schedulers. There can be many pollers.

The Poller definition is optionnal. If no poller is defined, Shinken will "create" one for the user. There will be no high availability for it (no spare), and will use the default port in the server where the deamon is launched.



Definition Format 
==================


Variables in red are required, while those in black are optional. However, you need to supply at least one optional variable in each definition for it to be of much use.



================= ========================
define poller{                            
poller_name       *poller_name*           
address           *dns name of ip address*
port              *port*                  
spare             //[0/1]//               
realm             *realm name*            
manage_sub_realms *[0,1]*                 
poller_tags       *poller_tags*           
modules           *modules*               
}                                         
================= ========================



Example Definition: 
====================


  
::

  	  define poller{
               poller_name        Europe-poller
               address            node1.mydomain
               port               7771
               spare              0
  
               
               # Optional configurations
  	       manage_sub_realms  0
  	       poller_tags        DMZ, Another-DMZ
               modules            module1,module2
               realm              Europe
               min_workers         0   ; Starts with N processes (0 = 1 per CPU)
               max_workers         0   ; No more than N processes (0 = 1 per CPU)
               processes_by_worker 256 ; Each worker manages N checks
               polling_interval    1   ; Get jobs from schedulers each 1 minute
  	  }
  


Variable Descriptions 
======================


   poller_name
  
This variable is used to identify the *short name* of the poller which the data is associated with.

   address
  
This directive is used to define the adress from where the main arbier can reach this poller. This can be a DNS name or a IP adress.

   port
  
This directive is used to define the TCP port used bu the daemon. The default value is *7771*.

   spare
  
This variable is used to define if the poller must be managed as a spare one (will take the conf only if a master failed). The default value is *0* (master).

   realm
  
This variable is used to define the :ref:`realm <configuringshinken/configobjects/realm>` where the poller will be put. If none is selected, it will be assigned to the default one.

   manage_sub_realms
  
This variable is used to define if the poller will take jobs from scheduler from the sub-realms of it's realm. The default value is *0*.

   poller_tags
  
This variable is used to define the checks the poller can take. If no poller_tags is defined, poller will take all untagued checks. If at least one tag is defined, it will take only the checks that are also taggued like it.

By default, there is no poller_tag, so poller can take all untagued checks (default).

   modules
  
This variable is used to define all modules that the scheduler will load.

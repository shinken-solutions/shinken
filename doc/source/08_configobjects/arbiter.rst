.. _arbiter:
.. _configuringshinken/configobjects/arbiter:



===================
Arbiter Definition 
===================




Description 
============


The Arbiter object is a way to defined Arbiter daemons that will manage all the configuration and all the architecture of shinken like distributed monitoring and high availability. It reads the configuration, cuts it into parts (N schedulers = N parts), and then send them to all others elements. It manages the high availability part : if an element dies, it re-routes the configuration managed by this falling element to a spare one. Its other role is to receive input from users (like external commands of shinken.cmd) and send them to other elements. There can be only one active arbiter in the architecture.

The Arbiter definition is optionnal. If no arbiter is defined, Shinken will "create" one for the user. There will be no high availability for the Arbiter (no spare), and will use the default port in the server where the deamon is launched.



Definition Format 
==================


Variables in red are required, while those in black are optional. However, you need to supply at least one optional variable in each definition for it to be of much use.



=============== ========================
define arbiter{                         
arbiter_name    *arbiter_name*          
address         *dns name of ip address*
host_name       *hostname*              
port            *port*                  
spare           //[0/1]//               
modules         *modules*               
=============== ========================



================== ================================================================
timeout            *number of seconds to block the arbiter waiting for an answer*  
data_timeout       *seconds to wait when sending data to another satellite(daemon)*
max_check_attempts *number*                                                        
check_interval     *seconds to wait before issuing a new check*                    
}                                                                                  
================== ================================================================




Example Definition: 
====================


  
::

  	  define arbiter{
               arbiter_name       Main-arbiter
               address            node1.mydomain
               host_name          node1
               port               7770
               spare              0
               modules            module1,module2
  	  }
  


Variable Descriptions 
======================


   arbiter_name
  
This variable is used to identify the *short name* of the arbiter which the data is associated with.

   address
  
This directive is used to define the adress from where the main arbier can reach this arbiter (that can be itself). This can be a DNS name or a IP adress.

   host_name
  
This variable is used by the arbiters daemons to define with 'arbiter' object they are : all theses daemons in differents servers use the same configuration, so the only difference is the serveur name. This value must be equal to the name of the server (like with the hostname command). If none is defined, the arbiter daemon will put the name of the server where it's launched, but this will not be tolerated with more than one arbiter (because each daemons will think it's the master).

   port
  
This directive is used to define the TCP port used bu the daemon. The default value is *7770*.

   spare
  
This variable is used to define if the daemon matching this arbiter definition is a spare one of not. The default value is *0* (master).

   modules
  
This variable is used to define all modules that the arbtier daemon matching this definition will load.

   timeout
  
This variable defines how much time the arbiter will block waiting for the response of a inter-process ping (Pyro). 3 seconds by default. This operation will become non blocking when Python 2.4 and 2.5 is dropped in Shinken 1.4.

   data_timeout
  
Data send timeout. When sending data to another process. 120 seconds by default.

   max_check_attempts
  
If ping fails N or more, then the node is dead. 3 attempts by default.

   check_interval
  
Ping node every N seconds. 60 seconds by default.

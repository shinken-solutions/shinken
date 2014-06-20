.. _configobjects/arbiter:

===================
Arbiter Definition 
===================


Description 
============

The Arbiter object is a way to define Arbiter daemons that will manage the configuration and all different architecture components of shinken (like distributed monitoring and high availability). It reads the configuration, cuts it into parts (N schedulers = N parts), and then sends them to all others elements. It manages the high availability part : if an element dies, it re-routes the configuration managed by this falling element to a spare one. Its other role is to receive input from users (like external commands of shinken.cmd) and send them to other elements. There can be only one active arbiter in the architecture.

The Arbiter definition is optional. If no arbiter is defined, Shinken will "create" one for the user. There will be no high availability for the Arbiter (no spare), and it will use the default port on the server where the daemon is launched.


Definition Format 
==================

Variables in red are required, while those in black are optional. However, you need to supply at least one optional variable in each definition for it to be of much use.


==================================== =================================================================
define arbiter{                                                                     
arbiter_name                          *arbiter_name*                                                  
address                               *dns name of ip address*                                        
host_name                             *hostname*                                                      
port                                  *port*                                                          
spare                                 //[0/1]//                                                       
modules                               *modules*                                                       
timeout                               *number of seconds to block the arbiter waiting for an answer*  
data_timeout                          *seconds to wait when sending data to another satellite(daemon)*
max_check_attempts                    *number*                                                        
check_interval                        *seconds to wait before issuing a new check*                    
accept_passive_unknown_check_results  //[0/1]//
}
==================================== =================================================================


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
  This variable is used to identify the *short name* of the arbiter with which the data will be associated with.

address
  This directive is used to define the address from where the main arbiter can reach this arbiter (that can be itself). This can be a DNS name or an IP adress.

host_name
  This variable is used by the arbiters daemons to define which 'arbiter' object they are : all theses daemons on different servers use the same configuration, so the only difference is their server name. This value must be equal to the name of the server (like with the hostname command). If none is defined, the arbiter daemon will put the name of the server where it's launched, but this will not be tolerated with more than one arbiter (because each daemons will think it's the master).

port
  This directive is used to define the TCP port used by the daemon. The default value is *7770*.

spare
  This variable is used to define if the daemon matching this arbiter definition is a spare one or not. The default value is *0* (master/non-spare).

modules
  This variable is used to define all modules that the arbtier daemon matching this definition will load.

timeout
  This variable defines how much time the arbiter will block waiting for the response of a inter-process ping (Pyro). 3 seconds by default. This operation will become non blocking when Python 2.4 and 2.5 is dropped in Shinken 1.4.

data_timeout
  Data send timeout. When sending data to another process. 120 seconds by default.

max_check_attempts
  If ping fails N or more, then the node is considered dead. 3 attempts by default.

check_interval
  Ping node every N seconds. 60 seconds by default.

accept_passive_unknown_check_results
  If this is enabled, the arbiter will accept passive check results for unconfigured hosts and will generate unknown host/service check result broks.

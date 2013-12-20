.. _nsca_daemon_module:

NSCA module
===========


The NSCA daemon module is used to receive send_nsca packets and submit them to the Shinken command pipe. The NSCA module can be loaded by the Receiver or Arbiter process. It will listen on port TCP/5667 for send_nsca packets.

.. tip::  Passive checks can be submitted :ref:`natively to the Shinken command pipe <thebasics-passivechecks>` or from remote hosts to modules, such as NSCA, AMQP or collectd, loaded in the Shinken Arbiter or Receiver process. AMQP is implemented for integration with the Canopsis Hypervisor, but could be re-used for generic messaging.

.. note::  The Shinken NSCA module implementation is currently limited to the "xor" obfuscation/encryption.

In your shinken-specific.cfg file, just add (or uncomment):

  
::

  
  
::

  #You can send check result to Shinken using NSCA
  #using send_nsca command
  define module{
       module_name       NSCA
       module_type       nsca_server
       host              *
       port              5667
       encryption_method 0
       password          helloworld
  }
  
  define receiver{
  
::

       receiver_name    receiver-1
       address          localhost
       port             7773
       modules          NSCA
  
       timeout          3             ; 'ping' timeout
       data_timeout     120           ; 'data send' timeout
       max_check_attempts       3     ;  if at least max_check_attempts ping failed, the node is DEAD
       
       #advanced
       realm    All
       }
  
This daemon is totally optional.

It's main goal is to get all passive "things" (checks but why not other
commands) in distant realms. It will act as a "passive receive buffer" and will then dispatch the data or commands directly to the appropriate Scheduler or Arbiter process.

Data can be received from any Realm, thus the Realm option is nonsensical.

For now there is no init.d script to launch it. 
.. note::  Verify that the init script has been added.

It is launched like all other daemons:
  
::

  bin/shinken-receiver -c etc/receiverd.ini
  
  
.. tip::  Alternatively, for small installations with you can configure a modules inside your Arbiter instead of the Receiver. It will listen the TCP/5667 port for send_nsca packets. 


To configure the NSCA module in your Arbiter instead of Receiver. Add the NSCA module to your Arbiter object configuration.

  
::

  
  
::

  define arbiter{
       arbiter_name     Arbiter-Master
  #    host_name        node1       ;result of the hostname command under Unix
       address          localhost                   ;IP or DNS adress
       port             7770
       spare            0
       modules           NSCA
  }
  

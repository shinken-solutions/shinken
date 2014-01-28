.. _use_with_old_cgi_and_vshell:



===================================
Use Shinken with Old CGI and VShell
===================================


For the Old CGI & VShell 
~~~~~~~~~~~~~~~~~~~~~~~~~


The Old CGI and VShell uses the old flat file export. Shinken can export to this file, but beware: this method is very very slooooow!

.. warning::  You should migrate to a Livestatus enabled web interface.



Declare the status_dat module 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


Export all status into a flat file in the old Nagios format. It's for small/medium environment because it's very slow to parse. It can be used by the Nagios CGI. It also exports the objects.cache file for this interface.

Edit your /etc/shinken/shinken-specific.cfg file:

  
::

  
  define module{
  
::

       module_name              Status-Dat
       module_type              status_dat
       status_file              /var/lib/shinken/status.data
       object_cache_file        /var/lib/shinken/objects.cache
       status_update_interval   15 ; update status.dat every 15s
  }




Enable it 
~~~~~~~~~~


Edit your /etc/shinken/shinken-specific.cfg file and find the object Broker:

  
::

  
   define broker{
       broker_name      broker-1
   [...]
       modules          Simple-log,Status-Dat
   }
  

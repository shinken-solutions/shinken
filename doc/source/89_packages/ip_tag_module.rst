.. _ip_tag_module:


Ip Tag module
=============

Why tag a host based on it's IP address? 
-----------------------------------------


We learned on the :ref:`DMZ monitoring <setup_dmz_monitoring>` that you can "tag" a host with a poller_tag so it will be checked only by DMZ pollers. It can be tedious process to manually tag all these hosts. Shinken provides an automated method to do this.

This is handled by the arbiter ip_tag module.



Ip_tag module 
-------------


The ip_tag module is an arbiter module that looks up the host address during the configuration parsing and compares it to an predefined IP range (IPV4 or IPV6). If the range matches, it can apply or add a property, such as poller_tag. Other types of tags could be related to locations, functions, administrative groups, etc.

# Method: replace or append.

# replace will put the value if the property is unset. This is the default method.
.. warning::  Fix me: replace, implies overriding an existing value. And will cause user issues down the line. Rename it to set. Replace should be a different method altogether, so overall there should be 3 methods(set, append, replace).

# append will add with a , if a value already exist

Here is an example that will set the poller_tag property with the value DMZ of all hosts that:
  * have a their hostadress ip (or name resolved) in the range 192.168.0.1/24.
  * do not already have a poller_tag property set

  
::

  
  define module{
  
::

       module_name     IpTag
       module_type     ip_tag
       ip_range        192.168.0.1/24
       property        poller_tag
       value           DMZ
  }


To use the module add it in the arbiter object:

  
::

  
  
::

  define arbiter {
      [...]
      modules   NSCA,IpTag
  }
  


Add value instead of setting it 
--------------------------------

In the previous example we set the property poller_tag to a value. But what if we want to "add" a value, like a template name? We can change the "method" property of the module to "append" so we can add the "value" to the host property instead of replace it.

Here is an example where we want to add the "dmz" template on the hosts, while also keeping any defined templates:

  
::

  
  define module{
  
::

       module_name   IpTag
       module_type   ip_tag
       ip_range      192.168.0.1/24
       property      use
       value         dmz
       
       # Optional method
       method append
  }


For a host defined as:

  
::

  
  define host{
  
::

       host_name   example_host1
       address     192.168.0.2
       use         linux
  }

It will be "changed" internaly in:
  
::

  
  define host{
  
::

       host_name   example_host1
       address     192.168.0.2
       use         linux,dmz
  }




Name resolution 
~~~~~~~~~~~~~~~~

Of course you don't need to set IP address in the address of your host. You can set a hostname, and it will be resolved, and then compared to the range. :)

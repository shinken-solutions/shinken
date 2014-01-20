.. _multi-layer-discovery:


=====================
Multi layer discovery 
=====================


Shinken provides a discovery mecanism in several steps. There are on a side the **runners** (cf :ref:`Runners description <use_the_discovery_with_shinken_advanced>`) which are script that output in formatted way properties list of scanned host and on another side discovery rules which use properties list to tag hosts when some of these properties are meaningful.

There are two kinds of rules, those which generate a host definition and those which launch another runners more specific to the scanned object. Better an image than a long speech :


.. image:: /_static/images/shinken_multilayer_discovery.png
   :scale: 90 %





Runners available 
==================




Filesystems 
~~~~~~~~~~~




Pre-requisites 
---------------


To make this plugin works you must have snmp activated on targeted hosts. Take care to activate it and make HOST-RESSOURCES MIB OID available to it. Beginning OID of HOST-RESSOURCES MIB is : **.1.3.6.1.2.1.25**.
The default discovery runner rule trigger this runner on unix host with port 161 open.



How it works: 
--------------


FS discovery runner provides two modes : __macros__ and __tags__ modes. First one, __macros__ mode, will output a comma-separated list of filesystems under host macro '_fs', the other one will output tags with filesystems mountpoint.

.. important::  All filesystems will output with character **/** replaced by an underscore _.



Macros mode. 
-------------


It is the easiest mode. It will add a line into host definition with host macro '_fs' with comma-separated list of filesystems. Then it is only needed to write a service definition using 
that macro with shinken directive "duplicate_foreach". Here is an example :

::
  
  define service{
   service_description    Disks$KEY$
   use            generic-service
   register       0
   host_name      linux
   check_command  check_linux_disks!$KEY$
  
   duplicate_foreach    _fs
  }

$KEY$ will be replaced by '_fs' host macros value.



Tag mode 
---------


This mode will let you more flexibility to monitor filesystems. Each filesystems will be a tag named with filesystem mountpoint then you need discovery rules to tag scanned host with
filesystem name.
Example if you want to monitor "/var" filesystem on a host with following filesystems "/usr", "/var", "/opt", "/home", "/". You will need a discovery rules to match "/var", then a host 
template materializing the tag and a service applied to host template :

::
  
  define discoveryrule {
        discoveryrule_name     fs_var
        creation_type          host
        fs                     var$
        +use                   fs_var
  }

will match "/var" filesystem and tell to tag with "fs_var".

::
  
  define host{
        name                   fs_var
        register               0
  }

Host template used be scanned host.

::
  
  define service{
        host_name              fs_var
        use                    10min_short
        service_description    Usage_var
        check_command          check_snmp_storage!"var$$"!50!25
        icon_set               disk
        register               0
  }

and service applied to "fs_var" host template, itself applied to scanned host.

Now, if you want to apply same treatment to several filesystems, like "/var" and "/home" by example :

::
  
  define discoveryrule {
        discoveryrule_name     fs_var_home
        creation_type          host
        fs                     var$|home$
        +use                   fs_var_home
  }


::
  
  define host{
        name                   fs_var_home
        register               0
  }



::
  
  define service{
        host_name              fs_var_home
        use                    10min_short
        service_description    Usage_var_and_home
        check_command          check_snmp_storage!"var$$|home$$"!50!25
        icon_set               disk
        register               0
  }

Pay attention to double "$$", it is needed cause macros interpretation. When more than one "$" is used just double them else in this example we gotten Shinken trying to interprate macro '$|home$'.



Cluster 
~~~~~~~




Pre-requisites 
---------------


SNMP needed to make this runner works. You have to activate SNMP daemon on host discovered and make OID of clustering solution available to read.
OID beginning for HACMP-MIB is : **.1.3.6.1.4.1.2.3.1.2.1.5.1** and for Safekit is : **.1.3.6.1.4.1.107.175.10**.



How it works 
-------------


Runner does only detects HACMP/PowerHA and Safekit clustering solutions for the moment. It will scan OID and return cluster name or module name list, depends on Safekit or HACMP.
For an host with two Safekit modules **test** and **prod**, runner will output :

::

  # ./cluster_discovery_runnner.py -H sydlrtsm1 -O linux -C public
  sydlrtsm1::safekit=Test,Prod



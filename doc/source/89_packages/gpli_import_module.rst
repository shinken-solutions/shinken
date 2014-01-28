.. _gpli_import_module:



Shinken GLPI integration 
=========================


Shinken supports importing hosts from GLPI

For people not familiar with GLPI, it is an Open-Source CMDB. Applicable to servers, routers, printers or anything you want for that matter. It is also a help-desk tool. GLPI also integrates with tools like FusionInventory for IT inventory management.

You can still have flat files AND GLPI if you want. Hosts imported from GLPI will be treated as standard hosts from flat file (inheritance, groups, etc). In fact, in this first version the module only sends the host_name to Shinken, but there should be more information extracted like network connexions for parents relations in the future. :)



Requirements 
-------------


  - python module MySQLdb
  - Compatible version of GLPI Shinken module and GLPI version
    - ...
  - etc..



Enabling GLPI Shinken module 
-----------------------------

In your shinken-specific.cfg file, just add (or uncomment):

  
::

  #You know GLPI? You can load all configuration from this app(
  #with the webservices plugins for GLPI, in xmlrpc mode
  #and with plugin monitoring for GLPI)
  # =============== Work with Plugin Monitoring of GLPI ===============
  #All configuration read from this will be added to the others of the
  #standard flat file
  define module{
       module_name      GLPI
       module_type      glpi
       uri              http://localhost/glpi/plugins/webservices/xmlrpc.php
       login_name       glpi
       login_password   glpi
  }
  
And add it in your Arbiter object as a module.
  
::

  define arbiter{
       arbiter_name     Arbiter-Master
  #    host_name       node1       ;result of the hostname command under Unix
       address          localhost                   ;IP or DNS adress
       port             7770
       spare            0
       modules           GLPI
       }
  
It's done :)
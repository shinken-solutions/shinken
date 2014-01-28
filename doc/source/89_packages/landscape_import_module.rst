.. _landscape_import_module:



Ubuntu Landscape import 
========================




Description 
------------


You can import data from Ubuntu `Landscape`_ into Shinken to create hosts.

Ubuntu Landscape, is a web app to manage all your linux servers (update and co), which is provided by Canonical, Ubuntu's parent company.

This is an Arbiter import module. The Arbiter manages the configuration.



Prerequisites 
--------------


   You will need the `landscape-api`_ package installed on your Arbiter server.
  


Configuring the Landscape import module 
----------------------------------------


In your shinken-specific.cfg file, just add (or uncomment):


   define module {
   module_name      Landscape
   module_type      landscape_import
  
   # Configure your REAL key and secret from Landscape
   key              PAAAB2CILT80I0ZA0999
   secret           GGtWAAAzEItz0utWUeCe9BJKIYWX/hdSbA6YCHHH
   default_template generic-host        ; if the host is not tagged, use this one
  
   # If you are using a specific certificate for landscape_api
   #ca             /path/to.ca.cert
  
   # If you need a proxy to access https://landscape.canonical.com/api/
   #https_proxy    http://user:secret@myproxy.com:3128
}


  * Put in key and secret your private Landscape access.
  * default_template will be used if your host is not "tagged" in Landscape
  * If you are using a specific certificate for connexion, give the full path in ca
  * You will certainly need an https proxy to access the Landscape API. If so, configure it there.



Configuring the Arbiter module 
-------------------------------


And add it in your Arbiter object as a module.
  
::

  define arbiter{
       arbiter_name     Arbiter-Master
  #    host_name       node1       ;result of the hostname command under Unix
       address          localhost                   ;IP or DNS adress
       port             7770
       spare            0
       modules           Landscape
       }
  
Restart your Arbiter and it's done :)

.. tip::  Your "tags" will be applied as templates for your hosts.
.. _landscape-api: https://launchpad.net/~landscape/+archive/landscape-api
.. _Landscape: http://www.ubuntu.com/business/landscape
.. _realm:
.. _configuringshinken/configobjects/realm:



=================
Realm Definition 
=================



Description 
============


The realms are a optional feature useful if the administrator want to divide it's resources like schedulers or pollers.

The Realm definition is optional. If no scheduler is defined, Shinken will "create" one for the user and will be the default one.



Definition Format 
==================


Variables in red are required, while those in black are optional. However, you need to supply at least one optional variable in each definition for it to be of much use.



============= ===============
define realm{                
realm_name    *realm_name*   
realm_members *realm_members*
default       *default*      
}                            
============= ===============



Example Definition: 
====================


  
::

  	  define realm{
               realm_name     World
               realm_members  Europe,America,Asia
  	     default        0
  	  }
  


Variable Descriptions 
======================


   realm_name
  
This variable is used to identify the *short name* of the realm which the data is associated with.

   realm_members
  
This directive is used to define the sub-realms of this realms.

   default
  
This directive is used to define tis this realm is the default one (untagged host and satellites wil be put into it). The default value is *0*.

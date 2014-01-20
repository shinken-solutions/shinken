.. _contactgroup:
.. _configuringshinken/configobjects/contactgroup:




========================
Contact Group Definition
========================




Description 
============


A contact group definition is used to group one or more :ref:`contacts <configuringshinken/configobjects/contact>` together for the purpose of sending out alert/recovery :ref:`notifications <thebasics-notifications>`.



Definition Format: 
===================


Bold directives are required, while the others are optional.



===================== =======================
define contactgroup{                         
**contactgroup_name** **contactgroup_name**
**alias**             **alias**
members               *contacts*             
contactgroup_members  *contactgroups*        
}                                            
===================== =======================



Example Definition: 
====================


  
::

  	  define contactgroup{
  	  contactgroup_name       novell-admins
  	  alias                   Novell Administrators
  	  members                 jdoe,rtobert,tzach
  	  }
  


Directive Descriptions: 
========================


   contactgroup_name
  
This directive is a short name used to identify the contact group.

   alias
  
This directive is used to define a longer name or description used to identify the contact group.

   members
  
This directive is used to define a list of the *short names* of :ref:`contacts <configuringshinken-objectdefinitions#configuringshinken-objectdefinitions-contact>` that should be included in this group. Multiple contact names should be separated by commas. This directive may be used as an alternative to (or in addition to) using the *contactgroups* directive in :ref:`contact <configuringshinken-objectdefinitions#configuringshinken-objectdefinitions-contact>` definitions.

   contactgroup_members
  
This optional directive can be used to include contacts from other "sub" contact groups in this contact group. Specify a comma-delimited list of short names of other contact groups whose members should be included in this group.

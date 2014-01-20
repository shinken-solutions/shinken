.. _hostgroup:
.. _configuringshinken/configobjects/hostgroup:



======================
Host Group Definition 
======================




Description 
============


A host group definition is used to group one or more hosts together for simplifying configuration with :ref:`object tricks <advancedtopics-objecttricks>` or display purposes in the CGIs .



Definition Format 
==================


Bold directives are required, while the others are optional.



================== ====================
define hostgroup{                      
**hostgroup_name** ***hostgroup_name***
**alias**          ***alias***         
members            *hosts*             
hostgroup_members  *hostgroups*        
notes              *note_string*       
notes_url          *url*               
action_url         *url*               
realm              *realm*             
}                                      
================== ====================



Example Definition 
===================


  
::

  	  define hostgroup{
  	  hostgroup_name          novell-servers
  	  alias                   Novell Servers
  	  members                 netware1,netware2,netware3,netware4
  	  realm                   Europe
  	  }
  


Directive Descriptions 
=======================


   hostgroup_name
  
This directive is used to define a short name used to identify the host group.

   alias
  
This directive is used to define is a longer name or description used to identify the host group. It is provided in order to allow you to more easily identify a particular host group.

   members
  
This is a list of the *short names* of :ref:`hosts <configuringshinken/configobjects/host>` that should be included in this group. Multiple host names should be separated by commas. This directive may be used as an alternative to (or in addition to) the *hostgroups* directive in :ref:`host definitions <configuringshinken/configobjects/host>`.

   hostgroup_members
  
This optional directive can be used to include hosts from other “sub" host groups in this host group. Specify a comma-delimited list of short names of other host groups whose members should be included in this group.

   notes
  
This directive is used to define an optional string of notes pertaining to the host. If you specify a note here, you will see the it in the :ref:`extended information <thebasics-cgis>` CGI (when you are viewing information about the specified host).

   notes_url
  
This variable is used to define an optional URL that can be used to provide more information about the host group. If you specify an URL, you will see a red folder icon in the CGIs (when you are viewing hostgroup information) that links to the URL you specify here. Any valid URL can be used. If you plan on using relative paths, the base path will the the same as what is used to access the CGIs (i.e. ///cgi-bin/nagios///). This can be very useful if you want to make detailed information on the host group, emergency contact methods, etc. available to other support staff.

   action_url
  
This directive is used to define an optional URL that can be used to provide more actions to be performed on the host group. If you specify an URL, you will see a red “splat" icon in the CGIs (when you are viewing hostgroup information) that links to the URL you specify here. Any valid URL can be used. If you plan on using relative paths, the base path will the the same as what is used to access the CGIs (i.e. ///cgi-bin/shinken///).

   realm
  
This directive is used to define in which :ref:`realm <configuringshinken/configobjects/realm>` all hosts of this hostgroup will be put into. If the host are already tagged by a realm (and not the same), the value taken into account will the the one of the host (and a warning will be raised). If no realm is defined, the default one will be take..

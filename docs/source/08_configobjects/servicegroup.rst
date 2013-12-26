.. _servicegroup:
.. _configuringshinken/configobjects/servicegroup:



=========================
Service Group Definition 
=========================




Description 
============


A service group definition is used to group one or more services together for simplifying configuration with :ref:`object tricks <advancedtopics-objecttricks>` or display purposes in the :ref:`CGIs <thebasics-cgis>`.



Definition Format 
==================


Bold directives are required, while the others are optional.



===================== =======================
define servicegroup{                         
**servicegroup_name** ***servicegroup_name***
**alias**             ***alias***            
members               *services*             
servicegroup_members  *servicegroups*        
notes                 *note_string*          
notes_url             *url*                  
action_url            *url*                  
}                                            
===================== =======================



Example Definition 
===================


  
::

  	  define servicegroup{
  	  servicegroup_name       dbservices
  	  alias                   Database Services
  	  members                 ms1,SQL Server,ms1,SQL Serverc Agent,ms1,SQL DTC
  	  }
  


Directive Descriptions: 
========================


- servicegroup_name
  
This directive is used to define a short name used to identify the service group.

- alias
  
This directive is used to define is a longer name or description used to identify the service group. It is provided in order to allow you to more easily identify a particular service group.

- members
  
This is a list of the *descriptions* of :ref:`services <configuringshinken/configobjects/service>` (and the names of their corresponding hosts) that should be included in this group. Host and service names should be separated by commas. This directive may be used as an alternative to the *servicegroups* directive in :ref:`service definitions <configuringshinken/configobjects/service>`. The format of the member directive is as follows (note that a host name must precede a service name/description):

::

    members=<host1>,<service1>,<host2>,<service2>,...,<host*n*>,<service*n*>


- servicegroup_members
  
This optional directive can be used to include services from other “sub" service groups in this service group. Specify a comma-delimited list of short names of other service groups whose members should be included in this group.

- notes
  
This directive is used to define an optional string of notes pertaining to the service group. If you specify a note here, you will see the it in the :ref:`extended information <thebasics-cgis>` CGI (when you are viewing information about the specified service group).

- notes_url
  
This directive is used to define an optional URL that can be used to provide more information about the service group. If you specify an URL, you will see a red folder icon in the CGIs (when you are viewing service group information) that links to the URL you specify here. Any valid URL can be used. If you plan on using relative paths, the base path will the the same as what is used to access the CGIs (i.e. ///cgi-bin/shinken///). This can be very useful if you want to make detailed information on the service group, emergency contact methods, etc. available to other support staff.

- action_url
  
This directive is used to define an optional URL that can be used to provide more actions to be performed on the service group. If you specify an URL, you will see a red “splat" icon in the CGIs (when you are viewing service group information) that links to the URL you specify here. Any valid URL can be used. If you plan on using relative paths, the base path will the the same as what is used to access the CGIs (i.e. ///cgi-bin/shinken///).

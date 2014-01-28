.. _configuringshinken-configobject:




===============================
 Object Configuration Overview 
===============================



What Are Objects? 
==================


Objects are all the elements that are involved in the monitoring and notification logic. Types of objects include:

  * Services
  * Service Groups
  * Hosts
  * Host Groups
  * Contacts
  * Contact Groups
  * Commands
  * Time Periods
  * Notification Escalations
  * Notification and Execution Dependencies

More information on what objects are and how they relate to each other can be found below.



Where Are Objects Defined? 
===========================


Objects can be defined in one or more configuration files and/or directories that you specify using the :ref:`cfg_file <configuringshinken-configmain#configuringshinken-configmain-cfg_file>` and/or :ref:`cfg_dir <configuringshinken-configmain#configuringshinken-configmain-cfg_dir>` directives in the main configuration file.

When you follow the :ref:`Quickstart installation guide <gettingstarted-quickstart>`, several sample object configuration files are placed in "/etc/shinken/objects/". You can use these sample files to see how object inheritance works and learn how to define your own object definitions.



How Are Objects Defined? 
=========================


Objects are defined in a flexible template format, which can make it much easier to manage your Shinken configuration in the long term. Basic information on how to define objects in your configuration files can be found :ref:`here <configuringshinken-objectdefinitions>`.

Once you get familiar with the basics of how to define objects, you should read up on :ref:`object inheritance <advancedtopics-objectinheritance>`, as it will make your configuration more robust for the future. Seasoned users can exploit some advanced features of object definitions as described in the documentation on :ref:`object tricks <advancedtopics-objecttricks>`.



Objects Explained 
==================


Some of the main object types are explained in greater detail below...



Hosts 
------

  
:ref:`Hosts <configuringshinken/configobjects/host>` are one of the central objects in the monitoring logic. Important attributes of hosts are as follows:

  * Hosts are usually physical devices on your network (servers, workstations, routers, switches, printers, etc).
  * Hosts have an address of some kind (e.g. an IP or MAC address).
  * Hosts have one or more more services associated with them.
  * Hosts can have parent/child relationships with other hosts, often representing real-world network connections, which is used in the :ref:`network reachability <thebasics-networkreachability>` logic.



Host Groups 
------------


:ref:`Host Groups <configuringshinken/configobjects/hostgroup>` are groups of one or more hosts. Host groups can make it easier to 
  - view the status of related hosts in the Shinken web interface and 
  - simplify your configuration through the use of :ref:`object tricks <advancedtopics-objecttricks>`.



Services 
---------


:ref:`Services <configuringshinken/configobjects/service>` are one of the central objects in the monitoring logic. Services are associated with hosts and can be:

  * Attributes of a host (CPU load, disk usage, uptime, etc.)
  * Services provided by the host ("HTTP", "POP3", "FTP", "SSH", etc.)
  * Other things associated with the host ("DNS" records, etc.)



Service Groups 
---------------


:ref:`Service Groups <configuringshinken/configobjects/servicegroup>` are groups of one or more services. Service groups can make it easier to 
  - view the status of related services in the Shinken web interface and 
  - simplify your configuration through the use of :ref:`object tricks <advancedtopics-objecttricks>`.



Contacts 
---------


:ref:`Contacts <configuringshinken/configobjects/contact>` are people involved in the notification process:

  * Contacts have one or more notification methods (cellphone, pager, email, instant messaging, etc.)
  * Contacts receive notifications for hosts and service they are responsible for



Contact Groups 
---------------


:ref:`Contact Groups <configuringshinken/configobjects/contactgroup>` are groups of one or more contacts. Contact groups can make it easier to define all the people who get notified when certain host or service problems occur.



Timeperiods 
------------


:ref:`Timeperiods <configuringshinken/configobjects/timeperiod>` are are used to control:

  * When hosts and services can be monitored
  * When contacts can receive notifications

Information on how timeperiods work can be found :ref:`here <thebasics-timeperiods>`.



Commands 
---------


:ref:`Commands <configuringshinken/configobjects/command>` are used to tell Shinken what programs, scripts, etc. it should execute to perform:

  * Host and service checks
  * Notifications
  * Event handlers
  * and more...


.. _configobjects/broker:

==================
Broker Definition
==================


Description
============

The Broker daemon provides access to Shinken internal data. Its role is to get data from schedulers (like status and logs) and manage them. The management is done by modules. Many different modules exists : export to graphite, export to syslog, export into ndo database (MySQL and Oracle backend), service-perfdata export, couchdb export and more. To configure modules, consult the :ref:`broker module definitions <the_broker_modules>`.

The Broker definition is optional.


Definition Format
==================

Variables in red are required, while those in black are optional. However, you need to supply at least one optional variable in each definition for it to be of much use.


================= ========================
define broker{
broker_name       *broker_name*
address           *dns name of ip address*
port              *port*
spare             //[0/1]//
realm             *realm name*
manage_sub_realms *[0,1]*
modules           *modules*
}
================= ========================


Example Definition:
====================

::

  define broker{
      broker_name        broker-1
      address            node1.mydomain
      port               7772
      spare              0
      realm              All
      ## Optional
      manage_arbiters     1
      manage_sub_realms   1
      timeout             3   ; Ping timeout
      data_timeout        120 ; Data send timeout
      max_check_attempts  3   ; If ping fails N or more, then the node is dead
      check_interval      60  ; Ping node every minutes
      manage_sub_realms  1
      modules             livestatus,simple-log,webui2
  }


Variable Descriptions
======================

broker_name
  This variable is used to identify the *short name* of the broker which the data is associated with.

address
  This directive is used to define the address from where the main arbier can reach this broker. This can be a DNS name or a IP address.

port
  This directive is used to define the TCP port used bu the daemon. The default value is *7772*.

spare
  This variable is used to define if the broker must be managed as a spare one (will take the conf only if a master failed). The default value is *0* (master).

realm
  This variable is used to define the :ref:`realm <configobjects/realm>` where the broker will be put. If none is selected, it will be assigned to the default one.

manage_arbiters
  Take data from Arbiter. There should be only one broker for the arbiter.

manage_sub_realms
  This variable is used to define if the broker will take jobs from scheduler from the sub-realms of it's realm. The default value is *1*.

modules
  This variable is used to define all modules that the broker will load. The main goal of the Broker is to give status to theses modules.

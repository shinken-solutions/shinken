.. _advancedtopics-businessrules:





Business rules 
===============




View your infrastructure from a business perspective 
-----------------------------------------------------

The main role of this feature is to allow users to have in one "indicator" the aggregation of other states. This indicator can provide a unique view for users focused on different roles.

Typical roles :

  * Service delivery Management
  * Business Management
  * Engineering
  * IT support

Let's take a simple example of a service delivery role for an ERP application. It mainly consists of the following IT components :

  * 2 databases, in high availability, so with one database active, the service is considered up
  * 2 web servers, in load sharing, so with one web server active, the service is considered up
  * 2 load balancers, again in high availability

These IT components (Hosts in this example) will be the basis for the ERP service.

With business rules, you can have an "indicator" representing the "aggregated service" state for the ERP service! Shinken already checks all of the IT components one by one including processing for root cause analysis from a host and service perspective.



How to define Business Rules? 
------------------------------

It's a simple service (or a host) with a "special" check_command named bp_rule. :)

This makes it compatible with all your current habits and UIs. As the service aggregation is considered as any other state from a host or service, you can get notifications, actions and escalations. This means you can have contacts that will receive only the relevant notifications based on their role.

.. warning::  You do not have to define "bp_rule" command, it's purely internal. You should NOT define it in you checkcommands.cfg file, or the configuration will be invalid due to duplicate commands!

Here is a configuration for the ERP service example, attached to a dummy host named "servicedelivery".


::
  
  define service{

     use         standard-service
     host_name   servicedelivery
     service_description  ERP
     check_command        bp_rule!(h1,database1 | h2,database2) & (h3,Http1 | h4,Http4) & (h5,IPVS1 | h6,IPVS2)
  }

That's all!

.. note::  A complete service delivery view should include an aggregated view of the end user availability perspective states, end user performance perspective states, IT component states, application error states, application performance states. This aggregated state can then be used as a metric for Service Management (basis for defining an SLA).



With "need at least X elements" clusters 
-----------------------------------------

In some cases, you know that in a cluster of N elements, you need at least X of them to run OK. This is easily defined, you just need to use the "X of:" operator.

Here is an example of the same ERP but with 3 http web servers, and you need at least 2 of them (to handle the load) :


::
  
  define service{

     use         standard-service
     host_name   servicedelivery
     service_description  ERP
     check_command        bp_rule!(h1,database1 | h2,database2) & (2 of: h3,Http1 & h4,Http4 & h5,Http5) & (h6,IPVS1 | h7,IPVS2)
  }

It's done :)




The NOT rule 
-------------

You can define a not state rule. It can be useful for active/passive setups for example. You just need to add a ! before your element name.

For example :

::
  
  define service{
  
     use         generic-service
     host_name   servicedelivery
     service_description  Cluster_state
     check_command        bp_rule!(h1,database1 & !h2,database2)
  }


Aggregated state will be ok if database1 is ok and database2 is warning or critical (stopped).


Manage degraded status 
-----------------------

In the Xof: way the only case where you got a "warning" (="degraded but not dead") it's when all your elements are in warning. But you should want to be in warning if 1 or your 3 http server is critical : the service is still running, but in a degraded state.

For this you can use the extended operator *X,Y,Zof:*
  * X : number min of OK to get an overall OK state
  * Y : number min of WARNING to get an overall WARNING state
  * Z : number min of CRITICAL to get an overall CRITICAL state

State processing will be done the following order :
  * is Ok possible?
  * is critical possible?
  * is warning possible?
  * if none is possible, set OK.

Here are some example for business rules about 5 services A, B, C, D and E. Like 5,1,1of:A|B|C|D|E



Sample 1 
~~~~~~~~~



==== == == == ==
A    B  C  D  E 
Warn Ok Ok Ok Ok
==== == == == ==

Rules and overall states :

  * 4of:  --> Ok
  * 5,1,1of: --> Warning
  * 5,2,1of: --> Ok



Sample 2 
~~~~~~~~~



==== ==== == == ==
A    B    C  D  E 
Warn Warn Ok Ok Ok
==== ==== == == ==

Rules and overall states :

  * 4of:  --> Warning
  * 3of: --> Ok
  * 4,1,1of: --> Warning



Sample 3 
~~~~~~~~~



==== ==== == == ==
A    B    C  D  E 
Crit Crit Ok Ok Ok
==== ==== == == ==

Rules and overall states :

  * 4of:  --> Critical
  * 3of: --> Ok
  * 4,1,1of: --> Critical



Sample 4 
~~~~~~~~~



==== ==== == == ==
A    B    C  D  E 
Warn Crit Ok Ok Ok
==== ==== == == ==

Rules and overall states :

  * 4of:  --> Critical
  * 4,1,1of: --> Critical



Sample 5 
~~~~~~~~~



==== ==== ==== == ==
A    B    C    D  E 
Warn Warn Crit Ok Ok
==== ==== ==== == ==

Rules and overall states :

  * 2of:  --> Ok
  * 4,1,1of: --> Critical



Sample 6 
~~~~~~~~~



==== ==== ==== == ==
A    B    C    D  E 
Warn Crit Crit Ok Ok
==== ==== ==== == ==

   Rules and overall states :
  

* 2of:  --> Ok
  * 2,4,4of: --> Ok
  * 4,1,1of: --> Critical
  * 4,1,2of: --> Critical
  * 4,1,3of: --> Warning



Classic cases 
~~~~~~~~~~~~~~

Let's look at some classic setups, for MAX elements.

  * ON/OFF setup : MAXof: <=> MAX,MAX,MAXof:
  * Warning as soon as problem, and critical if all criticals : MAX,1,MAXof:
  * Worse state : MAX,1,1



.. _medium/business-rules:



===============
Business rules
===============


View your infrastructure from a business perspective
=====================================================

The main role of this feature is to allow users to have in one "indicator" the aggregation of other states. This indicator can provide a unique view for users focused on different roles.

Typical roles:

  * Service delivery Management
  * Business Management
  * Engineering
  * IT support

Let's take a simple example of a service delivery role for an ERP application. It mainly consists of the following IT components:

  * 2 databases, in high availability, so with one database active, the service is considered up
  * 2 web servers, in load sharing, so with one web server active, the service is considered up
  * 2 load balancers, again in high availability

These IT components (Hosts in this example) will be the basis for the ERP service.

With business rules, you can have an "indicator" representing the "aggregated service" state for the ERP service! Shinken already checks all of the IT components one by one including processing for root cause analysis from a host and service perspective.


How to define Business Rules?
==============================

It's a simple service (or a host) with a "special" check_command named bp_rule. :)

This makes it compatible with all your current habits and UIs. As the service aggregation is considered as any other state from a host or service, you can get notifications, actions and escalations. This means you can have contacts that will receive only the relevant notifications based on their role.

.. warning::  You do not have to define "bp_rule" command, it's purely internal. You should NOT define it in you checkcommands.cfg file, or the configuration will be invalid due to duplicate commands!

Here is a configuration for the ERP service example, attached to a dummy host named "servicedelivery".


::

  define service{
         use                  standard-service
         host_name            servicedelivery
         service_description  ERP
         check_command        bp_rule!(h1,database1 | h2,database2) & (h3,Http1 | h4,Http4) & (h5,IPVS1 | h6,IPVS2)
  }

That's all!

.. note::  A complete service delivery view should include an aggregated view of the end user availability perspective states, end user performance perspective states, IT component states, application error states, application performance states. This aggregated state can then be used as a metric for Service Management (basis for defining an SLA).


With "need at least X elements" clusters
=========================================

In some cases, you know that in a cluster of N elements, you need at least X of them to run OK. This is easily defined, you just need to use the "X of:" operator.

Here is an example of the same ERP but with 3 http web servers, and you need at least 2 of them (to handle the load):


::

  define service{
         use                  standard-service
         host_name            servicedelivery
         service_description  ERP
         check_command        bp_rule!(h1,database1 | h2,database2) & (2 of: h3,Http1 & h4,Http4 & h5,Http5) & (h6,IPVS1 | h7,IPVS2)
  }

It's done :)

Possible values of X in X of: expressions
------------------------------------------


The ``X of:`` expression may be configured different values depending on the needs. The supported expressions are described below:

  * **A positive integer**, which means "*at least X host/servicices should be up*"

  * **A positive percentage**, which means "*at least X percents of hosts/services should be up*". This percentage expression may be combined with Groupping expression expansion to build expressions such as "*95 percents of the web front ends shoud be up*". This way, adding hosts in the web frontend hostgroup is sufficient, and the QoS remains the same.

  * **A negative integer**, which means "*at most X host/servicices may be down*"

  * **A negative percentage**, which means "*at most X percents of hosts/services should may be down*". This percentage expression may be combined with Groupping expression expansion to build expressions such as "*5 percents of the web front ends may be down*". This way, adding hosts in the web frontend hostgroup is sufficient, and the QoS remains the same.

Example:

::

  define service{
         use                  standard-service
         host_name            servicedelivery
         service_description  ERP
         check_command        bp_rule!(h1,database1 | h2,database2) & (h6,IPVS1 | h7,IPVS2) & 95% of: g:frontend,Http
  }




The NOT rule
=============


You can define a not state rule. It can be useful for active/passive setups for example. You just need to add a ! before your element name.

Example:

::

  define service{
         use                  generic-service
         host_name            servicedelivery
         service_description  Cluster_state
         check_command        bp_rule!(h1,database1 & !h2,database2)
  }


Aggregated state will be ok if database1 is ok and database2 is warning or critical (stopped).



Manage degraded status
=======================


In the ``Xof:`` way the only case where you got a "warning" (="degraded but not dead") it's when all your elements are in warning. But you should want to be in warning if 1 or your 3 http server is critical: the service is still running, but in a degraded state.

For this you can use the extended operator *X,Y,Zof:*
  * X: number min of OK to get an overall OK state
  * Y: number min of WARNING to get an overall WARNING state
  * Z: number min of CRITICAL to get an overall CRITICAL state

State processing will be done the following order:
  * is Ok possible?
  * is critical possible?
  * is warning possible?
  * if none is possible, set OK.

Here are some example for business rules about 5 services A, B, C, D and E. Like 5,1,1of:A|B|C|D|E


Example 1
----------

===== ===== ===== ===== =====
**A** **B** **C** **D** **E**
Warn   Ok   Ok    Ok    Ok
===== ===== ===== ===== =====

Rules and overall states:

  * 4of:  --> Ok
  * 5,1,1of: --> Warning
  * 5,2,1of: --> Ok


Example 2
----------

===== ===== ===== ===== =====
**A** **B** **C** **D** **E**
Warn  Warn  Ok    Ok    Ok
===== ===== ===== ===== =====

Rules and overall states:

  * 4of:  --> Warning
  * 3of: --> Ok
  * 4,1,1of: --> Warning


Example 3
----------

===== ===== ===== ===== =====
**A** **B** **C** **D** **E**
Crit  Crit  Ok    Ok    Ok
===== ===== ===== ===== =====

Rules and overall states:

  * 4of:  --> Critical
  * 3of: --> Ok
  * 4,1,1of: --> Critical


Example 4
----------

===== ===== ===== ===== =====
**A** **B** **C** **D** **E**
Warn  Crit   Ok   Ok    Ok
===== ===== ===== ===== =====

Rules and overall states:

  * 4of:  --> Critical
  * 4,1,1of: --> Critical


Example 5
----------

===== ===== ===== ===== =====
**A** **B** **C** **D** **E**
Warn  Warn  Crit   Ok   Ok
===== ===== ===== ===== =====

Rules and overall states:

  * 2of:  --> Ok
  * 4,1,1of: --> Critical


Example 6
----------

===== ===== ===== ===== =====
**A** **B** **C** **D** **E**
Warn  Crit  Crit   Ok   Ok
===== ===== ===== ===== =====

Rules and overall states:

  * 2of:  --> Ok
  * 2,4,4of: --> Ok
  * 4,1,1of: --> Critical
  * 4,1,2of: --> Critical
  * 4,1,3of: --> Warning


Classic cases
--------------

Let's look at some classic setups, for MAX elements.

  * ON/OFF setup: MAXof: <=> MAX,MAX,MAXof:
  * Warning as soon as problem, and critical if all criticals: MAX,1,MAXof:
  * Worse state: MAX,1,1



Grouping expression expansion
==============================


Sometimes, you do not want to specify explicitly the hosts/services contained in a business rule, but prefer use a grouping expression such as *hosts from the hostgroup xxx*, *services holding lablel yyy* or *hosts which name matches regex zzz*.

To do so, it is possible to use a *grouping expression* which is expanded into hosts or services. The supported expressions use the following syntax:

::

  flag:expression

The flag is a single character qualifying the expansion type. The supported types (and associated flags) are described in the table below.


Host flags
-----------

===== ================================== =========== =========================
**F** **Expansion**                      **Example** **Equivalent to**
g     Content of the hostgroup           g:webs      web-srv1 & web-srv2 & ...
l     Hosts which are holding label      l:front     web-srv1 & db-srv1 & ...
r     Hosts which name matches regex     r:^web      web-srv1 & web-srv2 & ...
t     Hosts which are holding tag        t:http      web-srv1 & web-srv2 & ...
===== ================================== =========== =========================


Service flags
--------------

===== ============================================ ============= ===================================
**F** **Expansion**                                **Example**   **Equivalent to**
g     Content of the servicegroup                  g:web         web-srv1,HTTP & web-srv2,HTTP & ...
l     Services which are holding label             l:front       web-srv1,HTTP & db-srv1,MySQL & ...
r     Services which description matches regex     r:^HTTPS?     web-srv1,HTTP & db-srv2,HTTPS & ...
t     Services which are holding tag               t:http        web-srv1,HTTP & db-srv2,HTTPS & ...
===== ============================================ ============= ===================================

  * **Labels** are arbitrary names which may be set on any host or service using the ``label`` directive.

  * **Tags** are the template names inherited by hosts or services, generally coming from packs.

It is possible to combine both **host** and **service** expansion expression to build complex business rules.

.. note:: A business rule expression always has to be made of a host expression (selector if you prefer)
          AND a service expression (still selector) separated by a coma when looking at service status.
          If not so, there is no mean to distinguish a host status from a service status in the expression.
          In servicegroup flag case, as you do not want to apply any filter on the host (you want ALL services which are member of the XXX service group, whichever host they are bound to),
          you may use the * host selector expression. The correct expression syntax should be:
          ``bp_rule!*,g:my-servicegroup``
          The same rule applies to other service selectors (l, r, t, and so on).

Examples of combined expansion expression
-----------------------------------------

You want to build a business rule including all web servers composing the application frontend.

::

  l:front,r:HTTPS?

  which is equivalent to:

  web-srv1,HTTP & web-srv3,HTTPS

You may obviously combine expression expansion with standard expressions.

::

  l:front,h:HTTPS? & db-srv1,MySQL

  which is equivalent to:

  (web-srv1,HTTP & web-srv3,HTTPS) & db-srv1,MySQL




Smart notifications
====================


As of any host or service check, a business rule having its state in a non ``OK`` state may send notifications depending on its ``notification_options`` directive. But what if the underlying problems are known, and may be acknowledged ? The default behaviour is to continue sending notifications.

This may be what you need, but what if you want the business rule to stop sending notifications ?

Imagine your business rule is composed of all your site's web front ends. If a host fails, you want to know it, but once someone starts to fix the issue, you don't want to be notified anymore. A possible solution is to acknowledge the business rule itself. But if you do so, any other failing host won't get notified. Another solution is to enable *smart notification* on the business rule check.

*Smart notifications* is a way to disable notifications on a business rule having all its problems acknowledged. If a new problem occurs, notifications will be enabled back while it has not been acknowledged.

To enable smart notifications, simply set the ``business_rule_smart_notifications`` to ``1``.


Downtimes management
---------------------

Downtimes are a bit more tricky to handle. While acknowledgement are necessarily set by humans, downtimes may be set automatically (for instance, by *maintenance periods*). You may still want to be notified during downtime periods. As a consequence, downtimes are not taken into account by smart notification processing, unless explicitly told to do so.

To enable downtimes in smart notifications processing, simply set the ``business_rule_downtime_as_ack`` to ``1``.




Consolidated services
======================


Another useful usage of business rules is consolidated services. Imagine you have a large web cluster, composed of hundreds of nodes. If a small portion of the nodes fail, you may receive a large number of notifications, which is not convenient. To prevent this, you may use a business rule looking like ``bp_rule!g:web,...``. If you disable notifications by setting ``notification_options`` to ``n`` on the underlying hosts or services, you would receive a single notification with all the failing nodes in one time, which may be clearer.

To avoid having to manually set ``notification_options`` on each node, you may use two convenient directives on the business rule side: ``business_rule_host_notification_options`` which enforces notification options of underlying hosts, and ``business_rule_service_notification_options`` which does the same for services.

This feature, combined with the convenience of packs and `Smart notifications`_ allows to build large consolidated services very easily.

Example:

::

  define host {
         use http
         host_name web-01
         hostgroups web
         ...
         }

  define host {
         use http
         host_name web-02
         hostgroups web
         ...
         }

  define host {
         host_name meta
         ...
         }

  define service {
         host_name meta
         service_description Web cluster
         check_command bp_rule!g:web,g:HTTPS?
         business_rule_service_notification_options n
         ...
         }

In the previous example, HTTP/HTTPS services come from the ``http`` pack. If one or more http servers fail, a single notification would be sent, rather than one per failing service.

.. warning:: It would be very tempting in this situation to acknowledge the consolidated service if a notification is sent. Never do so, as any, as any new failure would not be reported. You still have to acknowledge each independent failure. Take care to explain this to people in charge of the operations.



Macro expansion
================

It is possible in a business rule expression to include macros, as you would do for normal check command definition. You may for instance define a custom macro on the host or service holding the business rule, and use it in the expression.

Combined with :ref:`macro modulation <advanced/macro-modulations>`, this allows to define consolidated services with variable fault tolerance thresholds depending on the timeperiod.

Imagine your web frontend cluster composed of dozens servers serving the web site. If one is failing, this would not impact the service so much. During the day, when the complete team is at work, a single failure should be notified and fixed immediately. But during the night, you may consider that losing let's say up to 5% of the cluster has no impact on the QoS: thus waking up the on-call guy is not useful.

You may handle that with a consolidated service using macro modulation combined with an ``Xof:`` expression.

Example:

::

  define macromodulation{
         macromodulation_name web-xof
         modulation_period night
         _XOF_WEB -5% of:
         }

  define host {
         use http
         host_name web-01
         hostgroups web
         ...
         }

  define host {
         use http
         host_name web-02
         hostgroups web
         ...
         }

  define host {
         host_name meta
         macromodulations web-xof
         ...
         }

  define service {
         host_name meta
         service_description Web cluster
         check_command bp_rule!$_HOSTXOF_WEB$ g:web,g:HTTPS?
         business_rule_service_notification_options n
         ...
         }

In the previous example, during the day, we're outside the modulation period. The ``_XOF_WEB`` is not defined, so the resulting business rule is ``g:web,g:HTTPS?``. During the night, the macro is set a value, then the resulting business rule is ``-5% of: g:web,g:HTTPS?``, allowing to lose 5% of the cluster silently.



Business rule check output
===========================


By default, business rules checks have no output as there's no real script or binary behind. But it is still possible to control their output using a templating system.

To do so, you may set the ``business_rule_output_template`` option on the host or service holding the business rule. This attribute may contain any macro. Macro expansion works as follows:

  * All macros **outside** the ``$(`` and ``)$`` sequences are expanded using attributes set on the host or service holding the business rule.

  * All macros **between** the ``$(`` and ``)$`` sequences are expanded for each underlying problem using its attributes.

All macros defined on hosts or services composing or holding the business rule may be used in the outer or inner part of the template respectively.

To ease writing output template for business rules made of both hosts and services, 3 convinience macros having the same meaning for each type may be used: ``STATUS``, ``SHORTSTATUS``, and ``FULLNAME``, which expand respectively to the host or service status, its status abreviated form and its full name (``host_name`` for hosts, or ``host_name/service_description`` for services).

Example:

Imagine you want to build a consolidated service which notifications contain links to the underlying problems in the WebUI, allowing to acknowledge them without having to search. You may use a template looking like:

::

  define service {
         host_name meta
         service_description            Web cluster
         check_command                  bp_rule!$_HOSTXOF_WEB$ g:web,g:HTTPS?
         business_rule_output_template  Down web services: $(<a href='http://webui.url/service/$HOSTNAME$/$SERVICEDESC$'>($SHORTSTATUS$) $HOSTNAME$</a> )$
         ...
         }


The resulting output would look like ``Down web services: link1 link2 link3 ...`` where ``linkN`` are urls leading to the problem in the WebUI.

Acknowledge management
======================

By default, if we acknowledge an element, it conserves its state to determine the status of our aggregated service.
In some cases, we want that an acknowledge element is considered as if it was in Ok/Up state for a business rule.

To enable this feature, simply set `business_rule_ack_as_ok`` to ``1``..

.. _ticket: https://github.com/naparuba/shinken/issues/509

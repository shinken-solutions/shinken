.. _advanced/distributed:

========================
 Distributed Monitoring
========================


Introduction
=============

Shinken can be configured to support distributed monitoring of network services and resources. Shinken is designed for it in contrast to the Nagios way of doing it: which is more of a "MacGyver" way.


Goals
======

The goal in the distributed monitoring environment is to offload the overhead (CPU usage, etc.) of performing and receiving service checks from a "central" server onto one or more "distributed" servers. Most small to medium sized shops will not have a real need for setting up such an environment. However, when you want to start monitoring thousands of hosts (and several times that many services) using Shinken, this becomes quite important.


The global architecture
========================

Shinken's architecture has been designed according to the Unix Way: one tool, one task. Shinken has an architecture where each part is isolated and connects to the others via standard interfaces. Shinken is based on the a HTTP backend. This makes building a highly available or distributed monitoring architecture quite easy. In contrast, the Nagios daemon does nearly everything: it loads the configuration, schedules and launches checks, and raises notifications.

Major innovations of Shinken over Nagios are to :
  * split the different roles into separate daemons
  * permit the use of modules to extend and enrich the various Shinken daemons

Shinken core uses **distributed** programming, meaning a daemon will often do remote invocations of code on other daemons, this means that to ensure maximum compatibility and stability, the core language, paths and module versions **must** be the same everywhere a daemon is running.


Shinken Daemon roles
=====================

    * **Arbiter**: The arbiter daemon reads the configuration, divides it into parts (N schedulers = N parts), and distributes them to the appropriate Shinken daemons. Additionally, it manages the high availability features: if a particular daemon dies, it re-routes the configuration managed by this failed daemon to the configured spare. Finally, it receives input from users (such as external commands from nagios.cmd) or passive check results and routes them to the appropriate daemon. Passive check results are forwarded to the Scheduler responsible for the check. There can only be one active arbiter with other arbiters acting as hot standby spares in the architecture.

      * Modules for data collection: NSCA, TSCA, Ws_arbiter (web service)
      * Modules for configuration data storage: MongoDB,
      * Modules for status retention: PickleRententionArbiter
      * Modules for configuration manipulation: IP_Tag, MySQLImport, GLPI, vmware autolinking and other task specific modules


    * **Scheduler**: The scheduler daemon manages the dispatching of checks and actions to the poller and reactionner daemons respectively. The scheduler daemon is also responsible for processing the check result queue, analyzing the results, doing correlation and following up actions accordingly (if a service is down, ask for a host check). It does not launch checks or notifications. It just keeps a queue of pending checks and notifications for other daemons of the architecture (like pollers or reactionners). This permits distributing load equally across many pollers. There can be many schedulers for load-balancing or hot standby roles. Status persistence is achieved using a retention module.

      * Modules for status retention: pickle, nagios, memcache, redis and MongoDB are available.


    * **Poller**: The poller daemon launches check plugins as requested by schedulers. When the check is finished it returns the result to the schedulers. Pollers can be tagged for specialized checks (ex. Windows versus Unix, customer A versus customer B, DMZ) There can be many pollers for load-balancing or hot standby spare roles.

      * Module for data acquisition: :ref:`NRPE Module <packages/setup-nrpe-booster-module>`
      * Module for data acquisition: CommandFile (Used for check_mk integration which depends on the nagios.cmd named pipe )
      * Module for data acquisition: `SNMPbooster`_ (in development)


    * **Reactionner**: The reactionner daemon issues notifications and launches event_handlers. This centralizes communication channels with external systems in order to simplify SMTP authorizations or RSS feed sources (only one for all hosts/services). There can be many reactionners for load-balancing and spare roles
      * Module for external communications: AndroidSMS

    * **Broker**: The broker daemon exports and manages data from schedulers.  The management is done exclusively with modules. Multiple :ref:`Broker modules <the_broker_modules>` can be enabled simultaneously.

      * Module for centralizing Shinken logs: Simple-log (flat file)
      * Modules for data retention: Pickle , ToNdodb_Mysql, ToNdodb_Oracle, couchdb
      * Modules for exporting data: Graphite-Perfdata, NPCDMOD(PNP4Nagios) and Syslog
      * Modules for the Livestatus API - status retention and history:  SQLite (default), MongoDB (experimental)
      * Modules for the Shinken WebUI: Graphite-UI, PNP-UI. Trending and data visualization.
      * Modules for compatibility: Service-Perfdata, Host-Perfdata and Status-Dat


    * **Receiver** (optional): The receiver daemon receives passive check data and serves as a distributed passive command buffer that will be read by the arbiter daemon. There can be many receivers for load-balancing and hot standby spare roles. The receiver can also use modules to accept data from different protocols. Anyone serious about using passive check results should use a receiver to ensure that when the arbiter is not available (when updating a configuration) all check results are buffered by the receiver and forwarded when the arbiter is back on-line.

      * Module for passive data collection: :ref:`NSCA <nsca_daemon_module>`, :ref:`TSCA <tsca_daemon_module>`, :ref:`Ws_arbiter (web service) <ws_daemon_module>`

This architecture is fully flexible and scalable: the daemons that require more performance are the poller and the schedulers. The administrator can add as many as he wants. The broker daemon should be on a well provisioned server for larger installations, as only a single broker can be active at one time. A picture is worth a thousand words:


.. image:: /_static/images///official/images/shinken-architecture.png
   :scale: 90 %


.. _advanced/distributed#the_smart_and_automatic_load_balancing:

The smart and automatic load balancing
=======================================


  * :ref:`Creating independent packs <advanced/distributed#creating_independent_packs>`
  * :ref:`The packs aggregations into scheduler configurations <advanced/distributed#the_packs_aggregations_into_scheduler_configurations>`
  * :ref:`The configurations sending to satellites <advanced/distributed#the_configurations_sending_to_satellites>`

Shinken is able to cut the user configuration into parts and dispatch it to the schedulers. The load balancing is done automatically: the administrator does not need to remember which host is linked with another one to create packs, Shinken does it for him.

The dispatch is a host-based one: that means that all services of a host will be in the same scheduler as this host. The major advantage of Shinken is the ability to create independent configurations: an element of a configuration will not have to call an element of another pack. That means that the administrator does not need to know all relations among elements like parents, hostdependencies or service dependencies: Shinken is able to look at these relations and put these related elements into the same packs.

This action is done in two parts:

  * create independent packs of elements
  * paste packs to create N configurations for the N schedulers


.. _advanced/distributed#creating_independent_packs:

Creating independent packs
---------------------------


The cutting action is done by looking at two elements: hosts and services. Services are linked with their host so they will be in the same pack. Other relations are taken into account :

  * parent relationship for hosts (like a distant server and its router)
  * hostdependencies
  * servicesdependencies

Shinken looks at all these relations and creates a graph with it. A graph is a relation pack. This can be illustrated by the following picture :


.. image:: /_static/images///official/images/pack-creation.png
   :scale: 90 %


In this example, we will have two packs:

  * pack 1: Host-1 to host-5 and all their services
  * pack 2: Host-6 to Host-8 and all their services


.. _advanced/distributed#the_packs_aggregations_into_scheduler_configurations:

The packs aggregations into scheduler configurations
-----------------------------------------------------


When all relation packs are created, the Arbiter aggregates them into N configurations if the administrator has defined N active schedulers (no spares). Packs are aggregated into configurations (it's like "Big packs"). The dispatch looks at the weight property of schedulers: the higher weight a scheduler has, the more packs it will have. This can be shown in the following picture :


.. image:: /_static/images///official/images/pack-agregation.png
   :scale: 90 %


.. _advanced/distributed#the_configurations_sending_to_satellites:

The configurations sending to satellites
-----------------------------------------


When all configurations are created, the Arbiter sends them to the N active Schedulers. A Scheduler can start processing checks once it has received and loaded it's configuration without having to wait for all schedulers to be ready(v1.2). For larger configurations, having more than one Scheduler, even on a single server is highly recommended, as they will load their configurations(new or updated) faster. The Arbiter also creates configurations for satellites (pollers, reactionners and brokers) with links to Schedulers so they know where to get jobs to do. After sending the configurations, the Arbiter begins to watch for orders from the users and is responsible for monitoring the availability of the satellites.


.. _advanced/distributed#the_high_availability:

The high availability
======================


  * :ref:`When a node dies <advanced/distributed#when_a_node_dies>`

The shinken architecture is a high availability one. Before looking at how this works,let's take a look at how the load balancing works if it's now already done.


.. _advanced/distributed#when_a_node_dies:

When a node dies
-----------------


Nobody is perfect. A server can crash, an application too. That is why administrators have spares: they can take configurations of failing elements and reassign them. For the moment the only daemon that does not have a spare is the Arbiter, but this will be added in the future. The Arbiter regularly checks if everyone is available. If a scheduler or another satellite is dead, it sends its conf to a spare node, defined by the administrator. All satellites are informed by this change so they can get their jobs from the new element and do not try to reach the dead one. If a node was lost due to a network interruption and it comes back up, the Arbiter will notice and ask the old system to drop its configuration.
The availability parameters can be modified from the default settings when using larger configurations as the Schedulers or Brokers can become busy and delay their availability responses. The timers are aggressive by default for smaller installations. See daemon configuration parameters for more information on the three timers involved.
This can be explained by the following picture :


.. image:: /_static/images///official/images/pack-creation.png
   :scale: 90 %


External commands dispatching
==============================

The administrator needs to send orders to the schedulers (like a new status for passive checks). In the Shinken way of thinking, the users only need to send orders to one daemon that will then dispatch them to all others. In Nagios the administrator needs to know where the hosts or services are to send the order to the right node. In Shinken the administrator just sends the order to the Arbiter, that's all. External commands can be divided into two types :

  * commands that are global to all schedulers
  * commands that are specific to one element (host/service).

For each command, Shinken knows if it is global or not. If global, it just sends orders to all schedulers. For specific ones instead it searches which scheduler manages the element referred by the command (host/service) and sends the order to this scheduler. When the order is received by schedulers they just need to apply them.


.. _advanced/distributed#poller_tag:

Different types of Pollers: poller_tag
=======================================


  * :ref:`Use cases <advanced/distributed#use_cases>`

The current Shinken architecture is useful for someone that uses the same type of poller for checks. But it can be useful to have different types of pollers, like GNU/Linux ones and Windows ones. We already saw that all pollers talk to all schedulers. In fact, pollers can be "tagged" so that they will execute only some checks.

This is useful when the user needs to have hosts in the same scheduler (like with dependencies) but needs some hosts or services to be checked by specific pollers (see usage cases below).

These checks can in fact be tagged on 3 levels :

  * Host
  * Service
  * Command

The parameter to tag a command, host or service, is "poller_tag". If a check uses a "tagged" or "untagged" command in a untagged host/service, it takes the poller_tag of this host/service. In a "untagged" host/service, it's the command tag that is taken into account.

The pollers can be tagged with multiple poller_tags. If they are tagged, they will only take checks that are tagged, not the untagged ones, unless they defined the tag "None".


.. _advanced/distributed#use_cases:

Use cases
----------


This capability is useful in two cases:

  * GNU/Linux and Windows pollers
  * DMZ

In the first case, it can be useful to have a windows box in a domain with a poller daemon running under a domain account. If this poller launches WMI queries, the user can have an easy Windows monitoring.

The second case is a classic one: when you have a DMZ network, you need to have a dedicated poller that is in the DMZ, and return results to a scheduler in LAN. With this, you can still have dependencies between DMZ hosts and LAN hosts, and still be sure that checks are done in a DMZ-only poller.


Different types of Reactionners: reactionner_tag
=================================================

  * :ref:`Use cases <advanced/distributed#use_cases>`

Like for the pollers, reactionners can also have 'tags'. So you can tag your host/service or commands with
"reactionner_tag". If a notification or an event handler uses a "tagged" or "untagged" command in a untagged host/service, it takes the reactionner_tag of this host/service. In a "untaged" host/service, it's the command tag that is taken into account.

The reactionners can be tagged with multiple reactionner_tags. If they are tagged, they will only take checks that are tagged, not the untagged ones, unless they defined the tag "None".

Like for the poller case, it's mainly useful for DMZ/LAN or GNU/Linux/Windows cases.


.. _advanced/distributed#realms:

Advanced architectures: Realms
===============================


  * :ref:`Realms in few words <advanced/distributed#realms_in_few_words>`
  * :ref:`Realms are not poller_tags! <advanced/distributed#realms_are_not_poller_tags>`
  * :ref:`Sub realms <advanced/distributed#sub_realms>`
  * :ref:`Example of realm usage <advanced/distributed#example_of_realm_usage>`

Shinken's architecture allows the administrator to have a unique point of administration with numerous schedulers, pollers, reactionners and brokers. Hosts are dispatched with their own services to schedulers and the satellites (pollers/reactionners/brokers) get jobs from them. Everyone is happy.

Or almost everyone. Think about an administrator who has a distributed architecture around the world. With the current Shinken architecture the administrator can put a couple scheduler/poller daemons in Europe and another set in Asia, but he cannot "tag" hosts in Asia to be checked by the asian scheduler . Also trying to check an asian server with an european scheduler can be very sub-optimal, read very sloooow. The hosts are dispatched to all schedulers and satellites so the administrator cannot be sure that asian hosts will be checked by the asian monitoring servers.

In the normal Shinken Architecture is useful for load balancing with high availability, for single site.

Shinken provides a way to manage different geographic or organizational sites.

We will use a generic term for this site management, **Realms**.


.. _advanced/distributed#realms_in_few_words:

Realms in few words
--------------------


A realm is a pool of resources (scheduler, poller, reactionner and broker) that hosts or hostgroups can be attached to. A host or hostgroup can be attached to only one realm. All "dependancies" or parents of this hosts must be in the same realm. A realm can be tagged "default"' and realm untagged hosts will be put into it. In a realm, pollers, reactionners and brokers will only get jobs from schedulers of the same realm.


.. _advanced/distributed#realms_are_not_poller_tags:

Realms are not poller_tags!
----------------------------


Make sure to undestand when to use realms and when to use poller_tags.

  * **realms are used to segregate schedulers**
  * **poller_tags are used to segregate pollers**

For some cases poller_tag functionality could also be done using Realms. The question you need to ask yourself: Is a poller_tag "enough", or do you need to fully segregate a the scheduler level and use Realms. In realms, schedulers do not communicate with schedulers from other Realms.

If you just need a poller in a DMZ network, use poller_tag.

If you need a scheduler/poller in a customer LAN, use realms.


.. _advanced/distributed#sub_realms:

Sub realms
-----------


A realm can contain another realm. It does not change anything for schedulers: they are only responsible for hosts of their realm not the ones of the sub realms. The realm tree is useful for satellites like reactionners or brokers: they can get jobs from the schedulers of their realm, but also from schedulers of sub realms. Pollers can also get jobs from sub realms, but it's less useful so it's disabled by default. Warning: having more than one broker in a scheduler is not a good idea. The jobs for brokers can be taken by only one broker. For the Arbiter it does not change a thing: there is still only one Arbiter and one configuration whatever realms you have.


.. _advanced/distributed#example_of_realm_usage:

Example of realm usage
-----------------------


Let's take a look at two distributed environnements. In the first case the administrator wants totally distinct daemons. In the second one he just wants the schedulers/pollers to be distincts, but still have one place to send notifications (reactionners) and one place for database export (broker).

Distincts realms :


.. image:: /_static/images///official/images/shinken-architecture-isolated-realms.png
   :scale: 90 %


More common usage, the global realm with reactionner/broker, and sub realms with schedulers/pollers :


.. image:: /_static/images///official/images/shinken-architecture-global-realm.png
   :scale: 90 %


Satellites can be used for their realm or sub realms too. It's just a parameter in the configuration of the element.


.. _SNMPbooster: https://github.com/titilambert/shinken/blob/snmp_booster/shinken/modules/snmp_poller.py

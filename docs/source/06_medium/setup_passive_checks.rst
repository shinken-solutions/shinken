.. _setup_passive_checks:



Passive data acquisition 
=========================



Overview 
---------




Definition 
~~~~~~~~~~~


Passive check results are received from external source in an unsolicited manner.



Data routing of Passive check results 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


Passive check results are received by the  Arbiter daemon or the Receiver daemon. Modules loaded on either of the daemons permit receiving various types of data formats.
The Arbiter is the only one who knows which Scheduler is responsible for the data received. The Arbiter is tasked with administrative blocking functions that can inhibit the responsiveness of the acquisition from a Receiver. This is not an issue for small Shinken installations, as the Arbiter daemon will be blocked for very very short periods of time. In large Shinken installations with tens of thousands of services the Arbiter may induce delays related to passive check result routing.

Shinken 1.2 Shinken uses a direct routing method from the Receiver daemon directly to the appropriate Scheduler for check results and to the Arbiter daemon for external commands.

In all cases, should the Arbiter or Scheduler process be busy doing another task data from the Receiver will **NOT** be lost. It will be queued in the Receiver until the remote daemon can process them.



Configuration Reference 
~~~~~~~~~~~~~~~~~~~~~~~~


:ref:`The basics of enabling passive check results in the Shinken configuration <thebasics-passivechecks>`

:ref:`State handling for passive check results <advancedtopics-passivestatetranslation>`



Passive acquisition protocols 
------------------------------




NSCA protocol 
~~~~~~~~~~~~~~


The NSCA addon consists of a daemon that runs on the Shinken host and a client that is executed from remote hosts. The daemon will listen for connections from remote clients, performs basic validation on the results being submitted, and then write the check results directly into the external command named pipe file (as described in the basics of passive check results configuration) of the Arbiter process or the Receiver process when scaling passive result processing.

The only consideration here is to make sure to configure Shinken Receiver daemons. These will receive the NSCA messages and queue them to be sent to the Arbiter or Scheduler for processing.
Benefit from the most common denominator, C compiled cross platform executable, UDP transport, single line output, raw text transmission.

:ref:`Learn how to configure the NSCA module <nsca_daemon_module>`.



TSCA protocol 
~~~~~~~~~~~~~~


Using :ref:`TSCA <tsca_daemon_module>`, you can directly embed in your programs check result submission using a variety of programming languages. Languages such as, but not limited to, Perl, Java and Ruby.
Benefit from direct access to Shinken, TCP transport, multi line output and high performance binary transmission.

:ref:`Learn how to configure the TSCA module <tsca_daemon_module>`.



Shinken WebService protocol 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~


Shinken has its own Python web service module to receive passive data via HTTP(s) using the bottle.py Python module. The Web Service is considered experimental, but is being used in production environments. The `WS module `_ is very simple and can be extended or improved easily. It is Python after all.

Benefit from direct access to Shinken, HTTP protocol, TCP transport, firewall friendly, multi line output and high performance binary transmission.

:ref:`Learn how to configure the Shinken WebService <ws_daemon_module>`.



NSCAweb protocol 
~~~~~~~~~~~~~~~~~


A much more evolved protocol for sending data than NSCA. Use curl from the command line to send your data, or submit check results using an HTTP post in your software.

The python NSCAweb listener, http://github.com/smetj/nscaweb, can be hacked to act as a Shinken Receiver module. It might also be possible to wrestle the current Web Service receiver module to process NSCAweb sent messages, the format is the same. 
.. important::  Should someone be interested in implementing an NSCAweb Shinken Receiver module, support will be provided.



SNMP Traps 
~~~~~~~~~~~


Net-SNMP's snmptrapd and SNMP trap translator are typically used to receive, process, and trigger an alerts. Once an alert has been identified an execution is launched of send_nsca, or other method to send result data to a Shinken Receiver daemon. There is no actual Shinken receiver module to receive SNMP traps, but the point is to get the data sent to the Shinken Receiver daemon.

:ref:`Learn more about SNMP trap handling. <integrationwithothersoftware-int-snmptrap>`

The snmptt documentation has a good writeup on integrating with Nagios, which also applies to Shinken.

There is also a new project by the Check MK team to build an Event console that will process Traps and Syslog messages to create Nagios/Shinken passive check results. It is experimental at this time.



OPC protocol 
~~~~~~~~~~~~~


Various open source and commercial SDKs are available to implement a Shinken Receiver module for getting date from OPC-DA or OPC-UA servers. There is a planned implementations of this module in 2013 for OPC-DA v2 and OPC-UA, but should someone be interested in implementing one, support will be provided.



AMQP protocol 
~~~~~~~~~~~~~~


Adding a Shinken Receiver module to act as a consumer of AMQP messages can be implemented without much fuss. There are no planned implementations of this module, but should someone be interested in implementing one, support will be provided. A new broker module for the Canopsis Hypervisor acts as an AMQP endpoint, so this can be used to develop an AMQP consumer or provider. There is also a Python MQ implementation called Krolyk by Jelle Smet that submits check results from AMQP to the Shinken command pipe.

.. _snmpbooster_how_it_works:



Shinken integrated SNMP Module 
===============================





Overview 
---------

  * Jump back to :ref:`SnmpBooster documentation index <setup_active_module_checks>`
.. tip::  The module is now in public beta as of 2012-10-26! Have Fun!
   
   Nothing new to add, more to come in 2013. 2013-01-19.
   



What is it 
~~~~~~~~~~~


The SnmpBooster module allows Shinken Pollers to directly manage SNMP data acquisition. This is an all Python cross-platform SNMP module. It is tightly integrated with the Shinken Poller, Scheduler and Arbiter daemons to provide the best possible user experience.



Why use it 
~~~~~~~~~~~


The SnmpBooster module is designed to be very efficient and scalable. It has a very flexible configuration method to make it easy to use with Shinken Monitoring Packs and Shinken discovery runners like genDevConfig.

This acquisition module was professionally designed and developed.

It is meant to be used by the very capable discovery engine genDevConfig (**v3.0.5 and newer**)  originally developed for the Cricket SNMP monitoring tool and converted for use with Shinken.

It is one of the very few serious SNMP v2c implementation making use of SnmpGetBulk type requests.



How does it work 
-----------------




Shinken Integration 
~~~~~~~~~~~~~~~~~~~~




.. image:: /_static/images/snmpbooster_data_model.png
   :scale: 90 %



1. The SnmpBooster Arbiter module reads the Shinken SnmpBooster configuration file(s). It reads the check commands and based on the values in the check commands that use the snmp_poller module it will creates a shared configuration cache using memcached/memcachedb. The memcache key is always the combination of the hostname. This permits to tie together Shinken Hosts and Services with the SNMP specific configuration. (MongoDB and Redis are planned to be supported in the future) The Scheduler daemon schedules Host and Service checks as it normally does. 

**3. The SnmpBooster module will check that a memcache host key exists for the check to be launched. Then the SnmpBooster poller module will query all services related to a host for a given acquisition frequency in one pass**. (all checks done every 2 minutes will be executed in bulk, same for those every 5 minutes)

**5. Check results are cached for the acquisition check_interval.** The next time a check request for data from the same host is received from the Scheduler, the data will be fetched from memcache. Resulting is extremely low check latency.

**2. 6. The SNMP checks still benefit from retries, timeouts, forced checks, dependencies and the powerful Scheduler daemon logic.** 

6. The Scheduler daemon can still force an immediate re-check by flushing the cache. This is required for the dependency model.



Performance 
~~~~~~~~~~~~

SnmpBooster uses SNMP v2c getbulk for high efficiency, unless forced to use SNMP v2c get-next or SNMPv1 get-next. GetBulk uses a single request PDU to ask for multiple OIDs or even entire tables, instead of sending one request PDU per OID. 

For example: *A typical 24 port network switch with two uplinks might use 375 OIDS (8 OIDs per interface, plus general OIDs for chassis health, memory, cpu, fans, etc.). **SnmpBooster will only require around 4 request PDUs instead of 375 request PDUs**. Each PDU is a request packet which takes time to create, send get processed and return. More timeouts to manage, more connections, more impact on the remote device and more latency means much fewer checks per second.*

The SnmpBooster module supports automatic instance mapping for OIDs. (Ex. Based on the interface name it will figure out that the SNMP index(or instance) is 136. This is automatically handled by genDevConfig and SnmpBooster, no user input required. :-)

The generic SNMP configuration information is stored in the Shinken SnmpBooster INI files. There is a Defaults_unified.ini and a series of other Defaults files, one per discovery plugin for genDevConfig.

.. important::  genDevConfig plugins have all been converted to use the new dynamic instance mapping methods. You are now free to use most if not all Defaults*.ini files included with genDevConfig. 2012-10-28




Limitations 
------------


You should have memcached instances running on each poller responsible for snmp polling.
You should have your pollers with SnmpBooster in the same datacenter, as they need to be on the same machine with good connectivity to the active memcached instance.
SnmpBooster is not compatible with distributed pollers in multiple datacenters, sorry, the current design of SnmpBooster uses a single centralized memcached instance for storing the timeseries data. For distributed datacenters to be supported, each poller+scheduler+memcached must be realm restrained, which is not the case today.




Design specification 
---------------------


:ref:`SnmpBooster design specification <snmpbooster_design_specification>` and current development status.



Data model 
-----------


The information required to define the data is split in two locations. 

The first location is the host and service Shinken configuration (You need to generate or write this)

  * Device specific information

    * IP addresses, host_names, device types, instance keys
    * A DSTEMPLATE must be referred to in the Service definition
    * A static SNMP instance could be referred to in the Service definition
    * An SNMP instance MAP function could be referred to in the Service definition
    * A TRIGGERGROUP could be refered to in the Service definition

The second location is SNMP Defaults.* templates. (Here you can create new devices or add new data sources)

  * DATASOURCE information

    * SNMP OID
    * Type of data and how can it be interpreted (GAUGE, COUNTER, COUNTER64, DERIVE, DERIVE64, TEXT, TIMETICK)
    * Data format preparation (Scaling the data for example bits to bytes)
    * Is there an instance to append to the

  * Instance MAP function
    * Mapping the instance dynamically using a function
    * Data or rules related to the mapping function

  * DSTEMPLATEs to associate DATASOURCE to actual device classes
    * List of DATASOURCES associated with a, for example, Cisco 1900 router. Which in turn can be applied to a Shinken service

  * TRIGGER and TRIGGERGROUPS to apply thresholding rules
    * Define triggers and associate them with a TRIGGERGROUP name that can be applied to a Shinken Service


A final location containes rules to build your Shinken configuration.
  * genDevConfig plugins create Shinken configurations


Installation and configuration 
-------------------------------


:ref:`SnmpBooster installation <setup_snmp_booster_module>`



Reference Dictionnary 
----------------------


:ref:`SnmpBooster reference dictionary <snmpbooster_dictionary>`



Troubleshooting 
----------------


:ref:`SnmpBooster troubleshooting <snmpbooster_troubleshooting>`



Graph templates 
----------------


These are .graph files defined in your Shinken configuration directory. Refer to the Shinken graphite templates(Not yet created) or PNP4Nagios how-to documentation. The graph templates are independent from SnmpBooster and provide templates for any collected data from Shinken.


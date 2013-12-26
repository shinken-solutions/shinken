.. _scaling_shinken:



======================================
Scaling Shinken for large deployments 
======================================




Planning your deployment  
--------------------------


A monitoring system needs to meet the expected requirements. The first thing you, as the system/network administrator need to do, is get management buy-in on deploying a supervisory and data acquisition system to meet corporate goals. The second is to define the scope of the monitoring system and its particularities.

  * Number of services to supervise
  * Service check frequency 
  * Method of supervising the services Passive versus Active
  * Protocol used for data acquisition (ping, SSH, NSCA, TSCA, SNMP, NRPE, NSCAweb, collectd, scripts, etc)
  * Retention duration for performance data
  * Retention duration for status data
  * For each status or performance data determine if it meets the scope and goals of the project.
  * Can you live with interpolated data (RRD) or do you require exact representation of data (Graphite)
  * Do you need to store performance data out of sequence (Graphite) or not (RRD)
  * Do you need Active-Active HA for performance data (Graphite)
  * Do you want to make use of Shinken's store and forward inter-process communications architecture to not lose performance data (Graphite) or not (RRD)



How scalable is Shinken 
~~~~~~~~~~~~~~~~~~~~~~~~


Shinken can scale out horizontally on multiple servers or vertically with more powerful hardware. Shinken deals automatically with distributed status retention. There is also no need to use external clustering or HA solutions.

Scalability can be described through a few key metrics

  * Number of hosts + services supervised
  * Number of active checks per second (type of active check having a major impact!)
  * Number of check results per second (hosts and services combined)

And to a lesser extent, as performance data is not expected to overload a Graphite server instance (Which a single server can do up to 80K updates per second with millions of metrics) or even RRDTool+RRDcache with a hardware RAID 10 of 10K RPM disks.

  * Number of performance data points (if using an external time-series database to store performance data)




Passive versus Active 
~~~~~~~~~~~~~~~~~~~~~~


Passive checks do not need to be scheduled by the monitoring server. Data acquisition and processing is distributed to the monitored hosts permitting lower acquisition intervals and more data points to be collected.

Active checks benefit from Shinken's powerful availability algorithms for fault isolation and false positive elimination. 

A typical installation should make use of both types of checks.



Scaling the data acquisition 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


Thought needs to be used in determining what protocol to use and how many data points need to be collected will influence the acquisition method. There are many ways to slice an apple, but only a few scale beyond a few thousand services.

What is a big deployment? It depends on check frequency, number of services and check execution latency. 10K per minute NSCA based passive services is nothing for Shinken. 10K SSH checks per minute is unrealistic. 10K SNMP checks per minute can grind a server to a halt if not using an efficient polling method. Large deployments could easily ask for 20K, 50K, 80K services per minute.

Large numbers of active checks need to use poller modules
  * nrpe_booster
  * snmp_booster

Other integrated poller modules can be easily developed as required for ICMP(ping), SSH, TCP probes, etc.

Check_mk also uses a daemonized poller for its Windows and Unix agents which also makes it a good choice for scaling  data acquisition from hosts. Note that WATO, the configuration front-end is not compatible with Shinken at this time. Check_mk is also limited to RRD backends.



Scaling the broker 
~~~~~~~~~~~~~~~~~~~


The broker is a key component of the scalable architecture. Only a single broker can be active per scheduler. A broker can process broks (messages) from multiple schedulers. In most modern deployments, Livestatus is the broker module that provides status information to the web frontends. (Nagvis, Multisite, Thruk, etc.) or Shinken's own WebUI module. The broker needs memory and processing power.

Avoid using any broker modules that write logs or performance data to disk as an intermediate step prior to submission to the time series database.
Use the Graphite broker module which will directly submit data to load-shared and/or redundant Graphite instances. `Graphite`_ is a time-series storage and retrieval database.

Make use of sqlite3 or mongodb to store Livestatus retention data. MongoDB integration with Livestatus is considered somewhat experimental, but can be very beneficial if performance and resiliency are desired. Especially when using a spare broker. MongoDB will ensure historical retention data is available to the spare broker, whereas with SQLite, it will not, and manual syncing is required.

.. important::  Code optimizations, a new JSON encoder/decoder, indexing and other means of decreasing access time to the in-memory data have been implemented in Shinken 1.2. These enhancements have improved markedly response time for small to extra large Livestatus instances.



Web Interface 
~~~~~~~~~~~~~~


MK Multisite and Nagvis are the only viable choices for very large installations. They can use multiple Nagios and Shinken monitoring servers as data providers and are based on the Livestatus API. Livestatus is a networked API for efficient remote access to Shinken run time data.



Dependancy model 
~~~~~~~~~~~~~~~~~


Shinken has a great dependency resolution model. Automatic root cause isolation, at a host level, is one method that Shinken provides. This is based on explicitly defined parent/child relationships. This means that on a service or host failure, it will automatically reschedule an immediate check of the parent(s). Once the root failure(s) are found, any children will be marked as unknown status instead of soft down.

This model is very useful in reducing false positives. What needs to be understood is that it depends on defining a dependency **tree**. A dependency tree is restricted to single scheduler. Shinken provides a distributed architecture, that needs at least two trees for it to make sense.

Splitting trees by a logical grouping makes sense. This could be groups of services, geographic location, network hierarchy or other. Some elements may need to be duplicated at a host level (ex. ping check) like common critical elements (core routers, datacenter routers, AD, DNS, DHCP, NTP, etc.). A typical tree will involve clients, servers, network paths and dependent services. Make a plan, see if it works. If you need help designing your architecture, a professional services offering is in the works by the Shinken principals and their consulting partners.



Scaling the acquisition daemons 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


Typically pollers and Schedulers use up the most network, CPU and memory resources. Use the distributed architecture to scale horizontally on multiple commodity servers. Use at least a pair of Scheduler daemons on each server. Your dependency model should permit at least two trees, preferably 4.



Active acquisition methods 
---------------------------




Scaling SNMP acquisition 
~~~~~~~~~~~~~~~~~~~~~~~~~


Typically for networking devices, SNMP v2c is the most efficient method of data acquisition. Security considerations should be taken into account on the device accepting snmpv2c requests so that they are filtered to specific hosts and restricted to the required OIDs, this is device specific. Snmpv2c does not encrypt or protect the data or the passwords.

There is a myriad of SNMP monitoring scripts, most are utter garbage for scalable installations. This is simply due to the fact that every time they are launched a perl or python interpreter needs to be launched, modules need to be imported, the script executed, results get returned and then the script is cleared from memory. Rinse and repeat, very inefficient. Only two SNMP polling modules can meet high scalability requirements.

Shinken's integrated SNMP poller can scale to thousands of SNMP checks per second.

Check_mk also has a good SNMP acquisition model.



Scaling NRPE acquisition  
~~~~~~~~~~~~~~~~~~~~~~~~~~


Shinken provides an integrated NRPE check launcher. It is implemented in the poller as a module that allows to bypass the launch of the check_nrpe process. It reads the check command and opens the connection itself. It allows a big performance boost for launching check_nrpe calls.

The command definitions should be identical to the check_nrpe calls.



Passive acquisition methods 
----------------------------




Scaling metric acquisition 
~~~~~~~~~~~~~~~~~~~~~~~~~~~


Metrics or performance data (in Nagios speak) are embedded with check results. A check result can have zero or more performance metrics associated with it.
Theses are transparently passed off to systems outside of Shinken using a Broker module. The Graphite broker module can easily send more than 2000 metrics per second. We have not tested the upper limit. Graphite itself can be configured to reach upper bounds of 80K metrics per second.

If a metric does not need its own service, it should be combined with a similar natured check being run on the server. Services are the expensive commodity, as they have all the intelligence like to them such as timeouts, retries, dependencies, etc. With Shinken 1.2 and fast servers, you should not exceed **60K services**  for optimum performance.

Recommended protocols for scalable passive acquisition

  - TSCA (Used under Z/OS and embedded in applications)
  - Ws_Arbiter (Used by GLPI)
  - NSCA (generic collection)
  - Collectd (metrics only, states are calculated from metrics by the Shinen Scheduler using Shinken Python Triggers)




Log management methods 
-----------------------


System and application logs should be gathered from servers and network devices. For this a centralized logging and analysis system is required.

Suggested centralized logging systems: OSSEC+Splunk for OSSEC, loglogic, MK Multisite log manager

Suggested windows agents: 
  * OSSEC agent
  * Splunk universal forwarder

Suggested linux agent: 
  * OSSEC agent
  * Splunk universal forwarder

Suggested Solaris agent:
  * OSSEC agent
  * Splunk universal forwarder

Splunk can aggregate the data, drop worthless data (unless mandated to log everything due to regulatory compliance), aggregate, analyze and alert back into Shinken. Log reporting and dashboards are a million times better in Splunk than anything else. If regulatory compliance causes too much data to be logged, look into using Kibana+logstash instead of Splunk, because Splunk costs a wicked lot per year.



SLA reporting methods 
----------------------


Feed Shinken event data back into Splunk, Thruk, Canopsis to get SLA reports.
Use MK Multisites Livestatus based reporting.



Practical optimization tips 
----------------------------



:ref:`Chapter 59. Tuning Shinken For Maximum Performance <securityandperformancetuning-tuning>`

:ref:`Internal Shinken metrics to monitor <internal_metrics>`

.. _Graphite: http://graphite.readthedocs.org/en/0.9.10/index.html

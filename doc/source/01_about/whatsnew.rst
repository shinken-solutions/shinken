.. _about/whatsnew:

===============================================
 Feature comparison between Shinken and Nagios 
===============================================

Shinken is not just a fork of Nagios. It has been rewritten completely as a modern distributed application while maintaining compatibility with the Nagios configuration, LiveStatus API and check plugins.

The major differences are listed below :

.. TODO: Update this OLD table

================================================================== ========= ======= ================== ===============================================================================================================================================================================================================================================
Feature                                                            Nagios    Shinken In Shinken roadmap Notes
Host/Service monitoring with HARD/SOFT status management           Yes       Yes     NA
Active monitoring with plugins                                     Yes       Yes     NA
Passive monitoring                                                 Yes       Yes     NA
Compatible with RRDtool based data graphing addons                 Yes       Yes     NA                 Shinken also supports  forwarding performance data to Graphite and has native Graphite template based graphs in the WebUI.
Network host hierarchy                                             Yes       Yes     NA
Hosts and services dependencies                                    Yes       Yes     NA
Proactive problem resolution                                       Yes       Yes     NA
User-defined notifications                                         Yes       Yes     NA
Notifications escalation                                           Yes       Yes     NA
Syslog logging                                                     Yes       Yes     NA
Flap detection                                                     Yes       Yes     NA
Obessive compulsive commands                                       Yes       Yes     NA                 It’s not useful in the Shinken architecture but it makes the switch to Shinken easier.
State freshness check                                              Yes       Yes     NA
Event broker modules: Livestatus API, ndo, pnp, sqlite etc..       Yes       Yes     NA                 Shinken includes a host of native Python modules to make it easy to extend and support. Other supported integration modules : Graphite time-series database, GLPI, MongoDB, memcached, redis and more.
Load modules for any daemon. (Poller, Scheduler, Receiver, etc.)   No        Yes     NA                 Modules can be loaded for any daemon. This makes supporting, extending and scaling Shinken very easy.
Graphite integration in the WebUI                                  No        Yes     NA                 Graphite is a next-generation time-series database and visualisation web application/API. It stores non interpolated data in a distributed and scalable manner. The current standard RRD interpolates all data limiting its applicability.
Notifications escalation is  not a pain in the ass to configure    No        Yes     NA                 You can call an escalation from any host or service. That’s way easier to use!
Distributed monitoring                                             Hard      Yes     NA                 Nagios can do DNX, but it’s not as easy to manage than Shinken architecture, and not as efficient.You think “easy as in cloud”?That’s Shinken.
High availability                                                  Hard      Yes     NA                 With Nagios, high availability implies a huge performance hit.
Distributed AND high availability                                  Hard      Yes     NA                 With Nagios, high availability implies a huge performance hit, and it is harder to get working and to maintain.
Integrated business rules                                          Hard      Yes     NA                 With Nagios it’s an addon, so it’s not easily manageable in a distributed configuration.
Problem/impacts                                                    Hard      Yes     NA                 With Nagios it is only available in the notification part, but with Shinken it’s also available in the real time monitoring views!
Easy DMZ monitoring                                                No        Yes     NA                 Shinken has poller_tag that allow the user to put a poller in a DMZ and do all DMZhosts/services with it. It make less Firewall holes.
UTF-8 support                                                      No        Yes     NA                 Thank you Python. Now %µ~@^-nöel is supported as a host name.
Good performatnces.                                                No        Yes     NA                 Need performance and scalability ? Try that with Nagios…
Runs on Windows                                                    No        Yes     NA                 Thank you Python again. Flexible monitoring : direct WMI or Powershell queries!
Configure flap history                                             No        Yes     NA                 Nagios handles flapping for the 20 latest states only. It’s hard-coded. In Shinken it’s a configuration option.
Impact management                                                  No        Yes     NA                 For Nagios it’s as important when an incident impacts a qualification application or a production one. Shinken computes dynamically the business impact of the root problem based on criticality!
Modern language and program design                                 No        Yes     NA                 Python is a forward looking and easy to program language. Shinken was developed using a TDD approach and makes use of modules with all the daemons to make it easy to extend and stability oriented.
Modern Web Interface built on twitter bootstart and jquery.        No        Yes     NA                 Shinken 1.2 introduces a rebuilt WebUI interface which exposes the unique features of the underlying monitoring system.
MongoDB distributed DB                                             No        Yes     NA                 Shinken 1.0 introduces mongoDB support for Livestatus and as the configuration database for the skonf preview.
Configuration pre-cache support                                    Yes       No      No                 Pre-cache was useful for host circular relation check. I corrected it in Nagios and in Shinken as well. Pre-cache is no longer a required feature.
Limit external command slots                                       Yes       No      No                 Shinken does not need to limit the number of external command in queue.
Advanced retain options                                            Yes       No      No                 No one uses this.
Inter check sleep time                                             Yes       No      No                 This is a historical Nagios option. Shinken has a real scheduler.
Configure reaper time                                              Yes       No      No                 Reaping? That is one reason which makes Nagios so slow. Shinken does everything in memory.
Auto rescheduling option                                           Hard      No      Yes                In Nagios, it’s still experimental and not documented. This feature is in the roadmap. It can be useful to “smooth” the scheduling load.
Embedded Perl                                                      Yes       Hard    NA                 Shinken is in Python. Perl checks can be loaded using persistent perl, which is a near equivalent to embedded perl, it requires changing the first line of each check. So you do this for the most used perl scripts.
Embedded Python                                                    No        Yes     NA                 Shinken is in Python. Checks can be executed as poller or receiver modules for maximum scalability.
Regular expression matching                                        Yes       No      No                 We believe this is a dangerous feature for the configuration and that most administrators avoid using it.
Binary Event broker compatibility                                  Yes       No      No                 Shinken does not load binary modules like the ndomod.o file. It has its own loadable modules written in python : ndo,  pnp, graphite, mongodb, sqlite, Livestatus API, NSCA, NRPE, TSCA, syslog, merlin and others
================================================================== ========= ======= ================== ===============================================================================================================================================================================================================================================


Change Log 
===========

The **Changelog** file is included in the source root directory of the source code distribution.

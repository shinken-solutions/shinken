.. _about:




==============
About Shinken 
==============



What Is It? 
============


Shinken is a system and network monitoring application. It supervises hosts and services from an IT and business point of view. Alerting or taking action on failures and recovery.

Shinken is a monitoring tool compatible with `Nagios`_ configuration, plugins and interfaces. It is written in `Python`_, so it should work under all Python supported platforms.

Some of the many features of Shinken include:

  * Web 2.0 Interface named WebUI that has innovative methods to visualize the state of your systems
  * Web 2.0 Interface named SkonfUI, that links discovery and configuration management
  * Livestatus networked API to provide realtime access to performance, status and configuration data
    * Interchangeable console or mobile interfaces
  * Providing operational or business insight
    * Ability to map business processes to Hosts and services
    * Ability to associate a business impact metrics to any warning or outages of hosts and services used to deliver a business process
    * Ability to define network host hierarchy using "parent" hosts, allowing detection of and distinction between hosts that are down and those that are unreachable
  * Monitoring Hosts and Services
    * Simple plugin design that allows users to easily develop their own service checks
    * Monitoring of network services ("SMTP", "POP3", "HTTP", "NTP", PING, etc.)
    * Monitoring of host resources (processor load, disk usage, etc.)
    * Hundreds of Nagios check scripts to choose from
    * High performance plugin modules integrated in the distributed daemons to easily extend the scope of the software
    * Parallelized service and host checks
    * Designed for highly available and load balanced monitoring
    * Acquire performance data from collectd via its network interface
  * Define Triggers in the Shinken core to calculate new performance metrics or states based on performance or state data 
  * Contact notifications when service or host problems occur and get resolved (via email, SMS, pager, or user-defined method)
  * Ability to define event handlers to be run during service or host events for proactive problem resolution
  * Integrates with PNP4Nagios and Graphite time-series databases for storing data, querying or displaying data.
  * Supports distributed retention modules, caches and databases to meet persistence and performance expectations




System Requirements 
====================


The :ref:`requirement for running Shinken <shinken_installation_requirements>` are the Python interpreter and a very short list of Python modules. You will also want to have TCP/IP configured, as the typical installation will download packages to install from the Internet and most service checks will be performed over the network.



Legacy Requirements 
====================


You are not required to use the original Nagios user interface CGIs included with Shinken. However, if you do decide to use them for migration purposes, you will need to have the following software installed...

  - A web server (preferrably `Apache`_)
  - Thomas Boutell's `gd library`_ version 1.6.3 or higher.



Licensing 
==========


Shinken is licensed under the terms of the `GNU Affero General Public License`_ as published by the `Free Software Foundation`_. This gives you legal permission to copy, distribute and/or modify Shinken under certain conditions. Read the 'LICENSE' file in the Shinken distribution or read the `online version of the license`_ for more details.

Shinken is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE WARRANTY OF DESIGN, MERCHANTABILITY, AND FITNESS FOR A PARTICULAR PURPOSE.

The Shinken documentation is based on Nagios so is licensed under the terms of the `GNU General Public License`_ Version 2 as published by the `Free Software Foundation`_. This gives you legal permission to copy, distribute and/or modify Shinken under certain conditions. Read the 'LICENSE' file in the Shinken distribution or read the `online version of the license`_ for more details.

Shinken is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE WARRANTY OF DESIGN, MERCHANTABILITY, AND FITNESS FOR A PARTICULAR PURPOSE.



Acknowledgements 
=================


A long list of people have contributed to Shinken. The THANKS file included as part of Shinken and the project page at http://www.shinken-monitoring.org provide more details.



Downloading The Latest Version 
===============================


You can check for new versions of Shinken at http://www.shinken-monitoring.org.


.. _Free Software Foundation: http://www.fsf.org/
.. _online version of the license: http://www.gnu.org/copyleft/gpl
.. _GNU Affero General Public License: http://www.gnu.org/licenses/agpl.txt
.. _Python: http://www.python.org/
.. _Nagios: http://www.nagios.org
.. _GNU General Public License: http://www.gnu.org/copyleft/gpl
.. _gd library: http://www.boutell.com/gd/
.. _Apache: http://www.apache.org/
.. _monitoring_a_linux:



Monitoring Linux Devices
========================


This document describes how you can monitor "private" services and attributes of GNU/Linux devices, such as:
  * Memory usage
  * CPU load
  * Disk usage
  * Running processes
  * etc.


Available Methods 
------------------


Several methods to monitor GNU/Linux devices are available:
  * **:ref:`SNMP <monitoring_a_linux_via_snmp>`** -- Install or activate the linux SNMP agent and configure it to serve system statistics;
  * **:ref:`Local Agent <monitoring_a_linux_via_local_agent>`** -- Provides faster query interval, more flexibility, passive and active communication methods;
  * **SSH** -- Should only be executed for infrequent checks as these have a high impact on the client and server CPU. It's also very slow to execute overall, and will not scale when polling thousands of devices;
  * **:ref:`Monitoring Publicly Available Services <monitoring_a_network_service>`** -- Public services provided by GNU/Linux devices (like HTTP, FTP, POP3, etc.) can be easily monitored.


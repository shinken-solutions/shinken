.. _integrationwithothersoftware-int-snmptrap:




=======================
 SNMP Trap Integration 
=======================



Introduction 
=============


Nagios is not designed to be a replacement for a full-blown "SNMP" management application like HP OpenView or `OpenNMS`_. However, you can set things up so that "SNMP" traps received by a host on your network can generate alerts in Nagios. Specific traps or groups of traps are associated with passive services.

As if designed to make the Gods of Hypocrisy die of laughter, "SNMP" is anything but simple. Translating "SNMP" traps and getting them into Nagios (as passive check results) can be a bit tedious. To make this task easier, I suggest you check out Alex Burger's "SNMP" Trap Translator project located at `http://www.snmptt.org`_. When combined with Net-"SNMP", SNMPTT provides an enhanced trap handling system that can be integrated with Nagios.

You are strongly suggested to eventually have a logging system, SNMP manager or Hypervisor to classify and identify new alerts and events.


.. _http://www.snmptt.org: http://www.snmptt.org/
.. _OpenNMS: http://www.opennms.org/
.. _thebasics/active-module-checks:

================================
Active data acquisition modules 
================================


Overview 
=========

An integrated acquisition module is an optional piece of software that is launched by a Shinken daemon. The module is responsible for doing data acquisition using a specific protocol in a very high performance method. This is preferred over repeatedly calling plugin scripts.

.. image:: /_static/images///poller_daemon_module.png
   :scale: 90 %


SNMP data acquisition module 
=============================

Shinken provides an integrated SNMP data acquisition module: SnmpBooster

  * :ref:`What is the SnmpBooster module <packages/snmp/how-it-works>`
  * :ref:`Install and configure the SNMP acquisition module. <packages/snmp/setup>`
  * :ref:`Reference - SnmpBooster troubleshooting <packages/snmp/troubleshooting>`
  * :ref:`Reference - SnmpBooster Design specification <packages/snmp/design-specification>`
  * :ref:`Reference - SnmpBooster configuration dictionnary <packages/snmp/dictionary>`


NRPE data acquisition module 
=============================

Shinken provides an integrated NRPE data acquisition module. NRPE is a protocol used to communicate with agents installed on remote hosts. It is implemented in the poller daemon to transparently execute NRPE data acquisition. It reads the check command and opens the connection itself. This provides a big performance boost for launching check_nrpe based checks. 

The command definitions are identical to the check_nrpe calls.

  * :ref:`Install and configure the NRPE acquisition module. <packages/snmp/setup-snmp-booster-module>`


Notes on community Packs 
=========================

Community provided :ref:`monitoring packs <contributing/create-and-push-packs>` may use the integrated acquisition modules.

Community provided plugins are complimentary to the integrated acquisition modules.


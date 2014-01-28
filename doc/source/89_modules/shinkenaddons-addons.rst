.. _shinkenaddons-addons:


.. _shinkenaddons-addons#shinkenaddons-addons-nrpe:


===================
 Extending Shinken 
===================



Introduction 
=============


There are a lot of “Modules" and "Addons" that are available for Shinken. Shinken can be extended by using different types of methods.

  * Web interfaces from various open-source vendors can be used (Based on Livestatus API)
  * Shinken itself can be extended using modules that are embedded into the various daemon processes 
  ** (Arbiter, Poller, Receiver, Broker, Scheduler, Reactionner)
  * External software can provide functional enhancements for reporting, management or usability aspects

Shinken itself provides methods to extend the base functionality:

  * :ref:`Broker modules <the_broker_modules>` provide external access to runtime data from Shinken
  * Poller modules such as :ref:`NRPE <setup_nrpe_booster_module>` and the :ref:`SNMP <setup_snmp_booster_module>`
  * Receiver modules like :ref:`NSCA <nsca_daemon_module>` provide acquisition methods for Shinken
  * Arbiter modules permit manipulating the configuration
  * The webUI that permits embedding web interface elements

Independent software that works in concert with Shinken is available for:

  * Monitoring remote hosts through agent software (\*NIX, Windows, etc.)
  * Submitting passive checks from remote hosts
  * Managing the config files through a web interface
  * Mobile phone UIs
  * Desktop UIs and Hypervisors
  * Desktop notification addons
  * ...and much more

You can find many addons that are compatible with Shinken by visiting. The only caveat is that the addons should not use the status.dat file and preferably the modern API interfaces like Livestatus:

  * `Nagios.org`_
  * `SourceForge.net`_
  * `NagiosExchange.org`_
  * `Shinken community exchange for monitoring packs`_


.. _SourceForge.net: http://www.sourceforge.net/
.. _Shinken community exchange for monitoring packs: http://community.shinken-monitoring.org/main
.. _Nagios.org: http://www.nagios.org/
.. _NagiosExchange.org: http://www.nagiosexchange.org/

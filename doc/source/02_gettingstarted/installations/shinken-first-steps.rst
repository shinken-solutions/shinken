.. _gettingstarted/installations/shinken-first-steps:


Where is the configuration?
----------------------------

The configuration is where you put the ``etc`` directory. Usually it's ``/etc/shinken`` or ``C:/Program Files/Shinken``.
  * ``shinken.cfg`` is meant to be main configuration file that will call all others


I migrate from Nagios, do I need to change my Nagios configuration?
--------------------------------------------------------------------

No, there is no need to change your existing Nagios configuration.
You can use an existing Nagios configuration as-is, as long as you have installed the plugins expected by the configuration.

Once you are comfortable with Shinken you can start to use its unique and powerful features.


What do I need to do next
--------------------------

The next logical steps for a new user are as listed in the :ref:`Getting Started <gettingstarted/index>` pages:

* Did you read the :ref:`Shinken Architecture <architecture/the-shinken-architecture>` presentation?
* Complete the :ref:`Shinken basic installation <configuration/index>`
* Start adding devices to monitor, such as:

  * :ref:`Public services <monitoring/network-service>` (HTTP, SMTP, IMAP, SSH, etc.)
  * :ref:`GNU/Linux <monitoring/monitoring-a-linux>` clients
  * :ref:`Windows <monitoring/windows>` clients
  * :ref:`Routers <monitoring/monitoring-routers>`
  * :ref:`Printers <monitoring/printer>`

* Setup the web interface:

  * Use the :ref:`default WebUI <integration/webui>`
  * Or set-up a :ref:`third-party web interface <integration/index>` and addons.


Getting Help
-------------

New and experienced users sometimes need to find documentation, troubleshooting tips, a place to chat, etc.
The :ref:`Shinken community provides many resources to help you <contributing/index>`. You can discuss installation documentation changes in the Shinken forums.

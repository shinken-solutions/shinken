.. _shinken_first_steps:





Where is the configuration?
----------------------------


The configuration is where you put the ``etc`` directory. Usually it's ``/etc/shinken``, ``/usr/local/shinken/etc`` or ``C:/Program Files/Shinken``.
  * ``nagios.cfg`` is meant to be fully compatible with Nagios;
  * ``shinken-specific.cfg`` contains all Shinken specific objects (ie. daemons, realms, etc.).



Do I need to change my Nagios configuration?
---------------------------------------------


No, there is no need to change your existing Nagios configuration.
You can use an existing Nagios configuration as-is, as long as you have installed the plugins expected by the configuration.

Once you are comfortable with Shinken you can start to use its unique and powerful features.



What do I need to do next
--------------------------


The next logical steps for a new user are as listed in the :ref:`Getting Started <start>` page:

* Setup the web interface:

  * Use the :ref:`default WebUI <use_with_webui>` (Note: it's the mandatory interface on Windows)
  * Or set-up a :ref:`third-party web interface <use_shinken_with>` and addons.

* Did you read the :ref:`Shinken Architecture <the_shinken_architecture>` presentation?
* Complete the :ref:`Shinken basic installation <configure_shinken>`
* Start adding devices to monitor, such as:

  * :ref:`Public services <monitoring_a_network_service>` (HTTP, SMTP, IMAP, SSH, etc.)
  * :ref:`GNU/Linux <monitoring_a_linux>` clients
  * :ref:`Windows <monitoring_a_windows>` clients
  * :ref:`Routers <monitoring_a_router_or_switch>`
  * :ref:`Printers <monitoring_a_printer>`



Getting Help
-------------


New and experienced users sometimes need to find documentation, troubleshooting tips, a place to chat, etc. The :ref:`Shinken community provides many resources to help you <how_to_contribute#Shinken resources for users>`. You can discuss installation documentation changes in the Shinken forums.

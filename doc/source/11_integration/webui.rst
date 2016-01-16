.. _integration/webui:

======================
Use Shinken with WebUI
======================


Shinken WebUI
==============

Shinken includes a self sufficient Web User Interface, which includes its own web server (No need to setup Apache or Microsoft IIS)
Shinken WebUI is started at the same time Shinken itself does, and is configured using the main Shinken configuration file by setting a few basic parameters.


.. image:: /_static/images/problems.png
   :scale: 90 %


* Homepage: https://github.com/shinken-monitoring/mod-webui/wiki
* Screenshots: https://github.com/shinken-monitoring/mod-webui/wiki
* Description: "Shinken WebUI is the default visualization interface. It's designed to be simple and focus on root problems analysis and business impacts."
* License: AGPL v3
* Shinken forum: http://www.shinken-monitoring.org/forum/


Set up the WebUI module
========================

Installing the Shinken **WebUI** is as simple as:

::

   # Log in with your shinken user account ...
   $ shinken install webui2

   # Install Python dependencies
   $ sudo pip install pymongo>=3.0.3 requests arrow bottle==0.12.8

   # By the time, mongodb is also mandatory to store user's parameters and many other information
   $ sudo apt-get install mongodb

   # Declare webui as a broker module
   $ vi /etc/shinken/brokers/broker-master.cfg
   [...]
   modules     webui2
   [...]

   $ sudo service shinken restart


.. important:: You will find more detailed information on this installation page: https://github.com/shinken-monitoring/mod-webui/wiki/Installation

.. note::  The web-server handling HTTP Request to the WebUI is a Python process. You *do not need* any web-server (like Apache) to run the WebUI.


Web UI configuration
=========================

The Web UI configuration file ''/etc/shinken/modules/webui2.cfg'' is heavily documented to explain the many available parameters.

Please have a look inside the file or read the configuration page in the Wiki: https://github.com/shinken-monitoring/mod-webui/wiki/Configuration



Web UI modules
=========================

In its actual version, the Web UI is self sufficent and not not need extra modules to be installed or configured, it is designed to run 'out of the box'!.

More information on embedded modules is available on the project Wiki: https://github.com/shinken-monitoring/mod-webui/wiki.



Use it!
========

The next step is very easy: just access the WebUI URI (something like %%http://127.0.0.1:7767/%%)

Log in with the user/password defined in one of the contact file of your configuration.


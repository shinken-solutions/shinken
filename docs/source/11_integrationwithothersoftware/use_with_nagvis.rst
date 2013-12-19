.. _use_with_nagvis:


=======================
Use Shinken with Nagvis
=======================


NagVis 
-------




.. image:: /_static/images/nagivs.jpg?640x480
   :scale: 90 %


  * Homepage: http://www.nagvis.org/
  * Screenshots: http://www.nagvis.org/screenshots
  * Description: "NagVis is a visualization addon for the well known network managment system Nagios."
  * License: GPL v2

  * Shinken dedicated forum: http://www.shinken-monitoring.org/forum/index.php/board,11.0.html


Using Shinken with NagVis 
--------------------------


NagVis communicates with Shinken through the LiveStatus module. If you used the sample configuration, everything should be ready already. :)

You can review the configuration using the following steps.



Enable Livestatus module 
~~~~~~~~~~~~~~~~~~~~~~~~~


The Livestatus API is server from the Shinken broker. It permits communications via TCP to efficiently retrieve the current state and performance data of supervised hosts and services from Shinken. It also exposes configuration information.

See :ref:`enable Livestatus module <enable_livestatus_module>`.



Nagvis Installation 
~~~~~~~~~~~~~~~~~~~~


Download the software and follow the installation guide from http://www.nagvis.org/



NagVis configuration 
~~~~~~~~~~~~~~~~~~~~~


Nagvis needs to know where the Shinken Livestatus API is hosted.

In NagVis configuration file ''/etc/nagvis/nagvis.ini.php'':

  
::

  [backend_live_1]
  backendtype="mklivestatus"
  htmlcgi="/nagios/cgi-bin"
socket="tcp:localhost:50000"

.. important::  If you are using a non local broker (or a distributed Shinken architecture with multiple brokers) you should change **localhost** to the **IP/Servername/FQDN of your broker**!

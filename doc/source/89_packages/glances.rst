.. _glances:



=========================================================
Monitoring Linux System with Glances and checkglances.py 
=========================================================


`Glances`_ is a fantastic multiplatform system monitoring tool writen by `Nicolargo`_. Glances can run on (Linux, Windows, MacOS ...). There is a growing `ecosystem`_ around Glances and of course a Nagios/Shinken plugin : `checkglances.py`_. 



How does it work 
=================


Glances can run in server mode. It provide a XML-RPC server (over http) and allow to retrieve system information throuh a restful API. The only thing to do is to install and start Glances as server on the monitored host, then install checkglances.py on the shinken server and finaly install the glances pack. 



Install glances 
================


See the glances documentation to install glances on Linux. 

<code bash>
easy_install glances
</code>

There is a debian startup script in the glances repository. And another one for centos `here`_.



Install checkglances.py 
========================


Just follow the documentation for the checkglances.py prerequisites and put it in your nagios plugins folder. 



Install the glances pack 
=========================


Open a terminal as the shinken user and just type the following command

<code bash>
shinken install glances
</code>

Then just edit the configuration for a linux monitored host and tag it as **glances**

  
::

  
  define host{
   name mylinuxhost
   use glances
   ...
  
  
Finaly restart the shinken arbiter

  
::

  
  service shinken-arbiter restart




What will be monitored ? 
=========================


For the moment just the basic system (ram, cpu, load, memory, filesystem and network).

If you want to modify the default thresholds for just a host you can do it by overiding the thresholds macro in your host definition. If you want to do it for several hosts, declare a new template and just add the desired thresholds macro to be overide. 

Here is a list of the macros 

  
::

  
  
::

   _LOAD_WARN           2
   _LOAD_CRIT           3
   _CPU_WARN            80
   _CPU_CRIT            90
   _MEMORY_WARN         90
   _MEMORY_CRIT         95
   _FS                  /, /home
   _FS_WARN             90
   _FS_CRIT             95
   _IFACES              eth0, eth1 
   _NET_WARN            7500000
   _NET_CRIT            10000000 
  
  
Note the _FS and _IFACES macros. They leverage the ability to duplicate service for a given list of things to be monitored. Here you see that / and /home partitions will be monitored. If you want to modify this then just add your own in a new template that will inherit the glances template.

.. _Glances: https://github.com/nicolargo/glances
.. _Nicolargo: http://blog.nicolargo.com/
.. _checkglances.py: https://github.com/nicolargo/checkglances
.. _here: https://github.com/david-guenault/shinken-packs/tree/master/pack-glances/share/init/centos
.. _ecosystem: https://github.com/nicolargo/glances/wiki/The-Glances-eco-system
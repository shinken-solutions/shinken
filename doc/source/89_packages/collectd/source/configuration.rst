.. _collectd_configuration:

=============
Configuration
=============

Shinken Collectd module
=======================

Collectd module declaration
---------------------------

Add and modify the following configuration in *collectd.cfg*

::

    define module {
       module_name Collectd
       module_type collectd
     
       # Specify exact host (optional)
       host        0.0.0.0
       port        25826
       multicast   False

       # Select which collectd plugin you want to group
       # Example :
       # grouped_collectd_plugins     cpu, df
       # This will group all 'cpu' plugin instances in one service called 'cpu' with all perf datas : cpu-0-wait, cpu-1-wait, cpu-0-idle, cpu-1-idle, ....
       #  AND yhis will group all 'df' plugin instances in one service called 'df' with all perf datas : df-complex-root-free, ....
       # If grouped_collectd_plugins is empty
       # This will not group plugin instances and you will have this following services : cpu-0, cpu-1, df-root, ...
       #
       # grouped_collectd_plugins 
    }

.. important:: You have to be sure that the *collectd.cfg* will be loaded by Shinken (watch in your shinken.cfg)


Parameters details
~~~~~~~~~~~~~~~~~~

:host:                          Bind address 
:port:                          Bind port. Default: 25826 
:multiscast:                    ?????. Default: False
:grouped_collectd_plugins:      List of collectd plugins where plugin instances will be group by plugin. Default: *empty*. Example: cpu,df,disk,interface


Receiver/Arbiter daemon configuration
-------------------------------------

Simply declare the module:

::

  modules Collectd



Collectd agent configuration
============================

You have to configure your Collectd agents for they send datas to Shinken.
In the collectd.conf file, you have to have:

::

  LoadPlugin network
  <Plugin network>
      Server "192.168.2.16" "25826"
  </Plugin>

Where *192.168.2.16* is the Receiver/Arbiter IP.

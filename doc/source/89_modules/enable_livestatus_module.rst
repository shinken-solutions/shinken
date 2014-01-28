.. _enable_livestatus_module:



How to enable and use Livestatus module 
----------------------------------------




Define the Livestatus module 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


Start by reviewing the ''/etc/shinken/shinken-specific.cfg'' file for this module:

  
::

  define module{
  
::

       module_name      Livestatus
       module_type      livestatus
       host             *       ; * = listen on all configured IP addresses
       port             50000   ; port to listen on
       database_file    /var/lib/shinken/livestatus.db
}

With these parameters:
    * module_name: name of the module called by the brokers
    * module_type: livestatus
    * host: IP interface to listen to. The default is *, which means "listen on all interfaces".
    * port: TCP port to listen to. 
    * socket: Unix socket to listen to.
    * database_file: the path to the sqlite database file which is used to store the log broks/messages. The default is "var/livelogs.db"
    * max_logs_age: the maximum age of the log messages (before they are deleted from the database). The default is 1 year. The argument to this parameter takes the form <number>[<period of time>], where <period of time> can be d for days, w for weeks, m for months and y for years.
    * allowed_hosts: a comma-separated list of IP-addresses which are allowed to contact the TCP port. Please keep in mind that these **must be IP-addresses, NOT host names**. Because DNS lookups for every incoming livestatus request could hang up and therefore block the module.




Enable the Livestatus module 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


Still in ''/etc/shinken/shinken-specific.cfg'', find the object Broker and add "Livestatus" to its "modules":

  
::

  
  define broker{
  
::

       broker_name      broker-1
  [...]
  
::

       modules          Simple-log,Livestatus
  }




Disable human readable logs 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~


In ''/etc/shinken/nagios.cfg'', verify that the option **human_timestamp_log** is set to **0**.

In version 0.6.5, you can not have at the same time a simple-log file with human readable timestamp and a Livestatus database.
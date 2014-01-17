.. _use_with_centreon:


=========================
Use Shinken with Centreon
=========================


Centreon 
---------


Centreon is a famous French monitoring solution based on Nagios, which can also be used with Shinken.



.. image:: /_static/images/centreon.png?640x480
   :scale: 90 %


  * Homepage: http://www.centreon.com/
  * Screenshots: http://www.centreon.com/Content-Products-IT-network-monitoring/screenshots-for-centreon-it-monitoring-centreon
  * Description: "Centreon is an Open Source software package that lets you supervise all the infrastructures and applications comprising your information system"
  * License: GPL v2

  * Shinken dedicated forum: http://www.shinken-monitoring.org/forum/index.php/board,8.0.html


How to use Shinken as a Centreon backend 
-----------------------------------------


The following Shinken Broker modules are required:
  * NDO/MySQL
  * Simple log
  * Flat file perfdata

Below is the configuration you should set (there is already a sample configuration in your ''/etc/shinken/shinken-specific.cfg'' file)



Simple log 
~~~~~~~~~~~


The module **simple_log** puts all Shinken's logs (Arbiter, Scheduler, Poller, etc.) into a single file.

In ''/etc/shinken/shinken-specific.cfg'':
  
::

  define module{
  
::

       module_name      Simple-log
       module_type      simple_log
       path             /var/lib/nagios/nagios.log
       archive_path     /var/lib/nagios/archives/
}

It takes these parameters:
    * module_name: name of the module called by the brokers
    * module_type: simple_log
    * path: path of the log file



NDO/MySQL 
~~~~~~~~~~


The module **ndodb_mysql** exports all data into a NDO MySQL database.

It needs the python module **MySQLdb** (Debian: ''sudo apt-get install python-mysqldb'', or ''easy_install MySQL-python'')

In ''/etc/shinken/shinken-specific.cfg'':
  
::

  define module{
  
::

       module_name      ToNdodb_Mysql
       module_type      ndodb_mysql
       database         ndo       ; database name
       user             root      ; user of the database
       password         root      ; must be changed
       host             localhost ; host to connect to
       character_set    utf8      ;optional, default: utf8
}

It takes the following parameters:
    * module_name: name of the module called by the brokers
    * module_type: ndodb_mysql
    * database: database name (ex ndo)
    * user: database user 
    * password: database user passworddt
    * host: database host
    * character_set: utf8 is a good one



Service Perfdata 
~~~~~~~~~~~~~~~~~


The module **service_perfdata** exports service's perfdata to a flat file.

In ''/etc/shinken/shinken-specific.cfg'':
  
::

  define module{
  
::

       module_name      Service-Perfdata
       module_type      service_perfdata
       path             /var/lib/shinken/service-perfdata
}

It takes the following parameters:
    * module_name: name of the module called by the brokers
    * module_type: service_perfdata
    * path: path to the service perfdata file you want



Configure Broker to use these modules 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


In ''/etc/shinken/shinken-specific.cfg'' find the object **Broker**, and add the above modules to the **modules** line:

  
::

  define broker{
  
::

       broker_name      broker-1
  [...]
  
::

       modules          Simple-log,ToNdodb_Mysql,Service-Perfdata
}



Configure Scheduler to match Centreon's Poller 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


Shinken's "Scheduler" is called a "Poller" in Centreon. If you keep the sample Scheduler name, you won't see any data in the Centreon interface.

So edit ''/etc/shinken/shinken-specific.cfg'' and change the Scheduler name to match the Centreon's Poller name ("default"):

  
::

  define scheduler{
  
::

       scheduler_name   default
       [...]
}

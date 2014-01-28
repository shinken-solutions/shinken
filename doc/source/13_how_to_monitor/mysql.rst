.. _mysql:



Monitoring MySQL
================


**Abstract**

This document describes how you can monitor a MySQL server such as:

  * Connection time
  * A recent restart
  * The number of connections
  * Cache hit
  * etc...



Introduction 
-------------


These instructions assume that you've installed Shinken according to the :ref:`Installation tutorial <shinken_10min_start>`. The sample configuration entries below reference objects that are defined in the sample config files ("commands.cfg", "templates.cfg", etc.) that are installed if you follow the quickstart.



Overview 
---------


.. note::  TODO: draw a check_mysql diag 

Monitoring a MySQL server need the plugin check_mysql_health available at `labs.consol.de/lang/en/nagios/check_mysql_health/`_ and a mysql user account for the connection.



Steps 
------


There are some steps you'll need to follow in order to monitor a new Linux machine. They are:

  - Install check plugins
  - setup the mysql user account
  - Update your server host definition for mysql monitoring
  - Restart the Shinken daemon



What's Already Done For You 
----------------------------


To make your life a bit easier, a few configuration tasks have already been done for you:

  * Some **check_mysql_** commands definition has been added to the "commands.cfg" file.
  * A Mysql host template (called "mysql") has already been created in the "templates.cfg" file.

The above-mentioned config files can be found in the ///etc/shinken/// directory (or *c:\shinken\etc* under windows). You can modify the definitions in these and other definitions to suit your needs better if you'd like. However, I'd recommend waiting until you're more familiar with configuring Shinken before doing so. For the time being, just follow the directions outlined below and you'll be monitoring your Mysql boxes in no time.

.. tip::  We are supposing here that the Mysql machine you want to monitor is named srv-lin-1 and is a Linux. Please change the above lines and commands with the real name of your server of course.



Installing the check plugins on Shinken 
----------------------------------------


First connect as root under you Shinken server (or all poller servers for a multi-box setup) and launch:

  
::

  
  shinken.sh -p check_mysql_health




Setup the mysql user account 
-----------------------------


Connect with a root account on your MySQL database. change 'password' with your mysql root password:

  
::

  
  lin-srv-1:# mysql -u root -ppassword

And create a shinken user:

  
::

  
  GRANT usage ON *.* TO 'shinken'@'%' IDENTIFIED BY 'shinkenpassword';


It's a good thing to change the shinkenpassword to another password. Then you need to update the /etc/shinken/resource.cfg file or c:\shinken\etc\resource.cfg file to setup the new password:
  
::

  
  $MYSQLUSER$=shinken
  $MYSQLPASSWORD$=shinkenpassword




Test the connection 
~~~~~~~~~~~~~~~~~~~~


To see if the connection is okay, just launch:
  
::

  
  
::

   /var/lib/nagios/plugins/check_mysql_health --hostname srv-lin-1 --username shinken --password shinkenpassword --mode connection-time
  
It should not return errors.



Declare your host as a mysql server 
------------------------------------


All you need to get all the MySQL service checks is to add the *mysql* template to this host. We suppose you already monitor the OS (linux or windows for example) for this host, and so you already got the host configuration file for it.

Under Linux:
  
::

  
  
::

  linux:~ # vi /etc/shinken/hosts/srv-lin-1.cfg
  
Or Windows:
  
::

  
  
::

  c:\ wordpad   c:\shinken\etc\hosts\srv-lin-1.cfg
  
  
You need to add the mysql template in the use line. It's better to follow the more precise template to the less one, like here mysql first, and then linux.

  
::

  
  
::

  define host{
      use             mysql,linux
      host_name       srv-lin-1
      address         srv-lin-1.mydomain.com
  }
  
  
  


What is checked with a mysql template? 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


At this point, you configure your host to be checked with a mysql template. What does it means? It means that you got some services checks already configured for you. Warning and alert levels are between ():

  * connection-time: Determines how long connection establishment and login take, 0..n Seconds (1, 5)
  * uptime: Time since start of the database server (recognizes DB-Crash+Restart), 0..n Seconds (10:, 5: Minutes)
  * threads-connected: Number of open connections,	1..n (10, 20)
  * threadcache-hitrate: Hitrate in the Thread-Cache	0%..100% (90:, 80:)
  * querycache-hitrate: Hitrate in the Query Cache	0%..100% (90:, 80:)
  * querycache-lowmem-prunes: Displacement out of the Query Cache due to memory shortness	n/sec (1, 10)
  * keycache-hitrate: Hitrate in the Myisam Key Cache	0%..100% (99:, 95:)
  * bufferpool-hitrate: Hitrate in the InnoDB Buffer Pool	0%..100% (99:, 95:)
  * bufferpool-wait-free: Rate of the InnoDB Buffer Pool Waits	0..n/sec (1, 10)
  * log-waits: Rate of the InnoDB Log Waits	0..n/sec (1, 10)
  * tablecache-hitrate: Hitrate in the Table-Cache	0%..100% (99:, 95:)
  * table-lock-contention: Rate of failed table locks	0%..100% (1, 2)
  * index-usage: Sum of the Index-Utilization (in contrast to Full Table Scans)	0%..100% (90:, 80:)
  * tmp-disk-tables: Percent of the temporary tables that were created on the disk instead in memory	0%..100% (25, 50)
  * slow-queries: Rate of queries that were detected as "slow"	0..n/sec (0.1, 1)
  * long-running-procs: Sum of processes that are runnning longer than 1 minute	0..n (10, 20)
  * slave-lag: Delay between Master and Slave	0..n Seconds
  * slave-io-running: Checks if the IO-Thread of the Slave-DB is running	 
  * slave-sql-running: Checks if the SQL-Thread of the Slave-DB is running	 
  * open-files: Number of open files (of upper limit)	0%..100% (80, 95)	 
  * cluster-ndb-running: Checks if all cluster nodes are running.



Restarting Shinken 
-------------------


You're done with modifying the Shiknen configuration, so you'll need to :ref:`verify your configuration files <runningshinken-verifyconfig>` and :ref:`restart Shinken <runningshinken-startstop>`.

If the verification process produces any errors messages, fix your configuration file before continuing. Make sure that you don't (re)start Shinken until the verification process completes without any errors!
.. _labs.consol.de/lang/en/nagios/check_mysql_health/: http://labs.consol.de/lang/en/nagios/check_mysql_health/

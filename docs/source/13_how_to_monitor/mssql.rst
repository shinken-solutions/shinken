.. _mssql:



Monitoring Microsoft Mssql server
=================================


**Abstract**

This document describes how you can monitor a Mssql server such as:

  * Connection time
  * A recent restart
  * The number of connections
  * Cache hit
  * Dead locks
  * etc ...



Introduction 
-------------


These instructions assume that you've installed Shinken according to the :ref:`Installation tutorial <shinken 10min start >`. The sample configuration entries below reference objects that are defined in the sample config files ("commands.cfg", "templates.cfg", etc.) that are installed if you follow the quickstart.



Overview 
---------


.. note::  TODO: draw a check_mssql diag 

Monitoring a Mssql server need the plugin check_mssql_health available at `labs.consol.de/lang/en/nagios/check_mssql_health/`_ and a mssql user account for the connection.



Steps 
------


There are some steps you'll need to follow in order to monitor a new database machine. They are:

  - Install check plugins
  - setup the mssql user account
  - Update your windows server host definition for mysql monitoring
  - Restart the Shinken daemon



What's Already Done For You 
----------------------------


To make your life a bit easier, a few configuration tasks have already been done for you:

  * Some **check_mssql_** commands definition has been added to the "commands.cfg" file.
  * A Mssql host template (called "mssql") has already been created in the "templates.cfg" file.

The above-mentioned config files can be found in the ///etc/shinken/// directory (or *c:\shinken\etc* under windows). You can modify the definitions in these and other definitions to suit your needs better if you'd like. However, I'd recommend waiting until you're more familiar with configuring Shinken before doing so. For the time being, just follow the directions outlined below and you'll be monitoring your Mssql boxes in no time.

.. tip::  We are supposing here that the Mssql machine you want to monitor is named srv-win-1. Please change the above lines and commands with the real name of your server of course.



Installing the check plugins on Shinken 
----------------------------------------


First connect as root under you Shinken server (or all poller servers for a multi-box setup)

.. note::  Todo: Use shinken.sh for this




Setup the mssql user account 
-----------------------------


Look at the `labs.consol.de/lang/en/nagios/check_mssql_health/`_ page about how to configure your user connection.

Then you will need to configure your user/password in the macros file so the plugins will have the good values for the connction. So update the /etc/shinken/resource.cfg file or c:\shinken\etc\resource.cfg file to setup the new password:
  
::

  
  $MSSQLUSER$=shinken
  $MSSQLPASSWORD$=shinkenpassword




Test the connection 
~~~~~~~~~~~~~~~~~~~~


To see if the connection is ok, just launch:
  
::

  
  
::

   /var/lib/nagios/plugins/check_mssql_health --hostname srv-win-1 --username shinken --password shinkenpassword --mode connection-time
  
It should not return errors.



Declare your host as a mssql server 
------------------------------------


All you need to get all the Msql service checks is to add the *mssql* template to this host. We suppose you already monitor the OS for this host, and so you already got the host configuration file for it.

Under Linux:
  
::

  
  
::

  linux:~ # vi /etc/shinken/hosts/srv-win-1.cfg
  
Or Windows:
  
::

  
  
::

  c:\ wordpad   c:\shinken\etc\hosts\srv-win-1.cfg
  
  
You need to add the mysql template in the use line. It's better to follow the more precise template to the less one, like here mssql first, and then windows.

  
::

  
  
::

  define host{
      use             mssql,windows
      host_name       srv-win-1
      address         srv-win-1.mydomain.com
  }
  
  


What is checked with a mssql template? 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


At this point, you configure your host to be checked with a mssql template. What does it means? It means that you got some services checks already configured for you. Warning and alert levels are between ():
  * connection-time: Measures how long it takes to login	0..n seconds (1, 5)
  * connected-users: Number of connected users	0..n (50, 80)
  * cpu-busy: CPU Busy Time	0%..100% (80, 90)
  * io-busy: IO Busy Time	0%..100% (80, 90)
  * full-scans: Number of Full Table Scans per second	0..n (100, 500)
  * transactions: Number of Transactions per second	0..n (10000, 50000)
  * batch-requests: Number of Batch Requests per second	0..n (100, 200)
  * latches-waits: Number of Latch-Requests per second, which could not be fulfilled	0..n (10, 50)
  * latches-wait-time: Average time a Latch-Request had to wait until it was granted	0..n ms (1, 5)
  * locks-waits: Number of Lock-Requests per second, which could not be satisfied.	0..n (100, 500)
  * locks-timeouts: Number of Lock-Requests per second, which resulted in a timeout.	0..n (1, 5)
  * locks-deadlocks: Number of Deadlocks per second	0..n (1, 5)
  * sql-recompilations: Number of Re-Compilations per second	0..n (1, 10)
  * sql-initcompilations: Number of Initial Compilations per second	0..n (100, 200)
  * total-server-memory: The main memory reserved for the SQL Server	0..n (nearly1G, 1G)
  * mem-pool-data-buffer-hit-ratio: Data Buffer Cache Hit Ratio	0%..100% (90, 80:)
  * lazy-writes: Number of Lazy Writes per second	0..n (20, 40)
  * page-life-expectancy: Average time a page stays in main memory	0..n (300:, 180:)
  * free-list-stalls: Number of Free List Stalls per second	0..n (4, 10)
  * checkpoint-pages: Number of Flushed Dirty Pages per second	0..n ()
  * database-free: Free space in a database (Default is percent, but –units can be used also). You can select a single database with the name parameter.	0%..100% (5%, 2%)
  * database-backup-age	Elapsed time since a database was last backupped (in hours). The performancedata also cover the time needed for the backup (in minutes).	0..n



Restarting Shinken 
-------------------


You're done with modifying the Shiknen configuration, so you'll need to :ref:`verify your configuration files <runningshinken-verifyconfig>` and :ref:`restart Shinken <runningshinken-startstop>`.

If the verification process produces any errors messages, fix your configuration file before continuing. Make sure that you don't (re)start Shinken until the verification process completes without any errors!
.. _labs.consol.de/lang/en/nagios/check_mssql_health/: http://labs.consol.de/lang/en/nagios/check_mssql_health/

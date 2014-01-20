.. _oracle:



Monitoring an Oracle database server
====================================


**Abstract**

This document describes how you can monitor an Oracle database server such as:

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


.. note::  TODO: draw a oracle diag 

Monitoring an Oracle server need the plugin check_oracle_health available at `labs.consol.de/lang/en/nagios/check_oracle_health/`_ and an oracle user account for the connection.



Steps 
------


There are some steps you'll need to follow in order to monitor a new database machine. They are:
  
::

  

- Install dependencies
  - Install check plugins
  - Setup the oracle user account
  - Creating an alias definition for Oracle databases
  - Update your server host definition for oracle monitoring
  - Restart the Shinken daemon



What's Already Done For You 
----------------------------


To make your life a bit easier, a few configuration tasks have already been done for you:

  * Some **check_oracle_** commands definition has been added to the "commands.cfg" file.
  * An Oracle host template (called "oracle") has already been created in the "templates.cfg" file.

The above-mentioned config files can be found in the ///etc/shinken/// directory (or *c:\shinken\etc* under windows). You can modify the definitions in these and other definitions to suit your needs better if you'd like. However, I'd recommend waiting until you're more familiar with configuring Shinken before doing so. For the time being, just follow the directions outlined below and you'll be monitoring your Oracle boxes in no time.

.. tip::  We are supposing here that the Oracle machine you want to monitor is named srv-lin-1 and is a linux. Please change the above lines and commands with the real name of your server of course.



Installing dependencies 
------------------------




Installing SQL*Plus on the Shinken server 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


Check_oracle_health plugin needs sqlplus oracle client on the Shinken server, you can download packages on the Oracle Technology Network website.
You need to have these 3 packages:
oracle-instantclient11.2-basic-11.2.0.3.0-1.x86_64.rpm
oracle-instantclient11.2-devel-11.2.0.3.0-1.x86_64.rpm
oracle-instantclient11.2-sqlplus-11.2.0.3.0-1.x86_64.rpm

You can install them like this:
  
::

  
  linux:~ # rpm -Uvh oracle-instantclient11.2-*


Then you have to create some symbolic links in order to have commands in the path:
  
::

  
  linux:~ # ln -s /usr/lib/oracle/11.2/client64/bin/adrci /usr/bin/adrci
  linux:~ # ln -s /usr/lib/oracle/11.2/client64/bin/genezi /usr/bin/genezi
  linux:~ # ln -s /usr/lib/oracle/11.2/client64/bin/sqlplus /usr/bin/sqlplus


Also, you need to export Oracle environment variables in order to install CPAN modules:
  
::

  
  linux:~ # export ORACLE_HOME=/usr/lib/oracle/11.2/client64
  linux:~ # export PATH=$PATH:$ORACLE_HOME/bin
  linux:~ # export LD_LIBRARY_PATH=$ORACLE_HOME/lib




Installing CPAN modules 
~~~~~~~~~~~~~~~~~~~~~~~~


  
::

  
  linux:~ # perl -MCPAN -e shell
  cpan[1]> install DBI
  cpan[2]> force install DBD::Oracle




Installing the check plugins on Shinken 
----------------------------------------


First connect as root under you Shinken server (or all poller servers for a multi-box setup) and launch:

  
::

  
  shinken.sh -p check_oracle_health




Setup the oracle user account 
------------------------------


.. tip::  You will need to configure the user for all your oracle databases.

Connect to your database as sysadmin on the oracle server:
  
::

  
  srv-lin-1:oracle# sqlplus "/ as sysdba"

And then create your shinken account on the database:
  
::

  
  CREATE USER shinken IDENTIFIED BY shinkenpassword; 
  GRANT CREATE SESSION TO shinken;
  GRANT SELECT any dictionary TO shinken;
  GRANT SELECT ON V_$SYSSTAT TO shinken;
  GRANT SELECT ON V_$INSTANCE TO shinken;
  GRANT SELECT ON V_$LOG TO shinken;
  GRANT SELECT ON SYS.DBA_DATA_FILES TO shinken;
  GRANT SELECT ON SYS.DBA_FREE_SPACE TO shinken;

And for old 8.1.7 database only:
  
::

  
  --
  -- if somebody still uses Oracle 8.1.7...
  GRANT SELECT ON sys.dba_tablespaces TO shinken;
  GRANT SELECT ON dba_temp_files TO shinken;
  GRANT SELECT ON sys.v_$Temp_extent_pool TO shinken;
  GRANT SELECT ON sys.v_$TEMP_SPACE_HEADER  TO shinken;
  GRANT SELECT ON sys.v_$session TO shinken;


Then you will need to configure your user/password in the macros file so the plugins will have the good values for the connction. So update the ///etc/shinken/resource.cfg* file or *c:\shinken\etc\resource.cfg// file to setup the new password:
  
::

  
  $ORACLEUSER$=shinken
  $ORACLEPASSWORD$=shinkenpassword




Creating an alias definition for Oracle databases 
--------------------------------------------------


First, you have to create a tnsnames.ora config file on the shinken server that will contain the alias definition for PROD database:
  
::

  
  linux:~ # mkdir -p /usr/lib/oracle/11.2/client64/network/admin
  linux:~ # vim /usr/lib/oracle/11.2/client64/network/admin/tnsnames.ora
  PROD =
  
::

  (DESCRIPTION =
    (ADDRESS = (PROTOCOL = TCP)(HOST = 192.168.0.X)(PORT = 1521))
    (CONNECT_DATA =
      (SERVER = DEDICATED)
      (SERVICE_NAME = PROD)
    )
  )
  
  :wq

Note that you have to declare all databases that you want to monitor with Shinken in this file. 
For example, if you want to monitor ERP and FINANCE databases, your config file will look like this:
  
::

  
  ERP =
  
::

  (DESCRIPTION =
    (ADDRESS = (PROTOCOL = TCP)(HOST = 192.168.0.X)(PORT = 1521))
    (CONNECT_DATA =
      (SERVER = DEDICATED)
      (SERVICE_NAME = ERP)
    )
  )
  
  FINANCE =
  
::

  (DESCRIPTION =
    (ADDRESS = (PROTOCOL = TCP)(HOST = 192.168.0.X)(PORT = 1521))
    (CONNECT_DATA =
      (SERVER = DEDICATED)
      (SERVICE_NAME = FINANCE)
    )
  )
  
  
Then, you need define an environment variable that will contain the path of this file with also all others variables related to sqlplus:
  
::

  
  linux:~ # vi /etc/profile.d/oracle.sh
  
  export PATH=$PATH:/usr/lib/oracle/11.2/client64
  export LD_LIBRARY_PATH=/usr/lib/oracle/11.2/client64/lib
  export ORACLE_HOME=/usr/lib/oracle/11.2/client64
  export TNS_ADMIN=$ORACLE_HOME/network/admin
  
  :wq

Adjust rights on the oracle client directory:
  
::

  
  linux:~ # chown -R shinken:shinken /usr/lib/oracle

Optionally, we may have to force loading the oracle client lib like this:
  
::

  
  linux:~ # vi /etc/ld.so.conf.d/oracle.conf
  /usr/lib/oracle/11.2/client64/lib
  :wq
  linux:~ # ldconfig




Test the connection 
~~~~~~~~~~~~~~~~~~~~


To see if the connection to the database named PROD is ok, just launch:
  
::

  
  
::

   /var/lib/nagios/plugins/check_oracle_health --connect "PROD" --hostname srv-lin-1 --username shinken --password shinkenpassword --mode connection-time
  
It should not return errors.



Edit shinken init script 
~~~~~~~~~~~~~~~~~~~~~~~~~


Now, you have to edit the shinken init script for loading this new environment:
  
::

  
  linux:~ # vim /etc/init.d/shinken
  (...)
  NAME="shinken"
  
  AVAIL_MODULES="scheduler poller reactionner broker receiver arbiter skonf"
  
  # Load environment variables
  . /etc/profile.d/oracle.sh
  
  ## SHINKEN_MODULE_FILE is set by shinken-* if it's one of these that's calling us.
  (...)
  :wq




Declare your host as an oracle server, and declare your databases 
------------------------------------------------------------------


All you need to get all the Oracle service checks is to add the *oracle* template to this host and declare all your databases name. We suppose you already monitor the OS for this host, and so you already got the host configuration file for it.

Under Linux:
  
::

  
  
::

  linux:~ # vi /etc/shinken/hosts/srv-lin-1.cfg
  
Or Windows:
  
::

  
  
::

  c:\ wordpad   c:\shinken\etc\hosts\srv-lin-1.cfg
  
  
You need to add the oracle template in the use line. It's better to follow the more precise template to the less one, like here oracle first, and then linux. You also need to declare in the _databases macros all your database names, separated with comas. Here we suppose you got two databases, ERP and FINANCE (don't forget to declare them into the tnsnames.ora config file such as we described it previously):

  
::

  
  
::

  define host{
      use             oracle,linux
      host_name       srv-lin-1
      address         srv-lin-1.mydomain.com
      _databases      ERP,FINANCE
  }
  
  


What is checked with a oracle template? 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


At this point, you configure your host to be checked with a oracle template. What does it means? It means that you got some services checks already configured for you, and one for each databases you declared. Warning and alert levels are between ():

  * tnsping: Listener	 
  * connection-time: Determines how long connection establishment and login take	0..n Seconds (1, 5)
  * connected-users: The sum of logged in users at the database	0..n (50, 100)
  * session-usage: Percentage of max possible sessions	0%..100% (80, 90)
  * process-usage: Percentage of max possible processes	0%..100% (80, 90)
  * rman-backup-problems: Number of RMAN-errors during the last three days	0..n (1, 2)
  * sga-data-buffer-hit-ratio: Hitrate in the Data Buffer Cache	0%..100% (98:, 95:)
  * sga-library-cache-gethit-ratio: Hitrate in the Library Cache (Gets)	0%..100% (98:, 95:)
  * sga-library-cache-pinhit-ratio: Hitrate in the Library Cache (Pins)	0%..100% (98:, 95:)
  * sga-library-cache-reloads: Reload-Rate in the Library Cache	n/sec (10,10)
  * sga-dictionary-cache-hit-ratio: Hitrate in the Dictionary Cache	0%..100% (95:, 90:)
  * sga-latches-hit-ratio: Hitrate of the Latches	0%..100% (98:, 95:)
  * sga-shared-pool-reloads: Reload-Rate in the Shared Pool	0%..100% (1, 10)
  * sga-shared-pool-free: Free Memory in the Shared Pool	0%..100% (10:, 5:)
  * pga-in-memory-sort-ratio: Percentage of sorts in the memory.	0%..100% (99:, 90:)
  * invalid-objects: Sum of faulty Objects, Indices, Partitions	 
  * stale-statistics: Sum of objects with obsolete optimizer statistics	n (10, 100)
  * tablespace-usage: Used diskspace in the tablespace	0%..100% (90, 98)
  * tablespace-free: Free diskspace in the tablespace	0%..100% (5:, 2:)
  * tablespace-fragmentation: Free Space Fragmentation Index	100..1 (30:, 20:)
  * tablespace-io-balanc: IO-Distribution under the datafiles of a tablespace	n (1.0, 2.0)
  * tablespace-remaining-time: Sum of remaining days until a tablespace is used by 100%. The rate of increase will be calculated with the values from the last 30 days. (With the parameter –lookback different periods can be specified)	Days (90:, 30:)
  * tablespace-can-allocate-next: Checks if there is enough free tablespace for the next Extent.	 
  * flash-recovery-area-usage: Used diskspace in the flash recovery area	0%..100% (90, 98)
  * flash-recovery-area-free: Free diskspace in the flash recovery area	0%..100% (5:, 2:)
  * datafile-io-traffic: Sum of IO-Operationes from Datafiles per second	n/sec (1000, 5000)
  * datafiles-existing: Percentage of max possible datafiles	0%..100% (80, 90)
  * soft-parse-ratio: Percentage of soft-parse-ratio	0%..100%
  * switch-interval: Interval between RedoLog File Switches	0..n Seconds (600:, 60:)
  * retry-ratio: Retry-Rate in the RedoLog Buffer	0%..100% (1, 10)
  * redo-io-traffic: Redolog IO in MB/sec	n/sec (199,200)
  * roll-header-contention: Rollback Segment Header Contention	0%..100% (1, 2)
  * roll-block-contention: Rollback Segment Block Contention	0%..100% (1, 2)
  * roll-hit-ratio: Rollback Segment gets/waits Ratio	0%..100% (99:, 98:)
  * roll-extends: Rollback Segment Extends	n, n/sec (1, 100)
  * roll-wraps: Rollback Segment Wraps	n, n/sec (1, 100)
  * seg-top10-logical-reads: Sum of the userprocesses under the top 10 logical reads	n (1, 9)
  * seg-top10-physical-reads: Sum of the userprocesses under the top 10 physical reads	n (1, 9)
  * seg-top10-buffer-busy-waits: Sum of the userprocesses under the top 10 buffer busy waits	n (1, 9)
  * seg-top10-row-lock-waits: Sum of the userprocesses under the top 10 row lock waits	n (1, 9)
  * event-waits: Waits/sec from system events	n/sec (10,100)
  * event-waiting: How many percent of the elapsed time has an event spend with waiting	0%..100% (0.1,0.5)
  * enqueue-contention: Enqueue wait/request-Ratio	0%..100% (1, 10)
  * enqueue-waiting: How many percent of the elapsed time since the last run has an Enqueue spend with waiting	0%..100% (0.00033,0.0033)
  * latch-contention: Latch misses/gets-ratio. With –name a Latchname or Latchnumber can be passed over. (See list-latches)	0%..100% (1,2)
  * latch-waiting: How many percent of the elapsed time since the last run has a Latch spend with waiting	0%..100% (0.1,1)
  * sysstat: Changes/sec for any value from v$sysstat	n/sec (10,10)



Restarting Shinken 
-------------------


You're done with modifying the Shiknen configuration, so you'll need to :ref:`verify your configuration files <runningshinken-verifyconfig>` and :ref:`restart Shinken <runningshinken-startstop>`.

If the verification process produces any errors messages, fix your configuration file before continuing. Make sure that you don't (re)start Shinken until the verification process completes without any errors!
.. _labs.consol.de/lang/en/nagios/check_oracle_health/: http://labs.consol.de/lang/en/nagios/check_oracle_health/

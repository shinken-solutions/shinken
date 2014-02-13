.. _configure_shinken:



Setting up a basic Shinken Configuration 
=========================================




Default Shinken configuration 
------------------------------


If you followed the :ref:`10 Minute Shinken Installation Guide <shinken_10min_start>` tutorial you were able to install and launch Shinken.

The default configuration deployed with the Shinken sources contains:
  * one arbiter
  * one scheduler
  * one poller
  * one reactionner
  * one broker
  * one receiver (commented out)

All these elements must have a basic configuration. The Arbiter must know about the other daemons and how to communicate with them, just as the other daemons need to know on which TCP port they must listen on.



Configure the Shinken Daemons 
------------------------------

The schedulers, pollers, reactionners and brokers daemons need to know in which directory to work on, and on which TCP port to listen. That's all.

.. note::  If you plan on using the default directories, user (shinken) and tcp port you shouldn't have to edit these files.

Each daemon has one configuration file. The default location is /usr/local/shinken/etc/. 

.. important::  Remember that all daemons can be on different servers: the daemons configuration files need to be on the server which is running the daemon, not necessarily on every server

Let's see what it looks like:

::

  $cat etc/schedulerd.ini
  
  [daemon]
  workdir=/usr/local/shinken/var
  pidfile=%(workdir)s/schedulerd.pid
  port=7768
  host=0.0.0.0
  
  daemon_enabled=1
  
  # Optional configurations
  
  user=shinken
  group=shinken
  idontcareaboutsecurity=0
  use_ssl=0
  #certs_dir=etc/certs
  #ca_cert=etc/certs/ca.pem
  #server_cert=etc/certs/server.pem
  hard_ssl_name_check=0
  use_local_log=1
  local_log=brokerd.log
  log_level=INFO
  max_queue_size=100000

So here we have a scheduler:

    * workdir: working directory of the daemon. By default /usr/local/shinken/var
    * pidfile: pid file of the daemon (so we can kill it :) ). By default /usr/local/shinken/var/schedulerd.pid for a scheduler.
    * port: TCP port to listen to. By default:

       * scheduler: 7768
       * poller: 7771
       * reactionner: 7769
       * broker: 7772
       * arbiter: 7770 (the arbiter configuration will be seen later)

    * host: IP interface to listen on. The default 0.0.0.0 means all interfaces
    * user: user used by the daemon to run. By default shinken
    * group: group of the user. By default shinken.
    * idontcareaboutsecurity: if set to 1, you can run it under the root account. But seriously: do not to this. The default is 0 of course.
    * daemon_enabled : if set to 0, the daemon won't run. Useful for distributed setups where you only need a poller for example.
    * use_ssl=0
    * #certs_dir=etc/certs
    * #ca_cert=etc/certs/ca.pem
    * #server_cert=etc/certs/server.pem
    * hard_ssl_name_check=0
    * use_local_log=1 : Log all messages that match the log_level for this daemon in a local directory
    * local_log=brokerd.log : name of the log file where to save the logs
    * log_level=INFO : Log_level that will be permitted to be logger. Warning permits Warning, Error, Critical to be logged. INFO by default.
    * max_queue_size=100000 : If a module got a brok queue() higher than this value, it will be killed and restarted. Put to 0 to disable it





Daemon declaration in the global configuration 
-----------------------------------------------

Now each daemon knows in which directory to run, and on which tcp port to listen. A daemon is a resource in the Shinken architecture. Such resources must be declared in the global configuration (where the Arbiter is) for them to be utilized.

The global configuration file is:  **/usr/local/shinken/etc/shinken-specific.cfg/**

The daemon declarations are quite simple: each daemon is represented by an object. The information contained in the daemon object are network parameters about how its resources should be treated (is it a spare, ...).

Each objects type corresponds to a daemon:
  * arbiter
  * scheduler
  * poller
  * reactionner
  * broker
  * receiver

The names were chosen to understand their roles more easily. :)

They have these parameters in common:
  * \*_name: name of the resource
  * address: IP or DNS address to connect to the daemon
  * port: I think you can find it on your own by now :)
  * [spare]: 1 or 0, is a spare or not. :ref:`See advanced features for this <advanced_features>`.
  * [realm]: realm membership :ref:`See advanced features for this <advanced_features>`.
  * [manage_sub_realms]: manage or not sub realms. :ref:`See advanced features for this <advanced_features>`.
  * [modules]: modules used by the daemon. See below.



special parameters 
~~~~~~~~~~~~~~~~~~~

Some daemons have special parameters:

For the arbiter:
  * host_name: hostname of the server where the arbiter is installed. It's mandatory for a high availability environment (2 arbiters or more).
For pollers:
  * poller_tags: "tags" that the poller manages. :ref:`See advanced features for this`.



module objects 
***************

All daemons can use modules. In the brokers case, they are mandatory for it to actually accomplish a task.

Modules have some common properties:
  * module_name: module name called by the resource.
  * module_type: module type of the module. It's a fixed value given by the module.
  * other options: each module can have specific parameters. See the respective module documentation to learn more about them.

Module references, :ref:`list of overall modules <the_shinken_architecture>`:
  * Arbiter modules
  * :ref:`Scheduler modules <distributed_retention_modules>`
  * :ref:`Broker modules <the_broker_modules>`
  * Receiver modules
  * Pollers modules
  * Reactionner modules


Configuration example 
~~~~~~~~~~~~~~~~~~~~~~

Here is an example of a simple configuration (which you already used without knowing it during the 10min installation tutorial). It has been kept to the strict minimum, with only one daemon for each type. There is no load distribution or high availability, but you'll get the picture more easily.

Here, we have a server named server-1 that has 192.168.0.1 as its IP address:

::

  define arbiter{
       arbiter_name  arbiter-1
       host_name     server-1
       address       192.168.0.1
       port          7770
       spare         0
  }
  
  define scheduler{
       scheduler_name	scheduler-1
       address	        192.168.0.1
       port	        7768
       spare	        0
  }
  
  define reactionner{
       reactionner_name	    reactionner-1
       address	            192.168.0.1
       port	            7769
       spare	            0
  }
  
  define poller{
       poller_name     poller-1
       address         192.168.0.1
       port            7771
       spare           0
  }
  
  define broker{
       broker_name	broker-1
       address	        192.168.0.1
       port	        7772
       spare	        0
       modules          Status-Dat,Simple-log
  }
  
  define module{
       module_name      Simple-log
       module_type      simple_log
       path             /usr/local/shinken/var/shinken.log
  }
  
  define module{
       module_name              Status-Dat
       module_type              status_dat
       status_file              /usr/local/shinken/var/status.data
       object_cache_file        /usr/local/shinken/var/objects.cache
       status_update_interval   15 ; update status.dat every 15s
  }
  


See? That was easy. And don't worry about forgetting one of them: if there is a missing daemon type, Shinken automatically adds one locally with a default address/port configuration.



Removing unused configurations 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


The sample shinken-specific.cfg file has all possible modules in addition to the basic daemon declarations.

  - Backup your shinken-specific.cfg file.
  - Delete all unused modules from your configuration file
    - Ex. If you do not use the openldap module, delete it from the file

This will make any warnings or errors that show up in your log files more pertinent. This is because the modules, if declared will get loadedup even if they are not use in your Modules declaration of your daemons.

If you ever lose your shinken-specific.cfg, you can simply go to the shinken github repository and download the file.



launch all daemons 
~~~~~~~~~~~~~~~~~~~

To launch daemons, simply type:

::

  daemon_path -d -c daemon_configuration.ini 


The command lines arguments are:
  * -c, --config: Config file.
  * -d, --daemon: Run in daemon mode
  * -r, --replace: Replace previous running scheduler
  * -h, --help: Print detailed help screen
  * --debug: path of the debug file

So a standard launch of the resources looks like:

::

  /usr/local/shinken/bin/shinken-scheduler -d -c /usr/local/shinken/etc/schedulerd.ini
  /usr/local/shinken/bin/shinken-poller -d -c /usr/local/shinken/etc/pollerd.ini
  /usr/local/shinken/bin/shinken-reactionner -d -c /usr/local/shinken/etc/reactionnerd.ini
  /usr/local/shinken/bin/shinken-broker -d -c /usr/local/shinken/etc/brokerd.ini

Now we can start the arbiter with the global configuration:

::

  #First we should check the configuration for errors
  python bin/shinken-arbiter -v -c etc/nagios.cfg -c etc/shinken-specific.cfg
  
  #then, we can really launch it
  python bin/shinken-arbiter -d -c etc/nagios.cfg -c etc/shinken-specific.cfg


Now, you've got the same thing you had when you launched bin/launch_all.sh script 8-) (but now you know what you're doing)



What next 
----------


You are ready to continue to the next section, :ref:`get DATA IN Shinken <#Getting data in Shinken>`.

If you feel in the mood for testing even more shinken features, now would be the time to look at :ref:`advanced_features <advanced_features>` to play with distributed and high availability architectures!

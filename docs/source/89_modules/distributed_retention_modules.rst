.. _distributed_retention_modules:



The distributed retention modules 
----------------------------------

The high availability allow the Arbiter to send a configuration to a spare scheduler, but a spare scheduler does not have any saved states for hosts and services. It will have to recheck them all. It's better to use a distributed retention module so spares will have all the information they need to start with an accurate picture of the current states and scheduling :)



Non distributed retention modules 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


If you are just running tests on a single server, use the pickle or memcache retention modules You can also use MongoDB if you already have it installed for use with the WebUI.



MongoDB 
~~~~~~~~


MongoDB is a scalable, high-performance, open source NoSQL database written in C++.

Step 1: Install MongoDB:

We will use mongodb package from 10gen repository, so we start by adding it in apt sources list:
  
::

  echo 'deb http://downloads-distro.mongodb.org/repo/debian-sysvinit dist 10gen' > /etc/apt/sources.list.d/10gen.list
  apt-get update
  
And we install it:
  
::

  apt-get install mongodb-10gen
  
And we install pymongo, the python interface to MongoDB, with easy_install to avoid packages versions problems (like here `forums.monitoring-fr.org/index.php?topic=5205.0`_):
  
::

  apt-get remove python-pymongo
  easy_install pymongo
  
And finally we start MongoDB :
  
::

  /etc/init.d/mongodb start
  
Step 2: define a mongodb_retention module in your shinken-specific.cfg file:

  
::

  define module {
    module_name MongodbRetention
    module_type mongodb_retention
    uri mongodb://localhost/?safe=true
    database shinken
  }
  
Step 3: Declare a retention module for your scheduler(s) :)

Example:
  
::

  #The scheduler is a "Host manager". It get hosts and theirs
  #services. It scheduler checks for them.
  define scheduler{
       scheduler_name   scheduler-1   ; just the name
       address  localhost             ; ip or dns address of the daemon
       port     7768                  ; tcp port of the daemon
  
       #optionnal: modules for things as retention
       modules    MongodbRetention
       }
  
Step 4: Restart the Arbiter, and your Scheduler will now save its state between restarts. :)



Memcached 
~~~~~~~~~~

Memcached is a distributed memory resident key/value server. It's very easy to install:
  
::

  sudo apt-get install memcached 
  sudo /etc/init.d/memcached start
  
The shinken module also needs the python-memcache package to talk to this server.
  
::

  sudo apt-get install python-memcache
  
To use it, 

Step 1: define a memcache_retention module in your shinken-specific.cfg file:

  
::

  define module{
       module_name      MemcacheRetention
       module_type      memcache_retention
       server           127.0.0.1
       port             11211
  }
  
Step 2: Declare a retention module for your scheduler(s) :)

Example:

  
::

  define scheduler{
       scheduler_name   scheduler-1   ; just the name
       address  localhost             ; ip or dns address of the daemon
       port     7768                  ; tcp port of the daemon
  
       #optional: modules for things as retention
       modules    MemcacheRetention
       }
  
Step 3: Restart the Arbiter, and your Scheduler will now save its state between restarts. :)




Redis 
~~~~~~

Redis is a distributed key/value server (on disk and in-memory). It's very easy to install:
  
::

  sudo apt-get install redis-server
  sudo /etc/init.d/redis-server start
  
The shinken module also need the python-redis package to talk to this server.
  
::

  sudo apt-get install python-redis
  
Step 1: define a redis_retention module in your shinken-specific.cfg file:

  
::

  define module{
       module_name      RedisRetention
       module_type      redis_retention
       server           127.0.0.1
  }
  
Step 2: Declare a retention module for your scheduler(s) :)

Example:
  
::

  #The scheduler is a "Host manager". It get hosts and theirs
  #services. It scheduler checks for them.
  define scheduler{
       scheduler_name   scheduler-1   ; just the name
       address  localhost             ; ip or dns address of the daemon
       port     7768                  ; tcp port of the daemon
  
       #optionnal: modules for things as retention
       modules    RedisRetention
       }
  
Step 3: Restart the Arbiter, and your Scheduler will now save its state between restarts. :)
.. _forums.monitoring-fr.org/index.php?topic=5205.0: http://forums.monitoring-fr.org/index.php?topic=5205.0
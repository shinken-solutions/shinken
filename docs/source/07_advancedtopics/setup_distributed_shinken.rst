.. _setup_distributed_shinken:

==================================
Shinken's distributed architecture
==================================


Shinken's distributed architecture for load balancing 
------------------------------------------------------


The load balancing feature is very easy to obtain with Shinken. If I say that the project's name comes from it you should believe me :)

If you use the distributed architecture for load balancing, know that load is typically present in 2 processes:
  * pollers: they launch checks, they use a lot of CPU resources
  * schedulers: they schedule, potentially lots of checks
For both, a limit of 150000 checks/5min is a reasonable goal on an average server(4 cores\@3Ghz). Scaling can be achieved horizontally by simply adding more servers and declaring them as pollers or schedulers.

.. tip::  The scheduler is NOT a multi-threaded process, so even if you add cores to your server, it won't change it's performances.

There are mainly two cases where load is a problem:
  * using plugins  that require lots of processing (check_esx3.pl is a good example)
  * scheduling a very large number of checks (> 150000 checks in 5 minutes).

In the first case, you need to add more pollers. In the second, you need to add more schedulers. In this last case, you should also consider adding more pollers (more checks = more pollers) but that can be determined by the load observed on your poller(s).

From now, we will focus on the first case, typically installations have less than 150K checks in 5 minutes, and will only need to scale pollers, not schedulers.




Setup a load balancing architecture with some pollers 
------------------------------------------------------




Install the poller on the new server 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


But I already hear you asking "How to add new satellites?". That's very simple: **you start by installing the application on a new server like you did in the 10 min starting tutorial but you can pass the discovery, the webUI and skip the /etc/init.d/shinken script (or Windows services)**.

Let say that this new server is called server2 and has the IP 192.168.0.2 and the "master" is called server1 with 192.168.0.1 as its IP.

.. tip::  You need to have all plugins you use in server1 also installed on server2, this should already done if you followed the 10 min tutorial.

On server2, you just need to start the poller service, not the whole Shinken stack.
  
::

  
   On ubuntu/debian:
  update-rc.d shinken-poller default
   On RedHat/Centos:
  chkconfig --add shinken-poller
  chkconfig shinken-poller on
  
Then start it:
  
::

  
  sudo /etc/init.d/shinken-poller start


.. warning::  DO NOT START the arbiter on the server2 for load balancing purpose. It can be done for high availability. Unless you know what you are doing, don't start the arbiter process!^_^



Declare the new poller on the main configuration file 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


Ok, now you have a brand new poller declared on your new server, server2. **But server1 needs to know that it must give work to it. This is done by declaring the new poller in the shinken-specific.cfg file.**

Edit your /etc/shinken-specific.cfg file (or c:\shinken\etc\shinken-specific.cfg under Windows) and define your new poller under the existing poller-1 definition (on server1):

::
  
  #Pollers launch checks                                                                                                                                                                                          
  define poller{
       poller_name      poller-2
       address          server2
       port             7771
  }


Be sure to have also those lines: 

::

  define scheduler{
       scheduler_name scheduler-1 ; just the name
       address  192.168.0.1           ; ip or dns address of the daemon
       port     7768                  ; tcp port of the daemon 
       
**The address has to be 192.168.0.1 or server1 but not localhost!**

.. important::  Check that the line named host in the scheduler.ini is 0.0.0.0 in order to listen on all interfaces.

When it's done, restart your arbiter:
  
::

  
  Under Linux:
  sudo /etc/init.d/shinken-arbiter restart
  Under Windows:
  net stop shinken-arbiter
  net start shinken-arbiter


It's done! You can look at the global shinken.log file (should be under /var/lib/shinken/shinken.log or c:\shinken\var\shinken.log) that the new poller is started and can reach scheduler-1. 
So look for lines like:
  
::

  
  [All] poller satellite order: poller-2 (spare:False), poller-1 (spare:False),
  [All] Trying to send configuration to poller poller-2
  [All] Dispatch OK of for configuration 0 to poller poller-2



You can also look at the poller logs on server2.
You may have lines like that:
  
::

  
  Waiting for initial configuration
  [poller-2] Init de connection with scheduler-1 at PYROLOC://192.168.0.1:7768/Checks
  [poller-2] Connexion OK with scheduler scheduler-1
  We have our schedulers: {0: {'wait_homerun': {}, 'name': u'scheduler-1', 'uri': u'PYROLOC://192.168.0.1:7768/Checks', 'actions': {}, 'instance_id': 0, 'running_id': '1312996582.0', 'address': u'192.168.0.1', 'active': True, 'port': 7768, 'con': <DynamicProxy for PYROLOC://192.168.0.1:7768/Checks>}}
  I correctly loaded the modules: []
  [poller-2] Allocating new fork Worker: 0

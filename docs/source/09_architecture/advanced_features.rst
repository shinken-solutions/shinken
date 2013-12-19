.. _advanced_features:




Advanced architectures 
-----------------------

Shinken has got some cool features in term of configuration management or performance, but it's true added value is in its architecture. It's been designed to achieve easy distributed architecture and high availability.



= Distributed architecture 
***************************

The load balancing feature is very easy to obtain with Shinken. If I say that the project's name comes from it you should believe me :-)

In fact the load is present in 2 major places:
  * pollers: they launch checks, they use a lot of resources
  * schedulers: they schedule, potentially lots of checks
For both, a limit of 150000 checks/5min is a reasonable goal on an average server(4 cores@3Ghz). But remember that is can be multiplied as much as you wish, just by adding another server.

There are 2 cases:
  * checks that ask for a lot of performance (perl or shell scripts for example)
  * a lot of scheduling (> 150000 checks in 5 minutes).
In the first case, you need to add more pollers. In the second, you need to add more schedulers. In this last case, you should also add more pollers (more launch need more pollers) but that's not compulsory.

But I already ear you asking "How to add new satellites?". That's very simple: You start by installing the application on a new server (don't forget the sinken user + application files). Let say that this new server is called server-2 and has the IP 192.168.0.2 (remember that the "master" is called server-1 with 192.168.0.1 as IP). 

Now you need to launch the scheduler and pollers (or just one of them if you want):

  
::

  
  /etc/init.d/shinken-scheduler start
  /etc/init.d/shinken-poller start


It looks like the launch in the master server? Yes, it's the same :-)

Here you just launch the daemons, now you need to declare them in the shinken-specific.cfg file on the master server (the one with the arbiter daemon). You need to add new entries for these satellites:
   
  
::

  
  
  define scheduler{
  
::

       scheduler_name	scheduler-2
       address	192.168.0.2
       port	7768
       spare	0
       }
  
  define poller{
  
::

       poller_name     poller-2
       address  192.168.0.2
       port     7771
       spare    0
  }


The differences with scheduler-1 and poller-1 are just the names and the address. Yep, that's all :-)

Now you can restart the arbiter, and you're done, the hosts will be distributed in both schedulers, and the checks will be distributed to all pollers. Congrats :)



High availability architecture 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Ok, a server can crash or a network can go down. The high availability is not a useless feature, you know?

With shinken, making a high availability architecture is very easy. Just as easy as the load balancing feature :)

You saw how to add new scheduler/poller satellites. For the HA it's quite the same. You just need to add new satellites in the same way you just did, and define them as "spares". You can (should) do the same for all the satellites (a new arbiter, reactionner and broker) for a whole HA architecture.

We keep the load balancing previous installation and we add a new server (if you do not need load balancing, just take the previous server). So like the previous case, you need to install the daemons and launch them.

  
::

  
  /etc/init.d/shinken-scheduler start
  /etc/init.d/shinken-poller start


Nothing new here. 

And we need to declare the new satellites in the shinken-specific.cfg file near the arbiter:
  
::

  
  
  define scheduler{
  
::

       scheduler_name	scheduler-3
       address	192.168.0.3
       port	7768
       spare	1
       }
  
  define poller{
  
::

       poller_name     poller-3
       address  192.168.0.3
       port     7771
       spare    1
  }


Do you see a difference here? Aside from the name and address, there is a new parameter: spare. From the daemon point of view, they do not know if they are a spare or not. That's the arbiter that says what they are.

You just need to restart the arbiter and you've got HA for the schedulers/pollers :)

..

Really?

Yes indeed, that's all. Until one of the scheduler/poller fall, these two new daemons will just wait. If anyone falls, the spare daemon will take the configuration and start to work.

You should do the same for arbiter, reactionner and broker. Just install them in the server-3 and declare them in the shinken-specific.cfg file with a spare parameter. Now you've got a full HA architecture (and with load balancing if you keep the server-2 :) ).

.. note::  Here you have high availability, but if a scheduler dies, the spare takes the configuration, but not the saved states. So it will have to reschedule all checks, and current states will be PENDING. To avoid this, you can link :ref:`distributed retention modules` <distributed retention modules> such as memcache to your schedulers



Mixed Architecture (poller GNU/Linux and Windows or LAN/DMZ) 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

There can be as many pollers as you want. And Shinken runs under a lot of systems, like GNU/Linux and Windows. It could be useful to make windows hosts checks by a windows pollers (by a server IN the domain), and all the others by a GNU/Linux one.

And in fact you can, and again it's quite easy :)
All pollers connect to all schedulers, so we must have a way to distinguish 'windows' checks from 'gnu/linux' ones.

The poller_tag/poller_tags parameter is useful here. It can be applied on the following objects:
 * pollers
 * commands 
 * services
 * hosts

It's quite simple: you 'tag' objects, and the pollers have got tags too. You've got an implicit inheritance between hosts->services->commands. If a command doesn't have a poller_tag, it will take the one from the service. And if this service doesn't have one neither, it will take the tag from its host.

Let take an example with a 'windows' tag:

  
::

  
  define command{
  
::

   command_name   
   command_line   c:\shinken\libexec\check_wmi.exe -H $HOSTADRESS$ -r $ARG1$
   poller_tag     Windows
  }
  
  define poller{
  
::

   poller_name  poller-windows
   address      192.168.0.4
   port     7771
   spare    0
   poller_tags  Windows,DMZ
  }


And the magic is here: all checks launched with this command will be taken by the poller-windows (or another that has such a tag). A poller with no tags will only take 'untagged' commands.

It also works with a LAN/DMZ network. If you do not want to open all monitoring ports from the LAN to the DMZ server, you just need to install a poller with the 'DMZ' tag in the DMZ and then add it to all hosts (or services) in the DMZ. They will be taken by this poller and you just need to open the port to this poller from the LAN. Your network admins will be happier :)

  
::

  
  define host{
  
::

   host_name  server-DMZ-1
   [...]
   poller_tag DMZ
   [...]
  }
  
  define service{
  
::

   service_description  CPU
   host_name  server-DMZ-2
   [...]
   poller_tag DMZ
   [...]
  }


And that's all :)



Multi customers and/or sites: REALMS 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The shinken's architecture like we saw allows us to have a unique administration and data location. All pollers the hosts are cut and sent to schedulers, and the pollers take jobs from all schedulers. Every one is happy.

Every one? In fact no. If an administrator got a continental distributed architecture he can have serious problems. If the architecture is common to multile customers network, a customer A scheduler can have a customer B poller that asks him jobs. It's not a good solution. Even with distributed network, distant pollers should not ask jobs to schedulers in the other continent, it's not network efficient.

That is where the site/customers management is useful. In Shinken, it's managed by the **realms**.

A realm is a group of resources that will manage hosts or hostgroups. Such a link will be unique: a host cannot be in multiple realms. If you put an hostgroup in a realm, all hosts in this group will be in the realm (unless a host already has the realm set, the host value will be taken).

A realm is:
 * at least a scheduler
 * at least a poller
 * can have a reactionner
 * can have a broker
In a realm, all realm pollers will take all realm schedulers jobs.

.. important::  Very important: there is only ONE arbiter (and a spare of couse) for ALL realms. The arbiter manages all realms and all that is inside.



Sub-realms 
~~~~~~~~~~~

A realm can have sub-realms. It doesnt change anything for schedulers, but it can be useful for other satellites and spares. Reactionners and brokers are linked to a realm, but they can take jobs from all sub-realms too. This way you can have less reactionners and brokers (like we soon will see).

The fact that reactionners/brokers (and in fact pollers too) can take jobs from sub-schedulers is decided by the presence of the manage_sub_realms parameter. For pollers the default value is 0, but it's 1 for reactionners/brokers.

.. important::  WARNING: having multiple brokers for one scheduler is not a good idea: after the information is send, it's deleted from the scheduler, so each brokers will only got partial data!





An example ? 
~~~~~~~~~~~~~

To make it simple: you put hosts and/or hostgroups in a realm. This last one is to be considered as a resources pool. You don't need to touch the host/hostgroup definition if you need more/less performances in the realm or if you want to add a new satellites (a new reactionner for example).

Realms are a way to manage resources. They are the smaller clouds in your global cloud infrastructure :)

If you do not need this feature, that's not a problem, it's optional. There will be a default realm created and every one will be put into.

It's the same for hosts that don't have a realm configured: they will be put in the realm that has the "default" parameter.



Picture example 
~~~~~~~~~~~~~~~~

Diagrams are good :)

Let's take two examples of distributed architectures around the world. In the first case, the administrator don't want to share resources between realms. They are distinct. In the second, the reactionners and brokers are shared with all realms (so all notifications are send from a unique place, and so is all data).

Here is the isolated one:



.. image:: /_static/images/official/images/shinken-architecture-isolated-realms.png?640
   :scale: 90 %



And a more common way of sharing reactionner/broker:



.. image:: /_static/images/official/images/shinken-architecture-global-realm.png?640
   :scale: 90 %



Like you can see, all elements are in a unique realm. That's the sub-realm functionality used for reactionner/broker.



Configuration of the realms 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Here is the configuration for the shared architecture:
  
::

  
  define realm {
  
::

   realm_name       All
   realm_members    Europe,US,Asia
   default          1    ;Is the default realm. Should be unique!       
  }
  define realm{
  
::

   realm_name       Europe
   realm_members    Paris   ;This realm is IN Europe
  }


An now the satellites:
  
::

  
  define scheduler{
  
::

   scheduler_name       scheduler_Paris
   realm                Paris             ;It will only manage Paris hosts
  }
  define reactionner{
  
::

   reactionner_name     reactionner-master
   realm                All                ;Will reach ALL schedulers
  }

And in host/hostgroup definition:
  
::

  
  define host{
  
::

   host_name         server-paris
   realm             Paris         ;Will be put in the Paris realm
   [...]
  }
  
  define hostgroups{
  
::

   hostgroup_name		linux-servers
   alias			Linux Servers
   members			srv1,srv2
   realm                        Europe       ;Will be put in the Europe realm
  }




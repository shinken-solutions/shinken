.. _setup_dependencies_in_shinken:

**Setup Network and logical dependencies in Shinken**



Network dependencies 
---------------------




What are network dependencies ? 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


If you've ever worked in tech support, you've undoubtedly had users tell you "the Internet is down". As a techie, you're pretty sure that no one pulled the power cord from the Internet. Something must be going wrong somewhere between the user's chair and the Internet.

Assuming its a technical problem, you begin to search for the root problem. Perhaps the user's computer is turned off, maybe their network cable is unplugged, or perhaps your organization's core router just took a dive. Whatever the problem might be, one thing is most certain - the Internet isn't down. It just happens to be unreachable for that user.

Shinken is able to determine whether the hosts you're monitoring are in a DOWN or UNREACHABLE state. To do this simply define a check_command for your host. These are very different (although related) states and can help you quickly determine the root cause of network problems. Such dependencies are also possible for applications problems, like your web app is not available because your database is down.



Example Network 
~~~~~~~~~~~~~~~~


Take a look at the simple network diagram below. For this example, lets assume you're monitoring all the hosts (server, routers, switches, etc) that are pictured by defining a check_command for each host. Shinken is installed and running on the Shinken host.
**If you have not defined a check_command for your host, Shinken will assume that the host is always UP. Meaning that the logic described will NOT kick-in.** 


.. image:: /_static/images///official/images/reachability1.png
   :scale: 90 %





Defining Parent/Child Relationships 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


The network dependencies will be named "parent/child" relationship. The parent is the switch for example, and the child will be the server.

In order for Shinken to be able to distinguish between DOWN and UNREACHABLE states for the hosts that are being monitored, you'll first need to tell Shinken how those hosts are connected to each other - from the standpoint of the Shinken daemon. To do this, trace the path that a data packet would take from the Shinken daemon to each individual host. Each switch, router, and server the packet encounters or passes through is considered a "hop" and will require that you define a parent/child host relationship in Shinken. Here's what the host parent/child relationships looks like from the viewpoint of Shinken:



.. image:: /_static/images///official/images/reachability2.png
   :scale: 90 %



Now that you know what the parent/child relationships look like for hosts that are being monitored, how do you configure Shinken to reflect them? The parents directive in your :ref:`host definitions <configuringshinken-objectdefinitions#configuringshinken-objectdefinitions-host>` allows you to do this. Here's what the (abbreviated) host definitions with parent/child relationships would look like for this example:

  
  
::

  define host{
    host_name    Shinken ; <-- The local host has no parent - it is the topmost host
  }
  
  define host{
    host_name    Switch1
    parents    Shinken 
  }
  
  define host{
    host_name    Web
    parents    Switch1
  }
  
  define host{
    host_name    FTP
    parents    Switch1
  }
  
  define host{
    host_name    Router1
    parents    Switch1
  }
  
  define host{
    host_name    Switch2
    parents    Router1
  }
  
  define host{
    host_name    Wkstn1
    parents    Switch2
  }
  
  define host{
    host_name    HPLJ2605
    parents    Switch2
  }
  
  define host{
    host_name    Router2
    parents    Router1
  }
  
  define host{
    host_name    somewebsite.com
    parents    Router2
  }
  
  
So basicaly: **in your "child", you declare who is your parent(s)**.



Reachability Logic in Action 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


Now that you're configured Shinken with the proper parent/child relationships for your hosts, let's see what happen when problems arise. Assume that two hosts - Web and Router1 - go offline...



.. image:: /_static/images///official/images/reachability3.png
   :scale: 90 %



When hosts change state (i.e. from UP to DOWN), the host reachability logic in Shinken kicks in. The reachability logic will initiate parallel checks of the parents and children of whatever hosts change state. This allows Shinken to quickly determine the current status of your network infrastructure when changes occur. During this additonal check time, the notification for the web and router1 hosts are blocked because we don't know yet **WHO** is the root problem.



.. image:: /_static/images///official/images/reachability4.png
   :scale: 90 %



In this example, Shinken will determine that Web and Router1 are both in DOWN states because the "path" to those hosts is not being blocked (switch1 is still alive), and so **it will allow web and router1 notifications to be sent**.

Shinken will determine that all the hosts "beneath" Router1 are all in an UNREACHABLE state because Shinken can't reach them. Router1 is DOWN and is blocking the path to those other hosts. Those hosts might be running fine, or they might be offline - Shinken doesn't know because it can't reach them. Hence Shinken considers them to be UNREACHABLE instead of DOWN, and won't send notifications about them. Such hosts and services beneath router1 are the **impacts** of the **root problem** "router1"



What about more than one parent for an host? 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


You see that there is a 's' in parents. Because you can define as many parent as you want for an host (like if you got an active/passive switch setup). **The host will be UNREACHABLE only, and only if all it's parents are down or unreachable**. If one is still alive, it will be down. See this as a big *OR* rule.



UNREACHABLE States and Notifications 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


One important point to remember is **Shinken only notifies about root problems**. If we allow it to notify for root problems AND impacts you will receive too many notifications to quickly find and solve the root problems. That's why Shinken will notify contacts about DOWN hosts, but not for UNREACHABLE ones.



What about notification about services of a down or unreachable hosts? 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


You will not be notified about all critical or warning errors on a down or unreachable host, because such service states are the impacts of the host root problem. You don't have to configure anything, Shinken will suppress these useless notifications automatically. The official documentation provides more information on  :ref:`how notifications work <thebasics-notifications>`.



Logical dependencies 
---------------------


Network is not the only element that can have problems. Applications can too.

Service and host dependencies are an advanced feature of Shinken that allows you to control the behavior of hosts and services based on the status of one or more other hosts or services. This section explains how dependencies work, along with the differences between host and service dependencies.

Let's starts with service dependencies. We can take the sample of a Web application service that will depend upon a database service. If the database is failed, it's useless to notify about the web application one, because you already know it's failed. **So Shinken will notify you about your root problem, the database failed, and not about all its impacts, here your web application**.

With only useful notifications, you will be able to find and fix them quickly and not take one hour to find the root problem in your mails.



Service Dependencies Overview 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


There are a few things you should know about service dependencies:

  * A service can be dependent on one or more other services
  * A service can be dependent on services which are not associated with the same host
  * Advanced service dependencies can be used to cause service check execution and service notifications to be suppressed under different circumstances (OK, WARNING, UNKNOWN, and/or CRITICAL states)
  * Advanced service dependencies might only be valid during specific :ref:`timeperiods <thebasics-timeperiods>`



Defining simple advanced dependencies 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


Define a service dependency is quite easy in fact. All you need is to define in your Web application service that it is dependent upon the database service. 

  
 
::

  define service{
    host_name              srv-web
    service_description    Http
    service_dependencies   srv-db,mysql
  }
  
  
  
So here the web service Http on the host srv-web will depend upon the database service mysql on the host srv-db. If the mysql service has failed, there will be no notifications for service srv-web. If Shinken gets an error state check on the Http service, it will raised a mysql check and suppress the http notification until it knows if the Http service is a root problem or an impact.



Dependencies inheritance 
~~~~~~~~~~~~~~~~~~~~~~~~~


By default, service dependencies are inherited. Let take an example where the mysql service depend upon a nfs service.

  
::

  define service{
    host_name              srv-bd
    service_description    mysql
    service_dependencies   srv-file,nfs,srv-dns,dns
  }
  
  
If Shinken find a problem on Http, it will raise a check on mysql. If this one got a problem too, it will raise a check on the nfs service and srv-dns dns service. If one of these has got a problem too, it will be tagged as the root problem, and will raise a notification for the nfs administrator or dns administrator. If these are ok (dns and nfs), the notification will be sentfor the mysql admin.



And with the host down/unreachable logic? 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


The dependency logic is done in parallel to the network one. If one logic say it's an impact, then it will tag the problem state as an impact. For example, if the srv-db is down a warning/critical alert on the Http service will be set as an **impact**, like the mysql one, and the root problem will be the srv-bd host that will raise only one notification, a host problem.



Advanced dependencies 
~~~~~~~~~~~~~~~~~~~~~~


For timeperiod limited dependencies or for specific states activation (like for critical states but not warning), please consult the :ref:`advanced dependencies <setup_advanced_dependencies_in_shinken>` documentation.

.. _setup_dmz_monitoring:



Monitoring a DMZ  
================


There is two ways for monitoring a DMZ network:
  * got a poller on the LAN, and launch check from it, so the firewall should allow monitoring traffic (like nrpe, snmp, etc)
  * got a poller on the DMZ, so only the Shinken communications should be open through the firewall

If you can take the first, use it :)

If you can't because your security manager is not happy about it, you should put a poller in the DMZ. So look at the page :ref:`setup_distributed_shinken` first, because you will need a distributed architecture.

Pollers a "dumb" things. They look for jobs to all scheduler (of their realm, if you don't know what is it from now, it's not important). So if you just put a poller in the DMZ network aside another in the LAN, some checks for the dmz will be take by the LAN one, and some for the lan will be take by the DMZ one. It's not a good thing of course :)



Tag your hosts and pollers for being "in the DMZ" 
--------------------------------------------------


So we will need to "tag" checks, so they will be able to run **only** in the dmz poller, or the lan one.

This tag is done with the **poller_tag** paramter. It can be applied on the following objects:
 * pollers
 * commands 
 * services
 * hosts

It's quite simple: you 'tag' objects, and the pollers have got tags too. You've got an implicit inheritance in this order: hosts->services->commands. If a command doesn't have a poller_tag, it will take the one from the service. And if this service doesn't have one neither, it will take the tag from its host.

You just need to install a poller with the 'DMZ' tag in the DMZ and then add it to all hosts (or services) in the DMZ. They will be taken by this poller and you just need to open the port to this poller fom the LAN. Your network admins will be happier :)



Configuration part 
-------------------


So you need to declare in the /etc/shinken.shinken-specific.cfg (or c:\shinken\etc\shinen-specific.cfg):
 
::
  
  define poller{
  
    poller_name    poller-DMZ
    address        server-dmz
    port           7771
    poller_tags    DMZ
  }


And "tag" some hosts and/or some services. 

 
::
  
  define host{

   host_name  server-DMZ-1
   [...]
   poller_tag DMZ
   [...]
  }


And that's all :)

All checks for the server-DMZ-1 will be launch from the poller-dmz, and only from it (unless there is another poller in the DMZ with the same tag). you are sure that this check won't be launched from the pollers within the LAN, because untagged pollers can't take tagged checks.

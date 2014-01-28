.. _setup_mix_windows_and_linux_polling:



Mixed GNU/linux AND Windows pollers 
====================================


There can be as many pollers as you want. And Shinken runs under a lot of systems, like GNU/Linux and Windows. It could be useful to make windows hosts checks :ref:`using windows pollers (by a server IN the domain) <configure_check_wmi_plus_onwindows>`, and all the others by a GNU/Linux one (like all pure network based checks).

And in fact you can, and again it's quite easy :)
Its important to remember that all pollers connect to all schedulers, so we must have a way to distinguish 'windows' checks from 'gnu/linux' ones.

The poller_tag/poller_tags parameter is useful here. It can be applied on the following objects:
 * pollers
 * commands 
 * services
 * hosts

It's quite simple: you 'tag' objects, and the pollers have got tags too. You've got an implicit inheritance between hosts->services->commands. If a command doesn't have a poller_tag, it will take the one from the service. And if this service doesn't have one neither, it will take the tag from its host. It's all like the "DMZ" case, but here apply for another purpose.

Let take an example with a 'windows' tag:

 
::
  
  define command{
  
   command_name   CheckWMI
   command_line   c:\shinken\libexec\check_wmi.exe -H $HOSTADRESS$ -r $ARG1$
   poller_tag     Windows
  }
  

  define poller{
  
   poller_name  poller-windows
   address      192.168.0.4
   port     7771
   poller_tags  Windows
  }


And the magic is here: all checks launched with this command will be taken by the poller-windows (or another that has such a tag). A poller with no tags will only take 'untagged' commands.

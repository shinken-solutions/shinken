.. _command:
.. _configuringshinken/configobjects/command:



===================
Command Definition 
===================




Description 
============


A command definition is just that. It defines a command. Commands that can be defined include service checks, service notifications, service event handlers, host checks, host notifications, and host event handlers. Command definitions can contain :ref:`macros <thebasics-macros>`, but you must make sure that you include only those macros that are “valid" for the circumstances when the command will be used. More information on what macros are available and when they are “valid" can be found :ref:`here <thebasics-macros>`. The different arguments to a command definition are outlined below.

.. tip::  If, you need to have the '$' character in one of your command (and not referring to a macro), please put "$$" instead. Shinken will replace it well



Definition Format 
==================


Bold directives are required, while the others are optional.



================ ==================
define command{                    
**command_name** ***command_name***
**command_line** ***command_line***
poller_tag       *poller_tag*      
}                                  
================ ==================



Example Definition 
===================


  
::

  	  define command{
            command_name   check_pop
            command_line   /usr/local/shinken/libexec/check_pop -H $HOSTADDRESS$    
  	  }
  


Directive Descriptions 
=======================


   command_name
  
This directive is the short name used to identify the command. It is referenced in :ref:`contact <configuringshinken/configobjects/contact>`, :ref:`host <configuringshinken/configobjects/host>`, and :ref:`service <configuringshinken/configobjects/service>` definitions (in notification, check, and event handler directives), among other places.

   command_line
  
This directive is used to define what is actually executed by Shinken when the command is used for service or host checks, notifications, or :ref:`event handlers <advancedtopics-eventhandlers>`. Before the command line is executed, all valid :ref:`macros <thebasics-macros>` are replaced with their respective values. See the documentation on macros for determining when you can use different macros. Note that the command line is *not* surrounded in quotes. Also, if you want to pass a dollar sign ($) on the command line, you have to escape it with another dollar sign.

You may not include a **semicolon** (;) in the *command_line* directive, because everything after it will be ignored as a config file comment. You can work around this limitation by setting one of the :ref:`$USER$ <thebasics-macrolist#thebasics-macrolist-user>` macros in your :ref:`resource file <configuringshinken-configmain#configuringshinken-configmain-resource_file>` to a semicolon and then referencing the appropriate $USER$ macro in the *command_line* directive in place of the semicolon.

If you want to pass arguments to commands during runtime, you can use :ref:`$ARGn$ macros <thebasics-macrolist#thebasics-macrolist-arg>` in the *command_line* directive of the command definition and then separate individual arguments from the command name (and from each other) using bang (!) characters in the object definition directive (host check command, service event handler command, etc.) that references the command. More information on how arguments in command definitions are processed during runtime can be found in the documentation on :ref:`macros <thebasics-macros>`.

   poller_tag
  
This directive is used to define the poller_tag of this command. If the host/service that call this command do nto override it with their own poller_tag, it will make this command if used in a check only taken by polelrs that also have this value in their poller_tags parameter.

By default there is no poller_tag, so all untagged pollers can take it.

.. _configobjects/command:

===================
Command Definition
===================


Description
============

A command definition is just that. It defines a command. Commands that can be defined include service checks, service notifications, service event handlers, host checks, host notifications, and host event handlers. Command definitions can contain :ref:`macros <thebasics/macros>`, but you must make sure that you include only those macros that are “valid" for the circumstances when the command will be used. More information on what macros are available and when they are “valid" can be found :ref:`here <thebasics/macros>`. The different arguments to a command definition are outlined below.

.. tip::  If, you need to have the '$' character in one of your command (and not referring to a macro), please put "$$" instead. Shinken will replace it well


Definition Format
==================

Bold directives are required, while the others are optional.

========================= ==================
define command{
**command_name**          ***command_name***
**command_line**          ***command_line***
enable_environment_macros *[0,1]*
poller_tag                *poller_tag*
reactionner_tag           *reactionner_tag*
priority                  *priority*
}
========================= ==================


Example Definition
===================


::

  define command{
      command_name   check_pop
      command_line   /var/lib/shinken/libexec/check_pop -H $HOSTADDRESS$
  }


Directive Descriptions
=======================

command_name
  This directive is the short name used to identify the command. It is referenced in :ref:`contact <configobjects/contact>`, :ref:`host <configobjects/host>`, and :ref:`service <configobjects/service>` definitions (in notification, check, and event handler directives), among other places.

command_line
  This directive is used to define what is actually executed by Shinken when the command is used for service or host checks, notifications, or :ref:`event handlers <advanced/eventhandlers>`. Before the command line is executed, all valid :ref:`macros <thebasics/macros>` are replaced with their respective values. See the documentation on macros for determining when you can use different macros. Note that the command line is *not* surrounded in quotes. Also, if you want to pass a dollar sign ($) on the command line, you have to escape it with another dollar sign.

  You may not include a **semicolon** (;) in the *command_line* directive, because everything after it will be ignored as a config file comment. You can work around this limitation by setting one of the :ref:`$USERn$ <thebasics/macrolist#usern>` macros in your :ref:`resource file <configuration/configmain-advanced#resource_file>` to a semicolon and then referencing the appropriate $USER$ macro in the *command_line* directive in place of the semicolon.

  If you want to pass arguments to commands during runtime, you can use :ref:`$ARGn$ macros <thebasics/macrolist#argn>` in the *command_line* directive of the command definition and then separate individual arguments from the command name (and from each other) using bang (!) characters in the object definition directive (host check command, service event handler command, etc.) that references the command. More information on how arguments in command definitions are processed during runtime can be found in the documentation on :ref:`macros <thebasics/macros>`.

.. _configobjects/command#enable_environment_macros:

enable_environment_macros
  This directive enabbles passing command parameters through the environment. See the global :ref:`enable_environment_macros <configuration/configmain#enable_environment_macros>` for more details. Enabling it on a command rather than globally allows to limit how much commands will receive environment macros. This is the preferred way, as processing environment macros and passing them to the command has a high cost in term of CPU and Memory.

poller_tag
  This directive is used to define the poller_tag of this command. This parameter may be defined, in order of precedence, on a`command`, a `host` or a `service`. If a poller tag is set, only pollers holding the same tag will handle the corresponding action.

  By default there is no poller_tag, so all untagged pollers can take it.

reactionner_tag
  This directive is used to define the reactionner_tag of this command. This parameter may be defined, in order of precedence, on a`command`, a `host` or a `service`. If a reactionner tag is set, only reactionners holding the same tag will handle the corresponding action.

  By default there is no reactionner_tag, so all untagged reactionners can take it.

priority
  This options defines the command's priority regarding checks execution. When a poller or a reactionner is asking for new actions to execute to the scheduler, it will return the highest priority tasks first (the lower the number, the higher the priority). The `priority` parameter may be set, in order of ascending precedence, on a `command`, on a `host` and on a `service`. Priority defaults to `100`.

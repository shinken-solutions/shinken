% shinken-broker(8) Shinken User Manuals
% David Hannequin
% Arthur Gautier
% Michael Leinartas
% December 29, 2011

# NAME

shinken-broker - Shinken broker daemon

# SYNOPSIS

shinken-broker [-dr] [-c *CONFIGFILE*] [--debugfile *DEBUGFILE*]

# DESCRIPTION

Shinken broker daemon.

The shinken-broker's role is to export and manage data from schedulers (such as status).
The management itself is done by modules.

The following management modules are included:
 * export into an NDO (Nagios Data Out) database (MySQL or Oracle backend)
 * export to MERLIN (Module for Effortless Redundancy and Loadbalancing In Nagios) database
   (MySQL backend)
 * service-perfdata export
 * export to CouchDB

Multiple modules can be enabled simultaneously

# OPTIONS

\--version
:   Show version number and exit

-c *CONFIGFILE*, \--config *CONFIGFILE*
:   Config file

-d, \--daemon
:   Run in daemon mode

-r, \--replace
:   Replace previously running broker

-h, \--help
:   Print detailed help screen

\--debugfile *DEBUGFILE*
:   Enable debug logging to *DEBUGFILE*

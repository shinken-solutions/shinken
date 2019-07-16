==============
shinken-broker
==============

---------------------
Shinken broker daemon
---------------------

:Author:            Michael Leinartas,
                    Arthur Gautier,
                    David Hannequin,
                    Thibault Cohen
:Date:              2014-04-24
:Version:           2.0.1
:Manual section:    8
:Manual group:      Shinken commands


SYNOPSIS
========

  **shinken-broker** [-dr] [-c *CONFIGFILE*] [--debugfile *DEBUGFILE*]

DESCRIPTION
===========

Shinken broker daemon.

The **shinken-broker**'s role is to export and manage data from schedulers (such as status). The management itself is done by modules.

The following management modules are included:
export into an NDO (Nagios Data Out) database (MySQL or Oracle backend)
export to MERLIN (Module for Effortless Redundancy and Loadbalancing In Nagios) database (MySQL backend)
service-perfdata export
export to CouchDB

Multiple modules can be enabled simultaneously

OPTIONS
=======

  -c INI-CONFIG-FILE, --config=INI-CONFIG-FILE  Config file
  -d, --daemon                                  Run in daemon mode
  -r, --replace                                 Replace previous running broker
  -h, --help                                    Show this help message
  --version                                     Show program's version number 
  --debugfile=DEBUGFILE                         Enable debug logging to *DEBUGFILE*
  -p PROFILE, --profile=PROFILE                 Dump a profile file. Need the python cProfile library


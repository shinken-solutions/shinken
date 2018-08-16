==============
shinken-poller
==============

---------------------
Shinken poller daemon
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

  **shinken-poller** [-dr] [-c *CONFIGFILE*] [--debugfile *DEBUGFILE*]

DESCRIPTION
===========

Shinken poller daemon.

The **shinken-poller** daemon is in charge of launching plugins as requested by schedulers. When the check is finished it returns the result to the schedulers.

OPTIONS
=======

  -c INI-CONFIG-FILE, --config=INI-CONFIG-FILE  Config file
  -d, --daemon                                  Run in daemon mode
  -r, --replace                                 Replace previous running poller
  -h, --help                                    Show this help message
  --version                                     Show program's version number 
  --debugfile=DEBUGFILE                         Enable debug logging to *DEBUGFILE*
  -p PROFILE, --profile=PROFILE                 Dump a profile file. Need the python cProfile library


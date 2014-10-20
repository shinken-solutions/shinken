=================
shinken-scheduler
=================

------------------------
Shinken scheduler daemon
------------------------

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

  **shinken-scheduler** [-dr] [-c *CONFIGFILE*] [--debugfile *DEBUGFILE*]

DESCRIPTION
===========

Shinken scheduler daemon.

The **shinken-scheduler** manages the dispatching of checks and actions sent to shinken-reactionner and shinken-poller based on configuration sent to it by shinken-arbiter.

OPTIONS
=======

  -c INI-CONFIG-FILE, --config=INI-CONFIG-FILE  Config file
  -d, --daemon                                  Run in daemon mode
  -r, --replace                                 Replace previous running scheduler
  -h, --help                                    Show this help message
  --version                                     Show program's version number 
  --debugfile=DEBUGFILE                         Enable debug logging to *DEBUGFILE*
  -p PROFILE, --profile=PROFILE                 Dump a profile file. Need the python cProfile librairy


===============
shinken-arbiter
===============

----------------------
Shinken arbiter daemon
----------------------

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

  **shinken-arbiter** [-dr] [-c *CONFIGFILE*] [--debugfile *DEBUGFILE*]
  **shinken-arbiter** -v [-c *CONFIGFILE*]

DESCRIPTION
===========

Shinken arbiter daemon

The **shinken-arbiter** daemon reads the configuration, divides it into parts
(N schedulers = N parts), and distributes them to the appropriate Shinken daemons.
Additionally, it manages the high availability features: if a particular daemon dies,
it re-routes the configuration managed by this failed  daemon to the configured spare.
Finally, it receives input from users (such as external commands from nagios.cmd) and
routes them to the appropriate daemon. There can only be one active arbiter in the
architecture.


OPTIONS
=======

  -v, --verify-config                       Verify config file and exit
  -c CONFIGFILE, --config=CONFIGFILE        Config file (your nagios.cfg). Multiple -c can be used, it will be like if all files was just one
  -d, --daemon                              Run in daemon mode
  -r, --replace                             Replace previous running arbiter
  -h, --help                                Show this help message
  --version                                 Show program's version number
  --debugfile=DEBUGFILE                     Enable debug logging to *DEBUGFILE*
  -p PROFILE, --profile=PROFILE             Dump a profile file. Need the python cProfile librairy
  -a ANALYSE, --analyse=ANALYSE             Dump an analyse statistics file, for support
  -m MIGRATE, --migrate=MIGRATE             Migrate the raw configuration read from the arbiter to another module. --> VERY EXPERIMENTAL!
  -n ARB_NAME, --name=ARB_NAME              Give the arbiter name to use. Optionnal, will use the hostaddress if not provide to find it.


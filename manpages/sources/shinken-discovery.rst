=================
shinken-discovery
=================

------------------------
Shinken discovery daemon
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

  **shinken-discovery** [-dr] [-c *CONFIGFILE*] [--debugfile *DEBUGFILE*]

DESCRIPTION
===========

Shinken discovery command.

There are two discovery modules included:

* Standard network discovery which uses the nmap tool
* VMware discovery which uses the check_esx3.pl script and a vcenter installation.

It is best to do the whole discovery in one pass because one module can use data from the other.

OPTIONS
=======

  --version                                 Show program's version number
  -h, --help                                Show this help message
  -c CFG_INPUT, --cfg-input=CFG_INPUT       Discovery configuration file (discovery.cfg)
  -o OUTPUT_DIR, --dir-output=OUTPUT_DIR    Directory output for results
  -w, --overwrite                           Allow overwriting an existing file (disabled by default)
  -r RUNNERS, --runners=RUNNERS             List of runners you allow to run, (like nmap,vsphere)
  -m MACROS, --macros=MACROS                List of macros (like NMAPTARGETS=192.168.0.0/24).
                                            Should be the last argument
  --db=DBMOD                                Optional : Name of the database module to use
  --backend=BACKEND                         Optional : Name of a module that will totally manage
                                            the object writing/update thing. If you don't know what it means, maybe you should not use this option :)
  --modules_path=MODULES_PATH               Optional : Path for the module loading. If you don't know what it means, maybe you should not use this option :)
  --merge                                   Optional : In multiple discovery level, it is the final host name which wins. Make possible merge of multiple IP but same final device

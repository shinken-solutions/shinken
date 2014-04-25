=========
 shinken
=========

---------------------------------
Shinken packs and modules manager
---------------------------------

:Author:            Thibault Cohen <thibault.cohen@savoirfairelinux.com>
:Date:              2014-04-24
:Version:           2.0.1
:Manual section:    8
:Manual group:      Shinken commands


SYNOPSIS
========

  **shinken** [OPTION]... [FILE]

DESCRIPTION
===========

**shinken** is a usefull tool to manage your Shinken packs and modules and.

**shinken** can be used to download packs and modules from http://shinken.io and also to publish yours to http://shinken.io


OPTIONS
=======

  --version             show program's version number and exit
  --proxy=PROXY         Proxy URI. Like http://user:password@proxy-server:3128
  -A API_KEY, --api-key=API_KEY
                        Your API key for uploading the package to the
                        Shinken.io website. If you don't have one, please go
                        to your account page
  -l, --list            List available commands
  --init                Initialize/refill your shinken.ini file (default to
                        /home/titilambert/.shinken.ini)
  -D                    Enable the debug mode
  -c INICONFIG, --config=INICONFIG
                        Path to your shinken.ini file. Default:
                        /home/titilambert/.shinken.ini
  -v                    Be more verbose
  -h, --help            Print help


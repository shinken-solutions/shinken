% shinken-broker(8) Shinken User Manuals
% Arthur Gautier
% September 14, 2011

# NAME

shinken-broker - Shinken broker command.

# SYNOPSIS

shinken-broker  [*options*] ...

# DESCRIPTION

Shinken receiver daemon.

Its role is to get data from schedulers (like status) and manage it (like
storing it in database). The management itself is done by modules.
Different modules exists : export into ndo database (MySQL and Oracle
backend), export to merlin database (MySQL), service-perfdata export and a
couchdb export, or a mix of them (why not?).

# OPTIONS

-c *CONFIGFILE*, \--config *CONFIGFILE*
:   Config file

-d, \--daemon
:   Run in daemon mode.

-h, \--help
:   Print detailed help screen.

\--debug *FILE*
:   Debug File.



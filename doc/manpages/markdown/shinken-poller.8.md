% shinken-poller(8) Shinken User Manuals
% Arthur Gautier
% September 14, 2011

# NAME

shinken-poller - Shinken poller command.

# SYNOPSIS

shinken-poller [*options*] ...

# DESCRIPTION

Daemon in charge of launching plugins as requested by schedulers. When the
check is finished it returns the result to the schedulers.

# OPTIONS

-c *CONFIGFILE*, \--config *CONFIGFILE*
:   Config file

-d, \--daemon
:   Run in daemon mode.

-r, \--replace
:   Replace previous running poller.

-h, \--help
:   Print detailed help screen.

\--debug *FILE*
:   Debug File.



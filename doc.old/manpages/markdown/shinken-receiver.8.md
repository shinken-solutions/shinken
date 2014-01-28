% shinken-receiver(8) Shinken User Manuals
% David Hannequin
% Arthur Gautier
% Michael Leinartas
% December 29, 2011

# NAME

shinken-receiver - Shinken receiver daemon

# SYNOPSIS

shinken-receiver  [*options*] ...

# DESCRIPTION

Shinken receiver daemon

The shinken-receiver daemon manages passive information and serves as a buffer
that will be read from by the shinken-arbiter to dispatch data.

# OPTIONS

\--version
:   Show version number and exit

-c *CONFIGFILE*, \--config *CONFIGFILE*
:   Config file

-d, \--daemon
:   Run in daemon mode.

-r, \--replace
:   Replace previous running arbiter.

-h, \--help
:   Print detailed help screen.

\--debugfile *FILE*
:   Enable debug logging to *FILE*

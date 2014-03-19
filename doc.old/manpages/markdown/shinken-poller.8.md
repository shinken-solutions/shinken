% shinken-poller(8) Shinken User Manuals
% David Hannequin
% Arthur Gautier
% Michael Leinartas
% December 29, 2011

# NAME

shinken-poller - Shinken poller daemon

# SYNOPSIS

shinken-poller [-dr] [-c *CONFIGFILE*] [--debugfile *DEBUGFILE*]

# DESCRIPTION

The shinken-poller daemon is in charge of launching plugins as requested by
schedulers. When the check is finished it returns the result to the schedulers.

# OPTIONS

\--version
:   Show version number and exit

-c *CONFIGFILE*, \--config *CONFIGFILE*
:   Config file

-d, \--daemon
:   Run in daemon mode.

-r, \--replace
:   Replace previous running poller.

-h, \--help
:   Print detailed help screen.

\--debugfile *DEBUGFILE*
:   Enable debug logging to *DEBUGFILE*

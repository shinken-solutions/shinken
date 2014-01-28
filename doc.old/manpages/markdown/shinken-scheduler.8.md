% shinken-scheduler(8) Shinken User Manuals
% Arthur Gautier
% December 29, 2011

# NAME

shinken-scheduler - Shinken scheduler daemon

# SYNOPSIS

shinken-scheduler [-dr] [-c *CONFIGFILE*] [--debugfile *DEBUGFILE*]

# DESCRIPTION

Shinken scheduler daemon

The shinken-scheduler manages the dispatching of checks and actions sent to
shinken-reactionner and shinken-poller based on configuration sent to it by
shinken-arbiter.

# OPTIONS

\--version
:   Show version number and exit

-c *CONFIGFILE*, \--config *CONFIGFILE*
:   Config file

-d, \--daemon
:   Run in daemon mode.

-r, \--replace
:   Replace previous running scheduler.

-h, \--help
:   Print detailed help screen.

\--debugfile *DEBUGFILE*
:   Enable debug logging to *DEBUGFILE*

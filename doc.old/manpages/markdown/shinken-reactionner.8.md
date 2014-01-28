% shinken-reactionner(8) Shinken User Manuals
% David Hannequin
% Arthur Gautier
% Michael Leinartas
% December 29, 2011

# NAME

shinken-reactionner - Shinken reactionner daemon

# SYNOPSIS

shinken-reactionner [-dr] [-c *CONFIGFILE*] [--debugfile *DEBUGFILE*]

# DESCRIPTION

Shinken reactionner daemon

The shinken-reactionner is similar to shinken-poller but handles actions such
as notifications and event-handlers from the schedulers rather than checks.

# OPTIONS

\--version
:   Show version number and exit

-c *CONFIGFILE*, \--config *CONFIGFILE*
:   Config file

-d, \--daemon
:   Run in daemon mode

-r, \--replace
:   Replace previous running reactionner

-h, \--help
:   Print detailed help screen

\--debugfile *DEBUGFILE*
:   Enable debug logging to *DEBUGFILE*

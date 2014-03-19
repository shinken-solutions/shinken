% shinken-arbiter(8) Shinken User Manuals
% David Hannequin
% Arthur Gautier
% Michael Leinartas
% December 29, 2011

# NAME

shinken-arbiter - Shinken arbiter daemon

# SYNOPSIS

shinken-arbiter [-dr] [-c *CONFIGFILE*] [--debugfile *DEBUGFILE*]
shinken-arbiter -v [-c *CONFIGFILE*]

# DESCRIPTION

Shinken arbiter daemon

The shinken-arbiter daemon reads the configuration, divides it into parts
(N schedulers = N parts), and distributes them to the appropriate Shinken daemons.
Additionally, it manages the high availability features: if a particular daemon dies,
it re-routes the configuration managed by this failed  daemon to the configured spare.
Finally, it receives input from users (such as external commands from nagios.cmd) and
routes them to the appropriate daemon. There can only be one active arbiter in the
architecture.

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

\--debugfile *DEBUGFILE*
:   Enable debug logging to *DEBUGFILE*

-v, \--verify-config
:   Verify config file and exit

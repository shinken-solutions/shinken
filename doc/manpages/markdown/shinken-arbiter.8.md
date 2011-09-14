% shinken-arbiter(8) Shinken User Manuals
% Arthur Gautier
% September 14, 2011


# NAME

shinken-arbiter - Shinken arbiter command.

# SYNOPSIS

shinken-arbiter [*options*] ...

# DESCRIPTION

Shinken arbiter daemon.

Reads the configuration, cuts it into parts (N schedulers = N parts), and
then send them to all others elements. It also manages the high
availability feature : if an element dies, it re-routes the configuration
managed by this falling element to a spare one. Its other role is to
receive input from users (like external commands from nagios.cmd) and
sends them to other elements. There can be only one active arbiter in the
architecture.

# OPTIONS

-c *CONFIGFILE*, \--config *CONFIGFILE*
:   Config file

-d, \--daemon
:   Run in daemon mode.

-r, \--replace
:   Replace previous running arbiter.

-h, \--help
:   Print detailed help screen.

\--debug *FILE*
:   Debug File.



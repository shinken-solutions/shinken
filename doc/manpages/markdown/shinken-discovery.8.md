% shinken-discovery(8) Shinken User Manuals
% Arthur Gautier
% September 14, 2011


# NAME

shinken-discovery - Shinken discovery command.

# SYNOPSIS

shinken-discovery [*options*] ...

# DESCRIPTION

Shinken discovery daemon.

Until now, there are two discovery modules :
 * Standard network one, that uses the nmap tool
 * VMware one, that uses the *check_esx3.pl* script and a vcenter installation.

It's better to do the whole discovery in one pass, because one module can
use data from the other.

# OPTIONS

-c *CONFIGFILE*, \--cfg-config *CONFIGGILE*
:   Configuration file.

-o *DIRECTORY*, \--dir-output *DIRECTORY*
:   output directory.

-w, \--overwrite
:   Allow overwriting existing files.

-r *PATH*
:   Indicate path to the nmap binary.

-m *NETWORK*
:   Indicate lan to scan.

-h, \--help
:   Print detailed help screen.

\--debug *FILE*
:   Debug File.



% shinken-discovery(8) Shinken User Manuals
% David Hannequin
% Arthur Gautier
% Michael Leinartas
% December 29, 2011

# NAME

shinken-discovery - Shinken discovery command

# SYNOPSIS

shinken-discovery [-w] [-c *CONFIGFILE*] [-o *OUTPUT_PATH*] [-r *RUNNER*[,*RUNNER,...]] [-m *MACRO* [*MACRO* ...]]

# DESCRIPTION

Shinken discovery command

There are two discovery modules included:
 * Standard network discovery which uses the nmap tool
 * VMware discovery which uses the *check_esx3.pl* script and a vcenter installation.

It is best to do the whole discovery in one pass because one module can
use data from the other.

# OPTIONS
\-- version
:   Show the version and exit

-c *CONFIGFILE*, \--cfg-input *CONFIGGILE*
:   Discovery configuration file

-o *OUTPUT_PATH*, \--dir-output *OUTPUT_PATH*
:   Directory output for results

-w, \--overright
:   Allow overwriting existing files (disabled by default)

-r *RUNNERS*
:   Comma-separated list of discovery runner modules to use

-m *MACROS*
:   List of macros to pass to discovery runner modules. Must be the last
    argument. Ex: NMAPTARGETS=192.168.0.0/24

-h, \--help
:   Print detailed help screen.

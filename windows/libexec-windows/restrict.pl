#!/usr/bin/perl

eval 'exec /usr/bin/perl -S $0 ${1+"$@"}'
    if 0;

# Set this to your local Nagios plugin path
my $pluginpath = "/usr/libexec/nagios/plugins/";

# Put all the legal commands (i.e. the commands that are
# not Nagios checks but are allowed to be executed anyway)
# in the following associative array.
my %legal_cmds = ("nc" => "/usr/sbin/nc");

# This will not work on OpenSSH
# It does work on ssh-1.2.27-1i
@arg = split ' ',$ENV{'SSH_ORIGINAL_COMMAND'};

$arg[0] =~ s/.*\///;            # strip leading path
$arg[0] =~ tr/-_.a-zA-Z0-9/X/c; # change atypical chars to X

if (!defined ($cmd = $legal_cmds{$arg[0]}))
{
  $cmd = $pluginpath . $arg[0];
}

exec { $cmd } @arg or die "Can't exec $cmd: $!";

#!/usr/bin/perl -wT

# check_rrd_data plugin for nagios
#
# usage:
#    check_rrd machine_id perlexp_warn perlexp_crit perlexp_default [ds]
#
# Checks data from a RRD file. machine_id is normally an IP address, that has
# to be mapped to a RRD file, by means of the config file (by default
# /var/spool/nagios/rrd-files, a file with pairs of (machine_id,rrd_file),
# separated by whitespace). It can be a RRD file, too.
#
# The Perl expressions are expressions to be evaluated in the following cases:
#
# - perlexp_crit. The first one, to check if there is a critical situation. If
# it returns other than "", it will be a critical message.
# - perlexp_warn. The second one to be evaluated. If returns other than "", a
# warning will be issued to Nagios.
# - perlexp_default. If both of the above return "", it will be evaluated, and
# wathever returns this expression will be returned by the script. NOTE that
# this is different from the other two cases, to allow the user issue a
# warning or critical failure even if the other two don't return it.
#
# Use these hosts.cfg entries as examples
#
# command[check_ping]=$USER1$/check_rrd_data.pl $HOSTADDRESS$ \
#	'return "CHECK_CRICKET_PING: Warning\n" if ($value > 10);' 'return \
#	"CHECK_CRICKET_PING: Critical\n" if ($value > 100);' 'printf \
#	"PING OK - RTA = %.2fms\n", $value; return 0;' 1
# service[machine]=PING;0;24x7;3;5;1;router-admins;240;24x7;1;1;1;;check_ping
#
# initial version: 28 Nov 2000 by Esteban Manchado Velázquez
# current status: 0.1
#
# Copyright Notice: GPL
#

# Doesn't work! Why?
# BEGIN {
        # my $runtimedir = substr($0,0,rindex($0,'/'));
        # require "$runtimedir/utils.pm";
# }

require '/usr/libexec/nagios/plugins/utils.pm';
use RRD::File;
# use strict;			# RRD:File and utils.pm don't like this

my $configfilepath = "/var/spool/nagios/rrd-files";	# Change if needed
my %hostfile;						# For storing config
my $rrdfile;						# RRD file to open

$ENV{'PATH'} = "/bin:/usr/bin";
$ENV{'ENV'} = "";

if (scalar @ARGV != 4 && scalar @ARGV != 5) {
	print STDERR join "' '", @ARGV, "\n";
	my $foo = 'check_rrd_data';
	print STDERR $foo, " <file.rrd> <perl_exp_warn> <perl_exp_crit> <perl_exp_default> [<ds>]\n\n";
	print STDERR "<perl_exp_*> is an expression that gets evaluated with \$_ at the current\n";
	print STDERR "value of the data source. If it returns something other than \"\", there\n";
	print STDERR "will be a warning or a critical failure. Else, the expression\n";
	print STDERR "<perl_exp_default> will be evaluated\n";
	exit;
}

# Check configuration file
open F, $configfilepath or do {
	print "Can't open config file $configfilepath\n";
	return $ERRORS{'UNKNOWN'};
};
while (<F>) {
	next unless /(.+)\s+(.+)/;
	$hostfile{$1} = $2;
}
close F;

# Default
my $ds = defined $ARGV[4]?$ARGV[4]:0;
	# print "\$ds = " . $ds . ":";
	# print "\$ARGV[4] = " . $ARGV[4] . ":";
$ds =~ s/\$//g;		# Sometimes Nagios gives 1$ as the last parameter

# Guess which RRD file have to be opened
$rrdfile = $ARGV[0] if (-r $ARGV[0]);		# First the parameter
$rrdfile = $hostfile{$ARGV[0]} unless $rrdfile;	# Second, the config file
	# print "$ARGV[0]:";

if (! $rrdfile) {
	print "Can't open data file for $ARGV[0]\n";	# Aaaargh!
	return $ERRORS{'UNKNOWN'};	# Unknown
}

	# print "Opening file $rrdfile:";
my $rrd = new RRD::File ( -file => $rrdfile );
$rrd->open();
if (! $rrd->loadHeader()) {
	print "Couldn't read header from $rrdfile\n";
	exit $ERRORS{'UNKNOWN'};	# Unknown
}
my $value = $rrd->getDSCurrentValue($ds);
$rrd->close();

# Perl expressions to evaluate
my ($perl_exp_warn, $perl_exp_crit, $perl_exp_default) =
		($ARGV[1], $ARGV[2], $ARGV[3]);
my $result;	# Result of the expressions (will be printed)
my @data;	# Special data reserved for the expressions, to pass data

# First check for critical errors
$perl_exp_crit =~ /(.*)/;
$perl_exp_crit = $1;
$result = eval $perl_exp_crit;
if ($result) {
	print $result;
	exit 2;		# Critical
}

# Check for warnings
$perl_exp_warn =~ /(.*)/;
$perl_exp_warn = $1;
$result = eval $perl_exp_warn;
if ($result) {
	print $result;
	exit 1;		# Warning
}

$perl_exp_default =~ /(.*)/;
$perl_exp_default = $1;
eval $perl_exp_default;	# Normally returns 0 (OK)

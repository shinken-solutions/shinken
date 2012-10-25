#!/usr/bin/perl -w

#
# Author: Wim Rijnders, 17-10-2002
#
# Description:
# -----------
#
# Nagios host script to check if any specified java processes are running.
#
# Implementation Notes:
# ---------------------
#
# check_disk_smb was used as a starting point, since it was written in perl.
#
# This script has been created and tested on Linux RH 7.1. 
#
# I tried OS-X Darwin (BSD), but the ps command works differently.
# Notably, you can't get a combined list of child processes. The best approach
# appears to be to use 'ps -wwaxo command' combined with 'ps -M' (or suchlike) 
#
########################################################################
####

require 5.004;
use POSIX;
use strict;
use Getopt::Long;
use vars qw($opt_w $opt_c $verbose $classname);
use vars qw($PROGNAME);
use lib "utils.pm" ;
use utils qw($TIMEOUT %ERRORS &print_revision &support &usage);

$PROGNAME="check_javaprocs";
sub getJavaList ();
sub check_ranges ($ $ $ $);

Getopt::Long::Configure('bundling', 'no_ignore_case');
GetOptions
	("V|version"     => \&version,
	 "h|help"        => \&help,
	 "v|verbose"     => \$verbose,
	 "w|warning=s"   => \$opt_w,
	 "c|critical=s"  => \$opt_c,
	 "n|name=s"      => \$classname
	 );


my $state    = 'OK';
my $min_warn = undef 
my $max_warn = undef;
my $min_crit = undef;
my $max_crit = undef;


($opt_w) || ($opt_w = shift);
check_ranges($opt_w,\$min_warn, \$max_warn, "warning");
($opt_c) || ($opt_c = shift);
check_ranges($opt_c,\$min_crit, \$max_crit, "critical");


#
# Determine # of running processes for the java programs that interest us. 
#
my @javalist = getJavaList();

my $total = 0;
my $msgout = "";
my @fields;

if ( defined $classname ) {

	#filter out a single java process based on class name
	foreach (@javalist) {
		@fields = split(/\s+/, $_);
		$total = $fields[-1] and last if $classname eq $fields[0];
	}
	$msgout .=  "$total processes for $classname\n";
} else {
	#Handle all java processes
	$msgout .= "\n";
	foreach (@javalist) {
		@fields = split(/\s+/, $_);
	
		$total += $fields[-1];
		$msgout .= "   $fields[-1] processes for ";
		$msgout .= (scalar @fields > 1)? $fields[0] : "unknown" ;
		$msgout .= "\n";
	}
	my $msgtotal =  "$total java processes for ". scalar @javalist .  " applications";

	if ( defined $verbose ) {
		$msgout = $msgtotal . $msgout;
	} else {
		$msgout = $msgtotal;
	}
	
}

#
# Set the state with the data we now have accumulated
# Note that due to the order of testing, warnings have precedence over
# criticals. This is logical, since you should be able to create a criticals
# range which encompasses a warning range. eg. following should be possible:
#
# check_javaproc -w 5:10 -c 3:12
# proper specification of the ranges is the responsibility of the script user.
#
$state = 'CRITICAL' if (defined $min_crit && $total < $min_crit);
$state = 'CRITICAL' if (defined $max_crit && $total > $max_crit);
$state = 'CRITICAL' if (!defined $min_crit && !defined $max_crit && $total==0 );
$state = 'WARNING' if (defined $min_warn && $total < $min_warn);
$state = 'WARNING' if (defined $max_warn && $total > $max_warn);

print $msgout;
print "$state\n" if ($verbose);
exit $ERRORS{$state};

###################################
# Support routines for Nagios
###################################
sub check_ranges($$$$) {
	my ($opt, $min, $max, $rangename) = @_;
	
	if ( defined $opt ) {
		if ( $opt =~ /^([0-9]*)\:([0-9]*)$/) {
			$$min = $1 if $1 > 0;
			$$max= $2 if $2 > 0;
		} else {
			usage("Invalid $rangename range: $opt\n");
		} 
	}
	
	if ( defined $$min && defined $$max ) {
		usage("Min value of $rangename range larger than max value: $opt\n") if ( $$min > $$max);
	}
}

sub print_usage () {
	print "Usage: $PROGNAME [-v] [-w <min:max>] [-c <min:max>] [ -n <classname>]\n";
}

sub print_help () {
	revision();
	print "Copyright (c) 2002 by Wim Rijnders

Perl Check java processes plugin for Nagios

";
	print_usage();
	print "
-v, --verbose
   Return additional information. 
   Intended as a command-line aid, not recommended for Nagios script usage.
   
-w, --warning=INTEGER:INTEGER
   Minimum and maximum number of processes outside of which a warning will be
   generated.  If omitted, no warning is generated. 
   
-c, --critical=INTEGER:INTEGER
   Minimum and maximum number of processes outside of which a critical will be
   generated. If omitted, a critical is generated if no processes are running.
   
-n, --name=STRING
   Name of class specified on the java command line (from which main() is run).
   If omitted, all java processes are taken into account.

";
	support();
}

sub revision() {
	print_revision($PROGNAME,'$Revision: 211 $ ');
}

sub version () {
	revision();
	exit $ERRORS{'OK'};
}

sub help () {
	print_help();
	exit $ERRORS{'OK'};
}

###################################
# Routines for delivering the data 
###################################

#
# Generate a formatted list of running java processes.
#
# Returns an array of strings having the following syntax:
#
#	<java class running as main> <parameters if any> <#processes for this class>
#
sub getJavaList() {

	my @output;

	# Untaint
	local $ENV{'PATH'} = '/bin:/usr/bin';	
	local $ENV{'BASH_ENV'} = '~/.bashrc';	
	
	# We are only interested in the full command line
	# The -H opstion is important for the order of the processes;
	# this option ensures that all child processes are listed under
	# their parents
	@output=`ps -AHo \"\%a\" -ww`;
	
	#remove preceding whitespace and final EOL
	foreach (@output) { 
		s/^\s*//;
		chop; 
	} 
	
	#Combine any consecutive processes with exactly the same command line
	#into a single item
	@output = checkSameLine(@output);
	
	#Filter out all java processes
	my @javalist;
	for (my $i = 0; $i < scalar @output; ++$i) {
		push @javalist, $output[$i] if $output[$i] =~ /^\S*java/;
	}
	
	foreach (@javalist) {
		#The java statement at the beginning is redundant; remove it
		s/^\S*java//; 
	
		#remove all defines
		s/\-D\S+//g;
	
		#remove classpath
		s/\-(classpath|cp)\s+\S+//g;
	
		#remove any other parameters we don't want to see
		s/\-server\s+//g;
		s/\-X\S*\s+//g;
	
		#remove any redundant whitespaces at the beginning
		s/^\s+//;

	}

	@javalist;
}


#
# Combine all consecutive lines with an identical command line 
# to a signle line with a count at the end
#
sub checkSameLine {
	my @input  = @_;
	my @output;
	my $prevline= "";
	my $prevcount = 0;

	foreach my $a (@input) {
		if ( $prevline eq $a) {
			++$prevcount;
		} else {
			push @output, $prevline . " " . ($prevcount + 1);
			$prevcount = 0;
		}
		$prevline = $a;
	}

	#don't forget the last item!
	if ( $prevcount > 0 ) {
		push @output, $prevline . " " . ($prevcount + 1);
	}

	@output;
}

#======= end check_javaproc =====

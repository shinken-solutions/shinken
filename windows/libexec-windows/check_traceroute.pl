#!/usr/bin/perl

# $Id: check_traceroute.pl 1115 2005-01-27 10:34:16Z stanleyhopcroft $

# Revision 1.1  2005/01/27 10:34:16  stanleyhopcroft
# Jon Meek's check_traceroute for Mon hacked by YT for Nagios. Prob pretty weak
#

use strict ;

use vars qw(%ERRORS $TIMEOUT) ;
use utils qw(%ERRORS  $TIMEOUT &print_revision &support &usage) ;

sub print_help ();
sub print_usage ();

$ENV{'PATH'}='/bin:/usr/bin:/usr/sbin';

my $PROGNAME			= 'check_traceroute' ;
										# delay units are millisecs.
my $MAX_INTERHOP_DELAY	= 200 ;
my $MAX_HOPS 			= 30 ;

use Getopt::Std;

use vars qw($opt_H $opt_N $opt_r $opt_R $opt_T $opt_d $opt_h $opt_i $opt_v $opt_V) ;

getopts('i:H:N:R:T:dhrvV');
										# H, N, R, T, and i take parms, others are flags

do { print_help ; exit $ERRORS{OK}; }
	if $opt_h ;

do { print_revision($PROGNAME, '$Revision: 1115 $'); exit $ERRORS{OK}; }
	if $opt_V ;

do { print_help; exit $ERRORS{OK}; }
	unless $opt_R || $opt_r ;

do { print_help; exit $ERRORS{OK}; }
	unless $opt_R =~	m|
							(?:\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}-)+
							\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}
						|x 
	|| $opt_r ;

my $should_be		= $opt_R ;
										# Set default timeout in seconds
my $TimeOut			= $opt_T || $TIMEOUT;

my $max_interhop_delay	= $opt_i || $MAX_INTERHOP_DELAY ;
my $max_hops 		= $opt_N || $MAX_HOPS ;

my $TRACEROUTE		= '/usr/sbin/traceroute';

my $TargetHost		= $opt_H ; 

print_help 
	unless $TargetHost ;

my ($route, $pid, $rta_list) = ( '', '', '' );
my %ResultString = () ;
 
$SIG{ALRM} = sub { die "timeout" };

eval {

	alarm($TimeOut);
										# XXXX Discarding STDERR _should_ reduce the risk
										# of unexpected output but consequently, results for
										# non existent hosts are stupid. However, why would you
										# specify a route to a NX host, other than a typo ...

	$pid = open(TR, "$TRACEROUTE -n $TargetHost 2>/dev/null |") 
		or do	{
					 "Failed. Cannot fork \"$TRACEROUTE\": $!" ;
					 $ERRORS{UNKNOWN} ;
				} ;

	my $hops = 0 ;
	while (<TR>) {

		print $_
			if $opt_d;

		if ( m|#\*\s+\*\s+\*| ) {
										# Get * * * then give up
			$route .= '*';
										# 13 = PIPE, prevents Broken Pipe Error, at least on Solaris
			kill 13, $pid;
			last;
		}
										# We will only pick up the first IP address listed on a line for now
										# traceroute to csg.citec.com.au (203.9.184.12), 64 hops max, 44 byte packets
										# 1  10.254.254.254  0.868 ms  0.728 ms  0.705 ms
										# 2  192.168.9.1  1.240 ms  1.165 ms  1.191 ms

		my ($ThisHopIP) = m|\s+(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\s+|;
		my ($max_rta)	= m|\d{1,3}\.\d{1,3}\.\d{1,3}\s+ (\d+\.\d+) ms| ; 

		$route		.= $ThisHopIP . '-';
		$rta_list	.= sprintf("%.1f", $max_rta) . '-' ; 

		if ( $opt_v ) {
			chomp $_ ;
			print $_, ' ' x (58 - length), $route, "\n";
		}

		$hops++ ;

		if ( ($hops >= $max_hops) && ! $opt_r ) {
				kill 13, $pid ;
				print qq(Failed. Max hops ($max_hops) exceeeded: incomplete after $hops hops, "$route".\n) ;
				exit $ERRORS{CRITICAL} ;
		}
		if ( ($hops %2 == 0) && ($hops >= 4)  && ! $opt_r ) {

										# Check for 2 cycles at end of path ie -(a-b)-(a-b)$
										# where a and b are IP v4 addresses of IS (routers).

			my ($last_2_is) = $route =~ /(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}-\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})-$/ ;
			if ( $route =~ /$last_2_is-$last_2_is-$/ ) {
				kill 13, $pid ;
				print qq(Failed. Last 2 routers ($last_2_is) repeated, "$route".\n) ;
				exit $ERRORS{CRITICAL} ;
			}

		} 

	}
};

alarm(0);

if ( $@ and $@ =~ /timeout/ ) {
		$route .= '*';
										# It was a traceroute timeout
		kill 13, $pid;
} elsif ( $@ and $@ !~ /timeout/ ) {
		close TR ;
		print "Failed. Somethings gone wrong with \"$TRACEROUTE\": $!" ;
		exit $ERRORS{UNKNOWN} ;
}

close TR;
										# Remove trailing '-'s
# $route =~ s/\-$//;
chop($route) ;
chop($rta_list) ;

print "$route\n"
	if $opt_d;

if ( $opt_r ) {
	print qq(Ok. Traceroute to host "$TargetHost" via route "$route".\n) ;
	exit $ERRORS{OK};
}

if ( &RouteEqual($should_be, $route) ) {
	print qq(Ok. Traceroute to "$TargetHost" via expected route "$route" ($rta_list).\n) ;
	exit $ERRORS{OK};
} else {
	print qq(Failed. Route "$route" ne expected "$should_be".\n) ;
	exit $ERRORS{CRITICAL};
}


sub RouteEqual {
	my ($current_route, $prev_route) = @_;
	return $current_route eq $prev_route ; 
}

sub print_usage () {
	print "Usage: $PROGNAME [ -R <route_string>|-r ] [ -d  -T timeout -v -h -i ] -H <host>\n";
}

sub print_help () {
	print_revision($PROGNAME, '$Revision: 1115 $') ;
	print "Copyright (c) 2004 J Meek/Karl DeBisschop

This plugin checks whether traceroute to the destination succeeds and if so that the route string option (-R) matches the list of routers
returned by traceroute.

";
print_usage();
	print "
-d
   Debug
-h
   Help
-i
   _TODO_
   Max inter-hop delay (msec).
-H
   Host.
-N
   Max number of hops.
-r
   Record current route (and output to STDOUT). Useful for getting the value of -R option ...
-v
   Greater verbosity.
-R
   Mandatory route string ie r1-r2-... where ri is the ip address of the ith router.
-T
   Maximum time (seconds) to wait for the traceroute command to complete. Defaults to $TIMEOUT seconds.

";
	support();
}

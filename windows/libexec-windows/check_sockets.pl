#! /usr/bin/perl
# ------------------------------------------------------------------------------
# File Name:		check_sockets.pl
# Author:		Richard Mayhew - South Africa
# Date:			2000/07/11
# Version:		1.0
# Description:		This script will check to see how may open sockets
#			a server has and waron respectivly
# Email:		netsaint@splash.co.za
# ------------------------------------------------------------------------------
# Copyright 1999 (c) Richard Mayhew
# Credits go to Ethan Galstad for coding Nagios
# If any changes are made to this script, please mail me a copy of the
# changes :)
# Some code taken from Charlie Cook (check_disk.pl)
# License GPL
#
# ------------------------------------------------------------------------------
# Date		Author		Reason
# ----		------		------
# 1999/09/20	RM		Creation
# 1999/09/20	TP		Changed script to use strict, more secure by
#				specifying $ENV variables. The bind command is
#				still insecure through.  Did most of my work
#				with perl -wT and 'use strict'
#
# ------------------------------------------------------------------------------

# -----------------------------------------------------------------[ Require ]--
require 5.004;
# --------------------------------------------------------------------[ Uses ]--
use Socket;
use strict;
# --------------------------------------------------------------[ Enviroment ]--
$ENV{'PATH'}='/bin:/sbin:/usr/bin:/usr/sbin';
$ENV{BASH_ENV} = "";
# ------------------------------------------------------------------[ Global ]--
my $TIMEOUT = 20;
my %ERRORS = (
	'UNKNOWN', '-1',
	'OK', '0',
	'WARNING', '1',
	'CRITICAL', '2');
# --------------------------------------------------------------[ connection ]--
sub connection
{
	my ($in_total,$in_warn,$in_crit,$in_high) = @_;
	my $state;
	my $answer;

	$in_total =~ s/\ //g;
	if ($in_total >= 0) {

		if ($in_total > $in_crit) {
			$state = "CRITICAL";
			$answer = "Critical Number Of Sockets Connected : $in_total (Limit = $in_crit)\n";

		} elsif ($in_total > $in_warn) {
			$state = "WARNING";
			$answer = "Warning Number Of Sockets Connected : $in_total (Limit = $in_warn)\n";

		} else {
			if ($in_high ne "") {
			$answer = "Sockets OK - Current Sockets: $in_total : $in_high\n";
			}
			if ($in_high eq "") {
			$answer = "Sockets OK - Current Sockets: $in_total\n";
			}
			$state = "OK";
			}

	} else {
		$state = "UNKNOWN";
		$answer = "Something is Really WRONG! Sockets Is A Negative Figure!\n";
	}
	
	print $answer;
	exit $ERRORS{$state};
}

# -------------------------------------------------------------------[ usage ]--
sub usage
{
	print "Minimum arguments not supplied!\n";
	print "\n";
	print "Perl Check Sockets plugin for Nagios\n";
	print "Copyright (c) 2000 Richard Mayhew\n";
	print "\n";
	print "Usage: check_sockets.pl <type> <warn> <crit>\n";
	print "\n";
	print "<type> = TOTAL, TCP, UDP, RAW.\n";
	print "<warn> = Number of sockets connected at which a warning message will be generated.[Default = 256]\n";
	print "<crit> = Number of sockets connected at which a critical message will be generated.[Default = 512]\n";
	exit $ERRORS{"UNKNOWN"};

}

# ====================================================================[ MAIN ]==
MAIN:
{
	my $type = shift || &usage;
	my $warn = shift || 256;
	my $crit = shift || 512;
	my $data;	
	my @data;
	my $line;
	my $data1;
	my $data2;
	my $data3;
	my $junk;
	my $total1;
	my $total2;
	$type = uc $type;
	if ($type eq "TOTAL") {
	$type = "sockets";
	}

	# Just in case of problems, let's not hang Nagios
	$SIG{'ALRM'} = sub {
		print "Somthing is Taking a Long Time, Increase Your TIMEOUT (Currently Set At $TIMEOUT Seconds)\n";
		exit $ERRORS{"UNKNOWN"};
	};

	$data = `/bin/cat /proc/net/sockstat`;
	@data = split("\n",$data);
	alarm($TIMEOUT);
	my $output = "";
	my $high;


	foreach $line (@data) {
		if ($line =~ /$type/) {
		($data1,$data2,$data3) = split(" ",$line,3);	

			if ($data3 =~ /highest/){
			($total1,$junk,$total2) = split(" ",$data3,3);	
			$output = $total1;
			$high = $total2;
			}
			else {$output = $data3;}
	alarm(0);
	connection($output,$warn,$crit,$high);
		}
	}
}

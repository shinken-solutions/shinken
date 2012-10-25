#!/usr/bin/perl -Wall
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
#
#
# check_traceroute is designed to generate and alarm if a traceroute exceeds
# a certain number of hops. This is useful in cases where a multi-homed 
# network looses a connection and can still ping the remote end because
# traffic is being re-routed out through the redundent connection.
#
# check_traceroute v0.1
# By mp@xmission.com
#
# Thanks to Sebastian Hetze, Linux Information Systems AG who wrote the
# excellent check_apache plugin, which this plugin was modeled after.
#
#############################################################################

use strict;
use Net::Traceroute;
use Getopt::Long;

my $version = "v0.1";
my $opt_v;
my $opt_t=undef; #for usage () unless ($opt_t) to work right
my $opt_help;
my $opt_w;
my $opt_c;

my %ERRORS = ('UNKNOWN' , '-1',
              'OK' , '0',
              'WARNING', '1',
              'CRITICAL', '2');
# Set this to whatever you like, but make sure you don't hang Nagios
# for too long.
my $timeout = "30";

GetOptions 
	("v"   => \$opt_v, "t=s"	=> \$opt_t, 
	"help"	=> \$opt_help, "h"	=> \$opt_help,
	"w=i"	=> \$opt_w, "c=i"	=> \$opt_c
	);

if ($opt_v) {
	print "\nThis is check_traceroute version $version\n";
	print "\n";
	print "Please report errors to mp\@xmission\.com";
	print "\n\n";
	}

#subs	
sub print_help () {
	print "\n\nThis is check_traceroute.pl. It is designed to send an alert\n";
	print "to Nagios if a route to a particular destination exceeds a\n";
	print "certain number of hops.\n\n";
	print "Usage:\n";
	print "\n";
	print "--help Display this help.\n";
	print "-v Display the version number of check_traceroute.\n";
	print "-t Host that you wish to traceroute to.\n";
	print "-w Number of hops before Nagios generates a WARNING.\n";
	print "-c Number of hops before Nagios generates a CRITICAL.\n";
	}

sub usage() {
	print "check_traceroute -t <host> [-w <warning>] [-c <critical>]\n";
	}

sub do_check() {
	if ($opt_t) {
		unless ($opt_w && $opt_c) {die "You must specify thresholds using -c and -w\n";}
		my $tr = Net::Traceroute->new(host=>"$opt_t") || die "Can't init traceroute!\n";
		if($tr->found) {
			my $hops = $tr->hops;
			if($hops > $opt_w) {
				print "Warning: $opt_t is $hops hops away!\n";
				exit $ERRORS{'WARNING'};
			}
			elsif($hops > $opt_c) {
				print "Critical: $opt_t is $hops hops away!\n";
				exit $ERRORS{'CRITICAL'};
			}
			else {
				print "OK: $opt_t is $hops hops away\n";
				exit $ERRORS{'OK'};
				}
		}		
		else {
			print "Couldn't locate host $opt_t!\n";
			exit $ERRORS{'UNKNOWN'};
		}
	}
	}

# Must be placed at the end for -Wall to compile cleanly, blech
if ($opt_help) {
	print_help();
	}
usage() unless ($opt_t);
#timeoutes
$SIG{'ALRM'} = sub {
     print ("ERROR: No response from $opt_t (timeout) in $timeout seconds\n");
          exit $ERRORS{"UNKNOWN"};
	  };
	  alarm($timeout);
do_check();


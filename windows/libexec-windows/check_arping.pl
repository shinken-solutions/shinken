#! /usr/bin/perl -w
#
# check_arping.pl - Nagios plugin to check host status via ARP ping
#
# usage:
#     check_arping -H hostname -I interface -T timeout
#
#
# Copyright (C) 2003  Kenny Root
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
#
# Report bugs to: kenny@the-b.org, nagiosplug-help@lists.sf.net

use POSIX;
use strict;
use lib "/usr/lib/nagios/plugins" ;
use utils qw($TIMEOUT %ERRORS &print_revision &support);

use Net::Arping;
use Getopt::Long;

my $PROGNAME = "check_arping";

my($status, $state, $answer);
my($opt_V, $opt_h, $opt_t, $opt_I, $opt_H);


#Option checking
$status = GetOptions(
	"V|version"	=> \$opt_V,
	"help"	=> \$opt_h, 
	"I|interface=s"	=> \$opt_I,
	"H|host=s"	=> \$opt_H,
	"t|timeout=i"	=> \$opt_t);
		
if ($status == 0)
{
	print_help() ;
	exit $ERRORS{'OK'};
}


if ($opt_V) {
	print_revision($PROGNAME,'$Revision: 1112 $ ');
	exit $ERRORS{'OK'};
}

if ($opt_h) {
	print_help();
	exit $ERRORS{'OK'};
}

if ($opt_t) {
	if ($opt_t ne int($opt_t)) {
		print "Timeout not in seconds!\n";
		print_help();
		exit $ERRORS{'OK'};
	}
	$opt_t = int($opt_t);
} else {
	$opt_t = 3;
}

if (! utils::is_hostname($opt_H)){
	usage();
	exit $ERRORS{"UNKNOWN"};
}

my $ping = Net::Arping->new();

my $reply = $ping->arping(Host => $opt_H, Interface => $opt_I, Timeout => $opt_t);

if ($reply eq "0") {
	$state = "CRITICAL";
	print "$state: no reply from $opt_H on interface $opt_I in $opt_t seconds.\n";
	exit $ERRORS{$state};
} else {
	$state = "OK";
	$answer = "replied with MAC address $reply";
}

print "ARPING $state - $answer\n";
exit $ERRORS{$state};


sub usage {
	print "\nMissing arguments!\n";
	print "\n";
	print "check_arping -I <interface> -H <host IP> [-t <timeout>]\n";
	print "\n\n";
	support();
	exit $ERRORS{"UNKNOWN"};
}

sub print_help {
	print "check_arping pings hosts that normally wouldn't allow\n";
  	print "ICMP packets but are still on the local network.\n";
	print "\nUsage:\n";
	print "   -H (--host)       IP to query - (required)\n";
	print "   -I (--interface)  Interface to use.\n";
	print "   -t (--timeout)    Timeout in seconds.\n";
	print "   -V (--version)    Plugin version\n";
	print "   -h (--help)       usage help \n\n";
	print_revision($PROGNAME, '$Revision: 1112 $');
	
}

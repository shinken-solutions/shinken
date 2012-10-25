#! /usr/bin/perl -wT
#
# check_atalk_ping plugin for nagios
#
# usage:
#    check_atalk_ping atalkaddress
#
# Checks if an atalkhost responds to an atalk echo
# using "aecho"
#
# initial version: 23 October 2002 by Stefan Beck, IT Software Solutions
# current status: $Revision: 1771 $
#
# Copyright Notice: GPL
#
BEGIN {
     if ( $0 =~ m/^(.*?)[\/\\]([^\/\\]+)$/ ) {
         $runtimedir = $1;
         $PROGNAME   = $2;
     }
     delete $ENV{'LANG'};
}

use strict;
use lib "/usr/local/nagios/libexec";

use utils qw($TIMEOUT %ERRORS &print_revision &support);
use vars qw($PROGNAME);

$PROGNAME = "check_atalk";

my (
     $verbose,      $host,          $warning_avg, $warning_loss,
     $critical_avg, $critical_loss, $count,       $cmd,
     $avg,          $loss,          $line
);
my ( $opt_c, $opt_w, $opt_H, $opt_p );
$opt_c = $opt_w = $opt_p = $opt_H = '';

sub print_help ();
sub print_usage ();
sub help ();
sub version ();

# Just in case of problems, let's not hang NetSaint
$SIG{'ALRM'} = sub {
         print "Plugin Timeout\n";
         exit 2;
};
alarm($TIMEOUT);

delete @ENV{ 'PATH', 'IFS', 'CDPATH', 'ENV', 'BASH_ENV' };

use Getopt::Long;
Getopt::Long::Configure( 'bundling', 'no_ignore_case' );
GetOptions(
     "V|version"    => \&version,
     "h|help"       => \&help,
     "p|packets=i"  => \$opt_p,
     "c|critical=s" => \$opt_c,
     "w|warning=s"  => \$opt_w,
     "H|hostname=s" => \$opt_H
);


# appletalk  hostname ot address
$opt_H = shift unless ($opt_H);
unless ($opt_H) { print_usage (); exit $ERRORS{'UNKNOWN'}; }
if ( $opt_H && $opt_H =~ m/^([-a-zA-Z\.\:0-9]+)$/ ) {
     $host = $1;
}
else {
     print "$opt_H is not a valid host name\n";
     exit $ERRORS{'UNKNOWN'};
}

# number of packets
$opt_p = 5 unless $opt_p;
if ( $opt_p && $opt_p =~ m/^([1-9]+[0-9]*)$/ ) {
     $count = $1;
}
else {
     print "$opt_p is not a valid packet number\n";
     exit $ERRORS{'UNKNOWN'};
}

if ( $opt_w && $opt_w =~ m/^([1-9]+[0-9]*),([1-9][0-9]*)%$/ ) {
     $warning_avg  = $1;
     $warning_loss = $2;
}
else {
     print "$opt_w is not a valid threshold\n";
     exit $ERRORS{'UNKNOWN'};
}

if ( $opt_c && $opt_c =~ m/^([1-9]+[0-9]*),([1-9][0-9]*)%$/ ) {
     $critical_avg  = $1;
     $critical_loss = $2;
}
else {
     print "$opt_c is not a valid threshold\n";
     exit $ERRORS{'UNKNOWN'};
}

$cmd = "/usr/bin/aecho -c $count $host 2>&1 |";
print "$cmd\n" if ($verbose);
open CMD, $cmd;

while (<CMD>) {
     print $_ if ($verbose);
     $line = $_;

     # 5 packets sent, 5 packets received, 0% packet loss
     # round-trip (ms)  min/avg/max = 0/0/0

     if (/received, ([0-9]+)% packet loss/) {
         $loss = $1;
     }
     if (/min\/avg\/max = [0-9]+\/([0-9]+)\/[0-9]+/) {
         $avg = $1;
     }
}

sub print_help() {
     print_revision( $PROGNAME, '$Revision: 1771 $ ' );
     print "Copyright (c) 2002 Stefan Beck\n";
     print "\n";
     print "Check if an atalkhost responds to an atalk echo using\n";
     print "      aecho -c <packets> <atalkhost>\n";
     print "\n";
     print_usage ();
     print "\n";
     print "-H, --hostname=HOST\n";
     print "   host to ping\n";
     print "-w, --warning=THRESHOLD\n";
     print "   warning threshold pair\n";
     print "-c, --critical=THRESHOLD\n";
     print "   critical threshold pair\n";
     print "-p, --packets=INTEGER\n";
     print "   number of ICMP ECHO packets to send (Default: 5)\n";
     print "\n";
     print
       "THRESHOLD is <rta>,<pl>% where <rta> is the round trip average 
travel\n";
     print
       "time (ms) which triggers a WARNING or CRITICAL state, and <pl> 
is the\n";
     print "percentage of packet loss to trigger an alarm state.\n";
     print "\n";

     support();
}

sub print_usage () {
     print "$PROGNAME -H atalkhost -w <wrta>,<wpl>% -c <crta>,<cpl>%\n";
     print "         [-p packets] [-t timeout] [-L]\n";
     print "$PROGNAME [-h | --help]\n";
     print "$PROGNAME [-V | --version]\n";
}

sub version () {
     print_revision( $PROGNAME, '$Revision: 1771 $ ' );
     exit $ERRORS{'OK'};
}

sub help () {
     print_help ();
     exit $ERRORS{'OK'};
}

my $state  = "OK";
my $answer = undef;

if ( defined $loss && defined $avg ) {
     if ( $loss >= $critical_loss ) {
         $state = "CRITICAL";
     }
     elsif ( $avg >= $critical_avg ) {
         $state = "CRITICAL";
     }
     elsif ( $loss >= $warning_loss ) {
         $state = "WARNING";
     }
     elsif ( $avg >= $warning_avg ) {
         $state = "WARNING";
     }
     else {
         $state = "OK";
     }
     $answer = "Appletalk PING $state - Packet loss = $loss%, RTA = $avg 
ms\n";
}
else {
     $state  = "UNKNOWN";
     $answer = "UNKNOWN - $line";
}
print $answer;
exit $ERRORS{$state};




-------------------------------------------------------
This sf.net email is sponsored by:ThinkGeek
Welcome to geek heaven.
http://thinkgeek.com/sf
_______________________________________________
Nagios-devel mailing list
Nagios-devel@lists.sourceforge.net
https://lists.sourceforge.net/lists/listinfo/nagios-devel

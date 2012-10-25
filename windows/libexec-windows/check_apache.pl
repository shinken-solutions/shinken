#!/usr/bin/perl
#
# (c)2001 Sebastian Hetze, Linux Information Systems AG
# send bug reports to <S.Hetze@Linux-AG.com>
# 
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# you should have received a copy of the GNU General Public License
# along with this program (or with Nagios);  if not, write to the
# Free Software Foundation, Inc., 59 Temple Place - Suite 330,
# Boston, MA 02111-1307, USA
#
#
# Check apache status information provided by mod_status to find
# out about the load (number of servers working) and the
# performance (average response time for recent requests).
#
# Usage:
# check_apache -H <host> [-lhV] [-w <warn>] [-c <crit>] [-u <url>]
#
# check_apache <host> <warn> <crit> <url> (if you cannot avoid it)
#

use LWP::UserAgent;
use URI::URL;
use Getopt::Long;
Getopt::Long::Configure('bundling');

$version=0.01;

my %ERRORS = ('UNKNOWN' , '-1',
              'OK' , '0',
              'WARNING', '1',
              'CRITICAL', '2');


#
#              some default values
#
$perf_w=500;
$perf_c=1000;
$load_w=20;
$load_c=30;
$TIMEOUT=15;

#
#              get command line options the regular way
#
GetOptions
        ("V"   => \$opt_V, "version"       => \$opt_V,
         "h"   => \$opt_h, "help"          => \$opt_h,
         "l"   => \$opt_l, "load"          => \$opt_l,
         "v" => \$verbose, "verbose"       => \$verbose,
         "w=s" => \$opt_w, "warning=s"     => \$opt_w,
         "c=s" => \$opt_c, "critical=s"    => \$opt_c,
         "H=s" => \$opt_H, "hostname=s"    => \$opt_H,
         "u=s" => \$opt_u, "url=s"         => \$opt_u);

#
#              handle the verbose stuff first
#
if ($opt_V) {
        print "\n";
        print "check_apache nagios plugin version $version\n";
        print "\n";
        print "The nagios plugins come with ABSOLUTELY NO WARRANTY.  You may redistribute\n";
        print "copies of the plugins under the terms of the GNU General Public License.\n";
        print "For more information about these matters, see the file named COPYING.\n";
        print "\n";
        print "Copyright (c) 2001 Sebastian Hetze  Linux Information Systems AG\n";
        print "\n";
        print "\n";
        exit $ERRORS{'UNKNOWN'};
} 

if ($opt_h) {
        print_help();
        exit $ERRORS{'UNKNOWN'};
}

#
#              now get options the weired way and set the defaults
#              if nothing else is provided
#
$opt_H = shift unless ($opt_H);
print_usage() unless ($opt_H);

if($opt_l) {
   $autostring="?auto";
   ($opt_w) || ($opt_w = shift) || ($opt_w = $load_w);
   $warn = $1 if ($opt_w =~ /([0-9]+)/);
   ($opt_c) || ($opt_c = shift) || ($opt_c = $load_c);
   $alert = $1 if ($opt_c =~ /([0-9]+)/);
} else {
   $autostring="";
   ($opt_w) || ($opt_w = shift) || ($opt_w = $perf_w);
   $warn = $1 if ($opt_w =~ /([0-9]+)/);
   ($opt_c) || ($opt_c = shift) || ($opt_c = $perf_c);
   $alert = $1 if ($opt_c =~ /([0-9]+)/);
}

($opt_u) || ($opt_u = shift) || ($opt_u = "/server-status");


#
#              dont let us wait forever...
#
$SIG{'ALRM'} = sub {
     print ("ERROR: No response from HTTP server (alarm)\n");
     exit $ERRORS{"UNKNOWN"};
};
alarm($TIMEOUT);


#
#              now we set things up for the real work
#              and fire up the request
#
$ua = new LWP::UserAgent;
$ua->agent("Nagios/0.1 " . $ua->agent);


$urlstring = "http://" . $opt_H . $opt_u . $autostring;
$url = url($urlstring);

my $req = new HTTP::Request 'GET', $url;
my $res = $ua->request($req);

#
#              hopefully we´ve got something usefull
#
if ($res->is_success) {
  if($opt_l) {
     foreach $_ (split /^/m, $res->content) {
        next if /^\s*$/;
#
#              this is the load checking section
#              we parse the whole content, just in case someone
#              wants to use this some day in the future
#
        if (/^Total Accesses:\s+([0-9.]+)/) { $accesses = $1; next; }
        if (/^Total kBytes:\s+([0-9.]+)/) { $kbytes = $1; next; }
        if (/^CPULoad:\s+([0-9.]+)\s+/) { $load = $1; next; }
        if (/^Uptime:\s+([0-9.]+)\s+/) { $uptime = $1; next; }
        if (/^ReqPerSec:\s+([0-9.]+)\s+/) { $rps = $1; next; }
        if (/^BytesPerSec:\s+([0-9.]+)\s+/) { $bps = $1; next; }
        if (/^BytesPerReq:\s+([0-9.]+)\s+/) { $bpr = $1; next; }
        if (/^BusyServers:\s+([0-9.]+)\s+/) { $busy = $1; next; }
        if (/^IdleServers:\s+([0-9.]+)\s+/) { $idle = $1; next; }
        if (/^Scoreboard:\s+([SRWKDLG_.]+)\s+/) { $score = $1; next; }
        print "Unknown Status\n";
	exit $ERRORS{"UNKNOWN"};
     }
#
#              now we even parse the whole scoreboard, just for fun
#
     foreach $scorepoint (split //m, $score) {
        if($scorepoint eq '.') { $scores{'.'}+=1; next; }  # Unused
        if($scorepoint eq '_') { $scores{'_'}+=1; next; }  # Waiting
        if($scorepoint eq 'S') { $scores{'S'}+=1; next; }  # Starting
        if($scorepoint eq 'R') { $scores{'R'}+=1; next; }  # Reading
        if($scorepoint eq 'W') { $scores{'W'}+=1; next; }  # Writing
        if($scorepoint eq 'K') { $scores{'K'}+=1; next; }  # Keepalive
        if($scorepoint eq 'D') { $scores{'D'}+=1; next; }  # DNS Lookup
        if($scorepoint eq 'L') { $scores{'L'}+=1; next; }  # Logging
        if($scorepoint eq 'G') { $scores{'G'}+=1; next; }  # Going
     }

     if($busy>$alert) {
        printf "HTTPD CRITICAL: %.0f servers running\n", $busy;
	exit $ERRORS{"CRITICAL"};
     }
     if($busy>$warn) {
        printf "HTTPD WARNING: %.0f servers running\n", $busy;
	exit $ERRORS{"WARNING"};
     }
     printf "HTTPD ok: %.0f servers running, %d idle\n", $busy, $idle;
     exit $ERRORS{"OK"};

  } else {
#
#              this is the performance check section
#              We are a bit lazy here, no parsing of the initial data
#              block and the scoreboard.
#              However, you have the whole set of per server
#              information to play with ;-)
#              The actual performance is measured by adding up the
#              milliseconds required to process the most recent
#              requests of all instances and then taking the average.
#
     foreach $tablerow (split /<tr>/m, $res->content) {
         ($empty,$Srv,$PID,$Acc,$M,$CPU,$SS,$Req,$Conn,$Child,$Slot,$Client,$VHost,$Request)
         = split /<td>/, $tablerow;
         if($Req) {
              $lines+=1;
              $req_sum+=$Req;
         }
         undef $Req;
     }
     $average=$req_sum/$lines;
     if($average>$alert) {
        printf "HTTPD CRITICAL: average response time %.0f
	milliseconds\n", $average;
	exit $ERRORS{"CRITICAL"};
     }
     if($average>$warn) {
        printf "HTTPD WARNING: average response time %.0f
	milliseconds\n", $average;
	exit $ERRORS{"WARNING"};
     }
     if($average>0) {
        printf "HTTPD ok: average response time %.0f milliseconds\n",
        $average;
        exit $ERRORS{"OK"};
     }
     print "Unknown Status\n";
     exit $ERRORS{"UNKNOWN"};
  }
} else {
	print "HTTP request failed\n";
	exit $ERRORS{"CRITICAL"};
}


#
#              ok, now we are almost through
#              These last subroutines do the things for those that do not
#              read source code.
#
sub print_usage () {
        print "Usage: $0 -H <host> [-lhV] [-w <warn>] [-c <crit>] [-u <url>]\n"; }
 
sub print_help () {
        print "\n";
        print "\n";
        print "check_apache nagios plugin version $version\n";
        print "\n";
        print "The nagios plugins come with ABSOLUTELY NO WARRANTY.  You may redistribute\n";
        print "copies of the plugins under the terms of the GNU General Public License.\n";
        print "For more information about these matters, see the file named COPYING.\n";
        print "\n";
        print "Copyright (c) 2001 Sebastian Hetze  Linux Information Systems AG\n";
        print "\n";
        print "\n";
        print "This plugin checks the apache HTTP service on the specified host.\n";
        print "It uses the mod_status facilities provided by the apache server.\n";
        print "The monitoring server must be authorized in httpd.conf.\n";
        print "\n";
        print "\n";
        print_usage();
        print "\n";
        print "Options:\n";
        print " -H, --hostname=ADDRESS\n";
        print "     host name argument for server.\n";
        print " -l, --load\n";
	print "     check load instead of performance.\n";
        print " -h, --help\n";
	print "     print detailed help screen.\n";
        print " -V, --version\n";
	print "     print version information.\n";
        print " -w, --warning=INTEGER\n";
        print "     load / performance level at which a warning message will be gererated.\n";
        print " -c, --critical=INTEGER\n";
        print "     load / performance level at which a critical message will be gererated.\n";
        print " -u, --url=PATH\n";
        print "     location to call mod_status.\n";
        print "\n";
        print "     Defaults for performance checking are $perf_w/$perf_c msec.\n";
        print "     Defaults for load checking are $load_w/$load_c servers running.\n";
        print "\n";
        print "\n";
} 
#
#              the end
#

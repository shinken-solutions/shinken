#!/usr/bin/perl -w
#
# check_bgpstate.pl - nagios plugin 
#
# Copyright (C) 2000 Christoph Kron
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
# Report bugs to: ck@zet.net
#
# 11.01.2000 Version 1.0



use strict;

use Net::SNMP;
use Getopt::Long;
&Getopt::Long::config('auto_abbrev');


# whois programm for RIPE database queries
my $whois = '/usr/bin/whois';
my $status;
my $TIMEOUT = 30;

# critical bgp sessions
my %uplinks = ( 1273, 'Uplink ECRC',
                1755, 'Uplink EBONE',
                3300, 'Uplink AUCS'
	      );

my %ERRORS = ('UNKNOWN' , '-1',
              'OK' , '0',
              'WARNING', '1',
              'CRITICAL', '2');


my %bgpPeerState = (  
           '1',"idle",
           '2',"connect",
           '3',"active",
           '4',"opensent",
           '5',"openconfirm",
           '6',"established"
        );
my $state = "UNKNOWN";
my $answer = "";
my $snmpkey;
my $snmpoid;
my $key;
my $community = "public";
my $port = 161;
my @snmpoids;
my $snmpbgpPeerState = '1.3.6.1.2.1.15.3.1.2';
my $snmpbgpPeerLocalAddr = '1.3.6.1.2.1.15.3.1.5';
my $snmpbgpPeerRemoteAddr = '1.3.6.1.2.1.15.3.1.7';
my $snmpbgpPeerRemoteAs = '1.3.6.1.2.1.15.3.1.9';
my $hostname;
my $session;
my $error;
my $response;
my %bgpStatus;
my $bgpestablished =0 ;
my $bgpcritical =0;
my $bgpdown =0;
my $bgpidle =0;
my $bgpmessage;
my $asname;
my $remoteas;
my @output;

sub usage {
  printf "\nMissing arguments!\n";
  printf "\n";
  printf "Perl bgpstate plugin for Nagios\n";
  printf "monitors all BGP sessions\n";
  printf "usage: \n";
  printf "check_bgpstate.pl -c <READCOMMUNITY> -p <PORT> <HOSTNAME>\n";
  printf "Copyright (C) 2000 Christoph Kron\n";
  printf "check_bgpstate.pl comes with ABSOLUTELY NO WARRANTY\n";
  printf "This programm is licensed under the terms of the ";
  printf "GNU General Public License\n(check source code for details)\n";
  printf "\n\n";
  exit $ERRORS{"UNKNOWN"};
}

# Just in case of problems, let's not hang Nagios
$SIG{'ALRM'} = sub {
     print ("ERROR: No snmp response from $hostname (alarm)\n");
     exit $ERRORS{"UNKNOWN"};
};
alarm($TIMEOUT);


$status = GetOptions("community=s",\$community,
                     "port=i",\$port);
if ($status == 0)
{
        &usage;
}
  
   #shift;
   $hostname  = shift || &usage;


push(@snmpoids, $snmpbgpPeerState);
push(@snmpoids, $snmpbgpPeerLocalAddr);
push(@snmpoids, $snmpbgpPeerRemoteAddr);
push(@snmpoids, $snmpbgpPeerRemoteAs);

foreach $snmpoid (@snmpoids) {

   ($session, $error) = Net::SNMP->session(
      -hostname  => $hostname,
      -community => $community,
      -port      => $port
   );

   if (!defined($session)) {
      $state='UNKNOWN';
      $answer=$error;
      print ("$state: $answer");
      exit $ERRORS{$state};
   }

   if (!defined($response = $session->get_table($snmpoid))) {
      $answer=$session->error;
      $session->close;
      $state = 'CRITICAL';
      print ("$state: $answer,$snmpkey");
      exit $ERRORS{$state};
   }

   foreach $snmpkey (keys %{$response}) {
      $snmpkey =~ m/.*\.(\d+\.\d+\.\d+\.\d+$)/;
      $key =  $1;
#      printf "debug: $snmpkey: $key -> $response->{$snmpkey}\n";
      $bgpStatus{$key}{$snmpoid} = $response->{$snmpkey};
   }
   $session->close;
}

foreach $key (keys %bgpStatus) {
   if ($bgpStatus{$key}{$snmpbgpPeerState} == 6 ) { 
      $bgpestablished++;
   }
   elsif ($bgpStatus{$key}{$snmpbgpPeerState} == 1 ) {
      $bgpidle++;
   }
   else { 
       $bgpdown++ ;
       if (exists($uplinks{$bgpStatus{$key}{$snmpbgpPeerRemoteAs}}) ) {
          $bgpcritical++;
       }
       @output = `$whois -T aut-num AS$bgpStatus{$key}{$snmpbgpPeerRemoteAs}`;

   $asname = "";
   foreach (@output) {
     if (m/as-name/) {
        $asname = $_;
        $asname =~ s/as-name://;
        last;
     }
     if ( $asname =~ "" && m/descr/ ) {
        $asname = $_;
        $asname =~ s/descr://;
     }
   }
   $asname =~ s/^\s*//;
   $asname =~ s/\s*$//;
       $bgpmessage .= sprintf("Peering with AS%s not established -> %s<BR>",
                           $bgpStatus{$key}{$snmpbgpPeerRemoteAs},
			   $asname);
   }
}
   

   if ($bgpdown > 0) {
      if ($bgpcritical > 0) {
         $state = 'CRITICAL';
      }
      else {
         $state = 'WARNING';
      }
      $answer = sprintf("host '%s', sessions up: %d, down: %d, shutdown: %d<BR>",
                        $hostname,
			$bgpestablished,
			$bgpdown, $bgpidle);
      $answer = $answer . $bgpmessage . "\n";
   }
   else {
      $state = 'OK';
      $answer = sprintf("host '%s', sessions up: %d, down: %d, shutdown: %d\n",
                        $hostname,
			$bgpestablished,
			$bgpdown,$bgpidle);
   }

print ("$state: $answer");
exit $ERRORS{$state};


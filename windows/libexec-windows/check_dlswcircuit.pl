#!/usr/bin/perl -w
#
# check_dlswcircuit.pl - nagios plugin 
# 
# Checks if a Cisco Dlsw circuit is connected.
#
#
# Copyright (C) 2000 Carsten Foss & Christoph Kron
# 
# Basically this is an adapted version of Christoph Kron's (ck@zet.net) check_ifoperstatus.pl plugin.
# most of the thanks should go to him.
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
# Arguments : -s <SourceMac> -d <DestMac> -c <READCOMMUNITY> -p <PORT> <HOSTNAME or IP-Addr>
#		-
# Source & Dest Mac/Sap arguments must be given in Hex as this example : 40.00.01.37.45.01.ss (Where ss is the sap) 
#
# Sample command line : check_dlswcircuit.pl -s 40.00.01.37.45.01.04 -d 40.00.02.37.45.02.04 -c secret 1.2.3.4
#
# Sample host.cfg entry :
#service[Dlsw-xx]=NCP1-NCP2;0;24x7;3;5;1;router-admins;240;24x7;1;1;0;;check_dlswcircuit!-s 40.00.01.37.45.01.04!-d 40.00..01.37.45.02.04!-c secret!1.2.3.4
# remember to add the service to commands.cfg , something like this:
# command[check_dlswcircuit]=$USER1$/check_dlswcircuit.pl $ARG1$ $ARG2$ $ARG3$ $ARG4$ $ARG5$
#
# Report bugs to: cfo@dmdata.dk
#
# 11.03.2000 Version 1.0

use strict;

use Net::SNMP;
use Getopt::Long;
&Getopt::Long::config('auto_abbrev');


my $status;
my $TIMEOUT = 15;

my %ERRORS = ('UNKNOWN' , '-1',
              'OK' , '0',
              'WARNING', '1',
              'CRITICAL', '2');

my %dlswCircuitStatus = (
	  '1','disconnected',
        '2','circuitStart',
        '3','resolvePending',
        '4','circuitPending',
        '5','circuitEstablished',
        '6','connectPending',
        '7','contactPending',
        '8','connected',
        '9','disconnectPending',
        '10','haltPending',
        '11','haltPendingNoack',
        '13','circuitRestart',
        '14','restartPending');

my $state = "UNKNOWN";
my $answer = "";
my $smac = "";
my $dmac = "";
my $community = "public";
my $port = 161;
#Dlsw Circuit Oid enterprises.9.10.9.1.5.2.1.17.6.0.96.148.47.230.166.4.6.64.0.1.55.69.2.4 = 8
my $enterpriseOid = "1.3.6.1.4.1";
my $ciscoDlswCircuitOid = ".9.10.9.1.5.2.1.17.";
my $unknownOid = "6.";
my $smacOid = "";
my $dmacOid = "";
my $tmpOid = "";
my @tmparg;
my $snmpoid;
my @snmpoids;
my $hostname;
my $session;
my $error;
my $response;
my $p = "";
my $q = "";

sub usage {
  printf "\nMissing arguments!\n";
  printf "\n";
  printf "Perl Check Cisco Dlsw Circuit State plugin for Nagios\n";
  printf  "checks operational status of specified DLSW Circuit\n";
  printf "usage: \n";
  printf "check_dlswcircuit.pl -s <SourceMac> -d <DestMac> -c <READCOMMUNITY> -p <PORT> <HOSTNAME>";
  printf "\nCopyright (C) 2000 Carsten Foss\n";
  printf "check_dlswcircuit.pl comes with ABSOLUTELY NO WARRANTY\n";
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


$status = GetOptions("sourcemac=s",\$smac,"destmac=s",\$dmac,
                     "community=s",\$community,
                     "port=i",\$port);
if ($status == 0)
{
        &usage;
}

#
#Convert Source Mac & Sap
#  
   @tmparg = split(/\./,$smac);
   #print "-$smac-\n";
   #print "@tmparg\n";
   #print "$#tmparg\n";
   if($#tmparg != 6)
   {
     print "SourceMac/Sap format $smac not valid\n";
     &usage;
   }
   while($p = shift @tmparg)
   {
     $q = hex($p); 
     $smacOid = $smacOid.$q;
     $smacOid = $smacOid.'.';
   }

   #print "@tmparg1\n";
   #print "$smacOid\n";

#
#Convert Dest Mac & Sap
#  
   @tmparg = split(/\./,$dmac);
   #print "-$dmac-\n";
   #print "@tmparg\n";
   #print "$#tmparg\n";
   if($#tmparg != 6)
   {
     print "DestMac/Sap format $dmac not valid\n";
     &usage;
   }

   while($p = shift @tmparg)
   {
     $q = hex($p); 
     $dmacOid = $dmacOid.$q;
     $dmacOid = $dmacOid.'.';
   }
#  Remove Trailing Dot
   $dmacOid = substr($dmacOid,0,length($dmacOid)-1);
   

   #print "@tmparg1\n";
   #print "$dmacOid\n";
#Build the Dlsw Oic to use
   $snmpoid = $enterpriseOid.$ciscoDlswCircuitOid.$unknownOid.$smacOid.$unknownOid.$dmacOid ;
   #print "$snmpoid\n";

   #shift;
   $hostname  = shift || &usage;

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

   push(@snmpoids,$snmpoid);
   #push(@snmpoids,$snmpLocIfDescr);

   if (!defined($response = $session->get_request(@snmpoids))) {
      $answer=$session->error;
      $session->close;
      $state = 'CRITICAL';
      print ("$state: $answer,$community,$smac - $dmac");
      exit $ERRORS{$state};
   }

   $answer = sprintf("dlsw circuit %s - %s at host '%s',is %s\n", 
      $smac,
	$dmac,
      $hostname, 
      $dlswCircuitStatus{$response->{$snmpoid}}
   );

   $session->close;

   if ( $response->{$snmpoid} == 8 ) {
      $state = 'OK';
   }
   else {
	$state = 'CRITICAL';
   }

print ("$state: $answer");
exit $ERRORS{$state};

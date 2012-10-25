#!/usr/bin/perl -w
#
# check_maxwanstate.pl - nagios plugin 
# 
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


my $status;
my $TIMEOUT = 1500;

my %ERRORS = ('UNKNOWN' , '-1',
              'OK' , '0',
              'WARNING', '1',
              'CRITICAL', '2');

my %wanLineState = (
            1,'ls-unknown',
            2,'ls-does-not-exist',
            3,'ls-disabled',
            4,'ls-no-physical',
            5,'ls-no-logical',
            6,'ls-point-to-point',
            7,'ls-multipoint-1',
            8,'ls-multipoint-2',
            9,'ls-loss-of-sync',
            10,'ls-yellow-alarm',
            11,'ls-ais-receive',
            12,'ls-no-d-channel',
            13,'ls-active',
            14,'ls-maintenance');

my %wanLineType = (
	'1.3.6.1.4.1.529.4.1','Any',
	'1.3.6.1.4.1.529.4.2','T1',
	'1.3.6.1.4.1.529.4.3','E1',
	'1.3.6.1.4.1.529.4.4','Dpnss',
	'1.3.6.1.4.1.529.4.5','Bri',
	'1.3.6.1.4.1.529.4.6','S562',
	'1.3.6.1.4.1.529.4.7','S564',
	'1.3.6.1.4.1.529.4.8','Sdsl',
	'1.3.6.1.4.1.529.4.9','AdslCap');
	
my $state = "UNKNOWN";
my $answer = "";
my $snmpkey;
my $snmpoid;
my $key;
my $community = "public";
my $port = 161;
my @snmpoids;
my $snmpWanLineName = '1.3.6.1.4.1.529.4.21.1.2';
my $snmpWanLineType = '1.3.6.1.4.1.529.4.21.1.3';
my $snmpWanLineState = '1.3.6.1.4.1.529.4.21.1.5';
my $snmpWanLineUsage = '1.3.6.1.4.1.529.4.21.1.8';

my $hostname;
my $session;
my $error;
my $response;
my %wanStatus;
my $ifup =0 ;
my $ifdown =0;
my $ifdormant = 0;
my $ifmessage;

sub usage {
  printf "\nMissing arguments!\n";
  printf "\n";
  printf "Perl Check maxwanstate plugin for Nagios\n";
  printf "monitors E1/T1 interface status\n";
  printf "usage: \n";
  printf "check_maxwanstate.pl -c <READCOMMUNITY> -p <PORT> <HOSTNAME>";
  printf "Copyright (C) 2000 Christoph Kron\n";
  printf "check_maxwanstate.pl comes with ABSOLUTELY NO WARRANTY\n";
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



push(@snmpoids,$snmpWanLineUsage);
push(@snmpoids,$snmpWanLineState);
push(@snmpoids,$snmpWanLineName);
push(@snmpoids,$snmpWanLineType);

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
      print ("$state: $answer,$community,$snmpkey");
      exit $ERRORS{$state};
   }

   foreach $snmpkey (keys %{$response}) {
      $snmpkey =~ /.*\.(\d+)$/;
      $key = $1;
      $wanStatus{$key}{$snmpoid} = $response->{$snmpkey};
   }
   $session->close;
}

   foreach $key (keys %wanStatus) {
      # look only at active Interfaces lu-trunk(5)
      if ($wanStatus{$key}{$snmpWanLineUsage} == 5 ) {

	 # 13 -> active
         if ($wanStatus{$key}{$snmpWanLineState} == 13 ) {
             $ifup++;
         }
         else {
             $ifdown++ ;
             $ifmessage .= sprintf("%s interface status : %s (%s)<BR>",
                         $wanLineType{$wanStatus{$key}{$snmpWanLineType}},
                         $wanLineState{$wanStatus{$key}{$snmpWanLineState}},
			 $wanStatus{$key}{$snmpWanLineName});

         }
      }
   }
   

   if ($ifdown > 0) {
      $state = 'CRITICAL';
      $answer = sprintf("host '%s', interfaces up: %d, down: %d<BR>",
                        $hostname,
			$ifup,
			$ifdown);
      $answer = $answer . $ifmessage . "\n";
   }
   else {
      $state = 'OK';
      $answer = sprintf("host '%s', interfaces up: %d, down: %d\n",
                        $hostname,
			$ifup,
			$ifdown);
   }

print ("$state: $answer");
exit $ERRORS{$state};


#!/usr/bin/perl -w
#
# check_maxchannels.pl - nagios plugin 
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
my $TIMEOUT = 15;

my %ERRORS = ('UNKNOWN' , '-1',
              'OK' , '0',
              'WARNING', '1',
              'CRITICAL', '2');

	
my $state = "UNKNOWN";
my $answer = "";
my $snmpkey;
my $snmpoid;
my $key;
my $community = "public";
my $port = 161;
my @snmpoids;
# free channels
my $snmpWanAvailableChannels = '1.3.6.1.4.1.529.4.23.0';
# maximum channels
my $snmpWanSwitchedChannels = '1.3.6.1.4.1.529.4.24.0';
my $snmpWanDisabledChannels = '1.3.6.1.4.1.529.4.25.0';
my $snmpWanActiveChannels = '1.3.6.1.4.1.529.4.26.0';
my $snmpWanNailedChannels = '1.3.6.1.4.1.529.4.27.0';
my $snmpWanOutOfServiceChannels = '1.3.6.1.4.1.529.4.28.0';
my $snmpEventCurrentActiveSessions = '1.3.6.1.4.1.529.10.6.0';
# since startup
my $snmpEventTotalNoModems = '1.3.6.1.4.1.529.10.15.0';
# lan modem
my $snmpDeadLanModem = '1.3.6.1.4.1.529.15.7.0';
my $snmpDisabledLanModem = '1.3.6.1.4.1.529.15.5.0';
my $snmpSuspectLanModem = '1.3.6.1.4.1.529.15.3.0';
my $snmpAvailLanModem = '1.3.6.1.4.1.529.15.1.0';
my $snmpBusyLanModem = '1.3.6.1.4.1.529.15.9.0';
# max modems
my $snmpMdmNumber  = '1.3.6.1.2.1.38.1.1.0';
my $hostname;
my $session;
my $error;
my $response;
my %wanStatus;


my $WanAvailableChannels;
my $WanSwitchedChannels;
my $WanDisabledChannels;
my $WanActiveChannels;
my $WanNailedChannels;
my $WanOutOfServiceChannels;
my $EventCurrentActiveSessions;
my $EventTotalNoModems;
my $DeadLanModem;
my $DisabledLanModem;
my $SuspectLanModem;
my $AvailLanModem;
my $BusyLanModem;
my $MdmNumber;


sub usage {
  printf "\nMissing arguments!\n";
  printf "\n";
  printf "Perl Check maxchannels plugin for Nagios\n";
  printf "monitors ISDN lines and modems on Ascend MAX 2000/4000/6000/TNT\n";
  printf "usage: \n";
  printf "check_maxchannel.pl -c <READCOMMUNITY> -p <PORT> <HOSTNAME>\n";
  printf "Copyright (C) 2000 Christoph Kron\n";
  printf "check_maxchannels.pl comes with ABSOLUTELY NO WARRANTY\n";
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



push(@snmpoids,$snmpWanAvailableChannels);
push(@snmpoids,$snmpWanSwitchedChannels);
push(@snmpoids,$snmpWanDisabledChannels);
push(@snmpoids,$snmpWanActiveChannels);
push(@snmpoids,$snmpWanNailedChannels);
push(@snmpoids,$snmpWanOutOfServiceChannels);

push(@snmpoids,$snmpEventCurrentActiveSessions);

push(@snmpoids,$snmpEventTotalNoModems);
push(@snmpoids,$snmpDeadLanModem);
push(@snmpoids,$snmpDisabledLanModem);
push(@snmpoids,$snmpSuspectLanModem);
push(@snmpoids,$snmpAvailLanModem);
push(@snmpoids,$snmpBusyLanModem);
push(@snmpoids,$snmpMdmNumber);

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

   if (!defined($response = $session->get_request(@snmpoids))) {
      $answer=$session->error;
      $session->close;
      $state = 'CRITICAL';
      print ("$state: $answer,$community");
      exit $ERRORS{$state};
   }


$WanAvailableChannels = $response->{$snmpWanAvailableChannels};
$WanSwitchedChannels = $response->{$snmpWanSwitchedChannels};
$WanDisabledChannels = $response->{$snmpWanDisabledChannels};
$WanActiveChannels = $response->{$snmpWanActiveChannels};
$WanNailedChannels = $response->{$snmpWanNailedChannels};
$WanOutOfServiceChannels = $response->{$snmpWanOutOfServiceChannels};
$EventCurrentActiveSessions = $response->{$snmpEventCurrentActiveSessions};
$EventTotalNoModems = $response->{$snmpEventTotalNoModems};
$DeadLanModem = $response->{$snmpDeadLanModem};
$DisabledLanModem = $response->{$snmpDisabledLanModem};
$SuspectLanModem = $response->{$snmpSuspectLanModem};
$AvailLanModem = $response->{$snmpAvailLanModem};
$BusyLanModem = $response->{$snmpBusyLanModem};
$MdmNumber = $response->{$snmpMdmNumber};

# less than 50% -> WARNING
if ( 0 < $WanOutOfServiceChannels 
     && $WanOutOfServiceChannels < ($snmpWanSwitchedChannels * 0.5) ) {
   $state = 'WARNING';
}
elsif ($WanOutOfServiceChannels > 0) {
   $state = 'CRITICAL';
}
elsif ($DeadLanModem > 0) {
   $state = 'CRITICAL';
}
elsif ($SuspectLanModem > 0) {
   $state = 'WARNING';
}
elsif ($AvailLanModem == 0) {
   $state = 'WARNING';
}
else {
   $state = 'OK';
}


$answer =  sprintf("active sessions: %d (%d), active modems: %d (%d)<BR>",
		$EventCurrentActiveSessions,
		$WanSwitchedChannels,
		$BusyLanModem,
		$MdmNumber);
		
$answer .= sprintf("channels available: %d, disabled: %d",
		$WanAvailableChannels,
		$WanDisabledChannels);

$answer .= sprintf(", out of service: %d, nailed: %d<BR>",
		$WanOutOfServiceChannels,
		$WanNailedChannels);

$answer .= sprintf("modems avail.: %d, disabled: %d, suspect: %d, dead: %d<BR>",
		$AvailLanModem,
		$DisabledLanModem,
		$SuspectLanModem,
		$DeadLanModem);

$answer .= sprintf("unserviced modem calls: %d (since startup)\n",
		$EventTotalNoModems);

$session->close;

print ("$state: $answer");
exit $ERRORS{$state};


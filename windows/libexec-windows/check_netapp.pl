#!/usr/bin/perl -wT
# check_netapp
# 
# Copyright (C) 2000  Leland E. Vandervort <leland@mmania.com>
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
####################################
# checks for overtemperature, fans, psu, and nfs operations/second on
# Network Appliance Filers.  
# Returns:  
#  OK if temp, fans, psu OK and Ops/Sec below warning and critical
#   Thresholds (default is warning=3500, critical=5000)  
#    ** Note:  See the specifications for your Filer model for 
#       the thresholds !
#  Returns Warning if NFS Ops/Sec is above warning threshold
#    (default 3500, or specified by -o command line option)
#  Returns Critical if NFS Ops/Sec is above critical threshold
#    ( -m option, or default 5000), or if overtem, psufault, or
#    fanfault detected.
#
####################################
#  Notes on operational limits for NetApp Filers:
#   Platform                     Maximum Ops/Second (recommended)
#   -------------------------------------------------------------
#   F230                         1000
#   F740                         5500
#   F760                         9000
####################################

use Net::SNMP;
use Getopt::Long;
&Getopt::Long::config('auto_abbrev');

my $status;
my $response = "";
my $TIMEOUT = 10;
my $community = "public";
my $port = 161;
my $opsthresh = "3500";
my $critical = "5000";

my $status_string = "";

my %OIDLIST = (
		overtemp 	=> 	'1.3.6.1.4.1.789.1.2.4.1.0',
		failedfan	=>	'1.3.6.1.4.1.789.1.2.4.2.0',
		failedpsu	=>	'1.3.6.1.4.1.789.1.2.4.4.0',
		nfsops		=>	'1.3.6.1.4.1.789.1.2.2.1.0'
	      );



my %STATUSCODE = (  'UNKNOWN' => '-1',
                    'OK' => '0',
                    'WARNING' => '1',
                    'CRITICAL' => '2');

my $state = "UNKNOWN";


$SIG{'ALRM'} = sub {
    print "ERROR: No snmp response from $hostname (sigALRM)\n";
    exit($STATUSCODE{"UNKNOWN"});
};

alarm($TIMEOUT);                    

sub get_nfsops {
	my $nfsops_start = &SNMPGET($OIDLIST{nfsops});
	sleep(1);
	my $nfsops_end = &SNMPGET($OIDLIST{nfsops});
	my $nfsopspersec = $nfsops_end - $nfsops_start;
	return($nfsopspersec);
}


sub show_help {
    printf("\nPerl NetApp filer plugin for Nagios\n");
    printf("Usage:\n");
    printf("
  check_netapp [options] <hostname>
  Options:
    -c snmp-community
    -p snmp-port
    -o Operations per second warning threshold 
    -m Operations per second critical threshold

");
    printf("Copyright (C)2000 Leland E. Vandervort\n");
    printf("check_netapp comes with absolutely NO WARRANTY either implied or explicit\n");
    printf("This program is licensed under the terms of the\n");
    printf("GNU General Public License\n(check source code for details)\n\n\n");
    exit($STATUSCODE{"UNKNOWN"});
}
 

$status = GetOptions( "community=s", \$community,
                      "port=i",      \$port,
		      "opsthresh=i", \$opsthresh,
		      "maxops=i",    \$critical );
                     
if($status == 0) {
    &show_help;
}

sub SNMPGET {
    $OID = shift;
    ($session,$error) = Net::SNMP->session(
        Hostname        =>      $hostname,
        Community       =>      $community,
        Port            =>      $port
        );
    if(!defined($session)) {
        printf("$state %s\n", $error);
        exit($STATUSCODE{$state});
    }
    if(!defined($response = $session->get_request($OID))) {
        printf("$state %s\n", $session->error());
        $session->close();
	exit($STATUSCODE{$state});
    }
    $session->close();
    return($response->{$OID});
}

$hostname = shift || &show_help;

my $tempcheck = &SNMPGET($OIDLIST{overtemp});
if($tempcheck == 1) {
	$state = "OK";
	$status_string .= "Temp OK ";
}
else {
	$state = "CRITICAL";
	$status_string .= "Temp CRIT";
}

foreach $element ('failedfan','failedpsu') {
	my $my_return = &SNMPGET($OIDLIST{$element});
	if(($my_return =~ /no/) || ($my_return == 0)) {
		$status_string .= "$element = $my_return ";
		$state = "OK";
	}
	else {
		$status_string .= "$element = $my_return ";
		$state = "CRITICAL";
	}
}

my $tmp_opssec = &get_nfsops();

if ($tmp_opssec >= $critical) {
	$state = "CRITICAL";
}
elsif ($tmp_opssec >= $opsthresh) {
	$state = "WARNING";
}
else {
	$state = "OK";
}

$status_string .= "Ops\/Sec = $tmp_opssec ";

print "$state $status_string\n";
exit($STATUSCODE{$state});

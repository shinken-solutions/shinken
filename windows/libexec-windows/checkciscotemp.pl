#!/usr/bin/perl -wT
# check_ciscotemp.pl
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
# Nagios pluging to check inlet and outlet temperatures on 
# Cisco router platforms which support environmental monitoring
# (7200, 7500, GSR12000...)
####################################
# default temperature thresholds are 30C for inlet, 40C outlet.
# if input or output is less than thresholds, returns OK
# if equal to (the temps don't change that rapidly) returns WARNING
# if greater than threshold, returns CRITICAL
# if undetermined, or cannot access environmental, returns UNKNOWN
# (in accordance with the plugin coding guidelines)
####################################

use Net::SNMP;
use Getopt::Long;
&Getopt::Long::config('auto_abbrev');

my $status;
my $response = "";
my $timeout = 10;
my $community = "public";
my $port = 161;
my $INTAKE_TEMP = "1.3.6.1.4.1.9.9.13.1.3.1.3.1";
my $OUTLET_TEMP = "1.3.6.1.4.1.9.9.13.1.3.1.3.3";
my $in_temp;
my $out_temp;
my $inlet_thresh = 30;
my $outlet_thresh = 40;

my %STATUSCODE = (  'UNKNOWN' => '-1',
                    'OK' => '0',
                    'WARNING' => '1',
                    'CRITICAL' => '2');

my $state = "UNKNOWN";


$SIG{'ALRM'} = sub {
    print "ERROR: No snmp response from $hostname (sigALRM)\n";
    exit($STATUSCODE{"UNKNOWN"});
};

Getopt::Long::Configure('bundling');
$status = GetOptions
	("community=s", \$community,
	 "C=s",         \$community,
	 "H=s",         \$hostname,
	 "hostname=s",  \$hostname,
	 "port=i",      \$port,
	 "timeout=i",   \$timeout,
	 "c=s",         \$critical_vals,
	 "w=s",         \$warning_vals,
	 "ithresh=i",   \$inlet_thresh,
	 "othresh=i",   \$outlet_thresh);
                     
if($status == 0) {
    &show_help;
}

unless (defined($hostname)) {
    $hostname = shift || &show_help;
}

if (defined($critical_vals)) {
    if ($critical_vals =~ m/^([0-9]+)[,:]([0-9]+)$/) {
        ($inlet_thresh,$outlet_thresh) = ($1, $2);
    } else {
        die "Cannot Parse Critical Thresholds\n";
    }
}

if (defined($warning_vals)) {
    if ($warning_vals =~ m/^([0-9]+)[:,]([0-9]+)$/) {
        ($inlet_warn,$outlet_warn) = ($1, $2);
    } else {
        die "Cannot Parse Warning Thresholds\n";
    }
}else{
    $inlet_warn=$inlet_thresh;
    $outlet_warn=$outlet_thresh;
}

alarm($timeout);                    

$in_temp = &SNMPGET($INTAKE_TEMP);
$out_temp = &SNMPGET($OUTLET_TEMP);

if (($in_temp < $inlet_thresh) && ($out_temp < $outlet_thresh)) {
    $state = "OK";
}
elsif (($in_temp == $inlet_thresh) || ($out_temp == $outlet_thresh)) {
    if(($in_temp > $inlet_thresh) || ($out_temp > $outlet_thresh)) {
        $state = "CRITICAL";
    }
    else {
        $state = "WARNING";
    }
}
elsif (($in_temp > $inlet_thresh) || ($out_temp > $outlet_thresh)) {
    $state = "CRITICAL";
}
else {
    $state = "WARNING";
}

print "$state Inlet Temp: $in_temp Outlet Temp: $out_temp\n";
exit($STATUSCODE{$state});

sub show_help {
    printf("\nPerl envmon temperature plugin for Nagios\n");
    printf("Usage:\n");
    printf("
  check_ciscotemp [options] <hostname>
  Options:
    -C snmp-community
    -p snmp-port
    -i input temperature threshold
    -o output temperature threshold

");
    printf("Copyright (C)2000 Leland E. Vandervort\n");
    printf("check_ciscotemp comes with absolutely NO WARRANTY either implied or explicit\n");
    printf("This program is licensed under the terms of the\n");
    printf("GNU General Public License\n(check source code for details)\n\n\n");
    exit($STATUSCODE{"UNKNOWN"});
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


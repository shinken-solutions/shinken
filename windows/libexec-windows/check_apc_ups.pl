#! /usr/bin/perl -wT
#
# Check_apc_ups - Check APC UPS status via SNMP
# Shamelessly copied from check_breeze.pl
#
# To do:
# - Send SNMP queries directly, instead of forking `snmpget`.
# - Make the status less verbose.  Maybe we can send an "onLine, time
#   remaining: hh:mm:ss" if all is well, and a list of specific problems
#   if something is broken. 

use strict;
use Getopt::Long;
use vars qw($opt_V $opt_h $opt_H $opt_T $opt_t $opt_R $opt_r 
  $opt_L $opt_l $PROGNAME);
use lib "/usr/local/nagios/libexec";
use utils qw(%ERRORS &print_revision &support &usage);

sub print_help ();
sub print_usage ();
sub get_snmp_int_val ($);
sub escalate_exitval ($);

$ENV{'PATH'}='';
$ENV{'BASH_ENV'}=''; 
$ENV{'ENV'}='';

Getopt::Long::Configure('bundling');
GetOptions
	("V"   => \$opt_V, "version"		=> \$opt_V,
	 "h"   => \$opt_h, "help"		=> \$opt_h,
	 "T=s" => \$opt_T, "temp-critical"	=> \$opt_T,
	 "t=s" => \$opt_t, "temp-warning"	=> \$opt_t,
	 "R=s" => \$opt_R, "runtime-critical"	=> \$opt_R,
	 "r=s" => \$opt_r, "runtime-warning"	=> \$opt_r,
	 "L=s" => \$opt_L, "load-critical"	=> \$opt_L,
	 "l=s" => \$opt_l, "load-warning"	=> \$opt_l,
	 "H=s" => \$opt_H, "hostname=s"		=> \$opt_H);

if ($opt_V) {
	print_revision($PROGNAME,'$Revision: 1771 $');
	exit $ERRORS{'OK'};
}

if ($opt_h) {print_help(); exit $ERRORS{'OK'};}

($opt_H) || ($opt_H = shift) || usage("Host name/address not specified\n");
my $host = $1 if ($opt_H =~ /([-.A-Za-z0-9]+)/);
($host) || usage("Invalid host: $opt_H\n");

# Defaults

$opt_R *= 60 * 100 if (defined $opt_R);	# Convert minutes to secs/100
$opt_r *= 60 * 100 if (defined $opt_R);

my $tempcrit    = $opt_T || 60;
my $tempwarn    = $opt_t || 40;
my $runtimecrit = $opt_R || 30 * 60 * 100;     # Secs / 100
my $runtimewarn = $opt_r || 60 * 60 * 100;
my $loadcrit    = $opt_L || 85;
my $loadwarn    = $opt_l || 50;

if ($tempcrit !~ /\d+/) { usage ("Invalid critical temperature threshold.\n"); }
if ($tempwarn !~ /\d+/) { usage ("Invalid critical temperature threshold.\n"); }

if ($runtimecrit !~ /\d+/) {
  usage ("Invalid critical run time threshold.\n");
}
if ($runtimewarn !~ /\d+/) {
  usage ("Invalid warning run time threshold.\n");
}

if ($loadcrit !~ /\d+/ || $loadcrit < 0 || $loadcrit > 100) {
  usage ("Invalid critical load threshold.\n");
}
if ($loadwarn !~ /\d+/ || $loadwarn < 0 || $loadwarn > 100) {
  usage ("Invalid warning load threshold.\n");
}


# APC UPS OIDs
# APC MIBs are available at ftp://ftp.apcftp.com/software/pnetmib/mib
my $upsBasicOutputStatus          = ".1.3.6.1.4.1.318.1.1.1.4.1.1.0";
my $upsBasicBatteryStatus         = ".1.3.6.1.4.1.318.1.1.1.2.1.1.0";
my $upsAdvInputLineFailCause      = ".1.3.6.1.4.1.318.1.1.1.3.2.5.0";
my $upsAdvBatteryTemperature      = ".1.3.6.1.4.1.318.1.1.1.2.2.2.0";
my $upsAdvBatteryRunTimeRemaining = ".1.3.6.1.4.1.318.1.1.1.2.2.3.0";
my $upsAdvBatteryReplaceIndicator = ".1.3.6.1.4.1.318.1.1.1.2.2.4.0";
my $upsAdvOutputLoad              = ".1.3.6.1.4.1.318.1.1.1.4.2.3.0";
my $upsAdvTestDiagnosticsResults  = ".1.3.6.1.4.1.318.1.1.1.7.2.3.0";

my @outputStatVals = (
  [ undef, undef ],					# pad 0
  [ undef, undef ],					# pad 1
  [ "onLine",			$ERRORS{'OK'} ],	# 2
  [ "onBattery",		$ERRORS{'WARNING'} ],	# 3
  [ "onSmartBoost",		$ERRORS{'WARNING'} ],	# 4
  [ "timedSleeping",		$ERRORS{'WARNING'} ],	# 5
  [ "softwareBypass",		$ERRORS{'WARNING'} ],	# 6
  [ "off",			$ERRORS{'CRITICAL'} ],	# 7
  [ "rebooting",		$ERRORS{'WARNING'} ],	# 8
  [ "switchedBypass",		$ERRORS{'WARNING'} ],	# 9
  [ "hardwareFailureBypass",	$ERRORS{'CRITICAL'} ],	# 10
  [ "sleepingUntilPowerReturn",	$ERRORS{'CRITICAL'} ],	# 11
  [ "onSmartTrim",		$ERRORS{'WARNING'} ],	# 12
);

my @failCauseVals = (
  undef,
  "noTransfer",
  "highLineVoltage",
  "brownout",
  "blackout",
  "smallMomentarySag",
  "deepMomentarySag",
  "smallMomentarySpike",
  "largeMomentarySpike",
  "selfTest",
  "rateOfVoltageChnage",
);

my @battStatVals = (
  [ undef, undef ],				# pad 0
  [ undef, undef ],				# pad 1
  [ "batteryNormal",	$ERRORS{'OK'} ],	# 2
  [ "batteryLow",	$ERRORS{'CRITICAL'} ],	# 3
);

my @battReplVals = (
  [ undef, undef ],		 			# pad 0
  [ "noBatteryNeedsReplacing",	$ERRORS{'OK'} ],	# 1
  [ "batteryNeedsReplacing",	$ERRORS{'CRITICAL'} ],	# 2
);

my @diagnosticsResultsVals = (
  [ undef, undef ],				# pad 0
  [ "OK",		$ERRORS{'OK'} ],	# 1
  [ "failed",		$ERRORS{'CRITICAL'} ],	# 2
  [ "invalidTest",	$ERRORS{'CRITICAL'} ],	# 3
  [ "testInProgress",	$ERRORS{'OK'} ],	# 4
);

my $exitval     = $ERRORS{'UNKNOWN'};
my $data;
my $onbattery   = 3;

$data = get_snmp_int_val( $upsBasicOutputStatus );

print "Output status: ";
if (defined ($data) && defined ($outputStatVals[$data][0])) {
  print "$outputStatVals[$data][0] | ";
  escalate_exitval($outputStatVals[$data][1]);
} else {
  print "unknown | ";
}

$data = get_snmp_int_val( $upsAdvBatteryRunTimeRemaining );

print "Rem time: ";
if (defined ($data)) {
  my $hrs  = int($data / (60 * 60 * 100)); # Data is hundredths of a second
  my $mins = int($data / (60 * 100)) % 60;
  my $secs = ($data % 100) / 100;
  printf "%d:%02d:%05.2f | ", $hrs, $mins, $secs;
  if ($data <= $runtimecrit) {
    escalate_exitval($ERRORS{'CRITICAL'});
  } elsif ($data <= $runtimewarn) {
    escalate_exitval($ERRORS{'WARNING'});
  } else {
    escalate_exitval($ERRORS{'OK'});
  }
} else {
  print "unknown | ";
}

$data = get_snmp_int_val( $upsBasicBatteryStatus );

print "Battery status: ";
if (defined ($data) && defined ($battStatVals[$data][0])) {
  my $failcause = "unknown";
  my $fc = get_snmp_int_val( $upsAdvInputLineFailCause );
  if ($data == $onbattery) {
    if (defined ($failCauseVals[$fc])) { $failcause = $failCauseVals[$fc]; }
    print "$battStatVals[$data][0] ($failcause) | ";
  } else {
    print "$battStatVals[$data][0] | ";
  }
  escalate_exitval($battStatVals[$data][1]);
} else {
  print "unknown | ";
}

$data = get_snmp_int_val( $upsAdvBatteryTemperature );

print "Battery temp(C): ";
if (defined ($data)) {
  print "$data | ";
  if ($data >= $tempcrit) {
    escalate_exitval($ERRORS{'CRITICAL'});
  } elsif ($data >= $tempwarn) {
    escalate_exitval($ERRORS{'WARNING'});
  } else {
    escalate_exitval($ERRORS{'OK'});
  }
} else {
  print "unknown | ";
}

$data = get_snmp_int_val( $upsAdvBatteryReplaceIndicator );

print "Battery repl: ";
if (defined ($data) && defined ($battReplVals[$data][0])) {
  print "$battReplVals[$data][0] | ";
  escalate_exitval($battReplVals[$data][1]);
} else {
  print "unknown | ";
}

$data = get_snmp_int_val( $upsAdvOutputLoad );

print "Output load (%): ";
if (defined ($data)) {
  print "$data | ";
  if ($data >= $loadcrit) {
    escalate_exitval($ERRORS{'CRITICAL'});
  } elsif ($data >= $loadwarn) {
    escalate_exitval($ERRORS{'WARNING'});
  } else {
    escalate_exitval($ERRORS{'OK'});
  }
} else {
  print "unknown | ";
}

$data = get_snmp_int_val( $upsAdvTestDiagnosticsResults );

print "Diag result: ";
if (defined ($data) && defined ($diagnosticsResultsVals[$data][0])) {
  print "$diagnosticsResultsVals[$data][0]\n";
  escalate_exitval($diagnosticsResultsVals[$data][1]);
} else {
  print "unknown\n";
}


exit $exitval;


sub print_usage () {
	print "Usage: $PROGNAME -H <host> -T temp -t temp -R minutes -r minutes\n";
	print "  -L percent -l percent\n";
}

sub print_help () {
	print_revision($PROGNAME,'$Revision: 1771 $');
	print "Copyright (c) 2001 Gerald Combs/Jeffrey Blank/Karl DeBisschop

This plugin reports the status of an APC UPS equipped with an SNMP management
module.

";
	print_usage();
	print "
-H, --hostname=HOST
   Name or IP address of host to check
-T --temp-critical
   Battery degrees C above which a CRITICAL status will result (default: 60)
-t --temp-warning
   Battery degrees C above which a WARNING status will result (default: 40)
-R --runtime-critical
   Minutes remaining below which a CRITICAL status will result (default: 30)
-r --runtime-warning
   Minutes remaining below which a WARNING status will result (default: 60)
-L --load-critical
   Output load pct above which a CRITICAL status will result (default: 85
-l --load-warning
   Output load pct above which a WARNING status will result (default: 50

";
	support();
}

sub get_snmp_int_val ($) {
  my $val=0;
  my $oid = shift(@_);

  $val = `/usr/bin/snmpget $host public $oid 2> /dev/null`;
  my @test = split(/ /,$val,3);

  return undef unless (defined ($test[2]));

  if ($test[2] =~ /\(\d+\)/) {	# Later versions of UCD SNMP
    ($val) = ($test[2] =~ /\((\d+)\)/);
  } elsif ($test[2] =~ /: \d+/) {
    ($val) = ($test[2] =~ /: (\d+)/);
  } else {
    $val = $test[2];
  }

  return $val;
}

sub escalate_exitval ($) {
  my $newval = shift(@_);

  if ($newval > $exitval) { $exitval = $newval; }
}

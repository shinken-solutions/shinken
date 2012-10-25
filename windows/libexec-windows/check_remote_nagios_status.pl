#!/usr/bin/perl -w

# check_status.pl Nagios Plugin - Version 1.3
# Last Updated: 1/9/2003
#
# Report any bugs/questions to Russell Scibetti at russell@quadrix.com
#
# check_status Change Log:
#
# To do for 1.4
# - Better help and documentation (separate doc?)
# - Take argument (patterns to match) from a separate spec file
#
# New Addition to 1.3
# - Added ChangeLog information and updated --help output
# - hostdown (hd) argument for how a service check should respond
#   when its host is Down/Unreachable
#   (--hostdown="ok|warning|critical|unknown")
# - Changed name from check_state to check_status
# - Set hostdown to default to OK when the argument isn't specified
# - Number of Hosts checked is now output in OK result
#
# Version 1.2 additions:
#
# - Added ability to handle ack'd and downtimed services differently 
#   depending on argument provided 
#   (--ack="ok|warning|critical|unknown|down|unreachable" 
#    --dt="ok|warning|critical|unknown|down|unreachable")
#
# Version 1.1 additions:
#
# - Added --host=<regex>, --servhost=<regex> to allow for specific field
#   matching (host for matching hostname in host checks, servhost for
#   matching the hostname in service checks, service for matching the 
#   service name in service checks)
# - Output the number of OK services for an OK output
#
# Version 1.0 features:
#
# - Freshness check of status.log (timestamp) 
# - Match service or host checks
# - Can ignore acknowledged or downtimes services/hosts (--ack, --dt)
# - Can output different levels of detail dependent on # of problems
# - Can check for number of critical, warning, or unknowns
#
#############################################################

use Getopt::Long;
use File::stat;

Getopt::Long::Configure('bundling');

GetOptions
        ("V"   => \$version, 	"version"       => \$version,
         "h"   => \$help, 	"help"          => \$help,
	 "v"   => \$verbose,	"verbose"	=> \$verbose,
         "w=s" => \$warning, 	"warning=s"     => \$warning,
         "c=s" => \$critical, 	"critical=s"    => \$critical,
	 "u=s" => \$unknown, 	"unknown=s"	=> \$unknown,
	 "p=s" => \$pattern, 	"pattern=s"	=> \$pattern,
	 "S:s" => \$service,	"service:s"	=> \$service,
	 "s=s" => \$status,	"status=s"	=> \$status,
	 "d=s" => \$dir,	"dir=s"		=> \$dir,
	 "D=s" => \$details,	"details=s"	=> \$details,
	 "H:s" => \$host,	"host:s" 	=> \$host,
         "f=s" => \$freshness,  "freshness=s"   => \$freshness,
	 			"servhost=s" 	=> \$servhost,
	 "a:s" => \$ack,	"ack:s"		=> \$ack,
	 "dt:s"=> \$dt,		"downtime:s"	=> \$dt,
	 "hd:s"=> \$hdown,	"hostdown:s"	=> \$hdown,
	 			"ok"  		=> \$ok);

#Constants:
my $OK       = 0;
my $WARNING  = 1;
my $CRITICAL = 2;
my $UNKNOWN  = 3;

my $crit="CRITICAL";
my $warn="WARNING";
my $unk="UNKNOWN";
my $down="DOWN";
my $unreach="UNREACHABLE";

# Print out Help information
if ($help) {
  printVersion();
  printHelp();
  exitcheck($UNKNOWN);
}

# Print out version information
if ($version) {
  printVersion();
  exitcheck($UNKNOWN);
}

# Check for status log or directory argument or print usage
if (!$status) {
  if (!$dir) {
    print "Usage: $0 -s <status file> | -d <Nagios log dir>\n";
    print "Use the --help option for full list of arguments\n";
    exitcheck($UNKNOWN);
  }
  elsif ($dir =~ m#[^/]/$#) {
    $status = $dir . "status.log";
  }
  else {
    $status = $dir . "/status.log";
  }
}

if (defined $host) {
  if (!$host) {
    $host="[^\\s]*";
  }
}

if (!$host && !$servhost) {
  $servhost="[^\\s]*";
}

if (!$host && !$service) {
  $service="[^\\s]*";
}

if (defined $ack) {
  if (!$ack) {
    $ack="ok";
  }
  elsif (!($ack =~ "ok|critical|warning|unknown|down|unreachable")) {
    print "Invalid value for ack\n";
    exitcheck($UNKNOWN);
  }
}

if (defined $dt) {
  if (!$dt) {
    $dt="ok";
  }
  elsif (!($dt =~ "ok|critical|warning|unknown|down|unreachable")) {
    print "Invalid value for dt\n";
    exitcheck($UNKNOWN);
  }
}

if (defined $hdown) {
  if (!$hdown) {
    $hdown="ok";
  }
  elsif (!($hdown =~ "ok|critical|warning|unknown|down|unreachable")) {
    print "Invalid value for hostdown\n";
    exitcheck($UNKNOWN);
  }
}

my $much_details = 0;

my $ServiceNotOK = "CRITICAL|WARNING|UNKNOWN";
my $HostNotOK	 = "DOWN|UNREACHABLE";

my %numprob = ("WARNING",0,"CRITICAL",0,"UNKNOWN",0,"DOWN",0,"UNREACHABLE",0);

my $CritOnly = 0;
my $WarnOnly = 0;
my $UnkOnly  = 0;

my @wlev;
my @clev;
my @ulev;
my %warnlevel = ("WARNING",0,"CRITICAL",0,"UNKNOWN",0);
my %critlevel = ("WARNING",0,"CRITICAL",0,"UNKNOWN",0);
my %unklevel = ("WARNING",0,"CRITICAL",0,"UNKNOWN",0);
my %hostlevel = ("DOWN",0,"UNREACHABLE",0);

# Store Hosts in downtime
my @hostdowntime;
my $numdowntime = 0;

# Store Hosts in a Down/Unreachable state
my @hostdown;
my $numdown = 0;

# Hash for storing state-change to OK times for hosts:
my %hostoktimes;

# Number of matches in parsing
my $nummatch = 0;

if ($warning) {
  if ($warning =~ /,/) {
    @wlev = split /,/,$warning;
    $warnlevel{"WARNING"} = $wlev[0];
    $warnlevel{"CRITICAL"} = $wlev[1];
    if ($wlev[2] ) {
      $warnlevel{"UNKNOWN"} = $wlev[2];
    }
  }
  else {
    $WarnOnly = $warning;
  }
}
else {
  $WarnOnly = 1;
}

if ($critical) {
  if ($critical =~ /,/) {
    @clev = split /,/,$critical;
    $critlevel{"WARNING"} = $clev[0];
    $critlevel{"CRITICAL"} = $clev[1];
    if ($clev[2] ) {
      $critlevel{"UNKNOWN"} = $clev[2];
    }
  }
  else {
    $CritOnly = $critical;
  }
}
else {
  $CritOnly = 1;
}
  
if ($unknown) {
  if ($unknown =~ /,/) {
    @ulev = split /,/,$unknown;
    $unklevel{"WARNING"} = $ulev[0];
    $unklevel{"CRITICAL"} = $ulev[1];
    if ($ulev[2] ) {
      $unklevel{"UNKNOWN"} = $ulev[2];
    }
  }
  else {
    $UnkOnly = $unknown;
  }
}
else {
  $UnkOnly = 1;
}


if (!$freshness) {
  $freshness = 30 * 60;
}
else {
  $freshness = $freshness * 60;
}

my %ct = ("CRITICAL",0,"WARNING",0,"UNKNOWN",0,"DOWN",0,"UNREACHABLE",0);
my %much_ct = ("CRITICAL",0,"WARNING",0,"UNKNOWN",0,"DOWN",0,"UNREACHABLE",0);

my %output = ("CRITICAL","","WARNING","","UNKNOWN","","DOWN","","UNREACHABLE","");
my %much_output = ("CRITICAL","","WARNING","","UNKNOWN","","DOWN","","UNREACHABLE","");

if ($details) {
  if ($details =~ /,/) {
    my @tempv = split /,/,$details;
    $much_details = $tempv[0];
    $details = $tempv[1]; 
  }
}

open("sta","$status") || die "Cannot open status file $status!";

$curr_time = time;
$file_time = stat($status)->mtime;

if ($curr_time - $file_time > $freshness) {
  printf "State CRITICAL - Status file is stale!!!\n";
  exitcheck($CRITICAL);
}

while(<sta>) {
  chomp;
  if (/^[^\s]+[\s]+HOST;/) {
    @hdata = split /;/,$_;
    
# If you care about matching hosts (not services):
    if ($host && $hdata[1] =~ /$host/) {
      $nummatch++;
      if ( $hdata[2] =~ /$HostNotOK/ ) {
        addproblem($_,$hdata[2]);
      }
    }

# If you are matching services, gather host information:
    else {
      if ( $hdata[2] =~ /$HostNotOK/ ) {
	$hostdown[$numdown] = $hdata[1];
	$numdown++;
      }
      else {
	$hostoktimes{$hdata[1]} = $hdata[4];
      }
      if ( $hdata[17] ne "0" ) {
	$hostdowntime[$numdowntime] = $hdata[1];
	$numdowntime++;
      }
    }
  }
  elsif (!$host && /^[^\s]+[\s]+SERVICE;/) {
    @servdata = split /;/,$_;
    if ( ( $pattern                     && ($_ =~ /$pattern/)) ||
	 (($servdata[1] =~ /$servhost/) && ($servdata[2] =~ /$service/)) ){
      $nummatch++;
      if (($servdata[5] eq "HARD") && ($servdata[3] =~ /$ServiceNotOK/)) {
        addproblem($_,$servdata[3]);
      }
    }
  }
}

close("sta");

if ($nummatch==0) {
  print "Nothing Matches your criteria!\n";
  exitcheck($UNKNOWN);
}

# Count the number of problems (for reference):
if ($host) {
  $total = $numprob{"DOWN"} + $numprob{"UNREACHABLE"};
} 
else {
  $total = $numprob{"WARNING"} + $numprob{"CRITICAL"} +  $numprob{"UNKNOWN"};
}

my $numok = $nummatch - $total;

# If this is a host state check:
if ($host) {
  if ($numprob{"DOWN"}>0 || $numprob{"UNREACHABLE"}>0 ) {
    if  ($details && ($total <= $details)) {
      print "State CRITICAL - $total Host Problems: $output{$down} $output{$unreach}\n";
      exitcheck($CRITICAL);
    }
    else {
      print "State CRITICAL - $numprob{$down} Hosts Down, $numprob{$unreach} Hosts Unreachable\n";
      exitcheck($CRITICAL);
    }
  }
  else {
    print "State OK - $numok Hosts Up, $total Problems\n";
    exitcheck($OK);
  }
}

#If you only defined a Critical level in terms of # of criticals...
elsif ($CritOnly && ($numprob{"CRITICAL"} >= $CritOnly)) {
  countAndPrint($crit,$numprob{$crit},0);
  exitcheck($CRITICAL);
}    

#Critical in terms on # criticals and # warnings...
elsif (!$CritOnly && ($numprob{"WARNING"}  >= $critlevel{"WARNING"}  || 
		      $numprob{"CRITICAL"} >= $critlevel{"CRITICAL"} ||
		      $numprob{"UNKNOWN"}  >= $critlevel{"UNKNOWN"} )) {
  countAndPrint($crit,$total,1);
  exitcheck($CRITICAL);
}

#Warning in terms of # warnings only...
elsif ($WarnOnly && ($numprob{"WARNING"} >= $WarnOnly)) {
  countAndPrint($warn,$numprob{$warn},0);
  exitcheck($WARNING);
}

#Warning in terms of # warnings and # criticals...
elsif (!$WarnOnly && ($numprob{"WARNING"}  >= $warnlevel{"WARNING"} || 
		      $numprob{"CRITICAL"} >= $warnlevel{"CRITICAL"} ||
		      $numprob{"UNKNOWN"}  >= $warnlevel{"UNKNOWN"})) {
  countAndPrint($warn,$total,1);
  exitcheck($WARNING);
}

#Unknown in terms on # unknown only...
elsif ( $UnkOnly && ($numprob{"UNKNOWN"}>=$UnkOnly) ) {
  countAndPrint($unk,$numprob{$unk},0);
  exitcheck($UNKNOWN);
}

#Unknown in terms of # warning, critical, and unknown...
elsif (!$UnkOnly && ($numprob{"WARNING"}  >= $unklevel{"WARNING"} ||
                     $numprob{"CRITICAL"} >= $unklevel{"CRITICAL"} ||
                     $numprob{"UNKNOWN"}  >= $unklevel{"UNKNOWN"})) {
  countAndPrint($unk,$total,1);
  exitcheck($UNKNOWN);
}

# Everything is OK!
else {
  print "State OK -  $numok OK, $total problems\n";
  exitcheck($OK);
}



############################
# Subroutines
############################

# Return the proper exit code for Critical, Warning, Unknown, or OK
sub exitcheck {
  if ($ok) {
    exit 0;
  }
  else {
    exit $_[0];
  }
} 

# Decide what to print for services:
sub countAndPrint {
  my $state = $_[0];
  my $count = $_[1];
  my $alltypes = $_[2];
  my $output = "State $state - ";

  if ($details) {
    if ($count<=$much_details) {
      if ($alltypes) {
        $output .= "$count problems: $much_output{$crit} $much_output{$warn} $much_output{$unk}";
      }
      else {
        $output .= "$count \L$state\E: $much_output{$state}";
      }
    }
    elsif ($count<=$details) {
      if ($alltypes) {
        $output .= "$count problems: $output{$crit} $output{$warn} $output{$unk}";
      }
      else {
        $output .= "$count \L$state\E: $output{$state}";
      }
    }
    else {
      if ($alltypes) {
        $output .= "$numprob{$crit} critical, $numprob{$warn} warning, $numprob{$unk} unknown";
      }
      else {
        $output .= "$count \L$state\E"; 
      }
    }
  }
  else {
    $output .= "$count problems";
  }

  print "$output\n";
}
  

# Add-in the problem found in the status log
sub addproblem {

  $test = 1;
  $type = $_[1];
  my $diffout = "";

  my @values = split /;/,$_[0];

  if (!$host) {
    my $namehold = $values[1];
    if ($ack && ($values[13] eq "1")) {
      if ($ack =~ "ok") {
        $test = 0;
      }
      else {
        $type = "\U$ack";
      }
    }
    elsif ($hdown && grep /$namehold/, @hostdown) {
      if ($hdown =~ "ok") {
        $test = 0;
      }
      else {
        $type = "\U$hdown";
	$diffout = "$values[1] is down";
      }
    }
    elsif ($dt && (($values[27] ne "0") || (grep /$namehold/, @hostdowntime))){
      if ($dt =~ "ok") {
        $test = 0;
      }
      else {
        $type = "\U$dt";
      }
    }
    elsif (exists $hostoktimes{$namehold}) {
      # If the state change time of the host is more recent than the last
      # service check, must wait until the next service check runs!
      if ($hostoktimes{$namehold} > $values[6]) {
	$test = 0;
      }
    }
  }
  else {
    if ($ack && $values[5]) { 
      if ($ack =~ "ok") {
        $test = 0;
      }
      else {
        $type = "\U$ack";
      }
    }
    elsif ($dt && ($values[17] ne "0")) {
      if ($dt =~ "ok") {
        $test = 0;
      }
      else {
        $type = "\U$dt";
      }
    }
  }

  if ($details && $test) {
    if (!$host) {
      if ($diffout) {
        $much_output{$type} .= " $diffout;";
	$output{$type} .= "$diffout;";
	$much_ct{$type}++;
	$ct{$type}++;
      }
      else {
        if ($much_details && $much_ct{$type}<$much_details) {
          $much_output{$type} .= " $values[2] on $values[1] $values[31];";
          $much_ct{$type}++;
        }
        if ($ct{$type} < $details) {
          $output{$type} .= " $values[2] on $values[1];";
          $ct{$type}++;
        }
      }
    }  
    else {
        $much_output{$type} .= " $values[1] $_[1] $values[20],";
	$much_ct{type}++;
        $output{$type} .= " $values[1] HOST $_[1],";
	$ct{$type}++;
    }
  }
  if ($test) {
    $numprob{$type}++;
  }
}

################################
#
# Version and Help Information
#
################################

sub printVersion {
  printf <<EndVersion;
$0 (nagios-plugins) 1.3
The nagios plugins come with ABSOLUTELY NO WARRANTY. You may redistribute
copies of the plugins under the terms of the GNU General Public License.
For more information about these matters, see the file named COPYING.
EndVersion
}

sub printHelp {
  printf <<EOF;

This plugin parses through the Nagios status log and will return a 
Critical, Warning, or Unknown state depending on the number of 
Critical, Warning, and/or Unknown services found in the log
(or Down/Unreachable hosts when matching against hosts)  

Usage: $0 -s <Status File> | -d <Nagios Log Directory> 
	[-w #[,#][,#]] [-c #[,#][,#]] [-u #[,#][,#]]
        [--service=<RegEx> | --servhost=<RegEx> | --pattern=<RegEx> |
	 --host            | --host=<RegEx>]
        [--ack[=string]]  [--dt[=string]]  [--hostdown[=string]]
        [-D #[,#]]  [--ok]  [-f <Log freshness in # minutes>]
       $0 --help
       $0 --version
NOTE: One of -s and -d must be specified

Options:
 -s, --status=FILE_NAME
   Location and name of status log (e.g. /usr/local/nagios/var/status.log)
 -d, --dir=DIRECTORY_NAME
   Directory that contains the nagios logs (e.g. /usr/local/nagios/var/)
 -w, --warning=INTEGER[,INTEGER][,INTEGER]
   #:     Number of warnings to result in a WARNING state
          OR
   #,#:   Warning,Criticals to result in a WARNING state
	  OR
   #,#,#: Warning,Critical,Unknown to result in a WARNING state 
   Default: -w=1
 -c, --critical=INTEGER[,INTEGER][,INTEGER]
   #:     Number of criticals to result in a CRITICAL state
          OR
   #,#:   Warning,Criticals to result in a CRITICAL state
          OR
   #,#,#: Warning,Critical,Unknown to result in a CRITICAL state
   Default: -c=1
 -u, --unknown=INTEGER[,INTEGER][,INTEGER]
   #:     Number of unknowns to result in a UNKNOWN state
          OR
   #,#:   Warning,Criticals to result in a UNKNOWN state
          OR
   #,#,#: Warning,Critical,Unknown to result in a UNKNOWN state
   Default: -u=1
 -r, --service[=REGEX]
   Only match services [that match the RegEx]
   (--service is default setting if no other matching arguments provided)
 --servhost=REGEX
   Only match services whose host match the RegEx
 -p, --pattern=REGEX
   Only parse for this regular expression (services only, not hosts)
 --host[=REGEX]
   Report on the state of hosts (whose name matches the RegEx if provided)
 -a, --ack[=ok|warning|critical|unknown|down|unreachable]
   Handle Acknowledged problems [--ack defaults to ok]
 --dt, --downtime[=ok|warning|critical|unknown|down|unreachable]
   Handle problems in scheduled downtime [--dt defaults to ok]
 --hd, --hostdown[=ok|warning|critical|unknown|down|unreachable]
   Handle services whose Host is down [--hd defaults to ok]
 -D, --details=INTEGER[,INTEGER]
   Amount of verbosity to output
   If # problems: 
    <= 1st integer, return full details (each plugin's output) 
    <= 2nd integer, return some details (list each service host pair)
    >  2nd integer, return the # of problems
 -f, --freshness=INTEGER
   Number of minutes old the log can be to make sure Nagios is running
   (Default = 30 minutes)
 --ok
   Return an OK exit code, regardless of number of problems found
 -h, --help
   Print detailed help screen
 -V, --version
   Print version information 

For service checking (use --service and/or --servhost): 
1.  The values of warning, critical, and unknown default to 1, i.e.
$0 will return CRITICAL if there is at least 1 critical service, 
WARNING if there is at least 1 warning service, and UNKNOWN if there is
at least one unknown service.

2.  If a service's host is DOWN or UNREACHABLE, $0 will use the 
value of --hostdown to determine how to treat the service.  Without that
argument, $0 will count the service as OK.

3.  If a service's host is OK, but the last host-state change occurred more 
recently than the last service check, $0 will ignore that service
(want to wait until the service has been checked after a host has recovered
or you may get service alert for services that still need to be checked)

4.  If the --dt, --ack, or --hd tags are used, $0 will use the value
of the arguments to determine how to handle services in downtime, acknowledged,
or with down hosts (default=OK). For service checks, --dt will also check
if the service's host is in a downtime.

For host checking (use --host):
1.  Using the --host argument, $0 will look for DOWN and UNREACHABLE
hosts.  If any are found, $0 will return a CRITICAL.  You can provide
an REGEX for --host to only check hosts with matching host names. 

2.  If the --dt or --ack tags are used, $0 will use the value of the
--dt/--ack arguments to determine the state of the host (default is OK)

EOF
}

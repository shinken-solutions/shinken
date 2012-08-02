#!/usr/bin/perl -w 
############################## check_snmp_hpux_load #################
# Version : 1.3.1
# Date : 8 Sept 2006
# Author2 : Paul Vogt ( paul dot unix at gmail.com )
# Author  : Patrick Proy ( patrick at proy.org)
# Help : http://www.manubulon.com/nagios/
# Licence : GPL - http://www.fsf.org/licenses/gpl.txt
# Changelog : HP-UX load added.
# Contributors : F. Lacroix and many others !!!
#################################################################
# See /opt/OV/newconfig/AGENT-MAN/snmp_mibs/hp-unix if available
# Help : ./check_snmp_hpux_load.pl -h
#
# Get load and cpu numbers. CPU numbers are for performance data only. 
# There is only a check on one load number with -M the 1 min, 5min or 15 min average can
# be selected to apply the warning and critical level check to.

use strict;
use Net::SNMP;
use Getopt::Long;

# Nagios specific

use lib "/usr/local/nagios/libexec";
use utils qw(%ERRORS $TIMEOUT);
#my $TIMEOUT = 15;
#my %ERRORS=('OK'=>0,'WARNING'=>1,'CRITICAL'=>2,'UNKNOWN'=>3,'DEPENDENT'=>4);


# average load : 0 = 1 min, 1 = 5 and 2 = 15 min
my @hpux_load_min=
	(".1.3.6.1.4.1.11.2.3.1.1.3.0",		#  1 min average
	 ".1.3.6.1.4.1.11.2.3.1.1.4.0",		#  5 min average
	 ".1.3.6.1.4.1.11.2.3.1.1.5.0");	# 15 min average
	 
my @hpux_cpu=
	(".1.3.6.1.4.1.11.2.3.1.1.13.0",	# user
	 ".1.3.6.1.4.1.11.2.3.1.1.14.0",	# system
	 ".1.3.6.1.4.1.11.2.3.1.1.15.0",	# idle
	 ".1.3.6.1.4.1.11.2.3.1.1.16.0");	# nice

# Globals

my $Version='1.3.1';

my $o_host = 	undef; 		# hostname
my $o_community = undef; 	# community
my $o_port = 	161; 		# port
my $o_help=	undef; 		# wan't some help ?
my $o_verb=	undef;		# verbose mode
my $o_version=	undef;		# print version
my $o_mode= 5;	
# End compatibility
my $o_warn=	undef;		# warning level
my $o_warnL=	undef;		# warning levels Load
my $o_crit=	undef;		# critical level
my $o_critL=	undef;		# critical level Load
my $o_timeout=  undef; 		# Timeout (Default 5)
my $o_perf=     undef;          # Output performance data
my $o_version2= undef;          # use snmp v2c
# SNMPv3 specific
my $o_login=	undef;		# Login for snmpv3
my $o_passwd=	undef;		# Pass for snmpv3
my $v3protocols=undef;	# V3 protocol list.
my $o_authproto='md5';		# Auth protocol
my $o_privproto='des';		# Priv protocol
my $o_privpass= undef;		# priv password

# functions

sub p_version { print "check_snmp_hpux_load version : $Version\n"; }

sub print_usage {
    print "Usage: $0 [-v] -H <host> -C <snmp_community> [-2] | (-l login -x passwd [-X pass -L <authp>,<privp>])  [-p <port>] -w <warn level> -c <crit level> [-M <1|5|15>] [-f] [-t <timeout>] [-V]\n";
}

sub isnnum { # Return true if arg is not a number
  my $num = shift;
  if ( $num =~ /^(\d+\.?\d*)|(^\.\d+)$/ ) { return 0 ;}
  return 1;
}

sub help {
   print "\nSNMP Load & CPU Monitor for Nagios version ",$Version,"\n";
   print " (c) 2007 Paul Vogt\n";
   print "GPL licence, (c)2004-2006 Patrick Proy\n\n";
   print_usage();
   print <<EOT;
-v, --verbose
   print extra debugging information 
-h, --help
   print this help message
-H, --hostname=HOST
   name or IP address of host to check
-C, --community=COMMUNITY NAME
   community name for the host's SNMP agent (implies v1 protocol)
-2, --v2c
   Use snmp v2c
-l, --login=LOGIN ; -x, --passwd=PASSWD
   Login and auth password for snmpv3 authentication 
   If no priv password exists, implies AuthNoPriv 
-X, --privpass=PASSWD
   Priv password for snmpv3 (AuthPriv protocol)
-L, --protocols=<authproto>,<privproto>
   <authproto> : Authentication protocol (md5|sha : default md5)
   <privproto> : Priv protocole (des|aes : default des) 
-P, --port=PORT
   SNMP port (Default 161)
-M, --mode=MODE
   Possible values 1, 5 (default) or 15  
-w, --warn=INTEGER
    warning level for average load in percent
-c, --crit=INTEGER
   critical level for average load in percent
-f, --perfparse
   Perfparse compatible output
-t, --timeout=INTEGER
   timeout for SNMP in seconds (Default: 5)
-V, --version
   prints version number
EOT
}

# For verbose output
sub verb { my $t=shift; print $t,"\n" if defined($o_verb) ; }

sub check_options {
    Getopt::Long::Configure ("bundling");
    GetOptions(
   	'v'	=> \$o_verb,		'verbose'	=> \$o_verb,
        'h'     => \$o_help,    	'help'        	=> \$o_help,
        'H:s'   => \$o_host,		'hostname:s'	=> \$o_host,
        'p:i'   => \$o_port,   		'port:i'	=> \$o_port,
        'C:s'   => \$o_community,	'community:s'	=> \$o_community,
	'l:s'	=> \$o_login,		'login:s'	=> \$o_login,
	'x:s'	=> \$o_passwd,		'passwd:s'	=> \$o_passwd,
	'X:s'	=> \$o_privpass,		'privpass:s'	=> \$o_privpass,
	'L:s'	=> \$v3protocols,		'protocols:s'	=> \$v3protocols,   
        't:i'   => \$o_timeout,       	'timeout:i'     => \$o_timeout,
	'V'	=> \$o_version,		'version'	=> \$o_version,
	'2'     => \$o_version2,        'v2c'           => \$o_version2,
        'c:s'   => \$o_crit,            'critical:s'    => \$o_crit,
        'w:s'   => \$o_warn,            'warn:s'        => \$o_warn,
        'f'     => \$o_perf,            'perfparse'     => \$o_perf,
	'M:s'	=> \$o_mode,		'mode:s'	=> \$o_mode
	);
	
    # Basic checks
	if (defined($o_timeout) && (isnnum($o_timeout) || ($o_timeout < 2) || ($o_timeout > 60))) 
	  { print "Timeout must be >1 and <60 !\n"; print_usage(); exit $ERRORS{"UNKNOWN"}}
	if (!defined($o_timeout)) {$o_timeout=5;}
    if (defined ($o_help) ) { help(); exit $ERRORS{"UNKNOWN"}};
    if (defined($o_version)) { p_version(); exit $ERRORS{"UNKNOWN"}};
    if ( ! defined($o_host) ) # check host and filter 
	{ print_usage(); exit $ERRORS{"UNKNOWN"}}
    # check snmp information
    if ( !defined($o_community) && (!defined($o_login) || !defined($o_passwd)) )
      {
        print "Put snmp login info!\n";
	print_usage(); exit $ERRORS{"UNKNOWN"}
      }
    if ((defined($o_login) || defined($o_passwd)) && (defined($o_community) || defined($o_version2)) )
      {
        print "Can't mix snmp v1,2c,3 protocols!\n";
        print_usage(); exit $ERRORS{"UNKNOWN"}
      }
    if (defined ($v3protocols))
      {
	if (!defined($o_login))
	  {
	    print "Put snmp V3 login info with protocols!\n";
	    print_usage(); exit $ERRORS{"UNKNOWN"}
	  }
	my @v3proto=split(/,/,$v3protocols);
	if ((defined ($v3proto[0])) && ($v3proto[0] ne "")) {$o_authproto=$v3proto[0];	}	# Auth protocol
	if (defined ($v3proto[1])) {$o_privproto=$v3proto[1];	}	# Priv  protocol
	if ((defined ($v3proto[1])) && (!defined($o_privpass)))
	  {
	    print "Put snmp V3 priv login info with priv protocols!\n";
	    print_usage(); exit $ERRORS{"UNKNOWN"}
	  }
       }
# Check warnings and critical
      if (!defined($o_warn) || !defined($o_crit))
 	{
	  print "put warning and critical info!\n";
	  print_usage(); exit $ERRORS{"UNKNOWN"}
	}
# Get rid of % sign
      $o_warn =~ s/\%//g; 
      $o_crit =~ s/\%//g;

      if ( isnnum($o_warn) || isnnum($o_crit) ) 
	{ 
	  print "Numeric value for warning or critical !\n";
	  print_usage(); exit $ERRORS{"UNKNOWN"}
	}
      if ($o_warn > $o_crit) 
        {
	  print "warning <= critical ! \n";
	  print_usage(); exit $ERRORS{"UNKNOWN"}
	}
	$o_warnL= $o_warn;
	$o_critL= $o_crit;
}

########## MAIN #######

check_options();

# Check gobal timeout if snmp screws up
if (defined($TIMEOUT)) {
  verb("Alarm at $TIMEOUT + 5");
  alarm($TIMEOUT+5);
} else {
  verb("no global timeout defined : $o_timeout + 10");
  alarm ($o_timeout+10);
}

# Connect to host
my ($session,$error);
if ( defined($o_login) && defined($o_passwd)) {
  # SNMPv3 login
  verb("SNMPv3 login");
    if (!defined ($o_privpass)) {
  verb("SNMPv3 AuthNoPriv login : $o_login, $o_authproto");
    ($session, $error) = Net::SNMP->session(
      -hostname   	=> $o_host,
      -version		=> '3',
      -username		=> $o_login,
      -authpassword	=> $o_passwd,
      -authprotocol	=> $o_authproto,
      -timeout          => $o_timeout
    );  
  } else {
    verb("SNMPv3 AuthPriv login : $o_login, $o_authproto, $o_privproto");
    ($session, $error) = Net::SNMP->session(
      -hostname   	=> $o_host,
      -version		=> '3',
      -username		=> $o_login,
      -authpassword	=> $o_passwd,
      -authprotocol	=> $o_authproto,
      -privpassword	=> $o_privpass,
	  -privprotocol => $o_privproto,
      -timeout          => $o_timeout
    );
  }
} else {
	if (defined ($o_version2)) {
		# SNMPv2 Login
		verb("SNMP v2c login");
		  ($session, $error) = Net::SNMP->session(
		 -hostname  => $o_host,
		 -version   => 2,
		 -community => $o_community,
		 -port      => $o_port,
		 -timeout   => $o_timeout
		);
  	} else {
	  # SNMPV1 login
	  verb("SNMP v1 login");
	  ($session, $error) = Net::SNMP->session(
		-hostname  => $o_host,
		-community => $o_community,
		-port      => $o_port,
		-timeout   => $o_timeout
	  );
	}
}
if (!defined($session)) {
   printf("ERROR opening session: %s.\n", $error);
   exit $ERRORS{"UNKNOWN"};
}

my $exit_val=undef;

## Checking hpux load. Only check on one number choosen by the -M option

my $mode_idx;
my $load_text;
my $warn1=0; my $warn5=0; my $warn15=0; my $crit1=0; my $crit5=0; my $crit15=0;

if ( $o_mode == 1 )
  { $mode_idx=$hpux_load_min[0];
    $load_text="load_1_min";
    $warn1=$o_warnL;
    $crit1=$o_critL;
  }
elsif ( $o_mode == 5 )
  { $mode_idx=$hpux_load_min[1];
    $load_text="load_5_min";
    $warn5=$o_warnL;
    $crit5=$o_critL;
  }
elsif ( $o_mode == 15 )
  { $mode_idx=$hpux_load_min[2];
    $load_text="load_15_min";
    $warn15=$o_warnL;
    $crit15=$o_critL;
  }
else {
  print("Invalid mode $o_mode, valid values <1|5|15>\n");
  print_usage(); exit $ERRORS{"UNKNOWN"}
  }
verb("Checking hpux load for oid: $mode_idx");
my @oidlists = ( @hpux_load_min,@hpux_cpu );

my $resultat = (Net::SNMP->VERSION < 4) ?
	  $session->get_request(@oidlists)
	: $session->get_request(-varbindlist => \@oidlists);
	
if (!defined($resultat)) {
   printf("ERROR: Load table : %s.\n", $session->error);
   $session->close;
   exit $ERRORS{"UNKNOWN"};
}

   $session->close;

	
foreach my $key ( keys %$resultat) { verb("$key  :res: $$resultat{$key}"); }

if (!defined ($$resultat{$mode_idx})) {
  print "No Load information : UNKNOWN $mode_idx\n";
  exit $ERRORS{"UNKNOWN"};
}

my $load = $$resultat{$mode_idx}/100.;


$exit_val=$ERRORS{"OK"};

  if ( $load > $o_critL ) {
    print " $load_text=$load > $o_critL : CRITICAL";
    $exit_val=$ERRORS{"CRITICAL"};
  }
  elsif ( $load > $o_warnL ) 
  {
    print " $load_text=$load > $o_warnL : WARNING"; 
    $exit_val=$ERRORS{"WARNING"};
  }
  else
  {
    print "$load_text=$load% ; OK" ;
  }

# Performance data, load and cpu information.
# The idea is to put the numbers in rrd files. The format is
#
#  load1=<n>;warn1;crit1 load5=<m>;warn5;crit5 load15=<o>;warn15;crit15 user=<ticks>
#  nice=<ticks> idle=<ticks> sys=<ticks>
#
# Note1 on hpux the ticks are <total ticks> / <no of CPUS>.

if (defined($o_perf)) {
  my $load1=$$resultat{$hpux_load_min[0]}/100.;
  my $load5=$$resultat{$hpux_load_min[1]}/100.;
  my $load15=$$resultat{$hpux_load_min[2]}/100.;
  my $user=$$resultat{$hpux_cpu[0]};
  my $system=$$resultat{$hpux_cpu[1]};
  my $idle=$$resultat{$hpux_cpu[2]};
  my $nice=$$resultat{$hpux_cpu[3]};
  
   print " | load1m=$load1;$warn1;$crit1 load2m=$load5;$warn5;$crit5 load15m=$load15;$warn15;$crit15 user=$user system=$system idle=$idle nice=$nice\n";
} else {
 print "\n";
}

exit $exit_val;


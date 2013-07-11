#!/usr/bin/perl -w 
############################## check_snmp_boostedge.pl #################
# Version : 1.0
# Date : Jan 16 2007
# Author  : Patrick Proy ( patrick at proy.org)
# Help : http://www.manubulon.com/nagios/
# Licence : GPL - http://www.fsf.org/licenses/gpl.txt
# Changelog : 
# Contributors : 
#################################################################
#
# Help : ./check_snmp_boostedge.pl -h
#

use strict;
use Net::SNMP;
use Getopt::Long;

# Nagios specific

use lib "/usr/local/shinken/libexec";
use utils qw(%ERRORS $TIMEOUT);
#my $TIMEOUT = 15;
#my %ERRORS=('OK'=>0,'WARNING'=>1,'CRITICAL'=>2,'UNKNOWN'=>3,'DEPENDENT'=>4);

# SNMP Datas

my $be_global_status=	"1.3.6.1.4.1.4185.12.1.1.3.0"; # boostedge global status (stop(0), start(1))

my $be_service_number=	"1.3.6.1.4.1.4185.12.1.5.1.0"; # beServiceNumber

my $be_service_table=	"1.3.6.1.4.1.4185.12.1.5";  		# beServices
my $be_service_name=	"1.3.6.1.4.1.4185.12.1.5.2.1.2"; 	# beServiceName
my $be_service_status=	"1.3.6.1.4.1.4185.12.1.5.2.1.4"; 	# status ("RUNNING")
my $be_service_mode=	"1.3.6.1.4.1.4185.12.1.5.2.1.5";	# beServiceMode (disabled(0), enabled(1))
my $be_service_datain=	"1.3.6.1.4.1.4185.12.1.5.2.1.6";	# beServiceDataIn (Not populated for now : HTTP/S - V5.2.16.0)
my $be_service_dataout=	"1.3.6.1.4.1.4185.12.1.5.2.1.7";	# beServiceDataOut (Not populated for now : HTTP/S - V5.2.16.0)
my $be_service_connect=	"1.3.6.1.4.1.4185.12.1.5.2.1.8";	# beServiceConnect (Not populated for now : HTTP/S - V5.2.16.0)

			
# Globals

my $Version='1.0';

my $o_host = 	undef; 		# hostname
my $o_community = undef; 	# community
my $o_port = 	161; 		# port
my $o_help=	undef; 		# wan't some help ?
my $o_verb=	undef;		# verbose mode
my $o_version=	undef;		# print version
my $o_timeout=  undef; 		# Timeout (Default 5)
my $o_perf=     undef;          # Output performance data
my $o_version2= undef;          # use snmp v2c
# Specific
my $o_service=	undef;	# service regexp selection
my $o_nservice=	undef;	# service number expected

# SNMPv3 specific
my $o_login=	undef;		# Login for snmpv3
my $o_passwd=	undef;		# Pass for snmpv3
my $v3protocols=undef;	# V3 protocol list.
my $o_authproto='md5';		# Auth protocol
my $o_privproto='des';		# Priv protocol
my $o_privpass= undef;		# priv password

# functions

sub p_version { print "check_snmp_boostedge version : $Version\n"; }

sub print_usage {
    print "Usage: $0 [-v] -H <host> -C <snmp_community> [-2] | (-l login -x passwd [-X pass -L <authp>,<privp>]) -s <service> -n <number> [-p <port>] [-f] [-t <timeout>] [-V]\n";
}

sub isnnum { # Return true if arg is not a number
  my $num = shift;
  if ( $num =~ /^(\d+\.?\d*)|(^\.\d+)$/ ) { return 0 ;}
  return 1;
}

sub set_status { # return worst status with this order : OK, unknwonw, warning, critical 
  my $new_status=shift;
  my $cur_status=shift;
  if (($cur_status == 0)|| ($new_status==$cur_status)){ return $new_status; }
  if ($new_status==3) { return $cur_status; }
  if ($new_status > $cur_status) {return $new_status;}
  return $cur_status;
}

sub is_pattern_valid { # Test for things like "<I\s*[^>" or "+5-i"
 my $pat = shift;
 if (!defined($pat)) { $pat=" ";} # Just to get rid of compilation time warnings
 return eval { "" =~ /$pat/; 1 } || 0;
}

sub help {
   print "\nSNMP Boostedge service monitor for Nagios version ",$Version,"\n";
   print "GPL Licensen, (c)2006-2007 Patrick Proy\n\n";
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
-s, --service=<service>
   Regexp of service to select
-n, --number=<number>
   Number of services selected that must be in running & enabled state
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
	'v'		=> \$o_verb,		'verbose'		=> \$o_verb,
	'h'     => \$o_help,    	'help'        	=> \$o_help,
	'H:s'   => \$o_host,		'hostname:s'	=> \$o_host,
	'p:i'   => \$o_port,   		'port:i'		=> \$o_port,
	'C:s'   => \$o_community,	'community:s'	=> \$o_community,
	'l:s'	=> \$o_login,		'login:s'		=> \$o_login,
	'x:s'	=> \$o_passwd,		'passwd:s'		=> \$o_passwd,
	'X:s'	=> \$o_privpass,	'privpass:s'	=> \$o_privpass,
	'L:s'	=> \$v3protocols,	'protocols:s'	=> \$v3protocols,   
	't:i'   => \$o_timeout,     'timeout:i'		=> \$o_timeout,
	'V'		=> \$o_version,		'version'		=> \$o_version,
	'2'     => \$o_version2,	'v2c'			=> \$o_version2,
	'f'     => \$o_perf,		'perfparse'		=> \$o_perf,
	's:s'	=> \$o_service,		'service:s'		=> \$o_service,
	'n:i'	=> \$o_nservice,	'number:i'		=> \$o_nservice
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
	  { print "Put snmp login info!\n"; print_usage(); exit $ERRORS{"UNKNOWN"}}
	if ((defined($o_login) || defined($o_passwd)) && (defined($o_community) || defined($o_version2)) )
	  { print "Can't mix snmp v1,2c,3 protocols!\n"; print_usage(); exit $ERRORS{"UNKNOWN"}}
	if (defined ($v3protocols)) {
	  if (!defined($o_login)) { print "Put snmp V3 login info with protocols!\n"; print_usage(); exit $ERRORS{"UNKNOWN"}}
	  my @v3proto=split(/,/,$v3protocols);
	  if ((defined ($v3proto[0])) && ($v3proto[0] ne "")) {$o_authproto=$v3proto[0];	}	# Auth protocol
	  if (defined ($v3proto[1])) {$o_privproto=$v3proto[1];	}	# Priv  protocol
	  if ((defined ($v3proto[1])) && (!defined($o_privpass))) {
	    print "Put snmp V3 priv login info with priv protocols!\n"; print_usage(); exit $ERRORS{"UNKNOWN"}}
	}
	if (!defined($o_service) || !(is_pattern_valid($o_service))) 
		{ print "Service selection must be set and be a valid regexp\n"; print_usage(); exit $ERRORS{"UNKNOWN"}}
	if (!defined($o_nservice) || isnnum($o_nservice))
		{ print "Service number must be set and be an integer\n"; print_usage(); exit $ERRORS{"UNKNOWN"}}
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

# Get global status
my @oidlist=($be_global_status);
my $resultat = (Net::SNMP->VERSION < 4) ?
          $session->get_request(@oidlist)
        : $session->get_request(-varbindlist => \@oidlist);

if (!defined($resultat)) {
   printf("ERROR: Gloabal status table : %s.\n", $session->error);
   $session->close;
   exit $ERRORS{"UNKNOWN"};
}

if ($$resultat{$be_global_status} != 1) {
  print "Global service is stopped (",$$resultat{$be_global_status},") : CRITICAL\n";
  exit $ERRORS{"CRITICAL"};
}

$resultat=undef;
# Get service  table
$resultat = (Net::SNMP->VERSION < 4) ? 
		  $session->get_table($be_service_table)
		: $session->get_table(Baseoid => $be_service_table); 
		
if (!defined($resultat)) {
   printf("ERROR: Description table : %s.\n", $session->error);
   $session->close;
   exit $ERRORS{"UNKNOWN"};
}
$session->close;

my $output="";
my $output_perf="";
my $global_status=0;
my ($nservice,$nservice_ok)=(0,0);
my (@found_service,@service_state)=undef;

foreach my $key ( keys %$resultat) {
	verb("OID : $key, Desc : $$resultat{$key}");
	if ( ($key =~ /$be_service_name\./) && ($$resultat{$key} =~ /$o_service/ )) { # Get index of service with name
		$found_service[$nservice]=$$resultat{$key};
		$key =~ s/$be_service_name//;
		$service_state[$nservice]=$$resultat{$be_service_status.$key};
		if (($service_state[$nservice] ne "RUNNING") || ($$resultat{$be_service_mode.$key}!=1)) { 
			$service_state[$nservice].="(".$$resultat{$be_service_mode.$key}.")";			
			$global_status=2;
		} else {
			$nservice_ok++
		}
		$nservice++;
		verb ("Found service $found_service[$nservice-1]");
	}	
}

if ($o_nservice > $nservice_ok) {
	for (my $i=0;$i<$nservice;$i++) {
		if ($output ne "") { $output .= ", "; }
		$output .= $found_service[$i] . ":" . $service_state[$i];
	}
	if ($output ne "") { $output .= ", "; }
	$output .= ":" . $nservice_ok . " services OK < ".$o_nservice;
	print $output, " : CRITICAL\n";
	exit $ERRORS{"CRITICAL"};
}

$output = $nservice_ok . " services OK";
if ($o_nservice < $nservice_ok) {
	print $output," > $o_nservice : WARNING\n";
	exit $ERRORS{"WARNING"};
}
print $output," : OK\n";
exit $ERRORS{"OK"};

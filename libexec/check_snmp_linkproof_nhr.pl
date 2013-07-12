#!/usr/bin/perl -w 
############################## check_snmp_linkproof_nhr #################
# Version : 1.0
# Date : Aug 24 2006
# Author  : Patrick Proy ( patrick at proy.org)
# Help : http://www.manubulon.com/nagios/
# Licence : GPL - http://www.fsf.org/licenses/gpl.txt
# Changelog : 
# Contributors : 
#################################################################
#
# Help : ./check_snmp_linkproof_nhr.pl -h
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

my $lp_type = "1.3.6.1.4.1.89.35.1.38.1.1.13"; # node type (1=regular, 2=nhr).
my $lp_name = "1.3.6.1.4.1.89.35.1.38.1.1.2"; # nhr name
my $lp_users = "1.3.6.1.4.1.89.35.1.38.1.1.5"; # nhr users
my $lp_state = "1.3.6.1.4.1.89.35.1.38.1.1.3"; # state : 1=active, 2=Notinservice, 3= nonewsessions.
my $lp_port = "1.3.6.1.4.1.89.35.1.38.1.1.15"; # nhr users

			
# Globals

my $Version='1.0';

my $o_host = 	undef; 		# hostname
my $o_community = undef; 	# community
my $o_port = 	161; 		# port
my $o_help=	undef; 		# wan't some help ?
my $o_verb=	undef;		# verbose mode
my $o_version=	undef;		# print version
# specific 
my $o_nhr_num= undef;	# nhr number TODO
my $o_nhr_max=	undef;	# Maximum connexions TODO

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

sub p_version { print "check_snmp_linkproof_nhr version : $Version\n"; }

sub print_usage {
    print "Usage: $0 [-v] -H <host> -C <snmp_community> [-2] | (-l login -x passwd [-X pass -L <authp>,<privp>]) [-p <port>] [-f] [-t <timeout>] [-V]\n";
}

sub isnnum { # Return true if arg is not a number
  my $num = shift;
  if ( $num =~ /^(\d+\.?\d*)|(^\.\d+)$/ ) { return 0 ;}
  return 1;
}

sub help {
   print "\nSNMP Radware Linkproof NHR monitor for Nagios version ",$Version,"\n";
   print "(c)2004-2006 Patrick Proy\n\n";
   print_usage();
   print <<EOT;
The plugin will test all nhr configured and will return 
OK if all nhr are active
WARNING if one nhr at least is in "no new session" or "inactive" mode.
CRITICAL if all nhr are inactive. 
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
        'f'     => \$o_perf,            'perfparse'     => \$o_perf,
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
########### NHR checks ##############

my $nhr_num=0; # nujmber of NHR
my @nhr_table=undef; # index of NHR 
my $output=undef; 
my $perf_output="";
my @oids=undef; 
my $inactive_nhr=0; 
my $global_status=0;

# Get load table
my $resultat = (Net::SNMP->VERSION < 4) ? 
		  $session->get_table($lp_type)
		: $session->get_table(Baseoid => $lp_type); 
		
if (!defined($resultat)) {
   printf("ERROR: NHR table : %s.\n", $session->error);
   $session->close;
   exit $ERRORS{"UNKNOWN"};
}
my $oidindex=0;
foreach my $key ( keys %$resultat) {
   verb("OID : $key, Desc : $$resultat{$key}");
   if ($$resultat{$key} == 2) { # found NHR
     $key =~ s/$lp_type\.//;
	 $nhr_table[$nhr_num++]=$key;
	 $oids[$oidindex++]=$lp_name.".".$key;
	 $oids[$oidindex++]=$lp_users.".".$key;
	 $oids[$oidindex++]=$lp_state.".".$key;
	 $oids[$oidindex++]=$lp_port.".".$key;	 
	 verb ("found nhr : $key");
   }
}

if ($nhr_num==0) {
  print "No NHR found : CRITICAL\n";
  exit $ERRORS{"CRITICAL"};
}

my $result=undef;
if (Net::SNMP->VERSION < 4) {
  $result = $session->get_request(@oids);
} else {
  if ($session->version == 0) { 
    # snmpv1
    $result = $session->get_request(-varbindlist => \@oids);
  } else {
    # snmp v2c or v3 : get_bulk_request is not really good for this, so do simple get
    $result = $session->get_request(-varbindlist => \@oids);
  }
}

if (!defined($result)) {
   printf("ERROR: NHR table get : %s.\n", $session->error);
   $session->close;
   exit $ERRORS{"UNKNOWN"};
}

my ($nhr_name,$nhr_state,$nhr_users)=(undef,undef,undef);
my @nhr_text_state=("","active","Not in service","No new session");
for (my $i=0;$i<$nhr_num;$i++) {
  if (defined ($output)) { $output .= "; ";} 
  $nhr_name=$$result{$lp_name .".".$nhr_table[$i]};
  $nhr_state=$$result{$lp_state .".".$nhr_table[$i]};
  $nhr_users=$$result{$lp_users .".".$nhr_table[$i]};
  $output .= $nhr_name ."(" . $nhr_users . "):" . $nhr_text_state[$nhr_state];
  if ($nhr_state == 1) {
    if (defined ($o_perf)) {
      if (defined ($perf_output)) { $perf_output .= " ";} 
	  $perf_output .= $nhr_name."=".$nhr_users;
    }
  } elsif ($nhr_state == 2) { 
    $inactive_nhr++; $global_status=1;
  } else { $global_status=1;}
}

$session->close;

if ($inactive_nhr == $nhr_num) {
  $output .= " : CRITICAL";
  if (defined ($o_perf)) {$output .= " | " . $perf_output;}
  print $output,"\n";
  exit $ERRORS{"CRITICAL"};
}

if ($global_status ==1) {
  $output .= " : WARNING";
  if (defined ($o_perf)) {$output .= " | " . $perf_output;}
  print $output,"\n";
  exit $ERRORS{"WARNING"};
}

$output .= " : OK";
if (defined ($o_perf)) {$output .= " | " . $perf_output;}
print $output,"\n";
exit $ERRORS{"OK"};

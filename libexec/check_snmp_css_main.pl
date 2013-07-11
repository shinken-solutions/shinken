#!/usr/bin/perl -w 
############################## check_snmp_css_main.pl #################
# Version : 1.0	
# Date : 27 Sept 2006
# Author  : Patrick Proy ( patrick at proy.org)
# Help : http://www.manubulon.com/nagios/
# Licence : GPL - http://www.fsf.org/licenses/gpl.txt
# Changelog : 
# Contributors : 
#################################################################
#
# Help : ./check_snmp_css.pl -h
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

my $css_svc_table = 	"1.3.6.1.4.1.9.9.368.1.15.2.1"; # Svc table
my $css_svc_name =		"1.3.6.1.4.1.9.9.368.1.15.2.1.1"; #  Service Name / apSvcName
my $css_svc_index =		"1.3.6.1.4.1.9.9.368.1.15.2.1.2"; #  apSvcIndex
my $css_svc_enable =	"1.3.6.1.4.1.9.9.368.1.15.2.1.12"; #  apSvcEnable
my $css_svc_state=		"1.3.6.1.4.1.9.9.368.1.15.2.1.17"; #  apSvcState : suspended(1),  down(2), alive(4), dying(5)
my $css_svc_maxconn =	"1.3.6.1.4.1.9.9.368.1.15.2.1.19"; #  Max connexions / apSvcMaxConnections
my $css_svc_conn =		"1.3.6.1.4.1.9.9.368.1.15.2.1.20"; #  apSvcConnections
my $css_svc_avgresp =	"1.3.6.1.4.1.9.9.368.1.15.2.1.65"; #  apSvcAvgResponseTime : average response time
my $css_svc_maxresp =	"1.3.6.1.4.1.9.9.368.1.15.2.1.66"; #  apSvcPeakAvgResponseTime : peak response time
my @css_svc_state_txt=	("","suspended","down","","alive","dying");
my @css_svc_state_nag=	(3,2,2,3,0,2);

# Globals

my $Version='1.0';

my $o_host = 	undef; 		# hostname
my $o_community = undef; 	# community
my $o_port = 	161; 		# port
my $o_help=	undef; 		# wan't some help ?
my $o_verb=	undef;		# verbose mode
my $o_version=	undef;		# print version
my $o_timeout=  undef; 		# Timeout (Default 5)
my $o_version2= undef;          # use snmp v2c
#Specific
my $o_dir=		"/tmp/";		# Directory to store temp file in it.
# SNMPv3 specific
my $o_login=	undef;		# Login for snmpv3
my $o_passwd=	undef;		# Pass for snmpv3
my $v3protocols=undef;	# V3 protocol list.
my $o_authproto='md5';		# Auth protocol
my $o_privproto='des';		# Priv protocol
my $o_privpass= undef;		# priv password

# functions

sub p_version { print "check_snmp_css_main version : $Version\n"; }

sub print_usage {
    print "Usage: $0 [-v] -H <host> -C <snmp_community> [-2] | (-l login -x passwd [-X pass -L <authp>,<privp>]) [-d directory] [-p <port>] [-t <timeout>] [-V]\n";
}

sub help {
   print "\nSNMP Cisco CSS monitor MAIN script for Nagios version ",$Version,"\n";
   print "GPL Licence, (c)2004-2006 Patrick Proy\n\n";
   print_usage();
   print <<EOT;
-v, --verbose
   print extra debugging information 
-h, --help
   print this help message
-H, --hostname=HOST
   name or IP address of host to check
-d, --dir=<directory to put file> 
   Directory where temp file with index is written
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
	'd:s'	=> \$o_dir,		'dir:s'		=> \$o_dir
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
	if (defined($o_dir)) {
		verb("Tmp directory : $o_dir");
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
$session->max_msg_size(10000);

########### Cisco CSS checks ##############

# Get load table
my $resultat = (Net::SNMP->VERSION < 4) ? 
		  $session->get_table($css_svc_name)
		: $session->get_table(Baseoid => $css_svc_name); 
		
if (!defined($resultat)) {
   printf("ERROR: Name table : %s.\n", $session->error);
   $session->close;
   exit $ERRORS{"UNKNOWN"};
}


# Get name data & index
my (@index,@svcname)=(undef,undef);
my $numsvc=0;
foreach my $key ( keys %$resultat) {
	verb("OID : $key, Desc : $$resultat{$key}");
	$svcname[$numsvc]=$$resultat{$key};
	$key =~ s/$css_svc_name//;
	verb ("Found : $svcname[$numsvc]");
	$index[$numsvc++]=$key;
}

# Write file

my $file_name=$o_dir."/Nagios_css_".$o_host;
my $file_lock=$file_name.".lock";

# First, make a lock file 
system ("touch $file_lock");
# allow scripts to finish reading file
sleep (0.5);
# create the file
if (!open(FILE,"> ".$file_name)) {
	print "Cannot write $file_name\n";
	unlink($file_lock);
	exit $ERRORS{"UNKNOWN"};
}
for (my $i=0;$i<$numsvc;$i++) {
    my $output=$index[$i].":".$svcname[$i]."\n";
	print FILE $output;
}
close (FILE);
unlink($file_lock);
print "Found $numsvc services : OK\n";
exit $ERRORS{"OK"};

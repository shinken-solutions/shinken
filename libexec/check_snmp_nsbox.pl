#!/usr/bin/perl -w 
############################## check_snmp_nsbox #################
# Version : 1.0
# Date : Jan 16 2007
# Author  : Patrick Proy ( patrick at proy.org)
# Help : http://www.manubulon.com/nagios/
# Licence : GPL - http://www.fsf.org/licenses/gpl.txt
# Changelog : 
# Contributors : 
#################################################################
#
# Help : ./check_snmp_nsbox.pl -h
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
my $ns_service_status=	"1.3.6.1.4.1.14020.2.2.1.3.0"; # service status 1= ok ??

my $ns_service_table=	"1.3.6.1.4.1.14020.2.3"; # vhost & diode table
my $ns_vhost_table=		"1.3.6.1.4.1.14020.2.3.1"; # vhost table
my $ns_vhost_name=		"1.0"; # GUI Vhost Name
my $ns_vhost_requests=	"2.0"; # Instant Vhost Requests per Second : NOT POPULATED IN V 2.0.8
my $ns_vhost_Trequests=	"2.0"; # Total Vhost Requests : NOT POPULATED IN V 2.0.8
my $ns_diode_table=		"1.3.6.1.4.1.14020.2.3.2"; # diode table
my $ns_diode_name=		"1.0"; # GUI Diode Name
my $ns_diode_status=	"2.0"; # Last diode Status (" " = OK?) (undocumented)

my $ns_rsa_prct_usage=	".1.3.6.1.4.1.14020.1.1.1.3.0"; #  % usage of RSA operations. (undocumented)
my $ns_rsa_oper_second=	".1.3.6.1.4.1.14020.1.1.3.4.0;"; # number of RSA operations/s (undocumented)
	
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
# specific
my $o_vhost=	undef;	# vhost regexp
my $o_diode=	undef;	# diode regexp
my $o_nvhost=	undef;	# vhost number
my $o_ndiode=	undef;	# diode number

# SNMPv3 specific
my $o_login=	undef;		# Login for snmpv3
my $o_passwd=	undef;		# Pass for snmpv3
my $v3protocols=undef;	# V3 protocol list.
my $o_authproto='md5';		# Auth protocol
my $o_privproto='des';		# Priv protocol
my $o_privpass= undef;		# priv password

# functions

sub p_version { print "check_snmp_nsbox version : $Version\n"; }

sub print_usage {
    print "Usage: $0 [-v] -H <host> -C <snmp_community> [-2] | (-l login -x passwd [-X pass -L <authp>,<privp>]) -d <diode> -s <vhost> -n <ndiode>,<nvhost> [-p <port>] [-f] [-t <timeout>] [-V]\n";
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
   print "\nSNMP NetSecureOne Netbox monitor for Nagios version ",$Version,"\n";
   print "(c)2004-2006 Patrick Proy\n\n";
   print_usage();
   print <<EOT;
Check that diode and vhost selected by regexp are active.
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
-d, --diode=<diode>
	Diode selection by regexp
-s, --vhost=<vhost> 
	Vhost selection by regexp
-n, --number=<ndiode>,<nvhost>
	number of diode and vhost that must be up.	
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
	'd:s'	=> \$o_diode,		'diode:s'		=> \$o_diode,
	's:s'	=> \$o_vhost,		'vhost:s'		=> \$o_vhost,
	'n:s'	=> \$o_nvhost,		'number:s'		=> \$o_nvhost
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
	if (!defined($o_vhost) || !(is_pattern_valid($o_vhost))) 
		{ print "Vhost selection must be set and be a valid regexp (-s)\n"; print_usage(); exit $ERRORS{"UNKNOWN"}}
	if (!defined($o_diode) || !(is_pattern_valid($o_diode))) 
		{ print "Diode selection must be set and be a valid regexp (-d)\n"; print_usage(); exit $ERRORS{"UNKNOWN"}}
	if (!defined($o_nvhost)) 
		{ print "Diode and vhost number must be set (-n)\n"; print_usage(); exit $ERRORS{"UNKNOWN"}}
	my @nsbox_number=split(/,/,$o_nvhost);
	if ($#nsbox_number != 1) 
		{ print "2 numbers must be set with -n option\n"; print_usage(); exit $ERRORS{"UNKNOWN"}}
	if (isnnum($nsbox_number[0]) || isnnum($nsbox_number[1]))
		{ print "2 numbers must be set with -n option\n"; print_usage(); exit $ERRORS{"UNKNOWN"}}
	$o_ndiode=$nsbox_number[0];
	$o_nvhost=$nsbox_number[1];
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


########### check global status ##############
my @oidlist=($ns_service_status);
my $resultat = (Net::SNMP->VERSION < 4) ?
          $session->get_request(@oidlist)
        : $session->get_request(-varbindlist => \@oidlist);

if (!defined($resultat) || ($$resultat{$ns_service_status} eq "noSuchObject")) {
   printf("ERROR: Global status oid not found : %s.\n", $session->error);
   $session->close;
   exit $ERRORS{"UNKNOWN"};
}

if ($$resultat{$ns_service_status} != 1) {
  print "Global service is in state ",$$resultat{$ns_service_status}," : CRITICAL\n";
  exit $ERRORS{"CRITICAL"};
}

########### check vhost & diode status ##############
$resultat=undef;
$resultat = (Net::SNMP->VERSION < 4) ? 
		  $session->get_table($ns_service_table)
		: $session->get_table(Baseoid => $ns_service_table); 

if (!defined($resultat)) {
   printf("ERROR: vhost and diode status table : %s.\n", $session->error);
   $session->close;
   exit $ERRORS{"UNKNOWN"};
}
$session->close;

my $output="";
my $output_perf="";
my ($index,$name)=undef;
my ($nvhost,$ndiode)=(0,0);
my (@found_vhost,@found_diode)=(undef,undef);

foreach my $key ( keys %$resultat) {
	verb("OID : $key, Desc : $$resultat{$key}");
	if ( $key =~ /($ns_vhost_table)\.(\d+)\.($ns_vhost_name)/ ) { # Get index of vhost with name
		$index=$2;$name=$$resultat{$key};
		if ($name =~ /$o_vhost/) {
			$found_vhost[$nvhost++]=$name;
			verb ("found vhost $name");
		}
	}
	if ( $key =~ /($ns_diode_table)\.(\d+)\.($ns_diode_name)/ ) { # Get index of diode with name
		$index=$2;$name=$$resultat{$key};
		if ($name =~ /$o_diode/) {
			# TODO Check diode status : undocumented for now.
			$found_diode[$ndiode++]=$name;
			verb ("found diode $name");
		}
	}	
}

if (($ndiode<$o_ndiode) || ($nvhost<$o_nvhost)) {
	$output = "Diode";
	if ($ndiode == 0 ) { $output.= ": none ";}
	else {
		$output.= "(".$ndiode."): :";
		for (my $i=0;$i<$ndiode;$i++) {
			$output.=$found_diode[$i]." ";
		}
	}
	$output .= "Vhost";
	if ($nvhost == 0 ) { $output.= ": none ";}
	else {
		$output.= "(".$nvhost."): :";
		for (my $i=0;$i<$nvhost;$i++) {
		$output.=$found_vhost[$i]." ";
		}
	}
	$output .= " < " . $o_ndiode .",". $o_nvhost ." : CRITICAL";
	print $output,"\n";
	exit $ERRORS{"CRITICAL"};
}

$output = $ndiode . " diodes, " .$nvhost." vhosts :";
if (($ndiode>$o_ndiode) || ($nvhost>$o_nvhost)) {
	$output .= " > " . $o_ndiode .",". $o_nvhost ." : WARNING";
} else {
	$output .= " OK";
}
print $output,"\n";
exit $ERRORS{"OK"};


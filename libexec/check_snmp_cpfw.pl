#!/usr/bin/perl -w 
############################## check_snmp_cpfw ##############
# Version : 1.2.1
# Date : April 19 2007
# Author  : Patrick Proy (patrick at proy.org)
# Help : http://nagios.manubulon.com
# Licence : GPL - http://www.fsf.org/licenses/gpl.txt
# TODO : 
# - check sync method
#################################################################
#
# Help : ./check_snmp_cpfw.pl -h
#

use strict;
use Net::SNMP;
use Getopt::Long;

# Nagios specific

use lib "/usr/local/shinken/libexec";
use utils qw(%ERRORS $TIMEOUT);
#my $TIMEOUT = 15;
#my %ERRORS=('OK'=>0,'WARNING'=>1,'CRITICAL'=>2,'UNKNOWN'=>3,'DEPENDENT'=>4);

########### SNMP Datas ########### 

###### FW data
my $policy_state	= "1.3.6.1.4.1.2620.1.1.1.0"; # "Installed"
my $policy_name		= "1.3.6.1.4.1.2620.1.1.2.0"; # Installed policy name
my $connections		= "1.3.6.1.4.1.2620.1.1.25.3.0"; # number of connections
#my $connections_peak	= "1.3.6.1.4.1.2620.1.1.25.4.0"; # peak number of connections
my @fw_checks 		= ($policy_state,$policy_name,$connections);

###### SVN data
my $svn_status		= "1.3.6.1.4.1.2620.1.6.102.0"; # "OK" svn status
my %svn_checks		= ($svn_status,"OK");
my %svn_checks_n	= ($svn_status,"SVN status");
my @svn_checks_oid	= ($svn_status);

###### HA data

my $ha_active		= "1.3.6.1.4.1.2620.1.5.5.0"; 	# "yes"
my $ha_state		= "1.3.6.1.4.1.2620.1.5.6.0"; 	# "active" / "standby"
my $ha_block_state	= "1.3.6.1.4.1.2620.1.5.7.0"; 	#"OK" : ha blocking state
my $ha_status		= "1.3.6.1.4.1.2620.1.5.102.0"; # "OK" : ha status

my %ha_checks		=( $ha_active,"yes",$ha_state,"active",$ha_block_state,"OK",$ha_status,"OK");
my %ha_checks_stand	=( $ha_active,"yes",$ha_state,"standby",$ha_block_state,"OK",$ha_status,"OK");
my %ha_checks_n		=( $ha_active,"HA active",$ha_state,"HA state",$ha_block_state,"HA block state",$ha_status,"ha_status");
my @ha_checks_oid	=( $ha_active,$ha_state,$ha_block_state,$ha_status);

my $ha_mode		= "1.3.6.1.4.1.2620.1.5.11.0";  # "Sync only"/"High Availability (Active Up)" : ha Working mode

my $ha_tables		= "1.3.6.1.4.1.2620.1.5.13.1"; 	# ha status table
my $ha_tables_index	= ".1";
my $ha_tables_name	= ".2";
my $ha_tables_state	= ".3"; # "OK"
my $ha_tables_prbdesc	= ".6"; # Description if state is != "OK"

#my @ha_table_check	= ("Synchronization","Filter","cphad","fwd"); # process to check

####### MGMT data

my $mgmt_status		= "1.3.6.1.4.1.2620.1.7.5.0";	# "active" : management status
my $mgmt_alive		= "1.3.6.1.4.1.2620.1.7.6.0";   # 1 : management is alive if 1
my $mgmt_stat_desc	= "1.3.6.1.4.1.2620.1.7.102.0"; # Management status description
my $mgmt_stats_desc_l	= "1.3.6.1.4.1.2620.1.7.103.0"; # Management status long description

my %mgmt_checks		= ($mgmt_status,"active",$mgmt_alive,"1");
my %mgmt_checks_n	= ($mgmt_status,"Mgmt status",$mgmt_alive,"Mgmt alive");
my @mgmt_checks_oid	= ($mgmt_status,$mgmt_alive);

#################################### Globals ##############################""

my $Version='1.2.1';

my $o_host = 	undef; 		# hostname
my $o_community = undef; 	# community
my $o_version2	=undef;		# Version 2
my $o_port = 	161; 		# port
my $o_help=	undef; 		# wan't some help ?
my $o_verb=	undef;		# verbose mode
my $o_version=	undef;		# print version
my $o_timeout=  5;            	# Default 5s Timeout
my $o_warn=	undef;		# Warning for connections
my $o_crit=	undef;		# Crit for connections
my $o_svn=	undef;		# Check for SVN status
my $o_fw=	undef;		# Check for FW status
my $o_ha=	undef;		# Check for HA status
my $o_mgmt=	undef;		# Check for management status
my $o_policy=	undef;		# Check for policy name
my $o_conn=	undef;		# Check for connexions
my $o_perf=	undef;		# Performance data output 

# SNMPv3 specific
my $o_login=	undef;		# Login for snmpv3
my $o_passwd=	undef;		# Pass for snmpv3
my $v3protocols=undef;	# V3 protocol list.
my $o_authproto='md5';		# Auth protocol
my $o_privproto='des';		# Priv protocol
my $o_privpass= undef;		# priv password

# functions

sub p_version { print "check_snmp_cpfw version : $Version\n"; }

sub print_usage {
    print "Usage: $0 [-v] -H <host> -C <snmp_community> [-2] | (-l login -x passwd [-X pass -L <authp>,<privp>]) [-s] [-w [-p=pol_name] [-c=warn,crit]] [-m] [-a [standby] ] [-f] [-p <port>] [-t <timeout>] [-V]\n";
}

sub isnnum { # Return true if arg is not a number
  my $num = shift;
  if ( $num =~ /^(\d+\.?\d*)|(^\.\d+)$/ ) { return 0 ;}
  return 1;
}

sub help {
   print "\nSNMP Checkpoint FW-1 Monitor for Nagios version ",$Version,"\n";
   print "GPL Licence, (c)2004-2007 - Patrick Proy\n\n";
   print_usage();
   print <<EOT;
-v, --verbose
   print extra debugging information (including interface list on the system)
-h, --help
   print this help message
-H, --hostname=HOST
   name or IP address of host to check
-C, --community=COMMUNITY NAME
   community name for the host's SNMP agent (implies v1 protocol)
2, --v2c
   Use snmp v2c
-l, --login=LOGIN ; -x, --passwd=PASSWD
   Login and auth password for snmpv3 authentication 
   If no priv password exists, implies AuthNoPriv 
-X, --privpass=PASSWD
   Priv password for snmpv3 (AuthPriv protocol)
-L, --protocols=<authproto>,<privproto>
   <authproto> : Authentication protocol (md5|sha : default md5)
   <privproto> : Priv protocole (des|aes : default des) 
-s, --svn
   check for svn status
-w, --fw
   check for fw status
-a, --ha[=standby]
   check for ha status and node in "active" state
   If using SecurePlatform and monitoring a standby unit, put "standby" too
-m, --mgmt
   check for management status
-p, --policy=POLICY_NAME
   check if installed policy is POLICY_NAME (must have -w)
-c, --connexions=WARN,CRIT
   check warn and critical number of connexions (must have -w)
-f, --perfparse
   perfparse output (only works with -c)
-P, --port=PORT
   SNMP port (Default 161)
-t, --timeout=INTEGER
   timeout for SNMP (Default: Nagios default)   
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
        'P:i'   => \$o_port,   		'port:i'	=> \$o_port,
        'C:s'   => \$o_community,	'community:s'	=> \$o_community,
	'2'     => \$o_version2,        'v2c'           => \$o_version2,
	'l:s'	=> \$o_login,		'login:s'	=> \$o_login,
	'x:s'	=> \$o_passwd,		'passwd:s'	=> \$o_passwd,
	'X:s'	=> \$o_privpass,		'privpass:s'	=> \$o_privpass,
	'L:s'	=> \$v3protocols,		'protocols:s'	=> \$v3protocols,   
 	't:i'   => \$o_timeout,       	'timeout:i'     => \$o_timeout,
	'V'	=> \$o_version,		'version'	=> \$o_version,
	's'	=> \$o_svn,		'svn'		=> \$o_svn,
	'w'	=> \$o_fw,		'fw'		=> \$o_fw,
	'a:s'	=> \$o_ha,		'ha:s'		=> \$o_ha,
	'm'	=> \$o_mgmt,		'mgmt'		=> \$o_mgmt,
	'p:s'	=> \$o_policy,		'policy:s'	=> \$o_policy,
	'c:s'	=> \$o_conn,		'connexions:s'	=> \$o_conn,
	'f'	=> \$o_perf,		'perfparse'	=> \$o_perf
    );
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
    # Check firewall options
    if ( defined($o_conn)) {
      if ( ! defined($o_fw))
 	{ print "Cannot check connexions without checking fw\n"; print_usage(); exit $ERRORS{"UNKNOWN"}}
      my @warncrit=split(/,/ , $o_conn);
      if ( $#warncrit != 1 ) 
        { print "Put warn,crit levels with -c option\n";print_usage(); exit $ERRORS{"UNKNOWN"}}
      ($o_warn,$o_crit)=@warncrit;
      if ( isnnum($o_warn) || isnnum($o_crit) )
	{ print "Numeric values for warning and critical in -c options\n";print_usage(); exit $ERRORS{"UNKNOWN"}}
      if ($o_warn >= $o_crit)
	{ print "warning <= critical ! \n";print_usage(); exit $ERRORS{"UNKNOWN"}}
    }
    if ( defined($o_policy)) {
      if (! defined($o_fw))
	{ print "Cannot check policy name without checking fw\n"; print_usage(); exit $ERRORS{"UNKNOWN"}}
      if ($o_policy eq "")
        { print "Put a policy name !\n"; print_usage(); exit $ERRORS{"UNKNOWN"}}
    }
    if (defined($o_perf) && ! defined ($o_conn))
	{ print "Nothing selected for perfparse !\n";print_usage(); exit $ERRORS{"UNKNOWN"}}
    if (!defined($o_fw) && !defined($o_ha) && !defined($o_mgmt) && !defined($o_svn))
	{ print "Must select a product to check !\n";print_usage(); exit $ERRORS{"UNKNOWN"}}
    if (defined ($o_ha) && ($o_ha ne "") && ($o_ha ne "standby")) 
	{ print "-a option comes with 'standby' or nothing !\n";print_usage(); exit $ERRORS{"UNKNOWN"}}
	
}

########## MAIN #######

check_options();

# Check gobal timeout if snmp screws up
if (defined($TIMEOUT)) {
  verb("Alarm at $TIMEOUT");
  alarm($TIMEOUT);
} else {
  verb("no timeout defined : $o_timeout + 10");
  alarm ($o_timeout+10);
}

$SIG{'ALRM'} = sub {
 print "No answer from host\n";
 exit $ERRORS{"UNKNOWN"};
};

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
      -port      	=> $o_port,
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
      -port      	=> $o_port,
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

########### Global checks #################

my $global_status=0; # global status : 0=OK, 1=Warn, 2=Crit
my ($resultat,$key)=(undef,undef);

##########  Check SVN status #############
my $svn_print="";
my $svn_state=0;

if (defined ($o_svn)) {

$resultat = $session->get_request(
    Varbindlist => \@svn_checks_oid
);

  if (defined($resultat)) {
    foreach $key ( keys %svn_checks) {
      verb("$svn_checks_n{$key} : $svn_checks{$key} / $$resultat{$key}");
      if ( $$resultat{$key} ne $svn_checks{$key} ) {
	$svn_print .= $svn_checks_n{$key} . ":" . $$resultat{$key} . " ";
	$svn_state=2;
      }  
    }
  } else {
    $svn_print .= "cannot find oids";
    #Critical state if not found because it means soft is not activated
    $svn_state=2;
  }

  if ($svn_state == 0) {
    $svn_print="SVN : OK";
  } else {
    $svn_print="SVN : " . $svn_print;
  }
  verb("$svn_print");
}
##########  Check mgmt status #############
my $mgmt_state=0;
my $mgmt_print="";

if (defined ($o_mgmt)) {
# Check all states
  $resultat=undef;
  $resultat = $session->get_request(
      Varbindlist => \@mgmt_checks_oid
  );  
  if (defined($resultat)) {
    foreach $key ( keys %mgmt_checks) {
      verb("$mgmt_checks_n{$key} : $mgmt_checks{$key} / $$resultat{$key}");
      if ( $$resultat{$key} ne $mgmt_checks{$key} ) {
        $mgmt_print .= $mgmt_checks_n{$key} . ":" . $$resultat{$key} . " ";
        $mgmt_state=2;
      }
    }
  } else {
    $mgmt_print .= "cannot find oids";
    #Critical state if not found because it means soft is not activated
    $mgmt_state=2;
  }  
  if ($mgmt_state == 0) {
    $mgmt_print="MGMT : OK";
  } else {
    $mgmt_print="MGMT : " . $mgmt_print;
  }
  verb("$svn_print");
}

########### Check fw status  ##############

my $fw_state=0;
my $fw_print="";
my $perf_conn=undef;

if (defined ($o_fw)) {

# Check all states 
    
  $resultat = $session->get_request(
      Varbindlist => \@fw_checks
  );
  if (defined($resultat)) {
    verb("State : $$resultat{$policy_state}");
    verb("Name : $$resultat{$policy_name}");
    verb("connections : $$resultat{$connections}");

    if ($$resultat{$policy_state} ne "Installed") {
      $fw_state=2;
      $fw_print .= "Policy:". $$resultat{$policy_state}." ";
      verb("Policy state not installed"); 
    }

    if (defined($o_policy)) {
      if ($$resultat{$policy_name} ne $o_policy) {
	    $fw_state=2;
	    $fw_print .= "Policy installed : $$resultat{$policy_name}";
      }
    }

    if (defined($o_conn)) {
      if ($$resultat{$connections} > $o_crit) {
	 $fw_state=2;
        $fw_print .= "Connexions : ".$$resultat{$connections}." > ".$o_crit." ";
      } else {
	if ($$resultat{$connections} > $o_warn) {
	  if ($fw_state!=2) {$fw_state=1;}
	  $fw_print .= "Connexions : ".$$resultat{$connections}." > ".$o_warn." ";    
	}
      }
      $perf_conn=$$resultat{$connections};
    }
  } else {
    $fw_print .= "cannot find oids";
    #Critical state if not found because it means soft is not activated
    $fw_state=2;
  }

  if ($fw_state==0) {
    $fw_print="FW : OK";
  } else {
    $fw_print="FW : " . $fw_print;
  }

}
########### Check ha status  ##############

my $ha_state_n=0;
my $ha_print="";

if (defined ($o_ha)) {
  # Check all states 

  $resultat = $session->get_request(
      Varbindlist => \@ha_checks_oid
  );

  if (defined($resultat)) {
    foreach $key ( keys %ha_checks) {
      verb("$ha_checks_n{$key} : $ha_checks{$key} / $$resultat{$key}");
      if ( $o_ha eq "standby" ) {
        if ( $$resultat{$key} ne $ha_checks_stand{$key} ) {
	  $ha_print .= $ha_checks_n{$key} . ":" . $$resultat{$key} . " "; 
	  $ha_state_n=2;
        }
      } else {
        if ( $$resultat{$key} ne $ha_checks{$key} ) {
	  $ha_print .= $ha_checks_n{$key} . ":" . $$resultat{$key} . " "; 
	  $ha_state_n=2;
        }
      }  
    }
    #my $ha_mode		= "1.3.6.1.4.1.2620.1.5.11.0";  # "Sync only" : ha Working mode
  } else {
    $ha_print .= "cannot find oids";
    #Critical state if not found because it means soft is not activated
    $ha_state_n=2;
  }

  # get ha status table
  $resultat = $session->get_table(
	  Baseoid => $ha_tables
  ); 
  my %status;
  my (@index,@oid) = (undef,undef);
  my $nindex=0;
  my $index_search= $ha_tables . $ha_tables_index; 
  
  if (defined($resultat)) {
    foreach $key ( keys %$resultat) {
      if ( $key =~ /$index_search/) {
	@oid=split (/\./,$key);
	pop(@oid);
	$index[$nindex]=pop(@oid);
	$nindex++; 
      }
    }
  } else {
    $ha_print .= "cannot find oids" if ($ha_state_n ==0);
    #Critical state if not found because it means soft is not activated
    $ha_state_n=2;
  }
  verb ("found $nindex ha softs");
  if ( $nindex == 0 ) 
  { 
    $ha_print .= " no ha soft found" if ($ha_state_n ==0);
    $ha_state_n=2; 
  } else {
    my $ha_soft_name=undef;

    for (my $i=0;$i<$nindex;$i++) {

      $key=$ha_tables . $ha_tables_name . "." . $index[$i] . ".0";
      $ha_soft_name= $$resultat{$key};
      
      $key=$ha_tables . $ha_tables_state . "." . $index[$i] . ".0";
      if (($status{$ha_soft_name} = $$resultat{$key}) ne "OK") {
	    $key=$ha_tables . $ha_tables_prbdesc . "." . $index[$i] . ".0";
	    $status{$ha_soft_name} = $$resultat{$key};
	    $ha_print .= $ha_soft_name . ":" . $status{$ha_soft_name} . " ";
	    $ha_state_n=2
      }
      verb ("$ha_soft_name : $status{$ha_soft_name}");
    }
  }

  if ($ha_state_n == 0) {
    $ha_print = "HA : OK";
  } else {
    $ha_print = "HA : " . $ha_print;
  }

}

$session->close;

########## print results and exit

my $f_print=undef;

if (defined ($o_fw)) { $f_print = $fw_print }
if (defined ($o_svn)) { $f_print = (defined ($f_print)) ? $f_print . " / ". $svn_print : $svn_print }
if (defined ($o_ha)) { $f_print = (defined ($f_print)) ? $f_print . " / ". $ha_print : $ha_print }
if (defined ($o_mgmt)) { $f_print = (defined ($f_print)) ? $f_print . " / ". $mgmt_print : $mgmt_print }

my $exit_status=undef;
$f_print .= " / CPFW Status : ";
if (($ha_state_n+$svn_state+$fw_state+$mgmt_state) == 0 ) {
  $f_print .= "OK";
  $exit_status= $ERRORS{"OK"}; 
} else {
  if (($fw_state==1) || ($ha_state_n==1) || ($svn_state==1) || ($mgmt_state==1)) {
    $f_print .= "WARNING";
    $exit_status= $ERRORS{"WARNING"};
  } else {
    $f_print .= "CRITICAL";
    $exit_status=$ERRORS{"CRITICAL"};
  }
}

if (defined($o_perf) && defined ($perf_conn)) {
  $f_print .= " | fw_connexions=" . $perf_conn;
}

print "$f_print\n";
exit $exit_status;


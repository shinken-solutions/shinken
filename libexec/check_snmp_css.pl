#!/usr/bin/perl -w 
############################## check_snmp_css.pl #################
# Version : 1.0.1
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
my $o_perf=     undef;          # Output performance data
my $o_version2= undef;          # use snmp v2c
#Specific
my $o_dir=		"/tmp/";		# Directory to store temp file in it.
my $o_dir_set= undef;		# defined if names and index must be read form file.
my $o_name=		undef;		# service name (regexp)
my $o_warn_number=	undef;		# minimum number of service before warning
my $o_crit_number=	undef;		# minimum number of service before critical
my $o_warn_conn=	undef;		# % of max connexions for warning level
my $o_crit_conn=	undef;		# % of max connexions for critical level
my $o_warn_resp=	undef;		# average response time for warning level
my $o_crit_resp=	undef;		# average response time for critical level
my @o_levels=		undef;
# SNMPv3 specific
my $o_login=	undef;		# Login for snmpv3
my $o_passwd=	undef;		# Pass for snmpv3
my $v3protocols=undef;	# V3 protocol list.
my $o_authproto='md5';		# Auth protocol
my $o_privproto='des';		# Priv protocol
my $o_privpass= undef;		# priv password

# functions

sub p_version { print "check_snmp_css version : $Version\n"; }

sub print_usage {
    print "Usage: $0 [-v] -H <host> -C <snmp_community> [-2] | (-l login -x passwd [-X pass -L <authp>,<privp>]) -n <name> [-d directory] [-w <num>,<resp>,<conn> -c <num>,<resp>,<conn>]  [-p <port>] [-f] [-t <timeout>] [-V]\n";
}

sub isnnum { # Return true if arg is not a number
  my $num = shift;
  if ( $num =~ /^-?(\d+\.?\d*)|(^\.\d+)$/ ) { return 0 ;}
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

sub round ($$) {
    sprintf "%.$_[1]f", $_[0];
}

sub help {
   print "\nSNMP Cisco CSS monitor for Nagios version ",$Version,"\n";
   print "(c)2004-2006 Patrick Proy\n\n";
   print_usage();
   print <<EOT;
-v, --verbose
   print extra debugging information 
-h, --help
   print this help message
-H, --hostname=HOST
   name or IP address of host to check
-n, --name=<name> 
   regexp to select service
-w, --warning=<num>,<resp>,<conn> 
   Optional. Warning level for
   - minimum number of active & alive service 
   - average response time
   - number of connexions
   For no warnings, put -1 (ex : -w5,-1,3).
   When using negative numbers, dont put space after "-w"
-d, --dir=<directory to put file> 
   Directory where the temp file with index, created by check_snmp_css_main.pl, can be found
   If no directory is set, /tmp will be used
-c, --critical=<num>,resp>,<conn>
   Optional. Critical levels (-1 for no critical levels)
   See warning levels.
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
	'n:s'	=> \$o_name,		'name:s'		=> \$o_name,
	'w:s'	=> \$o_warn_conn,	'warning:s'		=> \$o_warn_conn,
	'c:s'	=> \$o_crit_conn,	'critical:s'		=> \$o_crit_conn,
	'd:s'	=> \$o_dir_set,		'dir:s'		=> \$o_dir_set	
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
	if (!defined($o_name) || ! (is_pattern_valid($o_name))) 
		{print "Need a service name!\n"; print_usage(); exit $ERRORS{"UNKNOWN"}}
	if (defined($o_warn_conn)) {
		@o_levels=split(/,/,$o_warn_conn);
		if (defined($o_levels[0])) {
			if (isnnum($o_levels[0])) {print "Need number for warning!\n"; print_usage(); exit $ERRORS{"UNKNOWN"}}
			if ($o_levels[0] != -1 ) {$o_warn_number=$o_levels[0];} 
		}
		if (defined($o_levels[1])) {
			if (isnnum($o_levels[1])) {print "Need number for warning!\n"; print_usage(); exit $ERRORS{"UNKNOWN"}}
			if ($o_levels[1] != -1 ) {$o_warn_conn=$o_levels[1];} else {$o_warn_conn=undef;}
		} else {$o_warn_conn=undef;}
		if (defined($o_levels[2]) ) {
			if (isnnum($o_levels[2])) {print "Need number for warning!\n"; print_usage(); exit $ERRORS{"UNKNOWN"}}
			if ($o_levels[2] != -1 ) {$o_warn_resp=$o_levels[2];}
		}
	}
	if (defined($o_crit_conn)) {
		@o_levels=split(/,/,$o_crit_conn);
		if (defined($o_levels[0]) ) {		
			if (isnnum($o_levels[0])) {print "Need number for critical!\n"; print_usage(); exit $ERRORS{"UNKNOWN"}}
			if ($o_levels[0] != -1 ) {
				$o_crit_number=$o_levels[0];
				if (defined($o_warn_number) && ($o_crit_number>=$o_warn_number)) 
					{print "critical must be < warning!\n"; print_usage(); exit $ERRORS{"UNKNOWN"}}
			}
		}
		if (defined($o_levels[1]) ) {		
			if (isnnum($o_levels[1])) {print "Need number for critical!\n"; print_usage(); exit $ERRORS{"UNKNOWN"}}
			if ($o_levels[1] != -1 ) {
				$o_crit_conn=$o_levels[1];
				if (defined($o_warn_conn) && ($o_warn_conn>=$o_crit_conn)) 
					{print "critical must be > warning!\n"; print_usage(); exit $ERRORS{"UNKNOWN"}}
			} else {$o_crit_conn=undef;}
		} else {$o_crit_conn=undef;}
		if (defined($o_levels[2]) ) {
			if (isnnum($o_levels[2])) {print "Need number for critical!\n"; print_usage(); exit $ERRORS{"UNKNOWN"}}
			if ($o_levels[2] != -1 ) {
				$o_crit_resp=$o_levels[1];
				if (defined($o_warn_resp) && ($o_warn_resp>=$o_crit_resp)) 
					{print "critical must be > warning!\n"; print_usage(); exit $ERRORS{"UNKNOWN"}}
			}
		}
	}
	if (defined($o_dir_set)) {
	    if ($o_dir_set ne "") {$o_dir=$o_dir_set;} 
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

my (@index,@svcname)=(undef,undef);
my ($numsvc,$numoid,$numoid2)=0;
my (@oid,@oid_list,@oid_list2)=undef;
my $resultat = undef;
# Get load table by snmp or file
if (defined($o_dir_set)) {
	my $file_name=$o_dir."/Nagios_css_".$o_host;
	my $file_lock=$file_name.".lock";

	# Check for lock file during 3 seconds max and quit if sill here.
	my $file_timeout=0;
	while (-e $file_lock) { 
		sleep(1);
		if ($file_timeout==3) {
		  print "Lock file remaining for more than 3 sec : UNKNOWN\n";
		  exit $ERRORS{"UNKNOWN"};
		}
		$file_timeout++;
	}
	# Open file for reading.
	open(FILE,"< ".$file_name);
	while (<FILE>) {
		my @file_line=split(/:/,$_);
		if ((defined ($file_line[1])) && ($file_line[1] =~ /$o_name/)) { # select service by name
			chomp($file_line[1]);
			$svcname[$numsvc]=$file_line[1];
			my $key = $file_line[0];
			verb ("Found : $svcname[$numsvc]");
			$index[$numsvc++]=$key;
			# Build oid for snmpget
			$oid_list[$numoid++]=$css_svc_enable.$key;
			$oid_list[$numoid++]=$css_svc_state.$key;
			$oid_list2[$numoid2++]=$css_svc_maxconn.$key;
			$oid_list2[$numoid2++]=$css_svc_conn.$key;
			$oid_list2[$numoid2++]=$css_svc_avgresp.$key;
		}
	}
	close (FILE);
} else {
	$resultat = (Net::SNMP->VERSION < 4) ? 
			  $session->get_table($css_svc_name)
			: $session->get_table(Baseoid => $css_svc_name); 
			
	if (!defined($resultat)) {
	   printf("ERROR: Description table : %s.\n", $session->error);
	   $session->close;
	   exit $ERRORS{"UNKNOWN"};
	}


	# Get name data & index

	foreach my $key ( keys %$resultat) {
		verb("OID : $key, Desc : $$resultat{$key}");
		if ($$resultat{$key} =~ /$o_name/) { # select service by name
			$svcname[$numsvc]=$$resultat{$key};
			$key =~ s/$css_svc_name//;
			verb ("Found : $svcname[$numsvc]");
			$index[$numsvc++]=$key;
			# Build oid for snmpget
			$oid_list[$numoid++]=$css_svc_enable.$key;
			$oid_list[$numoid++]=$css_svc_state.$key;
			$oid_list2[$numoid2++]=$css_svc_maxconn.$key;
			$oid_list2[$numoid2++]=$css_svc_conn.$key;
			$oid_list2[$numoid2++]=$css_svc_avgresp.$key;
		}
	}
}
# Check if a least one service found
if ($numsvc == 0) {
	print "No service matching ",$o_name," found : CRITICAL\n";
	exit $ERRORS{"CRITICAL"};	
}

$resultat = undef;
$resultat = (Net::SNMP->VERSION < 4) ?
          $session->get_request(@oid_list)
        : $session->get_request(-varbindlist => \@oid_list);

if (!defined($resultat)) {
   printf("ERROR: Status get : %s.\n", $session->error);
   $session->close;
   exit $ERRORS{"UNKNOWN"};
}
my $resultat2 = undef;
$resultat2 = (Net::SNMP->VERSION < 4) ?
          $session->get_request(@oid_list2)
        : $session->get_request(-varbindlist => \@oid_list2);

if (!defined($resultat2)) {
   printf("ERROR: Conn get : %s.\n", $session->error);
   $session->close;
   exit $ERRORS{"UNKNOWN"};
}

my $output="";
my $output_perf="";
my $numsvc_ok=0;
my $output_done=0;
my $global_status=0;

for (my $i=0;$i<$numsvc;$i++) {
	my $key=$index[$i];
	if ($$resultat{$css_svc_enable.$key} == 0 ) {
		# service disabled
		if ($output ne "") { $output.=", ";}
		$output .= $svcname[$i] . " : Disabled";
	} else {
		if ($css_svc_state_nag[$$resultat{$css_svc_state.$key}] != 0) {
			# state not OK
			if ($output ne "") { $output.=", ";}
			$output .= $svcname[$i] . " : " . $css_svc_state_txt[$$resultat{$css_svc_state.$key}];
		} else {
			$numsvc_ok++;
			$output_done=0;
			# state OK
			my $prctconn = round(($$resultat2{$css_svc_conn.$key}/$$resultat2{$css_svc_maxconn.$key}) * 100,0);
			my $resptime = $$resultat2{$css_svc_avgresp.$key};
			if (defined ($o_warn_conn) && ($prctconn>$o_warn_conn)) {
				if ($output ne "") { $output.=", ";}
				$output .= $svcname[$i]. ":" . $prctconn ."%, ".$resptime."ms";
				set_status(1,$global_status);$output_done=1;
			}
			if (defined ($o_crit_conn) && ($prctconn>$o_crit_conn)) {
				if ($output_done==0) {
					$output .= $svcname[$i]. ":" . $prctconn ."%, ".$resptime."ms";
					$output_done=1;
				}
				set_status(2,$global_status);
			}
			if (defined ($o_warn_resp) && ($prctconn>$o_warn_resp)) {
				if ($output_done==0) {
					$output .= $svcname[$i]. ":" . $prctconn ."%, ".$resptime."ms";
					$output_done=1;
				}
				set_status(1,$global_status);
			}
			if (defined ($o_crit_resp) && ($prctconn>$o_crit_resp)) {
				if ($output_done==0) {
					$output .= $svcname[$i]. ":" . $prctconn ."%, ".$resptime."ms";
					$output_done=1;
				}			
				set_status(2,$global_status);
			}			
		}
	}
}


$output .= " ".$numsvc_ok."/".$numsvc." services OK";

if (($global_status == 2) || ((defined ($o_crit_number)) && ($numsvc_ok<=$o_crit_number)) || ($numsvc_ok==0) ) {
	print $output," : CRITICAL\n";
	exit $ERRORS{"CRITICAL"}
}
if (($global_status == 1) || ((defined ($o_warn_number)) && ($numsvc_ok<=$o_warn_number))) {
	print $output," : WARNING\n";
	exit $ERRORS{"WARNING"}
}
print $output," : OK\n";
exit $ERRORS{"OK"};

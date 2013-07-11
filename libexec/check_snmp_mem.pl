#!/usr/bin/perl -w 
############################## check_snmp_mem ##############
# Version : 1.1
# Date : Jul 09 2006
# Author  : Patrick Proy (nagios at proy.org)
# Help : http://www.manubulon.com/nagios/
# Licence : GPL - http://www.fsf.org/licenses/gpl.txt
# Contrib : Jan Jungmann
# TODO : 
#################################################################
#
# Help : ./check_snmp_mem.pl -h
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

# Net-snmp memory 

my $nets_ram_free	= "1.3.6.1.4.1.2021.4.6.0";  # Real memory free
my $nets_ram_total	= "1.3.6.1.4.1.2021.4.5.0";  # Real memory total
my $nets_ram_cache      = "1.3.6.1.4.1.2021.4.15.0"; # Real memory cached
my $nets_swap_free	= "1.3.6.1.4.1.2021.4.4.0";  # swap memory free
my $nets_swap_total	= "1.3.6.1.4.1.2021.4.3.0";  # Swap memory total
my @nets_oids		= ($nets_ram_free,$nets_ram_total,$nets_swap_free,$nets_swap_total,$nets_ram_cache);

# Cisco 

my $cisco_mem_pool      = "1.3.6.1.4.1.9.9.48.1.1.1"; # Cisco memory pool
my $cisco_index         = "1.3.6.1.4.1.9.9.48.1.1.1.2"; # memory pool name and index
my $cisco_valid         = "1.3.6.1.4.1.9.9.48.1.1.1.4"; # Valid memory if 1
my $cisco_used          = "1.3.6.1.4.1.9.9.48.1.1.1.5"; # Used memory
my $cisco_free          = "1.3.6.1.4.1.9.9.48.1.1.1.6"; # Free memory
# .1 : type, .2 : name, .3 : alternate, .4 : valid, .5 : used, .6 : free, .7 : max free

# HP Procurve

my $hp_mem_pool		= "1.3.6.1.4.1.11.2.14.11.5.1.1.2.2.1.1";   # HP memory pool
my $hp_mem_index	= "1.3.6.1.4.1.11.2.14.11.5.1.1.2.2.1.1.1"; # memory slot index
my $hp_mem_total	= "1.3.6.1.4.1.11.2.14.11.5.1.1.2.2.1.1.5"; # Total Bytes
my $hp_mem_free		= "1.3.6.1.4.1.11.2.14.11.5.1.1.2.2.1.1.6"; # Free Bytes
my $hp_mem_free_seg	= "1.3.6.1.4.1.11.2.14.11.5.1.1.2.2.1.1.3"; # Free segments

# AS/400 

# Windows NT/2K/(XP?)

# check_snmp_storage.pl -C <community> -H <hostIP> -m "^Virtual Memory$"  -w <warn %> -c <crit %>


# Globals

my $Version='1.1';

my $o_host = 	undef; 		# hostname
my $o_community = undef; 	# community
my $o_port = 	161; 		# port
my $o_help=	undef; 		# wan't some help ?
my $o_verb=	undef;		# verbose mode
my $o_version=	undef;		# print version
my $o_netsnmp=	1;		# Check with netsnmp (default)
my $o_cisco=	undef;		# Check cisco router mem
my $o_hp=	undef;		# Check hp procurve mem
my $o_warn=	undef;		# warning level option
my $o_warnR=	undef;		# warning level for Real memory
my $o_warnS=	undef;		# warning levels for swap
my $o_crit=	undef;		# Critical level option
my $o_critR=	undef;		# critical level for Real memory
my $o_critS=	undef;		# critical level for swap
my $o_perf=	undef;		# Performance data option
my $o_cache=	undef;		# Include cached memory as used memory
my $o_timeout=  undef; 		# Timeout (Default 5)
my $o_version2= undef;          # use snmp v2c
# SNMPv3 specific
my $o_login=	undef;		# Login for snmpv3
my $o_passwd=	undef;		# Pass for snmpv3
my $v3protocols=undef;	# V3 protocol list.
my $o_authproto='md5';		# Auth protocol
my $o_privproto='des';		# Priv protocol
my $o_privpass= undef;		# priv password

# functions

sub p_version { print "check_snmp_mem version : $Version\n"; }

sub print_usage {
    print "Usage: $0 [-v] -H <host> -C <snmp_community> [-2] | (-l login -x passwd [-X pass -L <authp>,<privp>])  [-p <port>] -w <warn level> -c <crit level> [-I|-N|-E] [-f] [-m] [-t <timeout>] [-V]\n";
}

sub isnnum { # Return true if arg is not a number
  my $num = shift;
  if ( $num =~ /^(\d+\.?\d*)|(^\.\d+)$/ ) { return 0 ;}
  return 1;
}

sub round ($$) {
    sprintf "%.$_[1]f", $_[0];
}

sub help {
   print "\nSNMP Memory Monitor for Nagios version ",$Version,"\n";
   print "(c)2004-2006 to my cat Ratoune - Author: Patrick Proy\n\n";
   print_usage();
   print <<EOT;
-v, --verbose
   print extra debugging information (including interface list on the system)
-h, --help
   print this help message
-H, --hostname=HOST
   name or IP address of host to check
-C, --community=COMMUNITY NAME
   community name for the host's SNMP agent (implies SNMP v1 or v2c with option)
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
-w, --warn=INTEGER | INT,INT
   warning level for memory in percent (0 for no checks) 
     Default (-N switch) : comma separated level for Real Memory and Swap 
     -I switch : warning level
-c, --crit=INTEGER | INT,INT
   critical level for memory in percent (0 for no checks)
     Default (-N switch) : comma separated level for Real Memory and Swap 
     -I switch : critical level
-N, --netsnmp (default)
   check linux memory & swap provided by Net SNMP 
-m, --memcache
   include cached memory in used memory (only with Net-SNMP)
-I, --cisco
   check cisco memory (sum of all memory pools)
-E, --hp
   check HP proccurve memory
-f, --perfdata
   Performance data output
-t, --timeout=INTEGER
   timeout for SNMP in seconds (Default: 5)
-V, --version
   prints version number
EOT
}

# For verbose output
sub verb { my $t=shift; print $t,"\n" if defined($o_verb) ; }

# Get the alarm signal (just in case snmp timout screws up)
$SIG{'ALRM'} = sub {
     print ("ERROR: Alarm signal (Nagios time-out)\n");
     exit $ERRORS{"UNKNOWN"};
};

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
	'I'	=> \$o_cisco,		'cisco'		=> \$o_cisco,
	'N'	=> \$o_netsnmp,		'netsnmp'	=> \$o_netsnmp,
        'E'	=> \$o_hp,		'hp'		=> \$o_hp,
        '2'     => \$o_version2,        'v2c'           => \$o_version2,
        'c:s'   => \$o_crit,            'critical:s'    => \$o_crit,
        'w:s'   => \$o_warn,            'warn:s'        => \$o_warn,
        'm'   	=> \$o_cache,           'memcache'      => \$o_cache,
        'f'     => \$o_perf,            'perfdata'      => \$o_perf
    );
    if (defined ($o_help) ) { help(); exit $ERRORS{"UNKNOWN"}};
    if (defined($o_version)) { p_version(); exit $ERRORS{"UNKNOWN"}};
    if ( ! defined($o_host) ) # check host and filter 
	{ print "No host defined!\n";print_usage(); exit $ERRORS{"UNKNOWN"}}
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
	if (defined($o_timeout) && (isnnum($o_timeout) || ($o_timeout < 2) || ($o_timeout > 60))) 
	  { print "Timeout must be >1 and <60 !\n"; print_usage(); exit $ERRORS{"UNKNOWN"}}
	if (!defined($o_timeout)) {$o_timeout=5;}
	#Check Warning and crit are present
    if ( ! defined($o_warn) || ! defined($o_crit))
 	{ print "Put warning and critical values!\n"; print_usage(); exit $ERRORS{"UNKNOWN"}}
    # Get rid of % sign
    $o_warn =~ s/\%//g; 
    $o_crit =~ s/\%//g;
    # if -N or -E switch , undef $o_netsnmp
    if (defined($o_cisco) || defined($o_hp) ) {
      $o_netsnmp=undef;
      if ( isnnum($o_warn) || isnnum($o_crit)) 
	{ print "Numeric value for warning or critical !\n";print_usage(); exit $ERRORS{"UNKNOWN"} }
      if ( ($o_crit != 0) && ($o_warn > $o_crit) ) 
        { print "warning <= critical ! \n";print_usage(); exit $ERRORS{"UNKNOWN"}}
    }
    if (defined($o_netsnmp)) {
      my @o_warnL=split(/,/ , $o_warn);
      my @o_critL=split(/,/ , $o_crit);
      if (($#o_warnL != 1) || ($#o_critL != 1)) 
	{ print "2 warnings and critical !\n";print_usage(); exit $ERRORS{"UNKNOWN"}}
      for (my $i=0;$i<2;$i++) {
	if ( isnnum($o_warnL[$i]) || isnnum($o_critL[$i])) 
	    { print "Numeric value for warning or critical !\n";print_usage(); exit $ERRORS{"UNKNOWN"} }
	if (($o_critL[$i]!= 0) && ($o_warnL[$i] > $o_critL[$i]))
	   { print "warning <= critical ! \n";print_usage(); exit $ERRORS{"UNKNOWN"}}
 	if ( $o_critL[$i] > 100)
	   { print "critical percent must be < 100 !\n";print_usage(); exit $ERRORS{"UNKNOWN"}}
      }
      $o_warnR=$o_warnL[0];$o_warnS=$o_warnL[1];
      $o_critR=$o_critL[0];$o_critS=$o_critL[1];
    }
  
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

# Connect to host
my ($session,$error);
if ( defined($o_login) && defined($o_passwd)) {
  # SNMPv3 login
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
      -timeout      => $o_timeout
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

# Global variable
my $resultat=undef;

########### Cisco memory check ############
if (defined ($o_cisco)) {

  # Get Cisco memory table
  $resultat = (Net::SNMP->VERSION < 4) ?
                 $session->get_table($cisco_mem_pool)
                 :$session->get_table(Baseoid => $cisco_mem_pool);
  
  if (!defined($resultat)) {
    printf("ERROR: Description table : %s.\n", $session->error);
    $session->close;
    exit $ERRORS{"UNKNOWN"};
  }
  my (@oid,@index)=(undef,undef);
  my $nindex=0;
  foreach my $key ( keys %$resultat) {
     verb("OID : $key, Desc : $$resultat{$key}");
     if ( $key =~ /$cisco_index/ ) { 
	@oid=split (/\./,$key);
	$index[$nindex++] = pop(@oid);
     }
  }
  
  # Check if at least 1 memory pool exists
  if ($nindex == 0) { 
   printf("ERROR: No memory pools found");
   $session->close;
   exit $ERRORS{"UNKNOWN"};
  }

  # Test every memory pool
  my ($c_output,$prct_free)=(undef,undef);
  my ($warn_s,$crit_s)=(0,0);
  my ($used,$free)=(0,0);
  foreach (@index) {
    $c_output .="," if defined ($c_output);
    if ( $$resultat{$cisco_valid . "." . $_} == 1 ) {
      $used += $$resultat{$cisco_used . "." . $_};
      $free += $$resultat{$cisco_free . "." . $_};
      $prct_free=round($$resultat{$cisco_used . "." . $_}*100/($$resultat{$cisco_free . "." . $_}+$$resultat{$cisco_used . "." . $_}) ,0);
      $c_output .= $$resultat{$cisco_index . "." . $_} . ":" . $prct_free . "%";
      if (($o_crit!=0)&&($o_crit <= $prct_free)) { 
	$crit_s =1;
      } elsif (($o_warn!=0)&&($o_warn <= $prct_free)) {
	$warn_s=1;
      }
    } else {
      $c_output .= $$resultat{$cisco_index . "." . $_} . ": INVALID";
      $crit_s =1;
    }
  }
  my $total=$used+$free; 
  $prct_free=round($used*100/($total),0);
  verb("Total used : $used, free: $free, output : $c_output");
  my $c_status="OK";
  $c_output .=" : " . $prct_free ."% : ";
  if ($crit_s == 1 ) {
    $c_output .= " > " . $o_crit ;
    $c_status="CRITICAL";
  } else {
    if ($warn_s == 1 ) {
      $c_output.=" > " . $o_warn;
      $c_status="WARNING";
    }
  }
  $c_output .= " ; ".$c_status;
  if (defined ($o_perf)) {
    $c_output .= " | ram_used=" . $used.";";
    $c_output .= ($o_warn ==0)? ";" : round($o_warn * $total/100,0).";"; 
    $c_output .= ($o_crit ==0)? ";" : round($o_crit * $total/100,0).";";
    $c_output .= "0;" . $total ;
  }             
  $session->close; 
  print "$c_output \n";
  exit $ERRORS{$c_status};
}

########### HP Procurve memory check ############
if (defined ($o_hp)) {

  # Get hp memory table
  $resultat = (Net::SNMP->VERSION < 4) ?
                 $session->get_table($hp_mem_pool)
                 :$session->get_table(Baseoid => $hp_mem_pool);
  
  if (!defined($resultat)) {
    printf("ERROR: Description table : %s.\n", $session->error);
    $session->close;
    exit $ERRORS{"UNKNOWN"};
  }
  my (@oid,@index)=(undef,undef);
  my $nindex=0;
  foreach my $key ( keys %$resultat) {
     verb("OID : $key, Desc : $$resultat{$key}");
     if ( $key =~ /$hp_mem_index/ ) { 
	@oid=split (/\./,$key);
	$index[$nindex++] = pop(@oid);
     }
  }
  
  # Check if at least 1 memory slots exists
  if ($nindex == 0) { 
   printf("ERROR: No memory slots found");
   $session->close;
   exit $ERRORS{"UNKNOWN"};
  }

  # Consolidate the datas
  my ($total,$free)=(0,0);
  my ($c_output,$prct_free)=(undef,undef);
  foreach (@index) {
    $c_output .="," if defined ($c_output);
    $total += $$resultat{$hp_mem_total . "." . $_};
    $free += $$resultat{$hp_mem_free . "." . $_};
    $c_output .= "Slot " . $$resultat{$hp_mem_index . "." . $_} . ":" 
 		 .round( 
		   100 - ($$resultat{$hp_mem_free . "." . $_} *100 / 
                        $$resultat{$hp_mem_total . "." . $_}) ,0)
		 . "%";
  }
  my $used = $total - $free; 
  $prct_free=round($used*100/($total),0);
  verb("Used : $used, Free: $free, Output : $c_output");
  my $c_status="OK";
  $c_output .=" : " . $prct_free ."% : ";
  if (($o_crit!=0)&&($o_crit <= $prct_free)) {
    $c_output .= " > " . $o_crit ;
    $c_status="CRITICAL";
  } else {
    if (($o_warn!=0)&&($o_warn <= $prct_free)) {
      $c_output.=" > " . $o_warn;
      $c_status="WARNING";
    }
  }
  $c_output .= " ; ".$c_status;
  if (defined ($o_perf)) {
    $c_output .= " | ram_used=" . $used.";";
    $c_output .= ($o_warn ==0)? ";" : round($o_warn * $total/100,0).";"; 
    $c_output .= ($o_crit ==0)? ";" : round($o_crit * $total/100,0).";";
    $c_output .= "0;" . $total ;
  }             
  $session->close; 
  print "$c_output \n";
  exit $ERRORS{$c_status};
}

########### Net snmp memory check ############
if (defined ($o_netsnmp)) {

  # Get NetSNMP memory values
  $resultat = (Net::SNMP->VERSION < 4) ?
		$session->get_request(@nets_oids)
		:$session->get_request(-varbindlist => \@nets_oids);
  
  if (!defined($resultat)) {
    printf("ERROR: netsnmp : %s.\n", $session->error);
    $session->close;
    exit $ERRORS{"UNKNOWN"};
  }
  
  my ($realused,$swapused)=(undef,undef);
  
  $realused= defined($o_cache) ? 
    ($$resultat{$nets_ram_total}-$$resultat{$nets_ram_free})/$$resultat{$nets_ram_total}
  :
    ($$resultat{$nets_ram_total}-($$resultat{$nets_ram_free}+$$resultat{$nets_ram_cache}))/$$resultat{$nets_ram_total};

  if($$resultat{$nets_ram_total} == 0) { $realused = 0; }

  $swapused= ($$resultat{$nets_swap_total} == 0) ? 0 :
		($$resultat{$nets_swap_total}-$$resultat{$nets_swap_free})/$$resultat{$nets_swap_total}; 
  $realused=round($realused*100,0);
  $swapused=round($swapused*100,0);
  defined($o_cache) ? 
    verb ("Ram : $$resultat{$nets_ram_free} / $$resultat{$nets_ram_total} : $realused")
    :
    verb ("Ram : $$resultat{$nets_ram_free} ($$resultat{$nets_ram_cache} cached) / $$resultat{$nets_ram_total} : $realused");
  verb ("Swap : $$resultat{$nets_swap_free} / $$resultat{$nets_swap_total} : $swapused");
  
  my $n_status="OK";
  my $n_output="Ram : " . $realused . "%, Swap : " . $swapused . "% :";
  if ((($o_critR!=0)&&($o_critR <= $realused)) || (($o_critS!=0)&&($o_critS <= $swapused))) {
    $n_output .= " > " . $o_critR . ", " . $o_critS;
    $n_status="CRITICAL";
  } else {
    if ((($o_warnR!=0)&&($o_warnR <= $realused)) || (($o_warnS!=0)&&($o_warnS <= $swapused))) {
      $n_output.=" > " . $o_warnR . ", " . $o_warnS;
      $n_status="WARNING";
    }
  }
  $n_output .= " ; ".$n_status; 
  if (defined ($o_perf)) {
    if (defined ($o_cache)) {
      $n_output .= " | ram_used=" . ($$resultat{$nets_ram_total}-$$resultat{$nets_ram_free}).";";
    }
    else {
      $n_output .= " | ram_used=" . ($$resultat{$nets_ram_total}-$$resultat{$nets_ram_free}-$$resultat{$nets_ram_cache}).";";
    }
    $n_output .= ($o_warnR ==0)? ";" : round($o_warnR * $$resultat{$nets_ram_total}/100,0).";";  
    $n_output .= ($o_critR ==0)? ";" : round($o_critR * $$resultat{$nets_ram_total}/100,0).";";  
    $n_output .= "0;" . $$resultat{$nets_ram_total}. " ";
    $n_output .= "swap_used=" . ($$resultat{$nets_swap_total}-$$resultat{$nets_swap_free}).";";
    $n_output .= ($o_warnS ==0)? ";" : round($o_warnS * $$resultat{$nets_swap_total}/100,0).";";  
    $n_output .= ($o_critS ==0)? ";" : round($o_critS * $$resultat{$nets_swap_total}/100,0).";"; 
    $n_output .= "0;" . $$resultat{$nets_swap_total};
  }  
  $session->close;
  print "$n_output \n";
  exit $ERRORS{$n_status};

}

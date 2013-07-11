#!/usr/bin/perl -w
############################## check_snmp_win ##############
# Version : 0.6
# Date : Nov 29 2006 
# Author  : Patrick Proy (patrick at proy.org)
# Help : http://www.manubulon.com/nagios/
# Licence : GPL - http://www.fsf.org/licenses/gpl.txt
# TODO : 
###############################################################
#
# help : ./check_snmp_win.pl -h

use strict;
use Net::SNMP;
use Getopt::Long;

# Nagios specific

use lib "/usr/local/shinken/libexec";
use utils qw(%ERRORS $TIMEOUT);
#my $TIMEOUT = 5;
#my %ERRORS=('OK'=>0,'WARNING'=>1,'CRITICAL'=>2,'UNKNOWN'=>3,'DEPENDENT'=>4);

# SNMP Datas for processes (MIB II)
my $process_table= '1.3.6.1.2.1.25.4.2.1';
my $index_table = '1.3.6.1.2.1.25.4.2.1.1';
my $run_name_table = '1.3.6.1.2.1.25.4.2.1.2';
my $run_path_table = '1.3.6.1.2.1.25.4.2.1.4';
my $proc_mem_table = '1.3.6.1.2.1.25.5.1.1.2'; # Kbytes
my $proc_cpu_table = '1.3.6.1.2.1.25.5.1.1.1'; # Centi sec of CPU
my $proc_run_state = '1.3.6.1.2.1.25.4.2.1.7';

# Windows SNMP DATA

my $win_serv_table = '1.3.6.1.4.1.77.1.2.3.1'; # Windows services table
my $win_serv_name = '1.3.6.1.4.1.77.1.2.3.1.1'; # Name of the service
# Install state : uninstalled(1), install-pending(2), uninstall-pending(3), installed(4)
my $win_serv_inst = '1.3.6.1.4.1.77.1.2.3.1.2'; 
# Operating state : active(1),  continue-pending(2),  pause-pending(3),  paused(4)
my $win_serv_state = '1.3.6.1.4.1.77.1.2.3.1.3'; 
my %win_serv_state_label = ( 1 => 'active', 2=> 'continue-pending', 3=> 'pause-pending', 4=> 'paused');
# Can be uninstalled : cannot-be-uninstalled(1), can-be-uninstalled(2)
my $win_serv_uninst = '1.3.6.1.4.1.77.1.2.3.1.4'; 

# Globals

my $Version='0.6';
my $Name='check_snmp_win';

my $o_host = 	undef; 		# hostname 
my $o_community =undef; 	# community 
my $o_port = 	161; 		# port
my $o_version2	= undef;	#use snmp v2c
my $o_descr = 	undef; 		# description filter 
my @o_descrL = 	undef;		# Service descriprion list.
my $o_showall = undef;	# Show all services even if OK
my $o_type = "service";	# Check type (service, ...)
my $o_number = undef;  # Number of service for warn and crit levels
my $o_help=	undef; 		# wan't some help ?
my $o_verb=	undef;		# verbose mode
my $o_version=   undef;         # print version
my $o_noreg=	undef;		# Do not use Regexp for name
my $o_timeout=  5;            	# Default 5s Timeout
# SNMP V3 specific
my $o_login=	undef;		# snmp v3 login
my $o_passwd=	undef;		# snmp v3 passwd

# functions

sub p_version { print "$Name version : $Version\n"; }

sub print_usage {
    print "Usage: $Name [-v] -H <host> -C <snmp_community> [-2] | (-l login -x passwd) [-p <port>] -n <name>[,<name2] [-T=service] [-r] [-s] [-N=<n>] [-t <timeout>] [-V]\n";
}

sub isnotnum { # Return true if arg is not a number
  my $num = shift;
  if ( $num =~ /^-?(\d+\.?\d*)|(^\.\d+)$/ ) { return 0 ;}
  return 1;
}

sub is_pattern_valid { # Test for things like "<I\s*[^>" or "+5-i"
 my $pat = shift;
 if (!defined($pat)) { $pat=" ";} # Just to get rid of compilation time warnings
 return eval { "" =~ /$pat/; 1 } || 0;
}

# Get the alarm signal (just in case snmp timout screws up)
$SIG{'ALRM'} = sub {
     print ("ERROR: Alarm signal (Nagios time-out)\n");
     exit $ERRORS{"UNKNOWN"};
};

sub help {
   print "\nSNMP Windows Monitor for Nagios version ",$Version,"\n";
   print "GPL licence, (c)2004-2005 Patrick Proy\n\n";
   print_usage();
   print <<EOT;
-v, --verbose
   print extra debugging information (and lists all services)
-h, --help
   print this help message
-H, --hostname=HOST
   name or IP address of host to check
-C, --community=COMMUNITY NAME
   community name for the host's SNMP agent (implies SNMP v1 or v2c with option)
-2, --v2c
   Use snmp v2c
-l, --login=LOGIN
   Login for snmpv3 authentication (implies v3 protocol with MD5)
-x, --passwd=PASSWD
   Password for snmpv3 authentication
-p, --port=PORT
   SNMP port (Default 161)
-T, --type=service
   Check type : 
     - service (default) checks service
-n, --name=NAME[,NAME2...]
   Comma separated names of services (perl regular expressions can be used for every one).
   By default, it is not case sensitive.
-N, --number=<n>
   Compare matching services with <n> instead of the number of names provided.
-s, --showall
   Show all services in the output, instead of only the non-active ones.
-r, --noregexp
   Do not use regexp to match NAME in service description.
-t, --timeout=INTEGER
   timeout for SNMP in seconds (Default: 5)
-V, --version
   prints version number
Note :   
  The script will return 
    OK if ALL services are in active state,
    WARNING if there is more than specified (ex 2 service specified, 3 active services matching), 
    CRITICAL if at least one of them is non active.
  The -n option will allows regexp in perl format 
  -n "service" will match 'service WINS' 'sevice DNS' etc...
  It is not case sensitive by default : WINS = wins
EOT
}

sub verb { my $t=shift; print $t,"\n" if defined($o_verb) ; }

sub decode_utf8 { # just replaces UFT8 caracters by "."
  my $utfstr=shift;
  if (substr($utfstr,0,2) ne "0x") { return $utfstr; }
  my @stringL=split(//,$utfstr);
  my $newstring="";
  for (my $i=2;$i<$#stringL;$i+=2) {
    if ( ($stringL[$i] . $stringL[$i+1]) eq "c3") {
	  $i+=2;$newstring .= ".";
	} else {
	  $newstring .= chr(hex($stringL[$i] . $stringL[$i+1]));
	}
  }
  return $newstring;
}

sub check_options {
    Getopt::Long::Configure ("bundling");
    GetOptions(
   	'v'	=> \$o_verb,		'verbose'	=> \$o_verb,
        'h'     => \$o_help,    	'help'        	=> \$o_help,
        'H:s'   => \$o_host,		'hostname:s'	=> \$o_host,
        'p:i'   => \$o_port,   		'port:i'	=> \$o_port,
        'C:s'   => \$o_community,	'community:s'	=> \$o_community,
        'l:s'   => \$o_login,           'login:s'       => \$o_login,
        'x:s'   => \$o_passwd,          'passwd:s'      => \$o_passwd,
	't:i'   => \$o_timeout,       	'timeout:i'     => \$o_timeout,
        'n:s'   => \$o_descr,		'name:s'	=> \$o_descr,
        'r'     => \$o_noreg,           'noregexp'      => \$o_noreg,
        'T:s'   => \$o_type,           	'type:s'      	=> \$o_type,
        'N:i'   => \$o_number,          'number:i'      => \$o_number,
	'2'	=> \$o_version2,	'v2c'		=> \$o_version2,
	's'     => \$o_showall,  	'showall'       => \$o_showall,  
	'V'     => \$o_version,         'version'       => \$o_version
    );
    if (defined ($o_help)) { help(); exit $ERRORS{"UNKNOWN"}};
    if (defined($o_version)) { p_version(); exit $ERRORS{"UNKNOWN"}};
    # check snmp information
    if ( !defined($o_community) && (!defined($o_login) || !defined($o_passwd)) )
        { print "Put snmp login info!\n"; print_usage(); exit $ERRORS{"UNKNOWN"}}
    # Check compulsory attributes
    if ( $o_type ne "service" ) {
      print "Invalid check type !\n"; print_usage(); exit $ERRORS{"UNKNOWN"} 
    }
    if ( ! defined($o_descr) ||  ! defined($o_host) ) { print_usage(); exit $ERRORS{"UNKNOWN"}};
    @o_descrL=split(/,/,$o_descr);	
    foreach my $List (@o_descrL) {
      if ( ! is_pattern_valid ($List) ) { print "Invalid pattern ! ";print_usage(); exit $ERRORS{"UNKNOWN"} }
    }
    if (defined ($o_number)) {
      if (isnotnum($o_number) || ($o_number<0) ) 
        { print "Invalid number of services!\n";print_usage(); exit $ERRORS{"UNKNOWN"}}
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
  verb("SNMPv3 login");
  ($session, $error) = Net::SNMP->session(
      -hostname         => $o_host,
      -version          => '3',
      -username         => $o_login,
      -authpassword     => $o_passwd,
      -authprotocol     => 'md5',
      -privpassword     => $o_passwd,
      -timeout          => $o_timeout
   );
} else {
  if (defined ($o_version2)) {
    # SNMPv2 Login
	($session, $error) = Net::SNMP->session(
       -hostname  => $o_host,
	   -version   => 2,
       -community => $o_community,
       -port      => $o_port,
       -timeout   => $o_timeout
    );
  } else {
  # SNMPV1 login
    ($session, $error) = Net::SNMP->session(
       -hostname  => $o_host,
       -community => $o_community,
       -port      => $o_port,
       -timeout   => $o_timeout
    );
  }
}


if (!defined($session)) {
   printf("ERROR: %s.\n", $error);
   exit $ERRORS{"UNKNOWN"};
}

$session->max_msg_size(5000);
verb($session->max_msg_size);

# Look for process in name or path name table
my $resultat=undef;

$resultat = (Net::SNMP->VERSION < 4) ? 
		$session->get_table($win_serv_name)
		: $session->get_table(Baseoid => $win_serv_name);

if (!defined($resultat)) {
   printf("ERROR: Process name table : %s.\n", $session->error);
   $session->close;
   exit $ERRORS{"UNKNOWN"};
}

my @tindex = undef;
my @oids = undef;
my @descr = undef;
my $num_int = 0;
my $count_oid = 0;
# Select storage by regexp of exact match
# and put the oid to query in an array

verb("Filter : $o_descr");

foreach my $key ( keys %$resultat) {
   my $descr_d=decode_utf8($$resultat{$key});
   verb("Desc : $descr_d");
   # test by regexp or exact match
   my $test=undef;
   foreach my $List (@o_descrL) {
     if (!($test)) {
  	    $test = defined($o_noreg)
			 ? $descr_d eq $List
			 : $descr_d =~ /$List/i;
     }
  }
  if ($test) {
      # get the full description
     $descr[$num_int]=$descr_d;
	 # get the index number of the process
	 $key =~ s/$win_serv_name\.//;
     $tindex[$num_int] = $key;
     # put the oid of running state in an array.
     $oids[$count_oid++]=$win_serv_state . "." . $tindex[$num_int];
     verb("Name : $descr[$num_int], Index : $tindex[$num_int]");
     $num_int++;
  }
}

if ( $num_int == 0) {
   if (defined ($o_number) && ($o_number ==0)) {
    print "No services ",(defined ($o_noreg)) ? "named \"" : "matching \"", $o_descr, "\" found : OK\n";
    exit $ERRORS{"OK"};
  } else  {
    print "No services ",(defined ($o_noreg)) ? "named \"" : "matching \"", $o_descr, "\" found : CRITICAL\n";
    exit $ERRORS{"CRITICAL"};
  }
}

my $result=undef;
my $num_int_ok=0;

$result = (Net::SNMP->VERSION < 4) ? 
    $session->get_request(@oids)
  : $session->get_request(Varbindlist => \@oids);

if (!defined($result)) { printf("ERROR: running table : %s.\n", $session->error); $session->close;
   exit $ERRORS{"UNKNOWN"};
}

$session->close;

my $output=undef;
#Check if service are in active state
for (my $i=0; $i< $num_int; $i++) {
   my $state=$$result{$win_serv_state . "." . $tindex[$i]};
   verb ("Process $tindex[$i] in state $state");
   if ($state == 1) {
     $num_int_ok++
   } else {
     $output .= ", " if defined($output);
     $output .= $descr[$i] . " : " . $win_serv_state_label{$state};
   }
}

my $force_critical=0;

# Show the services that are not present
# Or all of them with -s option
foreach my $List (@o_descrL) {
  my $test=0;
  for (my $i=0; $i< $num_int; $i++) {
    if ( $descr[$i] =~ /$List/i  ) { $test++; }
  }
  if ($test==0) {
    $output .= ", " if defined($output);
    $output .= "\"" . $List . "\" not active";
    # Force a critical state (could otherwise lead to false OK)
    $force_critical=1; 
  } elsif ( defined ($o_showall) ) {
    $output .= ", " if defined($output);
    $output .= "\"" . $List . "\" active";
    if ($test != 1) {
      $output .= "(" .$test . " services)";
    }
  }
}

if (defined ($output) ) {
  print $output, " : ";  
} else {
  print $num_int_ok, " services active (", (defined ($o_noreg)) ? "named \"" : "matching \"", $o_descr, "\") : ";
}

$o_number = $#o_descrL+1 if (!defined($o_number));

if (($num_int_ok < $o_number)||($force_critical == 1)) { 
	print "CRITICAL\n";
	exit $ERRORS{"CRITICAL"};
} elsif ($num_int_ok > $o_number) {
  print "WARNING\n";
  exit $ERRORS{"WARNING"};
}
print "OK\n";
exit $ERRORS{"OK"};



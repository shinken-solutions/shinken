#!/usr/bin/perl -w
############################## check_snmp_hpux_storage ##############
# Version : 1.3.1
# Date :  2007 01 22
# Author2 : Paul Vogt (  paul dot unix at gmail.com )
# Author  : Patrick Proy ( patrick at proy.org)
# Help : http://www.manubulon.com/nagios/
# Licence : GPL - http://www.fsf.org/licenses/gpl.txt
# TODO : 
# Contribs : Dimo Velev
#################################################################
# See /opt/OV/newconfig/AGENT-MAN/snmp_mibs/hp-unix if available
# help : ./check_snmp_hpux_storage -h
 
use strict;
use Net::SNMP;
use Getopt::Long;

# Nagios specific

use lib "/usr/local/nagios/libexec";
use utils qw(%ERRORS $TIMEOUT);
#my $TIMEOUT = 15;
#my %ERRORS=('OK'=>0,'WARNING'=>1,'CRITICAL'=>2,'UNKNOWN'=>3,'DEPENDENT'=>4);

# SNMP Datas
my $descr_table = '1.3.6.1.4.1.11.2.3.1.2.2.1.10';
my $block_table = '1.3.6.1.4.1.11.2.3.1.2.2.1.4.';
my $bfree_table = '1.3.6.1.4.1.11.2.3.1.2.2.1.5.';
my $bsize_table = '1.3.6.1.4.1.11.2.3.1.2.2.1.7.';


# Globals

my $Name='check_snmp_hpux_storage';
my $Version='1.3';

my $o_host = 	undef; 		# hostname 
my $o_community = undef; 	# community 
my $o_port = 	161; 		# port
my $o_version2	= undef;	#use snmp v2c
my $o_descr = 	undef; 		# description filter 
my $o_warn = 	undef; 		# warning limit 
my $o_crit=	undef; 		# critical limit
my $o_help=	undef; 		# wan't some help ?
my $o_type=	undef;		# pl, pu, mbl, mbu 
my @o_typeok=   ("pu","pl","bu","bl"); # valid values for o_type
my $o_verb=	undef;		# verbose mode
my $o_version=  undef;          # print version
my $o_noreg=	undef;		# Do not use Regexp for name
my $o_negate;
my $o_sum=	undef;		# add all storage before testing
my $o_index=	undef;		# Parse index instead of description
my $o_exclude=	undef;		# exclude the regexp if set
my $o_timeout=  5;            	# Default 5s Timeout
my $o_perf=	undef;		# Output performance data
my $o_short=	undef;	# Short output parameters
my @o_shortL=	undef;		# output type,where,cut
# SNMPv3 specific
my $o_login=	undef;		# Login for snmpv3
my $o_passwd=	undef;		# Pass for snmpv3
my $v3protocols=undef;	# V3 protocol list.
my $o_authproto='md5';		# Auth protocol
my $o_privproto='des';		# Priv protocol
my $o_privpass= undef;		# priv password

# functions

sub p_version { print "$Name version : $Version\n"; }

sub print_usage {
    print "Usage: $Name [-v] -H <host> -C <snmp_community> [-2] | (-l login -x passwd [-X pass -L <authp>,<privp>]) [-p <port>] -m <name in desc_oid> [-q storagetype] -w <warn_level> -c <crit_level> [-t <timeout>] [-T pl|pu|bl|bu ] [-r] [-s] [-i] [-e] [-S 0|1[,1,<car>]]\n";
}

sub round ($$) {
    sprintf "%.$_[1]f", $_[0];
}

sub is_pattern_valid { # Test for things like "<I\s*[^>" or "+5-i"
 my $pat = shift;
 if (!defined($pat)) { $pat=" ";} # Just to get rid of compilation time warnings
 return eval { "" =~ /$pat/; 1 } || 0;
}

# Get the alarm signal (just in case snmp timout screws up)
$SIG{'ALRM'} = sub {
     print ("ERROR: General time-out (Alarm signal)\n");
     exit $ERRORS{"UNKNOWN"};
};

sub isnnum { # Return true if arg is not a number
  my $num = shift;
  if ( $num =~ /^-?(\d+\.?\d*)|(^\.\d+)$/ ) { return 0 ;}
  return 1;
}

sub help {
   print "\nSNMP Disk Monitor for Nagios version ",$Version,"\n";
   print "(c)2007 Paul Vogt\n";
   print "(c)2004-2006 Patrick Proy\n\n";
   print_usage();
   print <<EOT;
By default, plugin will monitor %used on drives :
warn if %used > warn and critical if %used > crit
-v, --verbose
   print extra debugging information (and lists all storages)
-h, --help
   print this help message
-H, --hostname=HOST
   name or IP address of host to check
-C, --community=COMMUNITY NAME
   community name for the host's SNMP agent (implies SNMP v1)
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
-x, --passwd=PASSWD
   Password for snmpv3 authentication
-p, --port=PORT
   SNMP port (Default 161)
-m, --name=NAME
   Name in description OID (usually a list of mounpoints)
   This is treated as a regexp : -m /var will match /var , /var/log, /opt/var ...
   Test it before, because there are known bugs (ex : trailling /)
   No trailing slash for mountpoints !
-r, --noregexp
   Do not use regexp to match NAME in description OID
-s, --sum
   Add all storages that match NAME (used space and total space)
   THEN make the tests.
-e, --exclude=NAME
   exclude the storages matching NAME. NAME is treated as a regexp.
   If -r is set, this option will negate the -m selection and NAME will
   be ignored.
-T, --type=TYPE
   pl : calculate percent left
   pu : calculate percent used (Default)
   bl : calculate MegaBytes left
   bu : calculate MegaBytes used
-w, --warn=INTEGER
   percent / MB of disk used to generate WARNING state
   you can add the % sign 
-c, --critical=INTEGER
   percent / MB of disk used to generate CRITICAL state
   you can add the % sign 
-f, --perfparse
   Perfparse compatible output
-S, --short=<type>[,<where>,<cut>]
   <type>: Make the output shorter :
     0 : only print the global result except the disk in warning or critical
         ex: "< 80% : OK"
     1 : Don't print all info for every disk 
         ex : "/ : 66 %used  (<  80) : OK"
   <where>: (optional) if = 1, put the OK/WARN/CRIT at the beginning
   <cut>: take the <n> first caracters or <n> last if n<0
-t, --timeout=INTEGER
   timeout for SNMP in seconds (Default: 5)
-V, --version
   prints version number
Note : 
  with T=pu or T=bu : OK < warn < crit
  with T=pl ot T=bl : crit < warn < OK
  
  If multiple storage are selected, the worse condition will be returned
  i.e if one disk is critical, the return is critical
 
  example : 
  Browse storage list : <script> -C <community> -H <host> -m <anything> -w 1 -c 2 -v 
  the -m option allows regexp in perl format : 
  Test drive C,F,G,H,I on Windows 	: -m ^[CFGHI]:    
  Test all mounts containing /var      	: -m /var
  Test all mounts under /var      	: -m ^/var
  Test only /                 		: -m / -r
  Test all except mounts under /var	: -m ^/ -e ^/var
  
  Note: Nagios does not support using a \$ sign in a regexp.

EOT
}

sub verb { my $t=shift; print $t,"\n" if defined($o_verb) ; }

sub check_options {
    Getopt::Long::Configure ("bundling");
    GetOptions(
		'v'	=> \$o_verb,		'verbose'	=> \$o_verb,
        'h'     => \$o_help,    	'help'        	=> \$o_help,
        'H:s'   => \$o_host,		'hostname:s'	=> \$o_host,
        'p:i'   => \$o_port,   		'port:i'	=> \$o_port,
        'C:s'   => \$o_community,	'community:s'	=> \$o_community,
	'2'     => \$o_version2,        'v2c'           => \$o_version2,
	'l:s'	=> \$o_login,		'login:s'	=> \$o_login,
	'x:s'	=> \$o_passwd,		'passwd:s'	=> \$o_passwd,
	'X:s'	=> \$o_privpass,		'privpass:s'	=> \$o_privpass,
	'L:s'	=> \$v3protocols,		'protocols:s'	=> \$v3protocols,   	
        'c:s'   => \$o_crit,    	'critical:s'	=> \$o_crit,
        'w:s'   => \$o_warn,    	'warn:s'	=> \$o_warn,
	't:i'   => \$o_timeout,       	'timeout:i'     => \$o_timeout,
        'm:s'   => \$o_descr,		'name:s'	=> \$o_descr,
	'T:s'	=> \$o_type,		'type:s'	=> \$o_type,
        'r'     => \$o_noreg,           'noregexp'      => \$o_noreg,
        's'     => \$o_sum,           	'sum'      	=> \$o_sum,
        'e:s'   => \$o_negate,         	'exclude:s'    	=> \$o_negate,
        'V'     => \$o_version,         'version'       => \$o_version,
	'S:s'   => \$o_short,         	'short:s'       => \$o_short,
	'f'	=> \$o_perf,		'perfparse'	=> \$o_perf
    );
    if (defined($o_help) ) { help(); exit $ERRORS{"UNKNOWN"}};
    if (defined($o_version) ) { p_version(); exit $ERRORS{"UNKNOWN"}};
    # check mount point regexp
    if (!is_pattern_valid($o_descr)) 
	{ print "Bad pattern for mount point !\n"; print_usage(); exit $ERRORS{"UNKNOWN"}}    
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
    # Check types
    if ( !defined($o_type) ) { $o_type="pu" ;}
    if ( ! grep( /^$o_type$/ ,@o_typeok) ) { print_usage(); exit $ERRORS{"UNKNOWN"}};   
    # Check compulsory attributes
    if ( ! defined($o_descr) ||  ! defined($o_host) || !defined($o_warn) || 
	!defined($o_crit)) { print_usage(); exit $ERRORS{"UNKNOWN"}};
    # Check for positive numbers
    if (($o_warn < 0) || ($o_crit < 0)) { print " warn and critical > 0 \n";print_usage(); exit $ERRORS{"UNKNOWN"}};
    # check if warn or crit  in % and MB is tested
    if (  ( ( $o_warn =~ /%/ ) || ($o_crit =~ /%/)) && ( ( $o_type eq 'bu' ) || ( $o_type eq 'bl' ) ) ) {
	print "warning or critical cannot be in % when MB are tested\n";
	print_usage(); exit $ERRORS{"UNKNOWN"};
    }
    # Get rid of % sign
    $o_warn =~ s/\%//; 
    $o_crit =~ s/\%//;
    # Check warning and critical values
    if ( ( $o_type eq 'pu' ) || ( $o_type eq 'bu' )) {
	if ($o_warn >= $o_crit) { print " warn < crit if type=",$o_type,"\n";print_usage(); exit $ERRORS{"UNKNOWN"}};
    }
    if ( ( $o_type eq 'pl' ) || ( $o_type eq 'bl' )) {
	if ($o_warn <= $o_crit) { print " warn > crit if type=",$o_type,"\n";print_usage(); exit $ERRORS{"UNKNOWN"}};
    }
    if ( ($o_warn < 0 ) || ($o_crit < 0 )) { print "warn and crit must be > 0\n";print_usage(); exit $ERRORS{"UNKNOWN"}}; 
    if ( ( $o_type eq 'pl' ) || ( $o_type eq 'pu' )) {
        if ( ($o_warn > 100 ) || ($o_crit > 100 )) { print "percent must be < 100\n";print_usage(); exit $ERRORS{"UNKNOWN"}}; 
    } 
	# Check short values
	if ( defined ($o_short)) {
 	  @o_shortL=split(/,/,$o_short);
	  if ((isnnum($o_shortL[0])) || ($o_shortL[0] !=0) && ($o_shortL[0]!=1)) {
	    print "-S first option must be 0 or 1\n";print_usage(); exit $ERRORS{"UNKNOWN"};
	  }
	  if (defined ($o_shortL[1])&& $o_shortL[1] eq "") {$o_shortL[1]=undef};
	  if (defined ($o_shortL[2]) && isnnum($o_shortL[2]))
	    {print "-S last option must be an integer\n";print_usage(); exit $ERRORS{"UNKNOWN"};}
	}
}

########## MAIN #######

check_options();

# Check gobal timeout
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
   printf("ERROR: %s.\n", $error);
   exit $ERRORS{"UNKNOWN"};
}

my $resultat=undef;
my $stype=undef;
# Get rid of UTF8 translation in case of accentuated caracters (thanks to Dimo Velev).
$session->translate(Net::SNMP->TRANSLATE_NONE);

  if (Net::SNMP->VERSION < 4) {
    $resultat = $session->get_table($descr_table);
  } else {
    $resultat = $session->get_table(Baseoid => $descr_table);
  }

if (!defined($resultat)) {
   printf("ERROR: Description/Type table : %s.\n", $session->error);
   $session->close;
   exit $ERRORS{"UNKNOWN"};
}

my @tindex1 = undef;
my @tindex2 = undef;
my @oids = undef;
my @descr = undef;
my $num_int = 0;
my $count_oid = 0;
my $test = undef;
my $perf_out=	undef;
my $oididx;


# Select storage by regexp of exact match
# and put the oid to query in an array

foreach my $key ( keys %$resultat) {
   verb("OID : $key, Desc : $$resultat{$key}");
   # test by regexp or exact match / include or exclude
   if (defined($o_negate)) {
     $test = defined($o_noreg)
                ? $$resultat{$key} eq $o_descr 
                : $$resultat{$key} =~ /$o_descr/ && $$resultat{$key} !~ /$o_negate/;
   } else {
     $test = defined($o_noreg)
                ? $$resultat{$key} eq $o_descr
                : $$resultat{$key} =~ /$o_descr/;
   }  
  if ($test) {
    # get the index numbers of the interface 
    my @oid_list = split (/\./,$key);
    $tindex2[$num_int] = pop (@oid_list);
    $tindex1[$num_int] = pop (@oid_list);
    if ($test) {
       # get the full description
       $descr[$num_int]=$$resultat{$key};
       # put the oid in an array
       $oididx = $tindex1[$num_int] . "." . $tindex2[$num_int];
       $oids[$count_oid++]=$block_table . $oididx;
       $oids[$count_oid++]=$bfree_table . $oididx;
       $oids[$count_oid++]=$bsize_table . $oididx;

       verb("   Name : $descr[$num_int], Index : $tindex1[$num_int] $tindex2[$num_int]");
       $num_int++;
    }
  }
}

my $result;
my %snmp_result;
my $getidxi = 0;
my $getidxl;
my $max_requests=10;
my $nr_requests = @oids;
my @oidlist;

verb(" nr_requests: $nr_requests");
while ( $getidxi < $nr_requests )
{
  if ( ($nr_requests - $getidxi) < $max_requests ) 
  {
    $getidxl = $getidxi + ($nr_requests - $getidxi) -1;
  } else
  {
    $getidxl = $getidxi + $max_requests -1;
  }
  @oidlist = @oids[$getidxi..$getidxl];
  if (Net::SNMP->VERSION < 4)
  {
    $result = $session->get_request(@oidlist);
  }
  else
  {
    if ($session->version == 0)
    { 
    # snmpv1
      $result = $session->get_request(Varbindlist => \@oidlist);
    }
    else
    { 
    # snmp v2c or v3 : get_bulk_request is not really good for this, so do simple get
      $result = $session->get_request(Varbindlist => \@oidlist);
      foreach my $key ( keys %$result) { verb("$key  :res: $$result{$key}"); } 
    }
  }  
  if (!defined($result))
  {
    printf("ERROR: Size table :%s.\n", $session->error);
    $session->close;
    exit $ERRORS{"UNKNOWN"};
  } 
  $getidxi += $max_requests;
  
  %snmp_result= (%snmp_result,%$result);
}

  $session->close;


# Only a few ms left...
alarm(0);

# Sum everything if -s and more than one storage
if ( defined ($o_sum) && ($num_int > 1) ) {
  verb("Adding all entries");
  $snmp_result{$block_table . $tindex1[0] . "."  . $tindex2[0] } *= $snmp_result{$bsize_table . $tindex1[0] . "."  . $tindex2[0]};
  $snmp_result{$bfree_table . $tindex1[0] . "."  . $tindex2[0]} *= $snmp_result{$bsize_table . $tindex1[0]  . "." . $tindex2[0]};
  $snmp_result{$bsize_table . $tindex1[0] . "."  . $tindex2[0]} = 1;
  for (my $i=1;$i<$num_int;$i++) {
    $snmp_result{$block_table . "."  . $tindex1[0] . $tindex2[0]} += ($snmp_result{$block_table . $tindex1[$i] . "."  . $tindex2[$i]} 
					  * $snmp_result{$bsize_table . $tindex1[$i] . $tindex2[$i]}); 
    $snmp_result{$bfree_table . "."  . $tindex1[0] . $tindex2[0]} += ($snmp_result{$bfree_table . $tindex1[$i] . "."  . $tindex2[$i]}
					  * $snmp_result{$bsize_table . $tindex1[$i] . "."  . $tindex2[$i]});
  }
  $num_int=1;
  $descr[0]="Sum of all $o_descr";
}

my $i=undef;
my $warn_state=0;
my $crit_state=0;
my ($p_warn,$p_crit);
my $output=undef;
my $idx;
for ($i=0;$i<$num_int;$i++) {
  verb("Descr : $descr[$i]");
  $idx = $tindex1[$i] . "." . $tindex2[$i];
  verb( "$block_table  $idx\n");
  verb("Size :  $snmp_result{$block_table . $idx}");
  verb("Free : $snmp_result{$bfree_table . $idx}");
  verb("Bsize : $snmp_result{$bsize_table . $idx}");
  my $to = $snmp_result{$block_table . $idx} * $snmp_result{$bsize_table . $idx} / 1024**2;
  my $pu;
  if ( $snmp_result{$block_table . $tindex1[$i] . "."  . $tindex2[$i]} != 0 ) {
    $pu = ($snmp_result{$block_table . $tindex1[$i] . "."  . $tindex2[$i]} -
           $snmp_result{$bfree_table . $tindex1[$i] . "."  . $tindex2[$i]} )
	   *100 / $snmp_result{$block_table . $tindex1[$i] . "."  . $tindex2[$i]};
  }else {
    $pu=0;
  } 
  my $pl = 100 - $pu;
  my $bl = ($snmp_result{$bfree_table . $tindex1[$i] . "." . $tindex2[$i]}) * $snmp_result{$bsize_table . $tindex1[$i] . "."  . $tindex2[$i]} / 1024**2;
  my $bu = $to - $bl;
  # add a ' ' if some data exists in $perf_out
  $perf_out .= " " if (defined ($perf_out)) ;
  ##### Ouputs and checks
  # Keep complete description fot performance output (in MB)
  my $Pdescr=$descr[$i];
  $Pdescr =~ s/[`~!\$%\^&\*'"<>|\?,\(= )]/_/g;
  ##### TODO : subs "," with something
 if (defined($o_shortL[2])) {
   if ($o_shortL[2] < 0) {$descr[$i]=substr($descr[$i],$o_shortL[2]);}
   else {$descr[$i]=substr($descr[$i],0,$o_shortL[2]);}   
 }
 if ($o_type eq "pu") { # Checks % used
    my $locstate=0;
	$p_warn=$o_warn*$to/100;$p_crit=$o_crit*$to/100; 
        (($pu >= $o_crit) && ($locstate=$crit_state=1))
	   || (($pu >= $o_warn) && ($locstate=$warn_state=1));
	if (defined($o_shortL[2])) {}
	if (!defined($o_shortL[0]) || ($locstate==1)) { # print full output if warn or critical state
	  $output.=sprintf ("%s: %.0f%%used(%.0fMB/%.0fMB) ",$descr[$i],$pu,$bu,$to);
    } elsif ($o_shortL[0] == 1) {
	  $output.=sprintf ("%s: %.0f%% ",$descr[$i],$pu);
	} 
  }
  
  if ($o_type eq 'bu') { # Checks MBytes used
    my $locstate=0;
	$p_warn=$o_warn;$p_crit=$o_crit;
    ( ($bu >= $o_crit) && ($locstate=$crit_state=1) ) 
	  || ( ($bu >= $o_warn) && ($locstate=$warn_state=1) );
	if (!defined($o_shortL[0]) || ($locstate==1)) { # print full output if warn or critical state
      $output.=sprintf("%s: %.0fMBused/%.0fMB (%.0f%%) ",$descr[$i],$bu,$to,$pu);
    } elsif ($o_shortL[0] == 1) {
	  $output.=sprintf("%s: %.0fMB ",$descr[$i],$bu);
    } 
 }
 
  if ($o_type eq 'bl') {
    my $locstate=0;
    $p_warn=$to-$o_warn;$p_crit=$to-$o_crit;
    ( ($bl <= $o_crit) && ($locstate=$crit_state=1) ) 
	  || ( ($bl <= $o_warn) && ($locstate=$warn_state=1) );
	if (!defined($o_shortL[0]) || ($locstate==1)) { # print full output if warn or critical state
      $output.=sprintf ("%s: %.0fMBleft/%.0fMB (%.0f%%) ",$descr[$i],$bl,$to,$pl);
    } elsif ($o_shortL[0] == 1) {
	  $output.=sprintf ("%s: %.0fMB ",$descr[$i],$bl);
    } 
 }
  
  if ($o_type eq 'pl') {
    my $locstate=0;
    $p_warn=(100-$o_warn)*$to/100;$p_crit=(100-$o_crit)*$to/100;
    ( ($pl <= $o_crit) && ($locstate=$crit_state=1) ) 
	  || ( ($pl <= $o_warn) && ($locstate=$warn_state=1) );
	if (!defined($o_shortL[0]) || ($locstate==1)) { # print full output if warn or critical state
      $output.=sprintf ("%s: %.0f%%left(%.0fMB/%.0fMB) ",$descr[$i],$pl,$bl,$to);
    } elsif ($o_shortL[0] == 1) {
	  $output.=sprintf ("%s: %.0f%% ",$descr[$i],$pl);
    } 
  }
  # Performance output (in MB)
  $perf_out .= "'".$Pdescr. "'=" . round($bu,0) . "MB;" . round($p_warn,0) 
	       . ";" . round($p_crit,0) . ";0;" . round($to,0);
}

verb ("Perf data : $perf_out");

my $comp_oper=undef;
my $comp_unit=undef;
($o_type eq "pu") && ($comp_oper ="<") && ($comp_unit ="%");
($o_type eq "pl") && ($comp_oper =">") && ($comp_unit ="%");
($o_type eq "bu") && ($comp_oper ="<") && ($comp_unit ="MB");
($o_type eq 'bl') && ($comp_oper =">") && ($comp_unit ="MB");

if (!defined ($output)) { $output="All selected storages "; }

if ( $crit_state == 1) {
    $comp_oper = ($comp_oper eq "<") ? ">" : "<";  # Inverse comp operator
    if (defined($o_shortL[1])) {
	  print "CRITICAL : (",$comp_oper,$o_crit,$comp_unit,") ",$output;
	} else {
	  print $output,"(",$comp_oper,$o_crit,$comp_unit,") : CRITICAL";
	}
	(defined($o_perf)) ?  print " | ",$perf_out,"\n" : print "\n";
     exit $ERRORS{"CRITICAL"};
    }
if ( $warn_state == 1) {
    $comp_oper = ($comp_oper eq "<") ? ">" : "<";  # Inverse comp operator
    if (defined($o_shortL[1])) {
       print "WARNING : (",$comp_oper,$o_warn,$comp_unit,") ",$output;
	} else {
       print $output,"(",$comp_oper,$o_warn,$comp_unit,") : WARNING";
	}
	(defined($o_perf)) ?  print " | ",$perf_out,"\n" : print "\n";
     exit $ERRORS{"WARNING"};
   }
if (defined($o_shortL[1])) {
  print "OK : (",$comp_oper,$o_warn,$comp_unit,") ",$output;
} else {
  print $output,"(",$comp_oper,$o_warn,$comp_unit,") : OK";
}
(defined($o_perf)) ? print " | ",$perf_out,"\n" : print "\n";

exit $ERRORS{"OK"};


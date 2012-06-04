#!/usr/bin/perl -w
########################## check_snmp_aixVGstate #################
my $Version='1.0';
# Date : Nov 17 2011
# Author  : Romain Forlot ( rforlot [at] yahoo [dot] com )
# Licence : GPL - http://www.fsf.org/licenses/gpl.txt
# Upon work of : Patrick Proy (patrick at proy.org)
#################################################################

use strict;
use Net::SNMP;
use Getopt::Long;

my $lvEntry  = ".1.3.6.1.4.1.2.6.191.2.2.1.1";
my $lvName   = ".1.3.6.1.4.1.2.6.191.2.2.1.1.1";
my $lvNameVg = ".1.3.6.1.4.1.2.6.191.2.2.1.1.2";
my $lvType   = ".1.3.6.1.4.1.2.6.191.2.2.1.1.3";
my $lvState  = ".1.3.6.1.4.1.2.6.191.2.2.1.1.6";

# specific

my $TIMEOUT = 15;
my %ERRORS=('OK'=>0,'WARNING'=>1,'CRITICAL'=>2,'UNKNOWN'=>3,'DEPENDENT'=>4);

# Globals

my $o_host =    undef;      # hostname
my $o_community= undef;    # community
my $o_port =    161;        # port
my $o_help=     undef;      # wan't some help ?
my $o_vgName=   undef;      # vgName
my $o_excluded= undef;      # excluded LV from scan
my $o_debug=    undef;      #debug flag
my $o_version=  undef;      # print version
# End compatibility
my $o_timeout=  undef;      # Timeout (Default 5)
my $o_perf=     undef;      # Output performance data
my $o_version2= undef;      # use snmp v2c
# SNMPv3 specific
my $o_login=    undef;      # Login for snmpv3
my $o_passwd=   undef;      # Pass for snmpv3
my $v3protocols=undef;  # V3 protocol list.
my $o_authproto='md5';      # Auth protocol
my $o_privproto='des';      # Priv protocol
my $o_privpass= undef;      # priv password

# For verbose output
sub verb { my $t=shift; print $t,"\n" if defined($o_debug) ; }

# Usage
sub print_usage {
    print "Usage: $0 [-v vgName] -H <host> -C <snmp_community> [-2] | (-l login -x passwd [-X pass -L <authp>,<privp>])  [-p <port>] [-f] [-t <timeout>] [-V]\n";
}

sub isnnum { # Return true if arg is not a number
  my $num = shift;
  if ( $num =~ /^(\d+\.?\d*)|(^\.\d+)$/ ) { return 0 ;}
  return 1;
}

sub help {
   print "\nSNMP AIX VG Monitor",$Version,"\n";
   print_usage();
   print <<EOT;
-v, --vgname
   Name of vg to monitor. 
-d, --debug
   Enabled debug message.
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
-p, --protocols=<authproto>,<privproto>
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

#Check parameters
sub check_options {
    Getopt::Long::Configure ("bundling");
    GetOptions(
    'v:s'     => \$o_vgName,        'vgname:s'      => \$o_vgName,
    'e:s'     => \$o_excluded,        'exclude:s'   => \$o_excluded,
    'h'     => \$o_help,            'help'          => \$o_help,
    'd'     => \$o_debug,           'debug'         => \$o_debug,
    'H:s'   => \$o_host,            'hostname:s'    => \$o_host,
    'p:i'   => \$o_port,            'port:i'        => \$o_port,
    'C:s'   => \$o_community,       'community:s'   => \$o_community,
    'l:s'   => \$o_login,           'login:s'       => \$o_login,
    'x:s'   => \$o_passwd,          'passwd:s'      => \$o_passwd,
    'X:s'   => \$o_privpass,        'privpass:s'    => \$o_privpass,
    'L:s'   => \$v3protocols,       'protocols:s'   => \$v3protocols,
    't:i'   => \$o_timeout,         'timeout:i'     => \$o_timeout,
    'V'     => \$o_version,         'version'       => \$o_version,
    '2'     => \$o_version2,        'v2c'           => \$o_version2,
    'f'     => \$o_perf,            'perfparse'     => \$o_perf,
    );
    # Basic checks
    if (defined($o_timeout) && (isnnum($o_timeout) || ($o_timeout < 2) || ($o_timeout > 60)))
      { print "Timeout must be >1 and <60 !\n"; print_usage(); exit $ERRORS{"UNKNOWN"}}
    if (!defined($o_timeout)) {$o_timeout=5;}
    if (defined ($o_help) ) { help(); exit $ERRORS{"UNKNOWN"}};
    if (! defined($o_vgName)) { $o_vgName = '.*' };
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
      if ((defined ($v3proto[0])) && ($v3proto[0] ne "")) {$o_authproto=$v3proto[0];        }       # Auth protocol
      if (defined ($v3proto[1])) {$o_privproto=$v3proto[1]; }       # Priv  protocol
      if ((defined ($v3proto[1])) && (!defined($o_privpass))) {
        print "Put snmp V3 priv login info with priv protocols!\n"; print_usage(); exit $ERRORS{"UNKNOWN"}}
    }
}
#######
# MAIN#
#######

check_options();

# Connect to host
verb("Connexion SNMPv3");
my ($session,$error);
if ( defined($o_login) && defined($o_passwd)) {
  # SNMPv3 login
    if (!defined ($o_privpass)) {
    ($session, $error) = Net::SNMP->session(
      -hostname     => $o_host,
      -version      => '3',
      -username     => $o_login,
      -authpassword     => $o_passwd,
      -authprotocol     => $o_authproto,
      -timeout      => $o_timeout
    );
  } else {
    ($session, $error) = Net::SNMP->session(
      -hostname     => $o_host,
      -version      => '3',
      -username     => $o_login,
      -authpassword     => $o_passwd,
      -authprotocol     => $o_authproto,
      -privpassword     => $o_privpass,
      -privprotocol => $o_privproto,
      -timeout      => $o_timeout
    );
  }
} else {
    verb("Connexion SNMPv2");
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
     verb("Connexion SMNPv1");
      # SNMPV1 login
      ($session, $error) = Net::SNMP->session(
            -hostname  => $o_host,
            -community => $o_community,
            -port      => $o_port,
            -timeout   => $o_timeout
      );
    }
}

verb("Get snmp table of lv informations");
my $LvTable = $session->get_table($lvEntry);

my @lv2monitor;
my $oid;
my $value;

# Append all vg browsed in one var
my @vgNameBrowsed = ();
my $vgName;

verb("Keep lv belong to $o_vgName");
verb(%$LvTable);
verb($o_vgName);
while (($oid, $value) = each(%$LvTable))
{
    verb ("oid: $oid value: $value");
    if ($value =~ /$o_vgName/ and $oid =~ /$lvNameVg\.(\d+)$/)
    {
            verb("Indice matched : $1");
            # Check if it is a jfs2 fs type else we don't care
            if ($$LvTable{"$lvType.$1"} == 5)
            {
                    push (@vgNameBrowsed, $value);
                    push (@lv2monitor, $1);
            }
    }
}

verb("Sort keep uniq entry in vgname list");
my %seen = ();
my @uniq_vgName = ();
my $item;
foreach $item (@vgNameBrowsed) {
    unless ($seen{$item}) {
            $seen{$item} = 1;
                   push(@uniq_vgName, $item);
    }
}
$vgName = join(", " , @uniq_vgName);

# Init counter
my %counters = (
    "openStale" => 0,
    "closeStale" => 0,
    "openSync" => 0,
    "closeSync" => 0,
    "undertermined" => 0,
);

verb("Test those lv for their state");
if(@lv2monitor)
{
    my $lv;
    foreach $lv (@lv2monitor)
    {
        verb($lv." : ".$$LvTable{"$lvState.$lv"});
        #Manage excluded LV
        next if ( defined($o_excluded) and $$LvTable{"$lvName.$lv"} =~ /$o_excluded/ );
        $$LvTable{"$lvState.$lv"} == 1 and do { $counters{"openStale"}++ };
        $$LvTable{"$lvState.$lv"} == 2 and do { $counters{"openSync"}++ };
        $$LvTable{"$lvState.$lv"} == 3 and do { $counters{"closeStale"}++ };
        $$LvTable{"$lvState.$lv"} == 4 and do {
        # set as opensync for other fs than jfs2 and jfs2log to not pollute final result
        if ($$LvTable{"$lvType.$lv"} != 5 && $$LvTable{"$lvType.$lv"} != 6 ) 
                { $counters{"openSync"}++; }
        else
                { $counters{"closeSync"}++; }
        };
            $$LvTable{"$lvState.$lv"} == 5 and do { $counters{"undeterminated"}++ };
    }
    my $output = "$vgName has $counters{'openStale'} opened stale LV, $counters{'closeStale'} closed Stale LV, $counters{'closeSync'} closed sync LV, $counters{'openSync'} opened sync LV and $counters{'undertermined'} undertermined state LV";
    if ( defined($o_perf) )
    {
    $output .= "| openStaleLV=$counters{'openStale'};;;; closeStaleLV=$counters{'closeStale'};;;; closeSyncLV=$counters{'closeSync'};;;; openSyncLV=$counters{'openSync'};;;; underterminatedLV=$counters{'undertermined'};;;;";
    }
    print $output;
    $counters{'openStale'} > 0     ? exit $ERRORS{CRITICAL} :
    $counters{'undertermined'} > 0 ? exit $ERRORS{CRITICAL} :
    $counters{'closeStale'} > 0    ? exit $ERRORS{CRITICAL} :
    $counters{'closeSync'} > 0     ? exit $ERRORS{WARNING} :
    $counters{'openSync'} > 0      ? exit $ERRORS{OK} :
                                     exit $ERRORS{UNKNOWN};
}
else
{
    print "$vgName does not exist";
    exit $ERRORS{UNKNOWN};
}

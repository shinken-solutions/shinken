#!/usr/bin/perl -w
############################ check_snmp_Safekit #################
my $Version='1.0';
# Date: Nov 17 2011
# Author: Romain Forlot ( rforlot [at] yahoo [dot] com )
# Licence: GPL - http://www.fsf.org/licenses/gpl.txt
# Upon work of: Patrick Proy (patrick at proy.org)
#################################################################

use strict;
use Net::SNMP;
use Getopt::Long;

# Specific

my $module                = ".1.3.6.1.4.1.107.175.10";
my $moduleId              = ".1.3.6.1.4.1.107.175.10.1.1.1";
my $moduleName            = ".1.3.6.1.4.1.107.175.10.1.1.2";
my $moduleState           = ".1.3.6.1.4.1.107.175.10.1.1.4";
my $moduleSyntheticState  = ".1.3.6.1.4.1.107.175.10.1.1.6";

my $TIMEOUT = 15;
my %ERRORS=('OK'=>0,'WARNING'=>1,'CRITICAL'=>2,'UNKNOWN'=>3,'DEPENDENT'=>4);

my %StateRet = (
        0 => "Stop",
        1 => "Wait",
        2 => "Alone",
        3 => "Prim",
        4 => "Second" );
my %SubStateRet = (
        0 => "available",
        1 => "transient",
        2 => "stopped" );

my $oid;        # Working var fill with oid of module table
my $value;      # Working var fill with value of module table
my @moduleIndex;# Index of Safekit Module in SNMP table

my $modTable;   # SNMP table of module

my $StateVal;
my $SubStateVal;
my $moduleNameVal;
my $GlobalStateVal = "UNKNOWN";

# Globals

my $o_host =    undef;          # hostname
my $o_module =    undef;          # Safekit module name
my $o_community = undef;        # community
my $o_port =    161;            # port
my $o_help=     undef;          # wan't some help?
my $o_verbose=     undef;          # verbosity increase
my $o_version=  undef;          # print version
# End compatibility
my $o_timeout=  undef;          # Timeout (Default 5)
my $o_version2= undef;          # use snmp v2c
# SNMPv3 specific
my $o_login=    undef;          # Login for snmpv3
my $o_passwd=   undef;          # Pass for snmpv3
my $v3protocols=undef;  # V3 protocol list.
my $o_authproto='md5';          # Auth protocol
my $o_privproto='des';          # Priv protocol
my $o_privpass= undef;          # priv password

# For verbose output
sub verb { my $t=shift; print $t,"\n" if defined($o_verbose) ; }

# Usage
sub print_usage {
    print "Usage: $0 [-v] -H <host> -C <snmp_community> [-2] | (-l login -x passwd [-X pass -L <authp>,<privp>]) [-p <port>] [-m Safekit_module] [-f] [-t <timeout>] [-V]\n";
}

sub isnnum { # Return true if arg is not a number
  my $num = shift;
  if ( $num =~ /^(\d+\.?\d*)|(^\.\d+)$/ ) { return 0 ;}
  return 1;
}

sub help {
   print "\nSNMP Safekit Global state Monitor",$Version,"\n";
   print_usage();
   print <<EOT;
-m, --module
   Name of Safekit module to monitor.
-v, --verbose
   Enabled verbosity.
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
   <authproto>: Authentication protocol (md5|sha: default md5)
   <privproto>: Priv protocole (des|aes: default des)
-p, --port=PORT
   SNMP port (Default 161)
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
        'm:s'   => \$o_module,          'module:s'        => \$o_module,
        'v'     => \$o_verbose,         'verbose'       => \$o_verbose,
        'h'     => \$o_help,            'help'          => \$o_help,
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
        );
    # Basic checks
        if (defined($o_timeout) && (isnnum($o_timeout) || ($o_timeout < 2) || ($o_timeout > 60)))
          { print "Timeout must be >1 and <60!\n"; print_usage(); exit $ERRORS{"UNKNOWN"}}
        if (!defined($o_timeout)) {$o_timeout=5;}
    if (defined ($o_help) ) { help(); exit $ERRORS{"UNKNOWN"}};
    if (defined($o_version)) { p_version(); exit $ERRORS{"UNKNOWN"}};
    if ( ! defined($o_host) ) # check host and filter
        { print_usage(); exit $ERRORS{"UNKNOWN"}}
#    if ( ! defined($o_module) ) { print "Specify a Safekit module.\n"; print_usage(); exit $ERRORS{"UNKNOWN"};}
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
      -hostname         => $o_host,
      -version          => '3',
      -username         => $o_login,
      -authpassword     => $o_passwd,
      -authprotocol     => $o_authproto,
      -timeout          => $o_timeout
    );
  } else {
    ($session, $error) = Net::SNMP->session(
      -hostname         => $o_host,
      -version          => '3',
      -username         => $o_login,
      -authpassword     => $o_passwd,
      -authprotocol     => $o_authproto,
      -privpassword     => $o_privpass,
      -privprotocol     => $o_privproto,
      -timeout          => $o_timeout
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

verb("Get snmp table of safekit module informations");
$modTable = $session->get_table($module);

if ( ! $modTable )
{
        print "Safekit SNMP agent isn't active or chosen port isn't the good one.";
        exit $ERRORS{CRITICAL};
}

while (($oid, $value) = each %$modTable)
{
        if ( $oid =~ /$moduleId.[0-9]+/ )
        {
                verb('Module detected, id:'.$value);
                push @moduleIndex, $value;
        }
}

my $index;
verb("Get information of module Table about his state");
for $index  (@moduleIndex)
{
        $moduleNameVal = $$modTable{"$moduleName.$index"};
        $StateVal = $StateRet{$$modTable{"$moduleState.$index"}};
        $SubStateVal = $SubStateRet{$$modTable{"$moduleSyntheticState.$index"}};
        if ((($o_module) and $moduleNameVal eq $o_module) or ( ! $o_module ))
        {
                if ( ($StateVal eq "Prim" or $StateVal eq "Second") and $SubStateVal eq "available" )
                {
                        print "$moduleNameVal: State = $StateVal and Synthetic State = $SubStateVal";
                        $GlobalStateVal = "OK";
                }
                else
                {
                        print "$moduleNameVal: State = $StateVal and Synthetic State = $SubStateVal";
                        $GlobalStateVal = "CRITICAL";
                }
        }
}
exit $ERRORS{$GlobalStateVal};

#!/usr/bin/perl -w
############################## check_snmp_HACMP #################
my $Version='1.0';
# Date : Nov 17 2011
# Author  : Romain Forlot ( rforlot [at] yahoo [dot] com )
# Licence : GPL - http://www.fsf.org/licenses/gpl.txt
# Upon work of : Patrick Proy (patrick at proy.org)
#################################################################

use strict;
use Net::SNMP;
use Getopt::Long;

# Global

my $cluster  = ".1.3.6.1.4.1.2.3.1.2.1.5.1";
my $clusterName = ".1.3.6.1.4.1.2.3.1.2.1.5.1.2.0";
my $clusterNodeName   = ".1.3.6.1.4.1.2.3.1.2.1.5.1.9.0";
my $clusterState  = ".1.3.6.1.4.1.2.3.1.2.1.5.1.4.0";
my $clusterSubState  = ".1.3.6.1.4.1.2.3.1.2.1.5.1.8.0";

# specific

my $TIMEOUT = 15;
my %ERRORS=('OK'=>0,'WARNING'=>1,'CRITICAL'=>2,'UNKNOWN'=>3,'DEPENDENT'=>4);

# Globals

my $o_host =    undef;          # hostname
my $o_community = undef;        # community
my $o_port =    161;            # port
my $o_help=     undef;          # wan't some help ?
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
    print "Usage: $0 [-v] -H <host> -C <snmp_community> [-2] | (-l login -x passwd [-X pass -L <authp>,<privp>])  [-p <port>] [-f] [-t <timeout>] [-V]\n";
}

sub isnnum { # Return true if arg is not a number
  my $num = shift;
  if ( $num =~ /^(\d+\.?\d*)|(^\.\d+)$/ ) { return 0 ;}
  return 1;
}

sub help {
   print "\nSNMP AIX HACMP Monitor",$Version,"\n";
   print_usage();
   print <<EOT;
-v, --erbose
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

verb("Get snmp table of cluster informations");
my $clTable = $session->get_table($cluster);

my $oid;
my $value;

my %StateRet = (
        2 => "Up",
        4 => "Down",
        8 => "Unknown",
        256 => "notConfigured" );
my %SubStateRet = (
        8 => "Unknown", 
        16 => "unstable",
        32 => "stable",
        64 => "error",
        128 => "reconfig",
        256 => "notconfigured",
        512 => "notsynced" );

verb("Get information of cluster Table about his state");
my $StateVal = $StateRet{$$clTable{$clusterState}};
my $SubStateVal = $SubStateRet{$$clTable{$clusterSubState}};

if ( $StateVal eq "Up" and $SubStateVal eq "stable" )
{
        print "Node $$clTable{$clusterNodeName}: $StateVal and $SubStateVal";
        exit $ERRORS{OK};
}
else
{
        print "Node $$clTable{$clusterNodeName}: $StateVal and $SubStateVal";
        exit $ERRORS{CRITICAL};
}
exit $ERRORS{UNKNOWN};

#!/usr/bin/perl -w

# $Id: check_wins.pl 940 2004-11-25 04:46:16Z stanleyhopcroft $

# Revision 1.3  2004/11/25 04:46:16  stanleyhopcroft
# Non functional tidy ups to check_wins
#
# Revision 1.2  2003/08/20 08:31:49  tonvoon
# Changed netsaint to nagios in use lib
#
# Revision 1.1  2003/02/09 14:16:28  sghosh
# more contribs
#

use strict ;

use Getopt::Long ;
use vars qw($opt_H $opt_D $opt_W $opt_T $debug @my_dcs);

use lib '/usr/local/nagios/libexec/' ;
use utils qw($TIMEOUT %ERRORS &print_revision &support &usage);

my $PROGNAME = 'check_wins' ;

use constant SAMBA_DEBUG_LVL	=> 2 ;
use constant MY_DCS 		=> ('dc1','dc2') ;

my $NMBLOOKUP_PATH		= '/usr/bin/nmblookup' ;
my $NMBLOOKUP			= sub { return `$NMBLOOKUP_PATH $_[2] -R -U $_[0] $_[1]` } ;
my $NMBLOOKUP_CMD		= $NMBLOOKUP_PATH  . ' -R -U' ;

sub print_help ();
sub print_usage ();
sub help ();
sub version ();

delete @ENV{'PATH', 'IFS', 'CDPATH', 'ENV', 'BASH_ENV'};

$SIG{"ALRM"} = sub { die "Alarm clock restart" } ;

Getopt::Long::Configure('bundling', 'no_ignore_case');
GetOptions
        ("V|version"     => \&version,
         "h|help"        => \&help,
         "d|debug"       => \$debug,
	 "C|controllers:s" => \@my_dcs,
         "T|timeout:i"	 => \$opt_T,
         "W|wins=s"	 => \$opt_W,
         "D|domain=s"    => \$opt_D);


($opt_D) || usage("MS Domain name not specified\n");
my $domain = $1 if $opt_D =~ m#(\w+)# ;                # NetBIOS names allow __any__ characters (more than \w)
($domain) || usage("Invalid MS D name: $opt_D\n");

($opt_W) || usage("WINS hostname or address not specified\n");
my $wins = $1 if $opt_W =~ m#((?:^\w+$)|(?:\d+(?:\.\d+){3,3}$))# ;
($wins) || usage("Invalid WINS hostname or address: $opt_W\n");

usage("You must provide the names of your domain controllers by updating MY_DCS in the text or use -C dc_name1 -C dc_name2 ..\n")
  unless (@my_dcs or MY_DCS) ;

@my_dcs = MY_DCS	unless defined $my_dcs[0] ;
$TIMEOUT = $opt_T	if defined $opt_T ;

my ($netbios_name, @dcs_of_domain, @dc_addresses) ;
my (@addr_dcs_of_domain, @found_dcs, %address2dc) ;
my (@dc_query) ;

# tsitc> /usr/local/samba/bin/nmblookup -R -U wins ipa01
# Sending queries to 192.168.1.29
# 192.168.1.16 ipa01<00>

eval {
  alarm($TIMEOUT) ;
  @dc_query = $debug ? map { $NMBLOOKUP->($wins, "$_#20", '-d ' . SAMBA_DEBUG_LVL) } @my_dcs :
		       map { ( $NMBLOOKUP->($wins, "$_#20", '') )[1] } @my_dcs ;
  alarm(0) ;
} ;

if ($@ and $@ =~ /Alarm clock restart/) {
  print qq(Failed. Timeout while waiting for response from  (one of) "$NMBLOOKUP_CMD $wins @my_dcs"\n) ;
  exit $ERRORS{"CRITICAL"} ;
}

if ($@ and $@ !~ /Alarm clock restart/) {
  print qq(Failed. "$@" in response to "NMBLOOKUP_CMD $wins @my_dcs"\n) ;
  exit $ERRORS{"UNKNOWN"} ;
}

chomp @dc_query ;
if ( scalar grep(/name_query failed/, @dc_query) ) {
  print qq(Failed. WINS "$wins" failed to resolve), scalar @my_dcs > 1 ? ' at least one of ' : ' ', qq("@my_dcs", the domain controller(s) of "$domain". Got "@dc_query"\n) ;
  exit $ERRORS{"CRITICAL"} ;
}

=begin comment

the results of looking up the DCs (by their name) in the WINS 

192.168.1.16 ipa01<20>
192.168.1.1 ipa02<20>
192.168.1.104 ipa03<20>

=end comment

=cut

@dc_addresses = () ;
foreach (@dc_query) {
  next unless /^(\S+)\s+(\S+?)<\S+?>$/ ;
  $address2dc{$1} = $2 ;
  push @dc_addresses, $1 ;
}

$netbios_name = "$domain#1C"  ;

eval {
  alarm($TIMEOUT) ;
  @dcs_of_domain = $NMBLOOKUP->($wins, $netbios_name, defined $debug ? '-d ' . SAMBA_DEBUG_LVL : '') ;
  alarm(0) ;

} ;

if ($@ and $@ =~ /Alarm clock restart/) {
  print qq(Failed. Timeout while waiting for response from "$NMBLOOKUP_CMD $wins $netbios_name"\n) ;
  exit $ERRORS{"CRITICAL"} ;
} 

if ($@ and $@ !~ /Alarm clock restart/) {
  print qq(Failed. "$@" in response to "$NMBLOOKUP_CMD $wins $netbios_name"\n) ;
  exit $ERRORS{"UNKNOWN"} ;
}

shift @dcs_of_domain ;
chomp @dcs_of_domain ;
@addr_dcs_of_domain = map /^(\S+)/, @dcs_of_domain ;

=begin comment

tsitc> /usr/local/samba/bin/nmblookup -R -U wins ipaustralia#1c
Sending queries to 192.168.1.29
192.168.1.114 ipaustralia<1c>
192.168.1.221 ipaustralia<1c>
192.168.1.61 ipaustralia<1c>
192.168.1.129 ipaustralia<1c>
192.168.1.128 ipaustralia<1c>
192.168.1.214 ipaustralia<1c>
192.168.1.67 ipaustralia<1c>
tsitc> 

=end comment

=cut


my %x ;
@found_dcs = grep { ! $x{$_}++ } @address2dc{ grep exists $address2dc{$_}, @addr_dcs_of_domain} ;
# @found_dcs = grep { defined $_} @address2dc{ grep exists $address2dc{$_}, @addr_dcs_of_domain} ;
								# Gotcha.
								# 'exists' is necessary to prevent autovivificatiton
								# of keys in %address2dc

if ( &set_eq( \@found_dcs, [ values %address2dc ] ) ) {
  print $debug ? qq(Ok. WINS named "$wins" resolved addresses of "@my_dcs" as "@dc_query" and controllers of domain "$domain" as "@dcs_of_domain"\n) :
		 qq(Ok. Found controllers named "@my_dcs" in response to "$domain#1C" name query from WINS named "$wins".\n) ;
  exit $ERRORS{"OK"} ;
} elsif ( scalar @found_dcs == 0 ) {
  print qq(Failed. Found __no__ controllers named "@my_dcs" in response to "$domain#1C" query from WINS named "$wins". Got "@dcs_of_domain"\n) ;
  exit $ERRORS{"CRITICAL"} ;
} elsif ( scalar @found_dcs < scalar keys %address2dc ) {
  print qq(Warning. Not all domain controllers found in response to "$domain#1C" query from WINS named "$wins". Expected "@my_dcs", got "@found_dcs"\n) ;
  exit $ERRORS{"WARNING"} ;
}

sub set_eq {

  return 0 unless scalar @{$_[0]} == scalar @{$_[1]} ;
  foreach my $a ( @{$_[0]} ) {
    return 0 unless scalar grep { $a eq $_ } @{$_[1]} ;
  } 
  return 1 ;

}


sub print_usage () {
	print "Usage: $PROGNAME -W <wins> -D <domain>\n";
}

sub print_help () {
	print_revision($PROGNAME,'$Revision: 940 $ ');
	print "Copyright (c) 2001 Karl DeBisschop/S Hopcroft

Perl Check WINS plugin for NetSaint.

Returns OK if the addresses of domain controllers are found in the list of domain controllers returned in the WINS response to a 'domain controllers query' 

Why would you want to do this ?

MS File server clients insist on connecting to file servers using NetBIOS names.
If they __don't__ resolve NetBIOS names with a WINS (NBNS) then they'll either fail to logon and  connect to shares or they will
broadcast requsts for names.
Both problems are eliminated by a healthy WINS.
Also, you may have a MS domain spanning a  number of WAN connected sites, with domain controllers far away from powerful local
domain controllers.
In this case, you want your local clients to have their logon requests validated by the local controllers.

The plugin works by
  asking the WINS to resolve the addresses of the domain controllers (supplied by -C or from the constant MY_DCS)
  asking the WINS to return the list of addresses of the domain controllers able to validate requests for the domain
   whose name is given by -D
  returning Ok		if all controller addresses are in that list (of addresses of domain controllers) or
  returning WARNING	if not all the controller addresses are in the list or
  returning CRITICAL	if there is no reply from the WINS or the list contains none of the contoller addresses

";
	print_usage();
	print '
-W, --wins=STRING
   Hostname or address of the WINS (Either Samba/nmbd or MS product)
-D, --domain=STRING
   MS Domain name to find the Domain controllers of.
-C, --controllers:STRING
   Optional __name(s)__ of domain controller that __must__ be found in the response to a domain controller name query.
   If not defined, then use the constant value MY_DCS. You must use either -C or make sure that MY_DCS contains the names 
   of __your__ domain controllers.
-T, --timeout:INTEGER
-d, --debug
   Debugging output.
-h, --help
   This stuff.

';
	support();
}

sub version () {
	print_revision($PROGNAME,'$Revision: 940 $ ');
	exit $ERRORS{'OK'};
}

sub help () {
	print_help();
	exit $ERRORS{'OK'};
}


#!/usr/bin/perl -w

# $Id: check_ica_master_browser.pl 1099 2005-01-25 09:09:33Z stanleyhopcroft $

# Revision 1.1  2005/01/25 09:09:33  stanleyhopcroft
# New plugin - checks that ICA master browser is what it should be (important for firewalled dialup)
#

use strict ;

use IO::Socket;
use IO::Select;
use Getopt::Long ;

use lib qw(/usr/local/nagios/libexec) ;
use utils qw(%ERRORS &print_revision &support &usage);
use packet_utils qw(&pdump &tethereal) ;

my $PROGNAME = 'check_ica_master_browser' ;

# You might have to change this...

my $PACKET_TIMEOUT	= 1;
												# Number of seconds to wait for further UDP packets
my $TEST_COUNT		= 2;
												# Number of datagrams sent without reply 
my $BUFFER_SIZE		= 1500;
												# buffer size used for 'recv' calls.
my $ICA_PORT		= 1604;
												# what port ICA runs on. Unlikely to change.

# End user config.

my ($debug, $preferred_master, $bcast_addr, $ica_browser, $timeout) ;

Getopt::Long::Configure('bundling', 'no_ignore_case');
GetOptions
        ("V|version"     => \&version,
         "h|help"        => \&help,
         "v|verbose"     => \$debug,
         "B|broadcast_addr:s"   => \$bcast_addr,
         "I|ica_browser:s"	=> \$ica_browser,
         "P|preferred_master:s"	=> \$preferred_master,
         "T|Packet_timeout:i"   => \$timeout,
) ;


my $broadcast_addr = $1 if $bcast_addr and $bcast_addr =~ m#(\d+\.\d+\.\d+\.\d+)# ;
usage("Invalid broadcast address: $bcast_addr")
	if $bcast_addr and not defined($broadcast_addr)  ;

usage("You must provide either the name of an ICA browser or the broadcast address of the subnet containing them\n")
	unless ($ica_browser or $broadcast_addr) ;

usage("You must provide the name or address of a preferred ICA master browser\n")
	unless ($preferred_master) ;

my $preferred_master_n = $preferred_master =~ m#(\d+\.\d+\.\d+\.\d+)#
	? $preferred_master
	: inet_ntoa(scalar gethostbyname($preferred_master)) ;

my $Timeout = $timeout || $PACKET_TIMEOUT ;

												# Definitions of query strings. Change at your own risk :)
												# this info was gathered with tcpdump whilst trying to use an ICA client,
												# so I'm not 100% sure of what each value is.

my $bcast_helo = &tethereal(<<'End_of_Tethereal_trace', '1e') ;
0020  ff ff 04 d6 06 44 00 26 4a 76 1e 00 01 30 02 fd   .....D.&Jv...0..
0030  a8 e3 00 02 f5 95 9f f5 30 07 00 00 00 00 00 00   ........0.......
0040  00 00 00 00 00 00 01 00                           ........
End_of_Tethereal_trace

my $direct_helo = &tethereal(<<'End_of_Tethereal_trace', '20') ;
0020  64 17 05 0f 06 44 00 28 ab b5 20 00 01 30 02 fd   d....D.(.. ..0..
0030  a8 e3 00 00 00 00 00 00 00 00 00 00 00 00 00 00   ................
0040  00 00 00 00 00 00 00 00 00 00                     ........
End_of_Tethereal_trace

my $Udp =  IO::Socket::INET->new( Proto => 'udp' )
	|| die "Socket failure: $!";

												# select is here to allow us to set timeouts on the connections.  Otherwise they 
												# just 'stop' until a server appears.

my $select =  IO::Select->new($Udp)
	|| die "Select failure: $!";

$Udp->sockopt(SO_BROADCAST, 1 );

my ($remote_host, $buff, $destination, $raddr, $rport, $rhost, @remote_response);
my ($query_message, $send_addr, $this_test) ;

$buff = '';
$this_test = 0;

												# If there is no response to the first helo packet it will be resent
												# up to $TEST_COUNT (see at the top).

$query_message = $broadcast_addr ? $bcast_helo : $direct_helo ;
$destination   = $broadcast_addr ? $broadcast_addr: $ica_browser ;
$send_addr = sockaddr_in($ICA_PORT, inet_aton($destination) ) ;

while ( ++$this_test <= $TEST_COUNT && !$buff ) {

	print "Sending helo datagram. datagram number: ", $this_test, "\n"
		if $debug ;

	print "Querying $destination for master browser\n"
		if  $debug  ;
  	&pdump($query_message)
		if $debug ;
	$Udp->send($query_message, 0, $send_addr ); 
	if ( $select->can_read($Timeout) ) {
		$remote_host = $Udp->recv($buff, $BUFFER_SIZE, 0 );
	}

	last
		if $buff ;
	sleep 1 ;

} 

												# Ok we've looped several times, looking for a response. If we don't have one 
												# yet, we simply mark the whole lot as being unavailable.

unless ( $buff ) {
	print "Failed. No response to helo datagram (master browser query) from $destination.\n" ;
	exit $ERRORS{CRITICAL} ;
}

($rport, $raddr) = sockaddr_in( $remote_host );
$rhost = gethostbyaddr( $raddr, AF_INET );
my @tmpbuf = unpack('C*', $buff );
if ( $debug ) {
	print "$rhost:$rport responded with: ",length($buff), " bytes\n";
	&pdump($buff) ;
}

												# Now we have a response, then we need to figure out the master browser, and 
												# query it for published applications...

my $master_browser = join '.', @tmpbuf[32..35] ;
my ($master_browser_a) = gethostbyaddr(inet_aton($master_browser), AF_INET) =~ /^(\w+?)\./ ;
     
												# Ok should probably error check this, because it's remotely possible
												# that a server response might be completely wrong...
      
print "Master browser = $master_browser_a/$master_browser\n"
	if  $debug ;

$send_addr = sockaddr_in($ICA_PORT, inet_aton($master_browser));

my $subject_clause = $bcast_addr ? "of the \"$destination\" subnet" : "known to ICA server \"$destination\"" ;

if ( $master_browser eq  $preferred_master_n ) {
	print "Preferred master browser \"$preferred_master\" __is__ the master browser (\"$master_browser_a/$master_browser\") $subject_clause.\n" ;
	exit $ERRORS{OK} ;
} else {
	print "\"\u$preferred_master\" is __not__ the master browser (\"$master_browser_a/$master_browser\") $subject_clause: remote clients (dialup) may not find Published applications from Master Browser.\n" ;
	exit $ERRORS{CRITICAL} ;
}

close $Udp;


sub print_usage () {
	print "Usage: $PROGNAME (-B <broadcast_address>| -I <citrix_server>) - P <preferred_master_browser>" ;
}

sub print_help () {
	print_revision($PROGNAME,'$Revision: 1099 $ ');
	print "Copyright (c) 2002 Ed Rolison/Tom De Blende/S Hopcroft

Perl Check Citrix Master Browser plugin for Nagios.

Returns OK if the Citrix master browser is that given by the -P option.

The plugin works by
  If the -B option is specified, sends a broadcast helo to find the address of the Citrix master browser in the specified subnet.
    return critical if there is no reply;
  Else if the -I option is specified 
    send a direct helo to the specified server until there is a response (containing the address of the Citrix master browser)


  return Critical if the response does not contain the address of the 'preferred master browser' (-P option).
  return OK

  How ICA Clients Use the Master ICA Browser.

Citrix ICA Clients must locate the master browser to get the address of a server or published application.

The Citrix ICA Client can locate the master browser by sending out broadcast packets, or,
if the address of a Citrix server is specified in the Citrix ICA Client or in an ICA file,
the ICA Client locates the master browser by sending directed packets to the specified address.
The ICA Client requests the address of the ICA master browser from the Citrix server.

";
	print_usage();
	print '
-B, --broadcast_address:STRING
   The broadcast address that should contain Citrix master browser. This option takes precedence over -I.
-I, --ica_browser:STRING
   Optional name or address of an ICA server that could be the master browser (used when broadcast not possible).
-P, --preferred_master:STRING
   Name or address of the ICA server that _should_ be the master browser.
   Required.
-T, --packet-timeout:INTEGER
   Time to wait for UDP packets (default 1 sec).
-v, --verbose
   Debugging output.
-h, --help
   This stuff.

';
	support();
}

sub version () {
	print_revision($PROGNAME,'$Revision: 1099 $ ');
	exit $ERRORS{'OK'};
}

sub help () {
	print_help();
	exit $ERRORS{'OK'};
}


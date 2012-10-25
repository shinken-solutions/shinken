#!/usr/bin/perl -w

# $Id: check_ica_metaframe_pub_apps.pl 1098 2005-01-25 09:07:39Z stanleyhopcroft $

# Revision 1.1  2005/01/25 09:07:39  stanleyhopcroft
# Replacement (structured name mainly) for check_citrix: check of ICA browse service
#
# Revision 1.1  2005-01-25 17:00:24+11  anwsmh
# Initial revision
#

use strict ;

use IO::Socket;
use IO::Select;
use Getopt::Long ;

my ($bcast_addr, $timeout, $debug, @citrix_servers, $crit_pub_apps, $warn_pub_apps, $long_list) ;

use lib qw(/usr/local/nagios/libexec) ;
use utils qw(%ERRORS &print_revision &support &usage) ;
use packet_utils qw(&pdump &tethereal) ;

my $PROGNAME = 'check_ica_metaframe_pub_apps' ;

sub print_help ();
sub print_usage ();
sub help ();
sub version ();

										# You might have to change this...

my $PACKET_TIMEOUT	= 1;
										# Number of seconds to wait for further UDP packets
my $TEST_COUNT		= 2;
# Number of datagrams sent without reply 
my $BUFFER_SIZE		= 1500;
				# buffer size used for 'recv' calls.
my $LONG_LIST		= 0 ;
										# this is for if you have many published applications.
										# if you set it, it won't do any harm, but may slow the test
										# down a little. (Since it does a 'recv' twice instead of 
										# once and therefore may have to wait for a timeout).
my $ICA_PORT		= 1604;
										# what port ICA runs on. Unlikely to change.

Getopt::Long::Configure('bundling', 'no_ignore_case');
GetOptions
        ("V|version"     => \&version,
         "h|help"        => \&help,
         "v|verbose"       => \$debug,
         "B|broadcast_addr:s"	=> \$bcast_addr,
         "C|citrix_servers:s"	=> \@citrix_servers,
         "L|long_list"		=> \$long_list,
         "P|crit_pub_apps:s"	=> \$crit_pub_apps,
         "T|Packet_timeout:i"   => \$timeout,
         "W|warn_pub_apps:s"	=> \$warn_pub_apps,
) ;


my $broadcast_addr = $1 if $bcast_addr and $bcast_addr =~ m#(\d+\.\d+\.\d+\.\d+)# ;
usage("Invalid broadcast address: $bcast_addr\n")
	if $bcast_addr and not defined($broadcast_addr)  ;

usage("You must provide either the names of citrix servers or the broadcast address of the subnet containing them\n")
	unless (@citrix_servers or $broadcast_addr) ;

my @target = defined $broadcast_addr ? ($broadcast_addr) : @citrix_servers ;

usage("You must provide the names of the published applications that the Citrix browser should be advertising\n")
	unless $crit_pub_apps or $warn_pub_apps ;

my $Timeout = $timeout
	if defined $timeout ;
$Timeout = $PACKET_TIMEOUT
	unless defined $Timeout ;
$long_list = $LONG_LIST
	unless defined $long_list ;

my @crit_pub_apps = $crit_pub_apps ? split(/,/, $crit_pub_apps) : () ;
my @warn_pub_apps = $warn_pub_apps ? split(/,/, $warn_pub_apps) : () ;

										# Definitions of query strings. Change at your own risk :)
										# this info was gathered with tcpdump whilst trying to use an ICA client,
										# so I'm not 100% sure of what each value is.

my $bcast_helo = &tethereal(<<'End_of_Tethereal_trace', '1e') ;
0020  ff ff 04 d6 06 44 00 26 4a 76 1e 00 01 30 02 fd   .....D.&Jv...0..
0030  a8 e3 00 02 f5 95 9f f5 30 07 00 00 00 00 00 00   ........0.......
0040  00 00 00 00 00 00 01 00                           .......
End_of_Tethereal_trace

my $bcast_query_app = &tethereal(<<'End_of_Tethereal_trace', '24') ;
0020  64 17 04 50 06 44 00 2c 85 6a 24 00 01 32 02 fd   d..P.D.,.j$..2..
0030  a8 e3 00 00 00 00 00 00 00 00 00 00 00 00 00 00   ................
0040  00 00 00 00 00 00 21 00 02 00 00 00 00 00         ......!......
End_of_Tethereal_trace

my $direct_helo = &tethereal(<<'End_of_Tethereal_trace', '20') ;
0020  64 17 05 0f 06 44 00 28 ab b5 20 00 01 30 02 fd   d....D.(.. ..0..
0030  a8 e3 00 00 00 00 00 00 00 00 00 00 00 00 00 00   ................
0040  00 00 00 00 00 00 00 00 00 00                     .........
End_of_Tethereal_trace

my $direct_query_app = &tethereal(<<'End_of_Tethereal_trace', '2c') ;
0020  64 17 05 10 06 44 00 34 7a 9a 2c 00 02 32 02 fd   d....D.4z.,..2..
0030  a8 e3 00 00 00 00 00 00 00 00 00 00 00 00 00 00   ................
0040  00 00 00 00 00 00 21 00 02 00 01 00 00 00 00 00   ......!.........
0050  00 00 00 00 00 00                                 ......       
End_of_Tethereal_trace

my $Udp =  IO::Socket::INET->new( Proto => 'udp' )
	|| die "Socket failure: $!";

										# Select is here to allow us to set timeouts on the connections.
										# Otherwise they just 'stop' until a server appears.

my $select =  IO::Select->new($Udp)
	|| die "Select failure: $!";
										# Helo needs to be broadcastt, but query does not.
$Udp->sockopt(SO_BROADCAST, 1 );

my ($remote_host, $buff, $buff2, $raddr, $rport, $rhost, @remote_response);
my ($query_message, $send_addr, $this_test) ;

$buff = $buff2 = '';
$this_test = 0;

										# If there is no response to the first helo packet it will be resent
										# up to TEST_COUNT (see at the top).

while ( ++$this_test <= $TEST_COUNT && !$buff ) {

	print "Sending helo datagram. datagram number: ", $this_test, "\n"
		if $debug ;

										# If we have multiple targets, we probe each of them until we get a 
										# response...

	foreach my $destination (@target) { 
		$query_message = $broadcast_addr ? $bcast_helo : $direct_helo ;
		print "Querying $destination for master browser\n"
			if  $debug  ;
		$send_addr = sockaddr_in($ICA_PORT, inet_aton($destination) );
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
}

										# Ok we've looped several times, looking for a response. If we don't have one 
										# yet, we simply mark the whole lot as being unavailable.

unless ( $buff ) {
	print "Failed. No response to helo datagram (master browser query) from ", $broadcast_addr ? $broadcast_addr : "@citrix_servers", ".\n" ;
	exit $ERRORS{CRITICAL} ;
}

($rport, $raddr) = sockaddr_in( $remote_host );
$rhost = gethostbyaddr( $raddr, AF_INET );
my @tmpbuf = unpack('C*', $buff );
if ( $debug ) {
	print "$rhost:$rport responded with: ", length($buff), " bytes\n";
	&pdump($buff) ;
}

										# Now we have a response, then we need to figure out the master browser, and 
										# query it for published applications...

my $master_browser = join '.', @tmpbuf[32..35] ;
     
										# Ok should probably error check this, because it's remotely possible
										# that a server response might be completely wrong...
      
print "Master browser = $master_browser\n"
	if  $debug ;

$send_addr = sockaddr_in($ICA_PORT, inet_aton($master_browser));

if ( $broadcast_addr ) {
	print "using broadcast query\n"
		if $debug ;
	$query_message = $bcast_query_app;
} else {
	print "using directed query\n"
		if $debug ;
	$query_message = $direct_query_app;
}
   
										# Now we send the appropriate query string, to the master browser we've found.

$buff = '';
$this_test = 0 ;

print "Querying master browser for published application list\n"
	if  $debug  ;

while ( ++$this_test <= $TEST_COUNT && !$buff ) {
	print "Sending application query datagram.  datagram number: ", $this_test, "\n"
		if $debug ;
	&pdump($query_message)
		if $debug ;
	$Udp->send($query_message, 0, $send_addr); 

	if ( $select->can_read($Timeout) ) {
		$remote_host = $Udp->recv($buff, $BUFFER_SIZE, 0 );
										# $buff = substr($buff, 32) ;
										# Hope that ICA preamble is first 32 bytes
	}

										# Long application lists are delivered in multiple packets
  
	my $buff2 = '' ;
	while ( $long_list && $select->can_read($Timeout) ) {
		$remote_host = $Udp->recv($buff2, $BUFFER_SIZE, 0);
		$buff .= $buff2
			if $buff2 ;
										# $buff .= substr($buff2, 32) if $buff2 ;
										# Hope that ICA preamble is first 32 bytes
	}

	last if $buff ;
	sleep 1 ;

}

unless ( $buff ) {
	print "Failed. No response to application query datagram from ", $master_browser, ".\n" ;
	exit $ERRORS{CRITICAL} ;
}

										# we got a response from a couple of retries of the app query

($rport, $raddr) = sockaddr_in ( $remote_host );
$rhost = gethostbyaddr ( $raddr, AF_INET );
if ( $debug ) {
	print "$rhost:$rport responded to app query with: ", length($buff), " bytes\n";
	&pdump($buff) ;
}

my $app_list = $buff ;
										# delete nulls in unicode
										# but only if there is unicode (usually from
										# broadcast query)

$app_list =~ s/(?:(\w| |-)\x00)/$1/g
  if $app_list =~ /(?:(?:(?:\w| |-)\x00){3,})/ ;
										# FIXME an application name is
										# 3 or more unicoded characters

										# FIXME locale
										# extract null terminated strings

my (@clean_app_list, $clean_app_list) ;
$clean_app_list = join(',', @clean_app_list = $app_list =~ m#([A-Za-z](?:\w| |-|[ƒ÷‹‰ˆ¸ﬂ])+?(?=\x00))#g ) ;

										# patch for German umlauts et al from Herr Mike Gerber.

										# $clean_app_list = join(',', @clean_app_list = $app_list =~ m#([A-Z](?:\w| |-)+?(?=\x00))#g ) ;

										# FIXME everyones apps don't start with caps

print qq(Received list of applications: "$clean_app_list".\n)
	if $debug ;

if ( scalar @crit_pub_apps and my @missing = &simple_diff(\@clean_app_list, \@crit_pub_apps) ) {
	print qq(Failed. "@missing" not found in list of published applications), 
		  qq(" $clean_app_list" from master browser "$master_browser".\n) ;
	exit $ERRORS{CRITICAL} ;
}

if ( my @missing = &simple_diff(\@clean_app_list, \@warn_pub_apps) ) {
	print qq(Warning. "@missing" not found in list of published applications), 
		  qq(" $clean_app_list" from master browser "$master_browser".\n) ;
	exit $ERRORS{WARNING} ;
}

my @x = (@crit_pub_apps, @warn_pub_apps) ;
my $blah = ( scalar(@x) == 1
		? 'the published application "'  . join(',', @x) . '" is available'
		: 'the published applications "' . join(',', @x) . '" are available' ) ;
 
print qq(Ok. Citrix master browser "$master_browser" reported that $blah.\n) ;
exit $ERRORS{OK} ;

										# sleep $Timeout;
										# because otherwise we can get responses from
										# the WRONG servers. DOH
close $Udp;


sub print_usage () {
	print "Usage: $PROGNAME (-B <broadcast_address>| -C <citrix_server>..) -W <pub_app1,pub_app2..> -P <pub_app1,pub_app2,>\n";
}

sub print_help () {
	print_revision($PROGNAME,'$Revision: 1098 $ ');
	print "Copyright (c) 2002 Ed Rolison/Tom De Blende/S Hopcroft

Perl Check Citrix plugin for Nagios.

Returns OK if the Citrix master browser returns  a 'published application' list that contain names specified by the -W or -P options

The plugin works by
  If the -B option is specified, sending a broadcast helo to find the address of the Citrix master browser in the specified subnet.
    return critical if there is no reply;
  Else if the -C option is specified 
    send a direct helo to the specified server until there is a response (containing the address of the Citrix master browser)

  Query the master browser (using a 'broadcast published applications query ' if -B) and compare the published applications returned
    to those specified by -W and -P options

  return Critical if the published applications specified by -P is not a subset of the query responses; 
  return Warning  if the published applications specified by -W is not a subset of the query responses; 
  return OK

";
	print_usage();
	print '
-B, --broadcast_address=STRING
   The broadcast address that should contain Citrix master browser. This option takes precedence over -C.
-C, --citrix_server:STRING
   Optional __name(s)__ of Citrix servers that could be the master browser (used when broadcast not possible).
-L, --long_list
   Set this if you have heaps of published applications (ie more than will fit in _one_ UDP packet)
-P, --crit_published_app=STRING
   Optional comma separated list of published application that must be in the response from the master browser.
   Check returns critical otherwise.
-T, --packet-timeout:INTEGER
   Time to wait for UDP packets (default 1 sec).
-W, --warn_published_app=STRING
   Optional comma separated list of published application that should be in the response from the master browser.
   Check returns warning otherwise.
-v, --verbose
   Debugging output.
-h, --help
   This stuff.

';
   	support();
}

sub version () {
	print_revision($PROGNAME,'$Revision: 1098 $ ');
	exit $ERRORS{'OK'};
}

sub help () {
	print_help();
	exit $ERRORS{'OK'};
}


sub simple_diff {

my ( $a_list, $b_list) = @_ ;

	# simple set difference 'Recipe 4.7 Perl Cookbook', Christiansen and Torkington

	my (%seen, @missing) ;

	@seen{@$a_list} = () ;

	foreach my $item (@$b_list) {
		push @missing, $item
			unless exists $seen{$item} ;
	}

	@missing ;
}




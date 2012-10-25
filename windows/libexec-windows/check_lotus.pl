#!/usr/bin/perl -w

# $Id: check_lotus.pl 1096 2005-01-25 09:04:26Z stanleyhopcroft $

# Revision 1.1  2005/01/25 09:04:26  stanleyhopcroft
# New plugin to check responsiveness of Louts Notes (v5 at least) servers
#
# Revision 1.10  2005-01-25 15:44:07+11  anwsmh
# 1 use packet_utils instead of hard coding subroutines (pdump and tethereal)
# 2 redo indentation using tabs (set at 4 spaces)
#

use strict ;

use IO::Socket;
use Getopt::Long ;

my ($timeout, $debug, $lotus_host, $server, $indiv_dn, $packet_debug) ;

use lib qw(/usr/local/nagios/libexec) ;
use utils qw($TIMEOUT %ERRORS &print_revision &support &usage) ;
use packet_utils qw(pdump &tethereal) ;

my $PROGNAME = 'check_lotus_notes' ;

sub print_help ();
sub print_usage ();
sub help ();
sub version ();

my $TEST_COUNT		= 2 ;
										# Number of Lotus client hellos sent without reply 
my $BUFFER_SIZE		= 1500 ;
										# buffer size used for 'recv' calls.
my $LOTUS_PORT		= 1352 ;

Getopt::Long::Configure('no_ignore_case');
GetOptions
        ("V|version"     => \&version,
         "h|help"        => \&help,
         "v|debug"       => \$debug,
         "vv|i_packet_debug"       => \$packet_debug,
         "H|lotus_host=s"=> \$lotus_host,
         # "I|indivual_dn:s" => \$indiv_dn,
         "S|server:s"    => \$server,
         "T|t_timeout:i" => \$timeout,
) ;

usage("You must provide the DNS name or IP (v4) address of the Lotus server to be checked.\n")
	unless $lotus_host and (
	     $lotus_host =~ m#^\d+\.\d+\.\d+\.\d+$# or
	     $lotus_host =~ m#^[\w\._-]+$#
	) ;

$server  ||= $lotus_host
	if $lotus_host =~ m#^[\w-]+$# ;

usage("You must provide a server option unless the lotus_host option looks like an unqualified host name.\n")
	unless $server ;

$timeout		||= $TIMEOUT ;
$debug			= 1 
	if $packet_debug ;

my $server_dn	= "CN=\U$server" . '(?:/\w+=[\w -]+)*' ;

										# Definitions of query strings. Change at your own risk :)
										# This info was gathered with tcpdump while using a Lotus Notes 5 client,
										# so I'm not sure of what each value is.

my $lotus_client_hello = &tethereal(<<'End_of_Tethereal_trace', '82') ;
0030  ff ff dc c5 00 00 82 00 00 00 77 00 00 00 02 00   ..........w.....
0040  00 40 02 0f 00 07 00 39 05 9e 45 54 ad ad 03 00   .@.....9..ET....
0050  00 00 00 02 00 2f 00 00 00 00 00 00 00 00 00 40   ...../.........@
0060  1f a0 af 19 d8 92 da 37 78 c9 ce 60 5e 35 b8 f7   .......7x..`^5..
0070  4e 05 00 10 00 0d 00 00 00 00 00 00 00 00 00 00   N...............
0080  00 00 00 00 00 02 00 08 00 9c dc 22 00 7c 6f 25   ...........".|o%
0090  4a 08 00 10 00 00 00 00 00 00 00 00 00 00 00 00   J...............
00a0  00 00 00 00 00 04 00 10 00 ba ac 8c 49 67 ee a1   ............Ig..
00b0  22 6f 63 bb 04 b4 75 0b 8f 00                     "oc...u...
End_of_Tethereal_trace

										# XXXX
										# Notes 5 accepts this
										# _wrongly_ encoded DN
										# but in general the 
										# server will reset
										# the connection if
										# it receives malformed
										# packets.

my $lotus_client_m1 = &tethereal(<<'End_of_Tethereal_trace', 'de') ;
0000  de 00 00 00 d4 00 00 00 13 00 00 40 01 00 9e 45  ...........@...E
0010  54 ad ad 03 00 00 00 00 02 00 29 13 23 00 b9 68  T.........).#..h
0020  25 00 9f 87 27 00 8f f4 25 00 00 00 88 00 24 00  %...'...%.....$.
0030  28 00 00 00 42 56 04 00 31 2e 30 00 42 43 01 00  (...BV..1.0.BC..
0040  03 42 41 01 00 30 42 4c 02 00 76 02 4e 4e 50 00  .BA..0BL..v.NNP.
0050  cf ee 9d 19 99 ca e0 bf 97 d3 59 a1 c5 78 16 82  ..........Y..x..
0060  76 09 8c 2c 96 ae 5a c1 15 bd 4e e9 b7 0f a9 d4  v..,..Z...N.....
0070  5a 03 d9 0d bc e4 7d 4f e0 f2 79 89 cf cd 23 19  Z.....}O..y...#.
0080  40 55 98 81 98 be d9 17 8d 69 8e 09 de c8 e8 92  @U.......i......
0090  24 86 6f 5a 09 81 1f 71 be 29 b7 47 78 8c 2e 00  $.oZ...q.).Gx...
00a0  45 4e 04 00 95 63 00 00 4d 41 08 00 64 a1 b4 b3  EN...c..MA..d...
00b0  a1 01 45 c2 80 00 50 55 52 53 41 46 22 00 43 4e  ..E...PURSAF".CN
00c0  3d 4d 72 20 46 6f 6f 2f 4f 55 3d 42 61 72 20 68  =Mr Foo/OU=Bar h
00d0  6f 74 65 6c 2f 4f 3d 42 61 7a 20 4a 75 6e 63 74  otel/O=Baz Junct
00e0  69 6f 6e                                         ion
End_of_Tethereal_trace

my $buff = '';

my $valid_resp_cr = sub {
	my ($resp, $dn, $err_ind_sr) = @_ ;
	if ( $resp =~ /($dn)/ ) {
		return $1 
	} else {
	($$err_ind_sr) = $resp =~ m#(CN=[\w -]+(?:/\w+=[\w -]+)*)# ;
	return 0 ;
	}
} ;

my @send = (
	{ Msg => 'Helo',	Send => $lotus_client_hello,	Ok => $valid_resp_cr },
	{ Msg => 'm1',		Send => $lotus_client_m1,		Ok => $valid_resp_cr },
) ;

my $tcp ;

eval {

	$tcp = IO::Socket::INET->new(Proto => 'tcp', PeerAddr => $lotus_host, PeerPort => $LOTUS_PORT, Timeout => $timeout)
										# Some versions (eg 1.1603) croak on a connect failure ..
} ;

&outahere("Connect to $lotus_host:$LOTUS_PORT failed:", $@)
  if $@ || ! defined($tcp) ;

my $found = '' ;

foreach (@send) {

	print STDERR "Sending Lotus client $_->{Msg} to $lotus_host.\n"
		if $debug ;

	&pdump($_->{Send})
		if $packet_debug ;

	eval {

		local $SIG{"ALRM"} = sub { die 'Alarm clock restart' } ;

		alarm($timeout) ;

		$tcp->send($_->{Send}, 0) ||
			&outahere("Send to $lotus_host failed: $!") ;

		defined( $tcp->recv($buff, $BUFFER_SIZE, 0 ) )  ||
			&outahere("Recv from $lotus_host failed: $!")

	} ;

	alarm(0) ;

	&outahere('Unexpected exception raised by eval:', $@)
		if $@ and $@ !~ /Alarm clock restart/ ;

	&outahere("Timeout after $timeout secs - no response from $lotus_host")
		if  $@ and $@ =~ /Alarm clock restart/ ;

	&outahere("Lotus server $lotus_host reset connection - client protocol (malformed packet sent) error", $@)
		if  $@ and $@ =~ /reset/ ;

	&outahere("Empty recv buff after sending client $_->{Msg} and waiting $timeout secs. NB _no_ timeout exception.")
		unless $buff ;

	&pdump($buff)
		if $packet_debug ;

	my $err = '' ;

	&outahere(qq(Response from $lotus_host failed to match CN=$server/.. got "$err") ) 
		unless $found = $_->{Ok}->($buff, $server_dn, \$err) ;

	print STDERR "Received Ok reply from $lotus_host - found DN $found in response.\n"
		if $debug ;

}

close $tcp;

print "Ok. Lotus server $lotus_host responded with $found after ", scalar @send, " packet dialogue.\n" ;
exit $ERRORS{OK} ;

=begin comment

Normal response from Lotus Notes 5 server 

0000  74 00 00 00 69 00 00 00 03 00 00 40 02 0f 00 05  t...i......@....
0010  00 3d 05 60 f0 3a 38 03 03 00 00 00 00 02 00 2f  .=.`.:8......../
0020  00 26 00 00 00 00 00 00 00 40 1f 3d 73 76 0e 57  .&.......@.=sv.W
0030  e0 d7 67 cd a3 50 10 e0 99 24 b4 43 4e 3d 43 42  ..g..P...$.CN=CB
0040  52 4e 4f 54 45 53 30 31 2f 4f 55 3d 53 45 52 56  RNOTES01/OU=SERV
0050  45 52 53 2f 4f 3d 49 50 41 75 73 74 72 61 6c 69  ERS/O=IPAustrali
0060  61 05 00 10 00 09 00 00 00 00 00 00 00 00 00 00  a...............
0070  00 00 00 00 00 00   

=end comment

=cut

sub outahere {
	print "Failed. @_.\n" ;
	exit $ERRORS{CRITICAL} ;
}

sub print_usage () {
	print "Usage: $PROGNAME -H <lotus_host (name _or_ address)>..) [-S <lotus_server name> -T <timeout> -v ]\n";
}

sub print_help () {
	print_revision($PROGNAME,'$Revision: 1096 $ ');
	print "Copyright (c) 2004 Ed Rolison/S Hopcroft

Perl Check Lotus Notes plugin for Nagios.

Returns OK if the named server responds with its name.

";
	print_usage();
	print '
-H, --lotus_host:STRING
    Name or IP Address of Lotus server to be checked.
-I, --individual_dn:NOT IMPLEMENTED
    String of form CN=\w+(?:/OU=\w+)?/O=\w+ 
-S, --server:STRING
    Alpha numeric string specifying the Lotus server name (the CN by which the server is known by
    in the Domino directory). Defaults to host name if the host name does not look like an IP address.
-T, --packet-timeout:INTEGER
   Time to wait for TCP dialogue to complete = send + rcv times (default Nagios timeout [$TIMEOUT sec]).
-v, --debug
   Debugging output.
-vv, --packet_debug
   Packet dump. Please post to Nag users in the event of trouble with this plugin.
-h, --help
   This stuff.

';
	support();
}

sub version () {
	print_revision($PROGNAME,'$Revision: 1096 $ ');
	exit $ERRORS{'OK'};
}

sub help () {
	print_help();
	exit $ERRORS{'OK'};
}


#!/usr/bin/perl -w

# $Id: check_ica_program_neigbourhood.pl 1097 2005-01-25 09:05:53Z stanleyhopcroft $

# Revision 1.1  2005/01/25 09:05:53  stanleyhopcroft
# New plugin to check Citrix Metaframe XP "Program Neighbourhood"
#
# Revision 1.1  2005-01-25 16:50:30+11  anwsmh
# Initial revision
#

use strict ;

use Getopt::Long;

use utils qw($TIMEOUT %ERRORS &print_revision &support);
use LWP 5.65 ;
use XML::Parser ;

my $PROGNAME = 'check_program_neigbourhood' ;
my ($debug, $xml_debug, $pn_server, $pub_apps, $app_servers, $server_farm, $usage) ;

Getopt::Long::Configure('bundling', 'no_ignore_case') ;
GetOptions
        ("V|version"     => \&version,
        "A|published_app:s"        => \$pub_apps,
        "h|help"         => \&help,
        'usage|?'        => \&usage,
        "F|server_farm=s"  => \$server_farm,
        "P|pn_server=s"  => \$pn_server,
        "S|app_server=s" => \$app_servers,
        "v|verbose"        => \$debug,
        "x|xml_debug"    => \$xml_debug,
) ;

$pn_server		|| do  {
	print "Name or IP Address of _one_ Program Neighbourhood server is required.\n" ;
	&print_usage ;
	exit $ERRORS{UNKNOWN} ;
} ;

$pub_apps		||= 'Word 2003' ;
$pub_apps =~ s/["']//g ;
my @pub_apps = split /,\s*/, $pub_apps ;

my @app_servers = split /,\s*/, $app_servers ;

@app_servers		|| do  {
	print "IP Address of _each_ Application server in the Metaframe Citrix XP server farm is required.\n" ;
	&print_usage ;
	exit $ERRORS{UNKNOWN} ;
} ;

my @non_ip_addresses = grep ! /\d+\.\d+\.\d+\.\d+/, @app_servers ;

scalar(@non_ip_addresses) && do { 
	print qq(Application servers must be specified by IP Address (not name): "@non_ip_addresses".\n) ;
	&print_usage ;
	exit $ERRORS{UNKNOWN} ;
} ;

$server_farm		|| do {
	print "Name of Citrix Metaframe XP server farm is required.\n" ;
	&print_usage ;
	exit $ERRORS{UNKNOWN} ;
} ;

my %xml_tag = () ;
my @tag_stack = () ;

my $xml_p = new XML::Parser(Handlers => {Start => \&handle_start,
					 End   => sub { pop @tag_stack },
					 Char  => \&handle_char}) ;

# values required by Metaframe XP that don't appear to matter too much

my $client_host		= 'Nagios server (http://www.Nagios.ORG)' ;
my $user_name		= 'nagios' ;
my $domain			= 'Nagios_Uber_Alles' ;

# end values  required by Metaframe XP

my $nilpotent_req	= <<'EOR' ;
<?xml version="1.0" encoding="ISO-8859-1"?>
<!DOCTYPE NFuseProtocol SYSTEM "NFuse.dtd"><NFuseProtocol version="1.1">
  <RequestProtocolInfo>
    <ServerAddress addresstype="dns-port" />
  </RequestProtocolInfo>
</NFuseProtocol>
EOR

my $server_farm_req	= <<'EOR' ;
<?xml version="1.0" encoding="ISO-8859-1"?>
<!DOCTYPE NFuseProtocol SYSTEM "NFuse.dtd">
<NFuseProtocol version="1.1">
  <RequestServerFarmData>
    <Nil />
  </RequestServerFarmData>
</NFuseProtocol>
EOR

my $spec_server_farm_req = <<EOR ;
<?xml version="1.0" encoding="ISO-8859-1"?>
<!DOCTYPE NFuseProtocol SYSTEM "NFuse.dtd">
<NFuseProtocol version="1.1">
  <RequestAddress>
    <Name>
      <UnspecifiedName>$server_farm*</UnspecifiedName>
    </Name>
    <ClientName>$client_host</ClientName>
    <ClientAddress addresstype="dns-port" />
    <ServerAddress addresstype="dns-port" />
    <Flags />
    <Credentials>
      <UserName>$user_name</UserName>
      <Domain>$domain</Domain>
    </Credentials>
  </RequestAddress>
</NFuseProtocol>
EOR

my $app_req		= <<EOR ;
<?xml version="1.0" encoding="ISO-8859-1"?>
<!DOCTYPE NFuseProtocol SYSTEM "NFuse.dtd">
<NFuseProtocol version="1.1">
  <RequestAddress>
    <Name>
      <UnspecifiedName>PUBLISHED_APP_ENCODED</UnspecifiedName>
    </Name>
    <ClientName>Nagios_Service_Check</ClientName>
    <ClientAddress addresstype="dns-port"/>
    <ServerAddress addresstype="dns-port" />
    <Flags />
    <Credentials>
      <UserName>$PROGNAME</UserName>
      <Domain>$domain</Domain>
    </Credentials>
  </RequestAddress>
</NFuseProtocol>
EOR

my $ua = LWP::UserAgent->new ;
my $req = HTTP::Request->new('POST', "http://$pn_server/scripts/WPnBr.dll") ;
   $req->content_type('text/xml') ;

my $svr ;

my @pubapp_encoded = map { my $x = $_ ; $x =~ s/(\W)/'&#' . ord($1) . ';'/eg; $x } @pub_apps ;

my $error_tag_cr = sub { ! exists($xml_tag{ErrorId}) } ;

my @app_reqs = (
	# { Content => url,				Ok => ok_condition,				Seq => \d+ }

	{ Content => $nilpotent_req,	Ok => $error_tag_cr,			Seq => 0 }, 
	{ Content => $server_farm_req,	Ok => sub {
							! exists($xml_tag{ErrorId})			&&
							exists( $xml_tag{ServerFarmName})	&&
							defined($xml_tag{ServerFarmName})	&&
							$xml_tag{ServerFarmName} eq  $server_farm
									},								Seq => 2 },
	{ Content => $nilpotent_req,	Ok => $error_tag_cr,			Seq => 4 },
	{ Content => $spec_server_farm_req,	Ok => sub {
							! exists($xml_tag{ErrorId})			&&
							exists( $xml_tag{ServerAddress})	&&
							defined($xml_tag{ServerAddress})	&&
							$xml_tag{ServerAddress} =~ /\d+\.\d+\.\d+\.\d+:\d+/
									},								Seq => 6 },
	{ Content => $nilpotent_req,	Ok => $error_tag_cr,			Seq => 8 },
	{ Content => $app_req,			Ok => sub {
							! exists($xml_tag{ErrorId})			&&
							exists( $xml_tag{ServerAddress})	&&
							defined($xml_tag{ServerAddress})	&&
							(($svr) = split(/:/, $xml_tag{ServerAddress})) &&
							defined($svr)						&&
							scalar(grep $_ eq $svr, @app_servers)
									},								Seq => 10 }
) ;

my $app_location ;

foreach my $pub_app (@pub_apps) {

	my $pubapp_enc = shift @pubapp_encoded ;
	my $app_req_tmp = $app_reqs[5]{Content} ;
	$app_reqs[5]{Content} =~ s/PUBLISHED_APP_ENCODED/$pubapp_enc/ ;

	foreach (@app_reqs) {

		$req->content($_->{Content}) ;

		$debug			&& print STDERR "App: $pub_app Seq: $_->{Seq}\n", $req->as_string, "\n" ;

		my $resp = $ua->request($req) ;

		$debug			&& print STDERR "App: $pub_app Seq: ", $_->{Seq} + 1, "\n", $resp->as_string, "\n" ;

		$resp->is_error	&& do {
			my $err = $resp->as_string ;
			$err =~ s/\n//g ;
			&outahere(qq(Failed. HTTP error finding $pub_app at seq $_->{Seq}: "$err")) ;
        } ;
		my $xml = $resp->content ;

		my $xml_disp ;
		   ($xml_disp = $xml) =~ s/\n//g ;
		   $xml_disp =~ s/ \s+/ /g ;

		&outahere($resp->as_string)
		unless $xml ;

		my ($xml_ok, $whine) = &valid_xml($xml_p, $xml) ;

		$xml_ok			|| &outahere(qq(Failed. Bad XML finding $pub_app at eq $_->{Seq} in "$xml_disp".)) ;

		&{$_->{Ok}}		|| &outahere(qq(Failed. \"\&\$_->{Ok}\" false finding $pub_app at seq $_->{Seq} in "$xml_disp".)) ;

							# Ugly but alternative is $_->{Ok}->().
							# eval $_->{Ok} where $_->{Ok} is an
							# expression returning a bool is possible. but
							# sub { } prevent recompilation.

	}

	$app_reqs[5]{Content} = $app_req_tmp ;

	$app_location .= qq("$pub_app" => $svr, ) ;

}

substr($app_location, -2, 2) = '' ; 
print qq(Ok. Citrix XML service located all published apps $app_location.\n) ;
exit $ERRORS{'OK'} ;

sub outahere {
	print "Citrix XML service $_[0]\n" ;
	exit $ERRORS{CRITICAL} ;
}

sub valid_xml {
	my ($p, $input) = @_ ;

	%xml_tag   = () ;
	@tag_stack = () ;

	eval {
	$p->parse($input)
	} ;

	return (0, qq(XML::Parser->parse failed: Bad XML in "$input".!))
		if $@ ;

	if ( $xml_debug ) {
	print STDERR pack('A4 A30 A40', ' ', $_, qq(-> "$xml_tag{$_}")), "\n"
		foreach (keys %xml_tag)
	}

	return (1, 'valid xml')

}


sub handle_start {
	push @tag_stack, $_[1] ;

	$xml_debug		&& print STDERR pack('A8 A30 A40', ' ', 'handle_start - tag', " -> '$_[1]'"), "\n" ;
	$xml_debug 		&& print STDERR pack('A8 A30 A60', ' ', 'handle_start - @tag_stack', " -> (@tag_stack)"), "\n" ;
}

sub handle_char {
	my $text = $_[1] ;

	!($text =~ /\S/  || $text =~ /^[ \t]$/)       && return ;

	$text =~ s/\n//g ;

	my $tag = $tag_stack[-1] ;

	$xml_debug 		&& print STDERR pack('A8 A30 A30', ' ', 'handle_char - tag', " -> '$tag'"), "\n" ;
	$xml_debug 		&& print STDERR pack('A8 A30 A40', ' ', 'handle_char - text', " -> '$text'"), "\n" ;

	$xml_tag{$tag} .= $text ;

}


sub print_help() {

#          1        2         3         4         5         6         7         8
#12345678901234567890123456789012345678901234567890123456789012345678901234567890

	print_revision($PROGNAME,'$Revision: 1097 $ ');

my $help = <<EOHELP ;
Copyright (c) 2004 Karl DeBisschop/S Hopcroft

$PROGNAME -P <pn_server> -S <svr1,svr2,..> -A <app1,app2,..>
          -F <Farm> [-v -x -h -V]

Check the Citrix Metaframe XP service by completing an HTTP dialogue with a Program
Neigbourhood server (pn_server) that returns an ICA server in the named Server farm
hosting the specified applications (an ICA server in a farm which runs some MS app).
EOHELP

	print $help ;
	print "\n";
	print "\n";
	print_usage();
	print "\n";
	support();
}

sub print_usage () {

#          1        2         3         4         5         6         7         8
#12345678901234567890123456789012345678901234567890123456789012345678901234567890

my $usage = <<EOUSAGE ;
$PROGNAME
[-P | --pn_server] The name or address of the Citrix Metaframe XP
                   Program Neigbourhood server (required).
[-A | --pub_apps] The name or names of an application published by the
                  server farm (default 'Word 2003').
[-F | --server_farm] The name of a Citrix Metaframe XP server farm. (required)
[-S | --app_servers] The _IP addresses_ of _all_ of the Farms ICA servers expected
                     to host the published application.
                     Enter as a comma separated string eg 'Srv1, Svr2, ..,Srvn'.
                     Since the PN servers round-robin the app servers to the clients,
                     _all_ the server farm addresses must be specified or the check
                     will fail (required).
[-v | --verbose]
[-h | --help]
[-x | --xml_debug]
[-V | --version]
EOUSAGE

	print $usage ;

}

sub usage {
	&print_usage ;
	exit $ERRORS{'OK'} ;
}

sub version () {
	print_revision($PROGNAME,'$Revision: 1097 $ ');
	exit $ERRORS{'OK'};
}

sub help () {
	print_help();
	exit $ERRORS{'OK'};
}

=begin comment

This is the set of requests and responses transmitted between a Citrix Metaframe XP Program Neigbourhood (PN) client and a PN server.

This dialogue was captured by and reconstructed from tcpdump.

Citrix are not well known for documenting their protocols although the DTD may be informative. Note that the pair(s) 0 and 1, 4 and 5, ...
do not appear to do anything.

req 0
POST /scripts/WPnBr.dll HTTP/1.1
Content-type: text/xml
Host: 10.1.2.2:80
Content-Length: 220
Connection: Keep-Alive


<?xml version="1.0" encoding="ISO-8859-1"?>
<!DOCTYPE NFuseProtocol SYSTEM "NFuse.dtd">
<NFuseProtocol version="1.1"><RequestProtocolInfo><ServerAddress addresstype="dns-port" /></RequestProtocolInfo></NFuseProtocol>

HTTP/1.1 100 Continue
Server: Citrix Web PN Server
Date: Thu, 30 Sep 2004 00:12:40 GMT


resp 1
HTTP/1.1 200 OK
Server: Citrix Web PN Server
Date: Thu, 30 Sep 2004 00:12:40 GMT
Content-type: text/xml
Content-length: 253


<?xml version="1.0" encoding="ISO-8859-1" ?>
<!DOCTYPE NFuseProtocol SYSTEM "NFuse.dtd">
<NFuseProtocol version="1.1">
    <ResponseProtocolInfo>
      <ServerAddress addresstype="no-change"></ServerAddress>
    </ResponseProtocolInfo>
</NFuseProtocol>

req 2
POST /scripts/WPnBr.dll HTTP/1.1
Content-type: text/xml
Host: 10.1.2.2:80
Content-Length: 191
Connection: Keep-Alive


<?xml version="1.0" encoding="ISO-8859-1"?>
<!DOCTYPE NFuseProtocol SYSTEM "NFuse.dtd">
<NFuseProtocol version="1.1"><RequestServerFarmData><Nil /></RequestServerFarmData></NFuseProtocol>

HTTP/1.1 100 Continue
Server: Citrix Web PN Server
Date: Thu, 30 Sep 2004 00:12:40 GMT


resp 3
HTTP/1.1 200 OK
Server: Citrix Web PN Server
Date: Thu, 30 Sep 2004 00:12:40 GMT
Content-type: text/xml
Content-length: 293


<?xml version="1.0" encoding="ISO-8859-1" ?>
<!DOCTYPE NFuseProtocol SYSTEM "NFuse.dtd">
<NFuseProtocol version="1.1">
    <ResponseServerFarmData>
      <ServerFarmData>
        <ServerFarmName>FOOFARM01</ServerFarmName>
      </ServerFarmData>
    </ResponseServerFarmData>
</NFuseProtocol>

req 4
POST /scripts/WPnBr.dll HTTP/1.1
Content-type: text/xml
Host: 10.1.2.2:80
Content-Length: 220
Connection: Keep-Alive


<?xml version="1.0" encoding="ISO-8859-1"?>
<!DOCTYPE NFuseProtocol SYSTEM "NFuse.dtd">
<NFuseProtocol version="1.1"><RequestProtocolInfo><ServerAddress addresstype="dns-port" /></RequestProtocolInfo></NFuseProtocol>

HTTP/1.1 100 Continue
Server: Citrix Web PN Server
Date: Thu, 30 Sep 2004 00:12:55 GMT


resp 5
HTTP/1.1 200 OK
Server: Citrix Web PN Server
Date: Thu, 30 Sep 2004 00:12:55 GMT
Content-type: text/xml
Content-length: 253


<?xml version="1.0" encoding="ISO-8859-1" ?>
<!DOCTYPE NFuseProtocol SYSTEM "NFuse.dtd">
<NFuseProtocol version="1.1">
    <ResponseProtocolInfo>
      <ServerAddress addresstype="no-change"></ServerAddress>
    </ResponseProtocolInfo>
</NFuseProtocol>

req 6
POST /scripts/WPnBr.dll HTTP/1.1
Content-type: text/xml
Host: 10.1.2.2:80
Content-Length: 442
Connection: Keep-Alive


<?xml version="1.0" encoding="ISO-8859-1"?>
<!DOCTYPE NFuseProtocol SYSTEM "NFuse.dtd">
<NFuseProtocol version="1.1">
<RequestAddress><Name>i
  <UnspecifiedName>FOOFARM01*</UnspecifiedName>
  </Name><ClientName>WS09535</ClientName>
  <ClientAddress addresstype="dns-port" />
  <ServerAddress addresstype="dns-port" />
  <Flags />
  <Credentials>
    <UserName>foo-user</UserName>
    <Domain>some-domain</Domain>
  </Credentials>
</RequestAddress></NFuseProtocol>

HTTP/1.1 100 Continue
Server: Citrix Web PN Server
Date: Thu, 30 Sep 2004 00:12:56 GMT


resp 7
HTTP/1.1 200 OK
Server: Citrix Web PN Server
Date: Thu, 30 Sep 2004 00:12:56 GMT
Content-type: text/xml
Content-length: 507


<?xml version="1.0" encoding="ISO-8859-1" ?>
<!DOCTYPE NFuseProtocol SYSTEM "NFuse.dtd">
<NFuseProtocol version="1.1">
    <ResponseAddress>
      <ServerAddress addresstype="dot-port">10.1.2.2:1494</ServerAddress>
      <ServerType>win32</ServerType>
      <ConnectionType>tcp</ConnectionType>
      <ClientType>ica30</ClientType>
      <TicketTag>10.1.2.2</TicketTag>
      <SSLRelayAddress addresstype="dns-port">ica_svr01.some.domain:443</SSLRelayAddress>
    </ResponseAddress>
</NFuseProtocol>

req 8
POST /scripts/WPnBr.dll HTTP/1.1
Content-type: text/xml
Host: 10.1.2.2:80
Content-Length: 220
Connection: Keep-Alive


<?xml version="1.0" encoding="ISO-8859-1"?>
<!DOCTYPE NFuseProtocol SYSTEM "NFuse.dtd">
<NFuseProtocol version="1.1"><RequestProtocolInfo><ServerAddress addresstype="dns-port" /></RequestProtocolInfo></NFuseProtocol>

HTTP/1.1 100 Continue
Server: Citrix Web PN Server
Date: Thu, 30 Sep 2004 00:13:29 GMT


resp 9
HTTP/1.1 200 OK
Server: Citrix Web PN Server
Date: Thu, 30 Sep 2004 00:13:29 GMT
Content-type: text/xml
Content-length: 253


<?xml version="1.0" encoding="ISO-8859-1" ?>
<!DOCTYPE NFuseProtocol SYSTEM "NFuse.dtd">
<NFuseProtocol version="1.1">
    <ResponseProtocolInfo>
      <ServerAddress addresstype="no-change"></ServerAddress>
    </ResponseProtocolInfo>
</NFuseProtocol>

req 10
POST /scripts/WPnBr.dll HTTP/1.1
Content-type: text/xml
Host: 10.1.2.2:80
Content-Length: 446
Connection: Keep-Alive


<?xml version="1.0" encoding="ISO-8859-1"?>
<!DOCTYPE NFuseProtocol SYSTEM "NFuse.dtd">
<NFuseProtocol version="1.1">
<RequestAddress>i
  <Name>
    <UnspecifiedName>EXCEL#32;2003</UnspecifiedName>
  </Name>
  <ClientName>WS09535</ClientName>
  <ClientAddress addresstype="dns-port" />
  <ServerAddress addresstype="dns-port" />
  <Flags />
    <Credentials><UserName>foo-user</UserName>
      <Domain>some-domain</Domain>
    </Credentials>
</RequestAddress>i
</NFuseProtocol>

HTTP/1.1 100 Continue
Server: Citrix Web PN Server
Date: Thu, 30 Sep 2004 00:13:29 GMT


resp 11
HTTP/1.1 200 OK
Server: Citrix Web PN Server
Date: Thu, 30 Sep 2004 00:13:29 GMT
Content-type: text/xml
Content-length: 509


<?xml version="1.0" encoding="ISO-8859-1" ?>
<!DOCTYPE NFuseProtocol SYSTEM "NFuse.dtd">
<NFuseProtocol version="1.1">
    <ResponseAddress>
      <ServerAddress addresstype="dot-port">10.1.2.14:1494</ServerAddress>
      <ServerType>win32</ServerType>
      <ConnectionType>tcp</ConnectionType>
      <ClientType>ica30</ClientType>
      <TicketTag>10.1.2.14</TicketTag>
      <SSLRelayAddress addresstype="dns-port">ica_svr02.some.domain:443</SSLRelayAddress>
    </ResponseAddress>
</NFuseProtocol>

** One sees this XML on an error (there may well be other error XML also, but I haven't seen it) **

<?xml version="1.0" encoding="ISO-8859-1" ?>
<!DOCTYPE NFuseProtocol SYSTEM "NFuse.dtd">
<NFuseProtocol version="1.1">
    <ResponseAddress>
      <ErrorId>unspecified</ErrorId>
      <BrowserError>0x0000000E</BrowserError>
    </ResponseAddress>
</NFuseProtocol>


=end comment

=cut


# You never know when you may be embedded ...



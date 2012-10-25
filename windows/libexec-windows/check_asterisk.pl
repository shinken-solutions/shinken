#!/usr/bin/perl -w

use strict;
use IO::Socket;
use Getopt::Long;
$|=1;

my (
	$host, $username, $password, $verbose, $help, $command, $mode,
	$ipaddr, $respaddr, $sendto, $msg, $recvfrom,
	$version, $response, $message, $line,
	$sock, $port, $reply,
	$warning, $critical, 
	%warnval, %critval,
	%channels,
	$runmode,
	$key,
	$s,
);
my $stop = 0;
my $mgr_port = 5038;
my $iax_port = 4569;
my $exitcode = 0;
my $cause = "";

my $iax_answer = 0;
my $iax_maxlen = 1024; 
my $iax_timeout = 5; 
my $iax_src_call = "8000"; #8000 most siginificant bit is IAX packet type full ... required for a poke etc... 
my $iax_dst_call = "0000"; 
my $iax_timestamp = "00000000"; 
my $iax_outbound_seq = "00"; 
my $iax_inbound_seq = "00"; 
my $iax_type = "06"; #IAX_Control 

sub ok {
	$s = shift;
	$s =~ s/[\r\n]//g;
	print "OK: $s\n";
	exit(0);
}

sub warning {
	$s = shift;
	$s =~ s/[\r\n]//g;
	print "WARNING: $s\n";
	exit(1);
}

sub error {
	$s = shift;
	$s =~ s/[\r\n]//g;
	print "ERROR: $s\n";
	exit(2);
}

sub unknown {
	$s = shift;
	$s =~ s/[\r\n]//g;
	print "UNKNOWN: $s\n";
	exit(3);
}

sub syntax {
	$s = shift;
	unless ($s =~ m/Help:/) {
		$s = "Error: (".$s.")" or $s = 'Unknown';
	}
	print "$s\n" unless ($help);
	print "Syntax: $0 -m mgr -h <host> -u <username> -p <password> [-cwv]\n";
	print "Syntax: $0 -m iax -h <host> [-v]\n";
	print "* --host -h         Host\n";
	print "* --mode -m         Mode - eithr 'mgr' or 'iax'\n";
	print "  --username -u     Username\n";
	print "  --password -p     Password\n";
	print "  --port -P n       Port (if not using $mgr_port for manager or $iax_port for IAX)\n";
	print "  --warning xxx=n   Return warning if > n channels of type xxx.\n";
	print "  --critical xxx=n  Return critical if > n channels of type xxx.\n";
	print "  --verbose -v      Verbose\n";
	print "  --help -h         This help\n";
	exit(3);
}

Getopt::Long::Configure('bundling');
GetOptions
	("p=s"        => \$password, "password=s" => \$password,
	 "u=s"        => \$username, "username=s" => \$username,
	 "h=s"        => \$host,     "host=s"     => \$host,
	 "P=i"        => \$port,     "port=i"     => \$port,
	 "H"          => \$help,     "help"       => \$help,
	 "v"          => \$verbose,  "verbose"    => \$verbose,
	 "m=s"        => \$mode,     "mode=s"     => \$mode,
	 "critical=s" => \$critical, "warning=s"  => \$warning);

syntax("Help:") if ($help);
syntax("Missing host") unless (defined($host));
syntax("Missing mode") unless (defined($mode));
if ($mode =~ /^iax$/i) {
	print "Running in IAX mode\n" if ($verbose);
	$runmode = 1;
} elsif ($mode =~ /^mgr$/i) {
	print "Running in Manager mode\n" if ($verbose);
	$runmode = 2;
} else {
	syntax("Unknown mode $mode") 
}

##############################################################################

if ($runmode == 2) {
	$port = $mgr_port;
	syntax("Missing username") unless (defined($username));
	syntax("Missing password") unless (defined($password));
	if (defined($warning)) {
		foreach $s (split(/,/, $warning)) {
			syntax("Warning value given, $s, is invalid")
				unless ($s =~ /^(\w+)=(\d+)$/);
			$warnval{$1} = $2;
			print "Clear to give WARNING after $2 connections on $1\n" if ($verbose);
		}
	}
	if (defined($critical)) {
		foreach $s (split(/,/, $critical)) {
			syntax("Critical value given, $s, is invalid")
				unless ($s =~ /^(\w+)=(\d+)$/);
			$critval{$1} = $2;
			print "Clear to give CRITICAL after $2 connections on $1\n" if ($verbose);
		}
	}

	print "Connecting to $host:$port\n" if ($verbose);
	unless ($sock = IO::Socket::INET->new(PeerAddr => $host, PeerPort => $port, Proto => 'tcp')) {
		print("Could not connect to asterisk server ".$host.":".$port."\n");
		exit(2);
	}
	print "Connected to $host:$port\n" if ($verbose);
	$version = <$sock>;
	print $version if ($verbose);

	print $sock "Action: Login\r\nUsername: $username\r\nSecret: $password\r\nEvents: off\r\n\r\n";
	print "Action: Login\r\nUsername: $username\r\nSecret: $password\r\n\r\n" if ($verbose);
	$response = <$sock>;
	$message = <$sock>;
	$s = <$sock>;
	print $response.$message if ($verbose);
	print $s if ($verbose);

	exit(1) unless ($response =~ m/^Response:\s+(.*)$/i);
	exit(1) unless ($1 =~ m/Success/i);

	print $sock "Action: Status\r\n\r\n";
	print "Action: Status\r\n\r\n" if ($verbose);

	$response = <$sock>;
	$message = <$sock>;
	print $response.$message if ($verbose);

	&unknown("Unknown answer $response (wanted Response: something)") unless ($response =~ m/^Response:\s+(.*)$/i);
	&unknown("$response didn't say Success") unless ($1 =~ m/Success/i);
	&unknown("Unknown answer $response (wanted Message: something)") unless ($message =~ m/^Message:\s+(.*)$/i);
	&unknown("didn't understand message $message") unless ($1 =~ m/Channel status will follow/i);

	$stop=0;
	while (($stop == 0) && ($line = <$sock>)) {
		print "$line" if ($verbose);
		if ($line =~ m/Channel:\s+(\w+)\//) {
			$channels{$1}++;
			print "Found $1 channel\n" if ($verbose);
		}
		if ($line =~ m/Event:\s*StatusComplete/i) {
			$stop++;
		}
	}

# Log out
	print $sock "Action: Logoff\r\n\r\n";

	undef($s);
	foreach $key (keys %channels) {
		$s .= " " . $key . " (" . $channels{$key} . ")";
	}

	foreach $key (keys %critval) {
		print "key = $key\n" if ($verbose);
		if (defined($channels{$key}) && ($channels{$key} > $critval{$key})) {
			$exitcode = 2;
			$cause .= $channels{$key} . " $key channels detected. ";
		}
	}

	if ($exitcode < 2) {
		foreach $key (keys %warnval) {
			print "key = $key\n" if ($verbose);
			if (defined($channels{$key}) && ($channels{$key} > $warnval{$key})) {
				$exitcode = 1;
				$cause .= $channels{$key} . " $key channels detected. ";
			}
		}
	}

	if ($exitcode == 0) {
		print "OK ";
	} elsif ($exitcode == 1) {
		print "WARNING ";
	} elsif ($exitcode == 2) {
		print "CRITICAL ";
	} elsif ($exitcode > 2) {
		print "UNKNOWN ";
	}
	if (defined($s)) {
		$cause .= " Channels:$s";
	} else {
		$cause .= " (idle)";
	}

	print $cause;

	print "\n" if ($verbose);

	exit($exitcode);
} elsif ($runmode == 1) {
	$port = $iax_port;

	socket(PING, PF_INET, SOCK_DGRAM, getprotobyname("udp")); 

	$msg = pack "H24", $iax_src_call . $iax_dst_call . $iax_timestamp .
		$iax_outbound_seq . $iax_inbound_seq . $iax_type . $iax_type;

	$ipaddr = inet_aton($host); 
	$sendto = sockaddr_in($port,$ipaddr); 

	send(PING, $msg, 0, $sendto) == length($msg) or die "cannot send to $host : $port : $!\n"; 

	eval { 
		local $SIG{ALRM} = sub { die("alarm time out"); }; 
		alarm $iax_timeout; 

		while (1) { 
			$recvfrom = recv(PING, $msg, $iax_maxlen, 0) or die "recv: $!"; 
			($port, $ipaddr) = sockaddr_in($recvfrom); 
			$respaddr = inet_ntoa($ipaddr); 
			$iax_answer++;
			# print "Response from $respaddr : $port\n"; 
		} 

	};

	if ($iax_answer) {
		if ($iax_answer == 1) {
			$reply = "reply";
		} else {
			$reply = "replies";
		}
		&ok("Got $iax_answer $reply");
	} else {
		&error("Got no reply");
	}
}


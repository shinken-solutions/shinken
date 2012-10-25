#!/usr/bin/perl -w

# $Id: check_ms_spooler.pl 64 2002-07-16 00:04:42Z stanleyhopcroft $

# Revision 1.1  2002/07/16 00:04:42  stanleyhopcroft
# Primitive and in need of refinement test of MS spooler (with smbclient)
#
# Revision 2.5  2002-02-13 07:36:08+11  anwsmh
# Correct 'apostrophe' disaster.
# Apostrophes in plugin output cause Netsaint notification commands
# ( sh echo 'yada $PLUGINOUTPUT$ ..') to fail, usually mysteriously
# eg notify OK works but notify CRITICAL does not.
# Replace '$var' in print "output" with \"$var\".
#
# Revision 2.4  2001-11-21 21:36:05+11  anwsmh
# Minor corrections
#  . replace 'die' by print .. exit $ERRORS{CRITICAL}
#  . change concluding message to list the queues (sorted) if there are no enqueued docs.
#
# Revision 2.3  2001-11-20 11:00:58+11  anwsmh
# Major corrections.
#  1. to sub AUTOLOAD: coderef parms must be @_ (ie the parm when the new sub is called)
#  2. to processing of queue report (no inspection of $last_line; entire $queue_report is
#     checked for errors)
#  3. cosmetic and debug changes in many places.
#
# Revision 2.2  2001-11-17 23:30:34+11  anwsmh
# After adapting two different queue reports resulting from
# different name resolution methods.
#
# Revision 2.1  2001-11-17 13:21:54+11  anwsmh
# Adapt to Netsaint ('use utils, Getopt::Long, and standard switch processing).
# Fix many peculiarities.
#


use strict ;

use Getopt::Long ;
use utils ;

use vars qw($opt_H $opt_s $opt_W $opt_u $opt_p $opt_w $opt_c $debug);
use vars '$AUTOLOAD' ;
use utils qw($TIMEOUT %ERRORS &print_revision &support &usage);

my $PROGNAME = 'check_ms_spooler' ;

sub print_help ();
sub print_usage ();
sub help ();
sub version ();

delete @ENV{'PATH', 'IFS', 'CDPATH', 'ENV', 'BASH_ENV'};

use constant SMBCLIENT_PATH	=> '/usr/local/samba/bin/smbclient' ;
use constant MAX_QUEUES_TO_CHECK => 20 ;		# So that the check doesn't take longer than $TIMEOUT

use constant SMBCLIENT_SVC	=> sub { return `${\SMBCLIENT_PATH} -L //$_[0] -U $_[1]%$_[2]` } ;
use constant SMBCLIENT_QUEUE	=> sub { return `${\SMBCLIENT_PATH} //$_[0]/$_[1] -U $_[2]%$_[3] -c 'queue; quit' 2>/dev/null` } ;

							# The queue results depend on the name resolution method.

							# Forcing 'wins' or 'bcat' name resolution makes the queue results the
							# same for all spoolers (those that are resolved with WINS have an extra line
							# 'Got a positive name query response from <ip address of WINS> ..)
							# but would fail if there is no WINS and when miscreant spoolers
							# don't respond to broadcasts.

use constant MIN		=> sub { my $min = $_[0] ; foreach (@_) { $min = $_ if $_ <= $min; } return $min ; } ;

$SIG{"ALRM"} = sub { die "Alarm clock restart" } ;

Getopt::Long::Configure('bundling', 'no_ignore_case');
GetOptions
        ("V|version"     => \&version,
         "h|help"        => \&help,
         "d|debug"       => \$debug,
         "p|password=s"  => \$opt_p,
         "u|username=s"  => \$opt_u,
         "H|hostname=s"  => \$opt_H);



($opt_H) || usage("MS Spooler name not specified\n");
my $spooler = $1 if $opt_H =~ m#(\w+)# ;		# MS host names allow __any__ characters (more than \w)
($spooler) || usage("Invalid MS spooler name: $opt_H\n");

($opt_u) || ($opt_u = 'guest');
my $user = $1 if $opt_u =~ m#(\w+)# ;
($user) || usage("Invalid user: $opt_u\n");

($opt_p) || ($opt_p = 'guest');
my $pass = $1 if ($opt_p =~ /(.*)/);
($pass) || usage("Invalid password: $opt_p\n");

my ($printer, $queue, @queues, $ms_spooler_status, @results, %junk) ;
my (@fault_messages, @queue_contents, @services, @prandom_queue_indices) ;
my ($queue_contents, $number_of_queues, $state, $queue_report) ;

$state = "getting service list (${\SMBCLIENT_PATH} -L $spooler -U $user%$pass) from spooler\n" ;

eval {
  alarm($TIMEOUT) ;
  @services = SMBCLIENT_SVC->( $spooler, $user, $pass ) ;
} ;
alarm(0) ;

if ($@ and $@ !~ /Alarm clock restart/) {
  print "Failed. $PROGNAME failed $state. Got \"$@\"\n" ;
  exit $ERRORS{"CRITICAL"} ;
}

if ($@ and $@ =~ /Alarm clock restart/) {
  print "Failed. $PROGNAME timed out $state. Got \"@services\"\n" ;
  exit $ERRORS{"CRITICAL"} ;
}

# tsitc> /usr/local/samba/bin/smbclient //ipaprint1/tt03 -U blah%blah -P -c 'queue; quit'
# Added interface ip=10.0.100.252 bcast=10.255.255.255 nmask=255.0.0.0
# Connection to ipaprint1 failed

# tsitc> /usr/local/samba/bin/smbclient -L sna_spl1 -U blah%blah | & more
# Added interface ip=10.0.100.252 bcast=10.255.255.255 nmask=255.0.0.0
# Got a positive name query response from 10.0.100.29 ( 10.0.6.20 )
# session setup failed: ERRDOS - ERRnoaccess (Access denied.)

if ( grep /Connection to $spooler failed|ERR/, @services ) {
  print "Failed. $PROGNAME failed $state. Got \"@services\"\n" ;
  # print "Failed. Request for services list to $spooler failed. Got \"@services\"\n" ;
  exit $ERRORS{"CRITICAL"} ;
}

# tsitc# /usr/local/samba/bin/smbclient -L ipaprint -U blah%blah
# Added interface ip=10.0.100.252 bcast=10.255.255.255 nmask=255.0.0.0
# Domain=[IPAUSTRALIA] OS=[Windows NT 4.0] Server=[NT LAN Manager 4.0]
# 
#         Sharename      Type      Comment
#         ---------      ----      -------
#         TH02           Printer   TH02
#         ADMIN$         Disk      Remote Admin
#         IPC$           IPC       Remote IPC
#         S431           Printer   S431
#         S402           Printer   S402
#         S401           Printer   S401
#         C$             Disk      Default share
#         BW01           Printer   BW01
#         BW02           Printer   BW02
#         TL11           Printer   TL11
#         TL07           Printer   TL07
#         S225           Printer   Discovery South - 2nd Floor - HP CLJ4500
#         S224           Printer   S224
#         S223           Printer   Discovery South 2nd Floor Trademarks Training
#         S222           Printer   S222
#         S203           Printer   S203
#         S202           Printer   S202

my @printers = map  { my @junk = split; $junk[0] }
	       grep { my @junk = split; defined $junk[1] and $junk[1] eq 'Printer' } @services ;
						# don't check IPC$, ADMIN$ etc.

$ms_spooler_status = 0 ;
$number_of_queues = MIN->(MAX_QUEUES_TO_CHECK, (scalar(@services) >> 3) + 1) ;

$state = "checking queues on $spooler" ;

eval {
						# foreach queues to check
						#   generate a pseudo-random int in 0 .. $#printers
						#   drop it if the index has already been generated ;

  %junk = () ;
  @prandom_queue_indices = grep { ! $junk{$_}++ } 
                           map  { int( rand($#printers) ) } ( 1 .. $number_of_queues ) ;

  @queues = @printers[@prandom_queue_indices] ;

  # @queues = @printers[ map { int( rand($#printers) ) } ( 1 .. $number_of_queues ) ] ;

  alarm($TIMEOUT) ;

  @queue_contents = @fault_messages = () ;

  foreach $printer (sort @queues) {

    # Expect 3 lines from a queue report.
    # If queue is empty, last line is null otherwise
    # it will contain a queue report or an SMB error
    
    # Empty Queue.
    # Added interface ip=10.0.100.252 bcast=10.255.255.255 nmask=255.0.0.0
    # Domain=[IPAUSTRALIA] OS=[Windows NT 4.0] Server=[NT LAN Manager 4.0]

    # Queue command from a spooler with a DNS name.  
    # Added interface ip=10.0.100.252 bcast=10.255.255.255 nmask=255.0.0.0
    # Domain=[IPAUSTRALIA] OS=[Windows NT 4.0] Server=[NT LAN Manager 4.0]
    # 65       16307        Microsoft Word - Servicesweoffer2.doc
    # 68       10410        Microsoft Word - Servicesweoffer.doc
    # 143      24997        Microsoft Word - Miss Samantha Anne Craig.doc
    # 182      15635        Microsoft Word - services we provide.doc
  
    # Error.
    # Added interface ip=10.0.100.252 bcast=10.255.255.255 nmask=255.0.0.0
    # Domain=[IPAUSTRALIA] OS=[Windows NT 4.0] Server=[NT LAN Manager 4.0]
    # tree connect failed: ERRDOS - ERRnosuchshare (You specified an invalid share name)
  
    # Can't connect error.
    # Added interface ip=10.0.100.252 bcast=10.255.255.255 nmask=255.0.0.0
    # Connection to sna_spl2 failed
  
  
    # Empty Queue from a spooler with no DNS name, NetBIOS name resolved by WINS.
    # Added interface ip=10.0.100.252 bcast=10.255.255.255 nmask=255.0.0.0
    # Got a positive name query response from 10.0.100.29 ( 10.0.6.20 )
    # Domain=[SNA_PRINT] OS=[Windows NT 4.0] Server=[NT LAN Manager 4.0]
  
    # There are 3 lines of output from smbclient for those spoolers whose names are
    # resolved by WINS (because those names are NetBIOS and therefore not in DNS);
    # 4 lines for errors or enqueued jobs
  
    print STDERR "${\SMBCLIENT_PATH} //$spooler/$printer -U $user%$pass -c 'queue; quit' ==>\n" if $debug ;
  
    @results = SMBCLIENT_QUEUE->( $spooler, $printer, $user, $pass ) ;

    print STDERR "\"@results\"\n" if $debug ;
    
    # set $ms_spooler_status somehow
  
    chomp( @results ) ;
    $queue_report = queue_report->(@results) ;
    print STDERR '$queue_report for $printer ', "$printer: \"$queue_report\"\n\n" if $debug ;
  
    if ( defined $queue_report and ($queue_report !~ /ERR/ && $queue_report !~ /failed/) ) {
      $ms_spooler_status = 1 ;
      push @queue_contents, "$printer: $queue_report" if $queue_report ;
    } else {
      push @fault_messages, "$printer: $queue_report" ;
    }
  }
  alarm(0) ;
} ;

if ($@ and $@ !~ /Alarm clock restart/) {
  print "Failed. $PROGNAME failed at $state. Got \"$@\"\n" ;
  exit $ERRORS{"CRITCAL"} ;
}

if ($@ and $@ =~ /Alarm clock restart/) {
  my $i ;
  foreach (@queues) { $i++ ; last if $_ eq $printer } 
  print "Failed. Timed out connecting to $printer ($i of $number_of_queues) on //$spooler after $TIMEOUT secs. Got \"@fault_messages\"\n" ;
  exit $ERRORS{"CRITICAL"} ;
}
  
if (! $ms_spooler_status) {
  print "Failed. Couldn't connect to @queues on //$spooler as user $user. Got \"@fault_messages\"\n" ;
  exit $ERRORS{"CRITICAL"} ;
}

$queue_contents = ( @queue_contents != 0 ? join(" ", (@queue_contents == 1 ? "Queue" : "Queues"), @queue_contents) :
				           "All Queues empty" ) ;
  
print "Ok. Connected to ", $queue_contents =~ /empty$/ ? "@{[sort @queues]}" : scalar @queues, " queues on //$spooler. $queue_contents\n" ;
exit $ERRORS{"OK"} ;

sub print_usage () {
	print "Usage: $PROGNAME -H <spooler> -u <user> -p <password>\n";
}

sub print_help () {
	print_revision($PROGNAME,'$Revision: 64 $ ');
	print "Copyright (c) 2001 Karl DeBisschop/S Hopcroft

Perl Check MS Spooler plugin for NetSaint. Display a subset of the queues on an SMB (Samba or MS) print spooler.

";
	print_usage();
	print '
-H, --hostname=STRING
   NetBIOS name of the SMB Print spooler (Either Samba or MS spooler)
-u, --user=STRING
   Username to log in to server. (Default: "guest")
-p, --password=STRING
   Password to log in to server. (Default: "guest")
-d, --debug
   Debugging output.
-h, --help
   This stuff.

';
	support();
}

sub version () {
	print_revision($PROGNAME,'$Revision: 64 $ ');
	exit $ERRORS{'OK'};
}

sub help () {
	print_help();
	exit $ERRORS{'OK'};
}

sub AUTOLOAD {

  my @queue_rep = @_ ;

  # 'Object Oriented Perl', D Conway, p 95

  no strict 'refs' ;

  if ( $AUTOLOAD =~ /.*::queue_report/ ) {

    if ( grep /Got a positive name query response from/, @queue_rep ){
      *{$AUTOLOAD} = sub { return join ' ', splice(@_, 3) } ;
      return join '', splice(@queue_rep, 3) ;
    } else {
      *{$AUTOLOAD} = sub { return join ' ',splice(@_, 2) } ;
      return join '', splice(@queue_rep, 2) ;
    }
  } else {
    die "No such subroutine: $AUTOLOAD" ;
  }
}


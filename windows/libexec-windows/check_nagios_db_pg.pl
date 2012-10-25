#!/usr/bin/perl -w

use strict;
$|++;

use vars qw/$opt_e $opt_c/;

$ENV{"PATH"} = "/usr/bin:/usr/sbin:/bin";

use Getopt::Std;
use DBI;

my $driver = "Pg";

my $CFG_DEF = "/etc/nagios/cgi.cfg";
# this works only in mysql
# my $QUERY = "select *, UNIX_TIMESTAMP(last_update) as ut from programstatus;";
# the following is the same for postgres
my $QUERY = "select *, round(date_part('epoch',last_update)) as ut from programstatus;";
my $EXPIRE_DEF = 5; ## expressed in minutes
my $PROCCNT = 0;

use constant OK => 1;
use constant WARN => 2;

my $STAT = WARN;

sub usage {
        print STDERR "\n";
        print STDERR "$0 -F -e &lt;expire time in minutes&gt; -C &lt;process string&gt;\n";
        print STDERR "\n";
        exit -1;
}

getopt("e:c:");

my $EXPIRE = $opt_e || $EXPIRE_DEF;
my $CFG = $opt_c || $CFG_DEF;

( -f $CFG ) or die "Can't open config file '$CFG': $!\n";

my ($dbhost, $dbport, $dbuser, $dbpass, $dbname);

open(F, "< $CFG");
while ( <F> ) {
        if (/^xsddb_host=(.+)/) { $dbhost = $1; next; };
        if (/^xsddb_port=(.+)/) { $dbport = $1; next; };
        if (/^xsddb_database=(.+)/) { $dbname = $1; next; };
        if (/^xsddb_username=(.+)/) { $dbuser = $1; next; };
        if (/^xsddb_password=(.+)/) { $dbpass = $1; next; };
}
close(F);

#print "($dbhost, $dbport, $dbuser, $dbpass, $dbname)\n";

my $dsn = "DBI:$driver:dbname=$dbname;host=$dbhost;port=$dbport";
my $dbh = DBI->connect($dsn, $dbuser, $dbpass, {'RaiseError' => 1});

my $sth = $dbh->prepare($QUERY);
if (!$sth) { die "Error:" . $dbh->errstr . "\n"; }
$sth->execute;
if (!$sth->execute) { die "Error:" . $sth->errstr . "\n"; }

my %status = ();

my $names = $sth->{'NAME'};
my $numFields = $sth->{'NUM_OF_FIELDS'};
my $ref = $sth->fetchrow_arrayref;
for (my $i = 0;  $i < $numFields;  $i++) {
        $status{"$$names[$i]"} = $$ref[$i];
}

#foreach (keys(%status)) {
#       print "$_: $status{$_}\n";
#}

my $lastupdated = time() - $status{"ut"};
if ( $lastupdated < ($EXPIRE*60) ) { ## convert $EXPIRE to seconds
        $STAT = OK;
}

open(PS, "ps -eaf | grep $status{nagios_pid} | grep -v grep | ");
$PROCCNT = 0;
while(<PS>) {
        $PROCCNT++;
}
close(PS);

if ( $STAT == OK ) {
        print "Nagios OK: located $PROCCNT processes, program status updated $lastupdated seconds ago\n";
}

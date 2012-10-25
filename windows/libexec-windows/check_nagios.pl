#!/usr/bin/perl
# denao - denao@uol.com.br - Systems Engineering
# Universo Online - http://www.uol.com.br 
use DBI;
use Time::Local;

my $t_lambuja = 5;           # (expire_minutes)
my $databasename = "";       # The name of nagios database (i.e.: nagios)
my $table = "programstatus";
my $where = "localhost";     # The machine where the database
my $port = "3306";
my $base = "DBI:mysql:$databasename:$where:$port";
my $user = "";               # the user to connect to the database 
                             # (needs permission to "select at programstatus table only"
my $password = "";           # the password (if any)
my %results;
my @fields = qw( last_update );
my $dbh = DBI->connect($base,$user,$password);
my $fields = join(', ', @fields);
my $query = "SELECT $fields FROM $table";

my $sth = $dbh->prepare($query);
$sth->execute();

@results{@fields} = ();
$sth->bind_columns(map { \$results{$_} } @fields);

$sth->fetch();
$sth->finish();
$dbh->disconnect();

check_update();

sub check_update {
($yea,$mon,$day,$hou,$min,$sec)=($results{last_update}=~/(\d+)\-(\d+)\-(\d+)\s(\d+)\:(\d+)\:(\d+)/);
($sec_now, $min_now, $hou_now, $day_now, $mon_now, $yea_now) = (localtime(time))[0,1,2,3,4,5];
$mon_now+=1; $yea_now+=1900;
$unixdate=timelocal($sec,$min,$hou,$day,$mon,$yea);
$unixdate_now=timelocal($sec_now,$min_now,$hou_now,$day_now,$mon_now,$yea_now);
   if (scalar($unixdate_now - $unixdate) > scalar($t_lambuja * 60)) {
       print "Nagios problem: nagios is down, for at least " . scalar($t_lambuja) . " minutes.\n";
       exit(1);
   } else {
       print "Nagios ok: status data updated " . scalar($unixdate_now - $unixdate) . " seconds ago\n";
       exit(0);
   }
}


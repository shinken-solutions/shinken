#!/usr/bin/perl
#
# Program check_ora_table_space
# Written by: Erwan Arzur (erwan@netvalue.com)
# License: GPL
#
# Last Modified: $Date: 2002-02-28 01:42:51 -0500 (Thu, 28 Feb 2002) $
# Revisiin: $Revision: 2 $
#
# "check_ora_table_space.pl" plugin to check the state of Oracle 
# table spaces. Scarce documentation.
#
# you need DBD-Oracle-1.03.tar.gz and DBI-1.13.tar.gz from CPAN.org as
# well as some Oracle client stuff to use it.
#
# The SQL request comes from www.dbasupport.com
#

use DBI;
$ENV{"ORACLE_HOME"}="/intranet/apps/oracle";

my $host = shift || &usage ("no host specified");
my $sid  = shift || &usage ("no sid specified");
my $port = shift || &usage ("no port specified");
my $dbuser = shift || &usage ("no user specified");
my $dbpass = shift || &usage ("no password specified");
my $tablespace = shift || &usage ("no table space  specified");

my $alertpct = int(shift) || &usage ("no warning state percentage specified");
my $critpct =  int(shift) || &usage ("no critical state percentage specified");

my $dbh = DBI->connect(	"dbi:Oracle:host=$host;port=$port;sid=$sid", $dbuser, $dbpass, { PrintError => 0, AutoCommit => 1, RaiseError => 0 } )
	|| &error ("cannot connect to $dbname: $DBI::errstr\n");

#$sth = $dbh->prepare(q{SELECT tablespace_name, SUM(BYTES)/1024/1024 FreeSpace FROM dba_free_space group by tablespace_name}) 
my $exit_code = -1;
$sth = $dbh->prepare(<<EOF
select a.TABLESPACE_NAME, a.total,nvl(b.used,0) USED, 
nvl((b.used/a.total)*100,0) PCT_USED 
from (select TABLESPACE_NAME, sum(bytes)/(1024*1024) total 
from sys.dba_data_files group by TABLESPACE_NAME) a, 
(select TABLESPACE_NAME,bytes/(1024*1024) used from sys.SM\$TS_USED) b 
where  a.TABLESPACE_NAME='$tablespace' and 
 a.TABLESPACE_NAME=b.TABLESPACE_NAME(+)
EOF
)
	|| &error("Cannot prepare request : $DBI::errstr\n");
$sth->execute 
	|| &error("Cannot execute request : $DBI::errstr\n");

while (($tbname, $total, $used, $pct_used) = $sth->fetchrow)
{
	$pct_used=int($pct_used);
	print STDOUT "size: " . $total . " MB Used:" . int($used) . " MB (" . int($pct_used) . "%)\n";
	#print "table space $answer\n";
	if ($pct_used > $alertpct) {
		if ($pct_used > $critpct) {
			$exit_code = 2
		} else {
			$exit_code = 1;
		}
	} else {
		$exit_code = 0;	
	}
}

$rc = $dbh->disconnect 
	|| &error ("Cannot disconnect from database : $dbh->errstr\n");

exit ($exit_code);

sub usage {
	print "@_\n" if @_;
	print "usage : check_ora_table_space.pl <host> <sid> <port> <user> <passwd> <tablespace> <pctwarn> <pctcrit>\n";
	exit (-1);
}

sub error {
	print "@_\n" if @_;
	exit (2);
}


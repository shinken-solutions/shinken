#!/usr/bin/perl
# $Id: check_oracle_instance.pl 10 2002-04-03 02:58:47Z sghosh $

#  Copyright (c) 2002  Sven Dolderer
#  some pieces of Code adopted from Adam vonNieda's oracletool.pl
#                                      (http://www.oracletool.com)
#
#   You may distribute under the terms of either the GNU General Public
#   License or the Artistic License, as specified in the Perl README file,
#   with the exception that it cannot be placed on a CD-ROM or similar media
#   for commercial distribution without the prior approval of the author.

#   This software is provided without warranty of any kind.

require 5.003;

use strict;
use Getopt::Long;

# We need the DBI and DBD-Oracle Perl modules:
require DBI || die "It appears that the DBI module is not installed! aborting...\n";
require DBD::Oracle || die "It appears that the DBD::Oracle module is not installed! aborting...\n";

use vars qw($VERSION $PROGNAME $logfile $debug $state $dbh $database $username $password $message $sql $cursor $opt_asession $opt_nsession $opt_tablespace $opt_nextents $opt_fextents $opt_aextents $privsok $warn $critical);

'$Revision: 10 $' =~ /^.*(\d+.\d+) \$$/;  # Use The Revision from RCS/CVS
$VERSION = $1;
$0 =~ m!^.*/([^/]+)$!;
$PROGNAME = $1;
#$debug="true";
$logfile = "/tmp/check_oracle_instance.log";
my %ERRORS = (UNKNOWN => -1, OK => 0, WARNING => 1, CRITICAL => 2);

# Read cmdline opts:
Getopt::Long::Configure('bundling', 'no_ignore_case');
GetOptions (
         "V|version"    => \&version,
         "h|help"       => \&usage,
         "u|user=s" => \$username,
         "p|passwd=s" => \$password,
         "c|connect=s" => \$database,
         "a|active-sessions:s"  => \$opt_asession,
         "s|num-sessions:s"  => \$opt_nsession,
         "t|tablespaces:s" => \$opt_tablespace,
         "n|num-extents:s" => \$opt_nextents,
         "f|free-extents:s" => \$opt_fextents,
         "x|allocate-extents" => \$opt_aextents
        );
($database && $username && $password) || die "mandatory parameters missing (try -h)\n";
logit("    \$opt_asession = \"$opt_asession\"");
logit("    \$opt_nsession = \"$opt_nsession\"");
logit("    \$opt_tablespace = \"$opt_tablespace\"");
logit("    \$opt_nextents = \"$opt_nextents\"");
logit("    \$opt_fextents = \"$opt_fextents\"");
logit("    \$opt_aextents = \"$opt_aextents\"");

# so let's connect to the instance...
$dbh = dbConnect($database,$username,$password);

$message="$database: ";
check_sessions($opt_nsession)   if ($opt_nsession && $privsok);
check_sessions($opt_asession,"active")   if ($opt_asession && $privsok);
check_tablespaces($opt_tablespace)   if ($opt_tablespace && $privsok);
check_nextents($opt_nextents)   if ($opt_nextents && $privsok);
check_fextents($opt_fextents)   if ($opt_fextents && $privsok);
check_aextents()   if ($opt_aextents && $privsok);

$message=$message . "ok. " . getDbVersion($dbh)   unless ($state);
print "$message\n";
exit $state;


sub usage {
   copyright();
   print "
This plugin will check various things of an oracle database instance.

Prerequisties are: a local oracle client,
                   perl > v5.003, and DBI and DBD::Oracle perl modules.

Usage: $PROGNAME -u <user> -p <passwd> -c <connectstring>
          [-a <w>/<c>] [-s <w>/<c>] [-t <w>/<c>] [-n <w>/<c>] [-f <w>/<c>] [-x]
       $PROGNAME [-V|--version]
       $PROGNAME [-h|--help]
";
   print "
Options:
 -u, --user=STRING
    the oracle user
 -p, --passwd=STRING
    the oracle password
 -c, --connect=STRING
    the oracle connectstring as defined in tnsnames.ora
 -a, --active-sessions=WARN/CRITICAL
    check the number of active (user-)sessions
      WARN(Integer): number of sessions to result in warning status,
      CRITICAL(Integer): number of sessions to result in critical status
 -s, --num-sessions=WARN/CRITICAL
    check the total number of (user-)sessions
      WARN(Integer): number of sessions to result in warning status,
      CRITICAL(Integer): number of sessions to result in critical status
 -t, --tablespaces=WARN/CRITICAL
    check the percent of used space in every tablespace
      WARN(Integer): percentage to result in warning status,
      CRITICAL(Integer): percentage to result in critical status
 -n, --num-extents=WARN/CRITICAL
    check the number of extents of every object (excluding SYS schema)
      WARN(Integer): number of extents to result in warning status,
      CRITICAL(Integer): number of extents to result in critical status
 -f, --free-extents=WARN/CRITICAL
    check the number of free extents of every object: max_extents - #extents
      WARN(Integer): number of free extents to result in warning status,
      CRITICAL(Integer): number of free extents to result in critical status
 -x, --allocate-extents
    warn if an object cannot allocate a next extent.
";
   exit $ERRORS{"UNKNOWN"};
}


sub version {
   copyright();
   print "
$PROGNAME $VERSION
";
   exit $ERRORS{"UNKNOWN"};
}


sub copyright {
   print "The netsaint plugins come with ABSOLUTELY NO WARRANTY. You may redistribute
copies of the plugins under the terms of the GNU General Public License.
For more information about these matters, see the file named COPYING.
Copyright (c) 2002 Sven Dolderer\n";
}


sub logit {
   my $text = shift;
   if ($debug) {
      open (LOG,">>$logfile") || die "Cannot open log file \"$logfile\"!";
      print LOG "$text\n";
      close (LOG);
   }
}


sub dbConnect {
   logit("Enter subroutine dbConnect");

   my $database = shift;
   my $username = shift;
   my $password = shift;

# Attempt to make connection to the database..
   my $data_source = "dbi:Oracle:$database";
   $dbh = DBI->connect($data_source,$username,$password,{PrintError=>0});

# Show an error message for these errors.
# ORA-12224 - "The connection request could not be completed because the listener is not running."
# ORA-01034 - "Oracle was not started up."
# ORA-01090 - "Shutdown in progress - connection is not permitted""
# ORA-12154 - "The service name specified is not defined correctly in the TNSNAMES.ORA file."
# ORA-12505 - "TNS:listener could not resolve SID given in connect descriptor."
# ORA-12545 - "TNS:name lookup failure."

   unless ($dbh) {
         logit("      Error message is ~$DBI::errstr~");
         if ( $DBI::errstr =~ /ORA-01017|ORA-1017|ORA-01004|ORA-01005/ ) {
            $message="Login error: ~$DBI::errstr~";
	    $state=$ERRORS{"UNKNOWN"};
         } elsif ( $DBI::errstr =~ /ORA-12224/ ) {
            $message= "You received an ORA-12224, which usually means the listener is down, or your connection definition in your tnsnames.ora file is incorrect. Check both of these things and try again.";
	    $state=$ERRORS{"CRITICAL"};
         } elsif ( $DBI::errstr =~ /ORA-01034/ ) {
            $message= "You received an ORA-01034, which usually means the database is down. Check to be sure the database is up and try again.";
	    $state=$ERRORS{"CRITICAL"};
         } elsif ( $DBI::errstr =~ /ORA-01090/ ) {
            $message= "You received an ORA-01090, which means the database is in the process of coming down.";
	    $state=$ERRORS{"CRITICAL"};
         } elsif ( $DBI::errstr =~ /ORA-12154/ ) {
            $message= "You received an ORA-12154, which probably means you have a mistake in your TNSNAMES.ORA file for the database that you chose.";
	    $state=$ERRORS{"UNKNOWN"};
         } elsif ( $DBI::errstr =~ /ORA-12505/ ) {
            $message= "You received an ORA-12505, which probably means you have a mistake in your TNSNAMES.ORA file for the database that you chose, or the database you are trying to connect to is not defined to the listener that is running on that node.";
	    $state=$ERRORS{"UNKNOWN"};
         } elsif ( $DBI::errstr =~ /ORA-12545/ ) {
            $message= "You received an ORA-12545, which probably means you have a mistake in your TNSNAMES.ORA file for the database that you chose. (Possibly the node name).";
	    $state=$ERRORS{"UNKNOWN"};
         } else {
            $message="Unable to connect to Oracle ($DBI::errstr)\n";
	    $state=$ERRORS{"UNKNOWN"};
         }
	 
   } else {
         logit("      Login OK.");

         # check to be sure this user has "SELECT ANY TABLE" privilege.
         logit("      checking for \"SELECT ANY TABLE\" privilege");
         if (checkPriv("SELECT ANY TABLE") < 1) {
            $message="user $username needs \"SELECT ANY TABLE\" privilege.";
            $state=$ERRORS{"UNKNOWN"};
         } else {
            $privsok="yep";
	    $state=$ERRORS{"OK"};
         }
   }
   return ($dbh);
}


sub getDbVersion {

   logit("Enter subroutine getDbVersion");

   my $dbh = shift;
   my $oraversion;

# Find out if we are dealing with Oracle7 or Oracle8
   logit("   Getting Oracle version");
   $sql = "select banner from v\$version where rownum=1";

   $cursor = $dbh->prepare($sql) or logit("Error: $DBI::errstr");
   $cursor->execute;
   (($oraversion) = $cursor->fetchrow_array);
   $cursor->finish;
   logit("   Oracle version = $oraversion");
   return $oraversion;
}


sub checkPriv {
   logit("Enter subroutine checkPriv");
   my ($privilege,$yesno);
   $privilege = shift;
   logit("   Checking for privilege \"$privilege\"");
   
   $sql = "SELECT COUNT(*) FROM SESSION_PRIVS WHERE PRIVILEGE = '$privilege'";  
   $cursor=$dbh->prepare($sql);
   $cursor->execute;                                                               $yesno = $cursor->fetchrow_array;
   $cursor->finish;

   return($yesno);
}


sub get_values {
   logit("Enter subroutine get_values");
   my ($args, $inverse, $abort);
   $args = shift;
   $inverse = shift;
   if ($args =~ m!^(\d+)/(\d+)$!) {
     $warn = $1;
     $critical = $2;

     # TODO: check for positive numbers!
     
     if (! $inverse && $warn >= $critical) {
        print "\"$args\": warning threshold must be less than critical threshold. aborting...\n";
	$abort="yep";
     }
     if ($inverse && $warn <= $critical) {
        print "\"$args\": warning threshold must be greater than critical threshold. aborting...\n";
	$abort="yep";
     }
   } else {
     print "\"$args\": invalid warn/critical thresholds. aborting...\n";
     $abort="yep";
   }
   exit $ERRORS{"UNKNOWN"}  if $abort;
   logit ("      args=$args, warn=$warn, critical=$critical");
}


sub check_sessions {
   logit("Enter subroutine check_sessions");
   my ($args, $add, $sqladd, $count);
   $args = shift;
   $add = shift || '#';   # Default: Number of sessions
   $sqladd = "AND STATUS = 'ACTIVE'"   if ($add eq "active");

   get_values($args);
   
   $sql = "SELECT COUNT(*) FROM V\$SESSION WHERE TYPE <> 'BACKGROUND' $sqladd";  
   $cursor=$dbh->prepare($sql);
   $cursor->execute;
   $count = $cursor->fetchrow_array;
   $cursor->finish;
   logit ("      $add sessions is $count");

   if ($count >= $critical) {
      $message = $message . "$add sessions critical ($count)    ";
      $state=$ERRORS{"CRITICAL"};
   } elsif ($count >= $warn) {
      $message = $message . "$add sessions warning ($count)    ";
      $state=$ERRORS{"WARNING"}  if $state < $ERRORS{"WARNING"};
   }
}


sub check_tablespaces {
   logit("Enter subroutine check_tablespaces");
   my ($args, $tablespace, $pctused, $mymsg, $mywarn, $mycritical);
   $args = shift;
   $mymsg = "Tablespace usage ";

   get_values($args);
   
   $sql = "SELECT
     DF.TABLESPACE_NAME \"Tablespace name\",
     NVL(ROUND((DF.BYTES-SUM(FS.BYTES))*100/DF.BYTES),100) \"Percent used\"
   FROM DBA_FREE_SPACE FS,
    (SELECT TABLESPACE_NAME, SUM(BYTES) BYTES FROM DBA_DATA_FILES GROUP BY
     TABLESPACE_NAME ) DF
   WHERE FS.TABLESPACE_NAME (+) = DF.TABLESPACE_NAME
   GROUP BY DF.TABLESPACE_NAME, DF.BYTES
   ORDER BY 2 DESC";

   $cursor=$dbh->prepare($sql);
   $cursor->execute;
   while (($tablespace, $pctused) = $cursor->fetchrow_array) {
      logit ("      $tablespace - $pctused% used");
      if ($pctused >= $critical) {
         unless ($mycritical) {
           $mymsg = $mymsg . "critical: ";
	   $mycritical="yep";
	 }
         $mymsg = $mymsg . "$tablespace ($pctused%) ";
         $state=$ERRORS{"CRITICAL"};
      } elsif ($pctused >= $warn) {
         unless ($mywarn) {
           $mymsg = $mymsg . "warning: ";
	   $mywarn="yep";
	 }
         $mymsg = $mymsg . "$tablespace ($pctused%) ";
         $state=$ERRORS{"WARNING"}  if $state < $ERRORS{"WARNING"};
      }
   }
   $cursor->finish;
   $message = $message . $mymsg . "   "   if ($mycritical || $mywarn);
}


sub check_nextents {
   logit("Enter subroutine check_nextents");
   my ($args, $owner, $objname, $objtype, $extents, $mymsg, $mywarn, $mycritical);
   $args = shift;
   $mymsg = "#Extents ";

   get_values($args);
   
   $sql = "SELECT
             OWNER              \"Owner\",
             SEGMENT_NAME       \"Object name\",
             SEGMENT_TYPE       \"Object type\",
             COUNT(*)           \"Extents\"
           FROM DBA_EXTENTS WHERE OWNER <> 'SYS'
             GROUP BY SEGMENT_TYPE, SEGMENT_NAME, TABLESPACE_NAME, OWNER
             HAVING COUNT(*) >= $warn
             ORDER BY 4 DESC";

   $cursor=$dbh->prepare($sql);
   $cursor->execute;
   while (($owner, $objname, $objtype, $extents) = $cursor->fetchrow_array) {
      if ($extents >= $critical) {
         unless ($mycritical) {
           $mymsg = $mymsg . "critical: ";
           $mycritical="yep";
         }
         $mymsg = $mymsg . "$owner.$objname($objtype)=$extents ";
         $state=$ERRORS{"CRITICAL"};
      } elsif ($extents >= $warn) {
         unless ($mywarn) {
           $mymsg = $mymsg . "warning: ";
           $mywarn="yep";
         }
         $mymsg = $mymsg . "$owner.$objname($objtype)=$extents ";
         $state=$ERRORS{"WARNING"}  if $state < $ERRORS{"WARNING"};
      }
   }
   $cursor->finish;
   $message = $message . $mymsg . "   "   if ($mycritical || $mywarn);
}


sub check_fextents {
   logit("Enter subroutine check_fextents");
   my ($args, $owner, $objname, $objtype, $extents, $maxextents, $freextents, $mymsg, $mywarn, $mycritical);
   $args = shift;
   $mymsg = "Free extents ";

   get_values($args, "inverse");
   
   $sql = "SELECT
      OWNER                        \"Owner\",
      SEGMENT_NAME                 \"Object name\",
      SEGMENT_TYPE                 \"Object type\",
      EXTENTS                      \"Extents\",
      MAX_EXTENTS                  \"Max extents\",
      MAX_EXTENTS - EXTENTS        \"Free extents\"
   FROM DBA_SEGMENTS
      WHERE (EXTENTS + $warn) >= MAX_EXTENTS
      AND SEGMENT_TYPE != 'CACHE'
      ORDER BY 6";

   $cursor=$dbh->prepare($sql);
   $cursor->execute;
   while (($owner, $objname, $objtype, $extents, $maxextents, $freextents) = $cursor->fetchrow_array) {
      if ($freextents <= $critical) {
         unless ($mycritical) {
           $mymsg = $mymsg . "critical: ";
           $mycritical="yep";
         }
         $mymsg = $mymsg . "$owner.$objname($objtype)=$extents ";
         $state=$ERRORS{"CRITICAL"};
      } elsif ($freextents <= $warn) {
         unless ($mywarn) {
           $mymsg = $mymsg . "warning: ";
           $mywarn="yep";
         }
         $mymsg = $mymsg . "$owner.$objname($objtype)=$extents/$maxextents ";
         $state=$ERRORS{"WARNING"}  if $state < $ERRORS{"WARNING"};
      }
   }
   $cursor->finish;
   $message = $message . $mymsg . "   "   if ($mycritical || $mywarn);
}


sub check_aextents {
   logit("Enter subroutine check_aextents");
   my ($args, $owner, $objname, $objtype, $tablespace_name, $mymsg, $mywarn);
   my (@tablespaces);

   # Get a list of all tablespaces
   $sql = "SELECT TABLESPACE_NAME
           FROM DBA_TABLESPACES ORDER BY TABLESPACE_NAME";
   $cursor = $dbh->prepare($sql);
   $cursor->execute;
   while ($tablespace_name = $cursor->fetchrow_array) {
      push @tablespaces, $tablespace_name;
   }
   $cursor->finish;

   # Search every tablespace for objects which cannot allocate a next extent.
   foreach $tablespace_name(@tablespaces) {
      logit ("        checking tablespace $tablespace_name");
      $sql = "SELECT
	   OWNER            \"Owner\",
	   SEGMENT_NAME     \"Object name\",
	   SEGMENT_TYPE     \"Object type\"
	FROM DBA_SEGMENTS
	   WHERE TABLESPACE_NAME = '$tablespace_name'
	   AND NEXT_EXTENT > (SELECT NVL(MAX(BYTES),'0') FROM DBA_FREE_SPACE
			      WHERE TABLESPACE_NAME = '$tablespace_name')";
      $cursor = $dbh->prepare($sql);
      $cursor->execute;
      while (($owner, $objname, $objtype) = $cursor->fetchrow_array) {
         logit ("        found: $owner.$objname($objtype)");
         unless ($mywarn) {
           $mymsg = $mymsg . "warning: ";
           $mywarn="yep";
         }
         $mymsg = $mymsg . "$owner.$objname($objtype) ";
         $state=$ERRORS{"WARNING"}  if $state < $ERRORS{"WARNING"};
      }
      $cursor->finish;
   }
   $message = $message . $mymsg . "cannot allocate a next extent.   "   if $mywarn;
}

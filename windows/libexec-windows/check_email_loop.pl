#!/usr/bin/perl -w
#
# $Id: check_email_loop.pl 1290 2005-11-29 23:21:06Z harpermann $
#
# (c)2000 Benjamin Schmid, blueshift@gmx.net (emergency use only ;-)
# Copyleft by GNU GPL
#
#
# check_email_loop Nagios Plugin
#
# This script sends a mail with a specific id in the subject via
# an given smtp-server to a given email-adress. When the script
# is run again, it checks for this Email (with its unique id) on
# a given pop3 account and send another mail.
# 
#
# Example: check_email_loop.pl -poph=mypop -popu=user -pa=password
# 	   -smtph=mailer -from=returnadress@yoursite.com
#	   -to=remaileradress@friend.com -pendc=2 -lostc=0
#
# This example will send eacht time this check is executed a new
# mail to remaileradress@friend.com using the SMTP-Host mailer.
# Then it looks for any back-forwarded mails in the POP3 host
# mypop. In this Configuration CRITICAL state will be reached if  
# more than 2 Mails are pending (meaning that they did not came 
# back till now) or if a mails got lost (meaning a mail, that was
# send later came back prior to another mail).
# 
# Michael Markstaller, mm@elabnet.de various changes/additions
# MM 021003: fixed some unquoted strings
# MM 021116: fixed/added pendwarn/lostwarn
# MM 030515: added deleting of orphaned check-emails 
#					  changed to use "top" instead of get to minimize traffic (required changing match-string from "Subject: Email-ping [" to "Email-Ping ["

use Net::POP3;
use Net::SMTP;
use strict;
use Getopt::Long;
&Getopt::Long::config('auto_abbrev');

# ----------------------------------------

my $TIMEOUT = 120;
my %ERRORS = ('OK' , '0',
              'WARNING', '1',
              'CRITICAL', '2');
              'UNKNOWN' , '3');

my $state = "UNKNOWN";
my ($sender,$receiver, $pophost, $popuser, $poppasswd, $smtphost,$keeporphaned);
my ($poptimeout,$smtptimeout,$pinginterval,$maxmsg)=(60,60,5,50);
my ($lostwarn, $lostcrit,$pendwarn, $pendcrit,$debug);
$debug = 0;

# Internal Vars
my ($pop,$msgcount,@msglines,$statinfo,@messageids,$newestid);
my (%other_smtp_opts);
my ($matchcount,$statfile) = (0,"check_email_loop.stat");

# Subs declaration
sub usage;
sub messagematchs;
sub nsexit;

# Just in case of problems, let's not hang Nagios
$SIG{'ALRM'} = sub {
     print ("ERROR: $0 Time-Out $TIMEOUT s \n");
     exit $ERRORS{"UNKNOWN"};
};
alarm($TIMEOUT);


# Evaluate Command Line Parameters
my $status = GetOptions(
		        "from=s",\$sender,
			"to=s",\$receiver,
                        "debug", \$debug,
                        "pophost=s",\$pophost,
                        "popuser=s",\$popuser,
			"passwd=s",\$poppasswd,
			"poptimeout=i",\$poptimeout,
			"smtphost=s",\$smtphost,
			"smtptimeout=i",\$smtptimeout,
			"statfile=s",\$statfile,
			"interval=i",\$pinginterval,
			"lostwarn=i",\$lostwarn,
			"lostcrit=i",\$lostcrit,
			"pendwarn=i",\$pendwarn,
			"pendcrit=i",\$pendcrit,
			"maxmsg=i",\$maxmsg,
			"keeporphaned=s",\$keeporphaned,
			);
usage() if ($status == 0 || ! ($pophost && $popuser && $poppasswd &&
	$smtphost && $receiver && $sender ));

# Try to read the ids of the last send emails out of statfile
if (open STATF, "$statfile") {
  @messageids = <STATF>;
  chomp @messageids;
  close STATF;
}

# Try to open statfile for writing 
if (!open STATF, ">$statfile") {
  nsexit("Failed to open mail-ID database $statfile for writing",'CRITICAL');
}

# Ok - check if it's time to release another mail

# ...

# creating new serial id
my $serial = time();
$serial = "ID#" . $serial . "#$$";


# sending new ping email
%other_smtp_opts=();
if ( $debug == 1  ) {
    $other_smtp_opts{'Debug'} = 1;
}

my $smtp = Net::SMTP->new($smtphost,Timeout=>$smtptimeout, %other_smtp_opts) 
  || nsexit("SMTP connect timeout ($smtptimeout s)",'CRITICAL');
($smtp->mail($sender) &&
 $smtp->to($receiver) &&
 $smtp->data() &&
 $smtp->datasend("To: $receiver\nSubject: E-Mail Ping [$serial]\n\n".
		 "This is an automatically sent E-Mail.\n".
		 "It is not intended for a human reader.\n\n".
		 "Serial No: $serial\n") &&
 $smtp->dataend() &&
 $smtp->quit
 ) || nsexit("Error delivering message",'CRITICAL');

# no the interessting part: let's if they are receiving ;-)

$pop = Net::POP3->new( $pophost, 
		 Timeout=>$poptimeout) 
       || nsexit("POP3 connect timeout (>$poptimeout s, host: $pophost)",'CRITICAL');

$msgcount=$pop->login($popuser,$poppasswd);

$statinfo="$msgcount mails on POP3";

nsexit("POP3 login failed (user:$popuser)",'CRITICAL') if (!defined($msgcount));

# Check if more than maxmsg mails in pop3-box
nsexit(">$maxmsg Mails ($msgcount Mails on POP3); Please delete !",'WARNING') if ($msgcount > $maxmsg);

my ($mid, $nid);
# Count messages, that we are looking 4:
while ($msgcount > 0) {
  @msglines = @{$pop->top($msgcount,1)};
  for (my $i=0; $i < scalar @messageids; $i++) {
    if (messagematchsid(\@msglines,$messageids[$i])) { 
      $matchcount++;
      # newest received mail than the others, ok remeber id.
      if (!defined $newestid) { 
        $newestid = $messageids[$i];
      } else {
	    $messageids[$i] =~ /\#(\d+)\#/;
        $mid = $1;
	    $newestid =~ /\#(\d+)\#/;
        $nid = $1;
        if ($mid > $nid) { 
          $newestid = $messageids[$i]; 
        }
      }
      $pop->delete($msgcount);  # remove E-Mail from POP3 server
      splice @messageids, $i, 1;# remove id from List
	  last;                     # stop looking in list
	} 
  } 
	# Delete orphaned Email-ping msg
	my @msgsubject = grep /^Subject/, @msglines;
	chomp @msgsubject;
	# Scan Subject if email is an Email-Ping. In fact we match and delete also successfully retrieved messages here again.
	if (!defined $keeporphaned && $msgsubject[0] =~ /E-Mail Ping \[/) {
	    $pop->delete($msgcount);  # remove E-Mail from POP3 server
	}

	$msgcount--;
}

$pop->quit();  # necessary for pop3 deletion!

# traverse through the message list and mark the lost mails
# that mean mails that are older than the last received mail.
if (defined $newestid) {
  $newestid =~ /\#(\d+)\#/;
  $newestid = $1;
  for (my $i=0; $i < scalar @messageids; $i++) {
    $messageids[$i] =~ /\#(\d+)\#/;
    my $akid = $1;
    if ($akid < $newestid) {
      $messageids[$i] =~ s/^ID/LI/; # mark lost
    }
  }
}

# Write list to id-Database
foreach my $id (@messageids) {
  print STATF  "$id\n";
}
print STATF "$serial\n";     # remember send mail of this session
close STATF;

# ok - count lost and pending mails;
my @tmp = grep /^ID/, @messageids;
my $pendingm = scalar @tmp;
@tmp = grep /^LI/, @messageids;
my $lostm = scalar @tmp; 

# Evaluate the Warnin/Crit-Levels
if (defined $pendwarn && $pendingm > $pendwarn) { $state = 'WARNING'; }
if (defined $lostwarn && $lostm > $lostwarn) { $state = 'WARNING'; }
if (defined $pendcrit && $pendingm > $pendcrit) { $state = 'CRITICAL'; }
if (defined $lostcrit && $lostm > $lostcrit) { $state = 'CRITICAL'; }

if ((defined $pendwarn || defined $pendcrit || defined $lostwarn 
     || defined $lostcrit) && ($state eq 'UNKNOWN')) {$state='OK';}


# Append Status info
$statinfo = $statinfo . ", $matchcount mail(s) came back,".
            " $pendingm pending, $lostm lost.";

# Exit in a Nagios-compliant way
nsexit($statinfo);

# ----------------------------------------------------------------------

sub usage {
  print "check_email_loop 1.1 Nagios Plugin - Real check of a E-Mail system\n";
  print "=" x 75,"\nERROR: Missing or wrong arguments!\n","=" x 75,"\n";
  print "This script sends a mail with a specific id in the subject via an given\n";
  print "smtp-server to a given email-adress. When the script is run again, it checks\n";
  print "for this Email (with its unique id) on a given pop3 account and sends \n";
  print "another mail.\n";
  print "\nThe following options are available:\n";
  print	"   -from=text         email adress of send (for mail returnr on errors)\n";
  print	"   -to=text           email adress to which the mails should send to\n";
  print "   -pophost=text      IP or name of the POP3-host to be checked\n";
  print "   -popuser=text      Username of the POP3-account\n";
  print	"   -passwd=text       Password for the POP3-user\n";
  print	"   -poptimeout=num    Timeout in seconds for the POP3-server\n";
  print "   -smtphost=text     IP oder name of the SMTP host\n";
  print "   -smtptimeout=num   Timeout in seconds for the SMTP-server\n";
  print "   -statfile=text     File to save ids of messages ($statfile)\n";
  print "   -interval=num      Time (in minutes) that must pass by before sending\n";
  print "                      another Ping-mail (gibe a new try);\n"; 
  print "   -lostwarn=num      WARNING-state if more than num lost emails\n";
  print "   -lostcrit=num      CRITICAL \n";
  print "   -pendwarn=num      WARNING-state if more than num pending emails\n";
  print "   -pendcrit=num      CRITICAL \n";
  print "   -maxmsg=num        WARNING if more than num emails on POP3 (default 50)\n";
  print "   -keeporphaned      Set this to NOT delete orphaned E-Mail Ping msg from POP3\n";
  print "   -debug             send SMTP tranaction info to stderr\n\n";
  print " Options may abbreviated!\n";
  print " LOST mails are mails, being sent before the last mail arrived back.\n";
  print " PENDING mails are those, which are not. (supposed to be on the way)\n";
  print "\nExample: \n";
  print " $0 -poph=host -pa=pw -popu=popts -smtph=host -from=root\@me.com\n ";
  print "      -to=remailer\@testxy.com -lostc=0 -pendc=2\n";
  print "\nCopyleft 19.10.2000, Benjamin Schmid / 2003 Michael Markstaller, mm\@elabnet.de\n";
  print "This script comes with ABSOLUTELY NO WARRANTY\n";
  print "This programm is licensed under the terms of the ";
  print "GNU General Public License\n\n";
  exit $ERRORS{"UNKNOWN"};
}

# ---------------------------------------------------------------------

sub nsexit {
  my ($msg,$code) = @_;
  $code=$state if (!defined $code);
  print "$code: $msg\n" if (defined $msg);
  exit $ERRORS{$code};
}

# ---------------------------------------------------------------------

sub messagematchsid {
  my ($mailref,$id) = (@_);
  my (@tmp);
  my $match = 0;
 
  # ID
  $id =~ s/^LI/ID/;    # evtl. remove lost mail mark
  @tmp = grep /E-Mail Ping \[/, @$mailref;
  chomp @tmp;
  if (($tmp[0] =~ /$id/)) 
    { $match = 1; }

  # Sender:
#  @tmp = grep /^From:\s+/, @$mailref;
#  if (@tmp && $sender ne "") 
#    { $match = $match && ($tmp[0]=~/$sender/); }

  # Receiver:
#  @tmp = grep /^To: /, @$mailref;
#  if (@tmp && $receiver ne "") 
#    { $match = $match && ($tmp[0]=~/$receiver/); }

  return $match;
}

# ---------------------------------------------------------------------

#!/usr/bin/perl 
#
# check_qmailq.pl - nagios plugin 
# This plugin allows you to check the number of Mails in a qmail-
# queue. PLUGIN NEEDS CONFIGURATION ! (see below) 
#
# Copyright 2000 Benjamin Schmid
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
#
# Emergency E-Mail :) blueshift@gmx.net
#

### CONFIGURATION SECTION ####################

my $statcommand  = "/var/qmail/bin/qmail-qstat";
my $queuewarn = 5;      # Warning, if more than x mail in Queue
my $queuecrit = 10;     # Critical if "--"
my $prewarn = 1;        # Warning, if more than x unhandled mails 
			# (not in Queue
my $precrit = 5;        # Critical, if  "--"

### CONFIURATION SECTION END ################

use strict;
use Carp;

#use Getopt::Long;
#&Getopt::Long::config('auto_abbrev');



my $TIMEOUT = 15;

my %ERRORS = ('UNKNOWN' , '-1',
              'OK' , '0',
              'WARNING', '1',
              'CRITICAL', '2');

my $state = "UNKNOWN";
my $answer = "";

#sub usage {
#  printf "\nMissing arguments!\n";
#  printf "\n";
#  printf "Printer Server Queue Nagios Plugin\n";
#  printf "monitors jobs in lpr queues\n";
#  printf "usage: \n";
#  printf "check_lpq.pl \n";
#  printf "Copyright (C) 2000 Benjamin Schmid\n";
#  printf "check_lpq.pl comes with ABSOLUTELY NO WARRANTY\n";
#  printf "This programm is licensed under the terms of the ";
#  printf "GNU General Public License\n(check source code for details)\n";
#  printf "\n\n";
#  exit $ERRORS{"UNKNOWN"};
#}

# Just in case of problems, let's not hang Nagios
$SIG{'ALRM'} = sub {
     print ("ERROR: check_lpq.pl Time-Out $TIMEOUT s \n");
     exit $ERRORS{"UNKNOWN"};
};
alarm($TIMEOUT);


#$status = GetOptions("community=s",\$community,
#                     "port=i",\$port);
#if ($status == 0)
#{
#        &usage;
#}
  
#   $hostname  = shift || &usage;

if (! open STAT, "$statcommand|") {
  print ("$state: $statcommand returns no result!");
  exit $ERRORS{$state};
}
my @lines = <STAT>;
close STAT;

# Mails in Queues
if ($lines[0]=~/^messages in queue: (\d+)/) {
  my $anzq = $1;
  $answer = $answer . "$anzq";
  $state='WARNING' if ($anzq >= $queuewarn);
  $state='CRITICAL' if ($anzq >= $queuecrit);
} else {
  $state='CRITICAL';
  $answer="Keine gueltigte Antwort (Zeile #1) von $statcommand\n";
}

# Unverarbeite Mails
if ($lines[1]=~/^messages in queue but not yet preprocessed: (\d+)/) {
  my $anzp = $1;
  $answer = $answer . " E-Mail(s) nicht ausgeliefert, $anzp unverarbeitet.";
  $state='WARNING' if ($anzp >= $prewarn && $state eq 'UNKNOWN');
  $state='CRITICAL' if ($anzp >= $precrit);
} else {
  $state='CRITICAL';
  $answer=$answer . "Keine gueltigte Antwort (Zeile #2) von $statcommand\n";
}

$state = 'OK' if ($state eq 'UNKNOWN');

print ("$state: $answer\n");
exit $ERRORS{$state};


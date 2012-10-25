#!/usr/bin/perl
#
# event_generic.pl - Generic Event handler script, only valid for Nagios Services
#
# Copyright (C) 2012 Matthew Jurgens
# You can email me using: mjurgens (the at goes here) edcint.co.nz
# Download link can be found at http://www.edcint.co.nz
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

my $VERSION="1.02";

use strict;
use Getopt::Long;

# uses the following NAGIOS_ environment variables that should be set in the environment for proper execution
#$ENV{'NAGIOS_SERVICESTATE'}='CRITICAL';  # CRITICAL, WARNING, UNKNOWN, OK 
#$ENV{'NAGIOS_SERVICEATTEMPT'}='1';  # a number
#$ENV{'NAGIOS_MAXSERVICEATTEMPTS'}='3';  # a number
#$ENV{'NAGIOS_SERVICESTATETYPE'}='SOFT';  # SOFT or HARD

# these ones are used by not really important
#$ENV{'NAGIOS_SERVICEDESC'}='My Test Service';
#$ENV{'NAGIOS_SERVICEOUTPUT'}='Service Info XX'; # important if you use the REGEX option
#$ENV{'NAGIOS_HOSTNAME'}='TestHost';

#==============================================================================
#================================= DECLARATIONS ===============================
#==============================================================================

# command line option declarations
my $opt_command=(); # this becomes an array reference
my $opt_timeout='';
my $debug=''; # '/tmp/event_generic.log'; # set this to a file name to log all runs of this event handler, leave blank to run only if parameter specified on command line
my $opt_hard='';
my $opt_soft='';
my $opt_numbersoft='';
my $opt_statelist=(); # this becomes an array reference
my $opt_timeout='';
my $opt_regex=(); # this becomes an array reference
my $opt_usefirstregex='';
my $opt_usefirststatelist='';
my $opt_test='';

# default timeout
my $TIMEOUT=30;

#==============================================================================
#================================== PARAMETERS ================================
#==============================================================================
# save the arguments before Getopt gets to it
my @saved_ARGV=@ARGV;

Getopt::Long::Configure('no_ignore_case');
GetOptions(
   "command=s@"            => \$opt_command,
   "debug=s"               => \$debug,
   "soft"                  => \$opt_soft,
   "hard"                  => \$opt_hard,
   "numbersoft=s"          => \$opt_numbersoft,
   "list=s@"               => \$opt_statelist,
   "timeout=i"             => \$opt_timeout,
   "regex=s@"              => \$opt_regex,
   "usefirstregex"         => \$opt_usefirstregex,
   "usefirststatelist"     => \$opt_usefirststatelist,
   "envtest=s"             => \$opt_test,
   );

if ($debug) {
   use Data::Dumper; # only use module if you have to
   # open the debug log file, redirect all output to the debug log file
   if ($debug=~/stdout/i) {
      # do not open a debug file and hence do not redirect STDOUT to the file
   } elsif (open(DEBUG,">>$debug")) {
      # looks ok
      select DEBUG; # redirect to debug file
   } else {
      die("Could not open debug file $debug for writing");
   }
   $|=1; # make output unbuffered
   print "\n=========================================================================================\n";
   print localtime(time) ."\n";
   my $command_line=join(' ',@saved_ARGV);
   print "CMD:$0 $command_line\n";
}

if ($opt_test) {
   # load the test parameters into the %ENV 
   # the incoming format is SERVICESTATE|ATTEMPT|MAXATTEMPTS|STATETYPE|SERVICEOUTPUT
   # no error checking here ...........
   my @testparam=split(/\|/,$opt_test);
   $ENV{'NAGIOS_SERVICESTATE'}=$testparam[0] || '';
   $ENV{'NAGIOS_SERVICEATTEMPT'}=$testparam[1] || '';
   $ENV{'NAGIOS_MAXSERVICEATTEMPTS'}=$testparam[2] || '';
   $ENV{'NAGIOS_SERVICESTATETYPE'}=$testparam[3] || '';
   $ENV{'NAGIOS_SERVICEOUTPUT'}=$testparam[4] || '';
   $debug && print "Setting Test Parameters:\n   'NAGIOS_SERVICESTATE'=$testparam[0]\n   'NAGIOS_SERVICEATTEMPT'=$testparam[1]\n   'NAGIOS_MAXSERVICEATTEMPTS'=$testparam[2]\n   'NAGIOS_SERVICESTATETYPE'=$testparam[3]\n   'NAGIOS_SERVICEOUTPUT'=$testparam[4]\n";
}

if ($opt_timeout) {
   $TIMEOUT=$opt_timeout;
}
# Setup the trap for a timeout
$SIG{'ALRM'} = sub {
   print "Event Handler $0 Timed out ($TIMEOUT sec)\n";
   exit 1;
};
alarm($TIMEOUT);
 
 
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
#--------------------------------------------------------------------------------


#==============================================================================
#===================================== MAIN ===================================
#==============================================================================


# process parameters

if ( $#$opt_command<0) {
   usage();
   exit 1;
}

if ( ! $opt_soft && ! $opt_hard ) {
   # neither hard nor soft specified so default to hard
   $opt_hard=1;
}

if ($opt_soft && $opt_numbersoft eq 'L') {
   # soft state execution on the last soft state which is calculated by 
   # NAGIOS_MAXSERVICEATTEMPTS - 1
   $opt_numbersoft=$ENV{'NAGIOS_MAXSERVICEATTEMPTS'}-1;
   $debug && print "Setting execution for Soft attempt number $opt_numbersoft\n";
}

# work out if we will execute this command under this NAGIOS_SERVICESTATE and NAGIOS_SERVICEATTEMPT number
my $nagios_hostname=$ENV{'NAGIOS_HOSTNAME'} || '';
my $nagios_servicedesc=$ENV{'NAGIOS_SERVICEDESC'} || '';
my $nagios_servicestate=$ENV{'NAGIOS_SERVICESTATE'} || '';
my $nagios_serviceattempt=$ENV{'NAGIOS_SERVICEATTEMPT'} || '';
my $nagios_maxserviceattempts=$ENV{'NAGIOS_MAXSERVICEATTEMPTS'} || '';
my $nagios_servicestatetype=$ENV{'NAGIOS_SERVICESTATETYPE'} || '';
my $nagios_serviceoutput=$ENV{'NAGIOS_SERVICEOUTPUT'} || '';

print "HOST=$nagios_hostname, SERVICE=$nagios_servicedesc, STATE=$nagios_servicestate, ATTEMPT $nagios_serviceattempt/$nagios_maxserviceattempts, TYPE=$nagios_servicestatetype, OUTPUT=$nagios_serviceoutput\n";

# determine if we should be executing based on soft/hard states
my $execute=0;
$debug && print "Determining whether to execute based on current State Type of $nagios_servicestatetype\n";
if ($opt_soft && $nagios_servicestatetype eq 'SOFT') {
   # within soft status only execute on the $softnum or always if softnum not specified
   if ($opt_numbersoft && $opt_numbersoft eq $nagios_serviceattempt) {
      $execute=1;
      print "Executing on SOFT Status (attempt $nagios_serviceattempt of $nagios_maxserviceattempts)\n";
   } elsif ( ! $opt_numbersoft ) {
      $execute=1;
      print "Executing on any SOFT Status (attempt $nagios_serviceattempt of $nagios_maxserviceattempts)\n";
   } else {
      $debug && print "Not executing for current Soft attempt number $nagios_serviceattempt\n";
   }
} elsif ($opt_hard && $nagios_servicestatetype eq 'HARD') {
   $execute=1;
   print "Executing on HARD Status\n";
} else {
   $debug && print "Not executing for current State Type\n";
}

if ($execute) {
   
   # now determine whcih commands should be run for the current NAGIOS_SERVICESTATE (critical, warning etc)
   # loop through all defined commands

   $execute=0;
   
   my $command_number=0;
   foreach my $command (@{$opt_command}) {
      # for each command that is defined check the states that it should be run for
      # see if the current NAGIOS_SERVICESTATE is in the statelist entry for command number $command_number
      # look in the statelist matching this command number 
      $debug && print "------------- Start of Command#$command_number -------------------\n";
      my $statetype=substr($nagios_servicestate,0,1);

      my $compare_statelist=$$opt_statelist[$command_number];
      if ($opt_usefirststatelist) {
         $compare_statelist=$$opt_statelist[0];
         $debug && print "Forcing use of only the first statelist defined\n";
      }

      if (!$compare_statelist) {
         # default to critical if nothing defined
         $compare_statelist='C';
         $debug && print "No State List defined - defaulting to $compare_statelist\n";
      }
      print "Looking for Current State $nagios_servicestate ($statetype) in defined State List $compare_statelist\n";
      if ($compare_statelist=~/$statetype/i) {
         # found current NAGIOS_SERVICESTATE in this state entry
         $execute=1;
      } else {
         $debug && print "Not executing since the current state type is not in the defined list\n";
      }
      
      # now make the regex decision
      my $compare_regex=$$opt_regex[$command_number];
      if ($opt_usefirstregex) {
         $compare_regex=$$opt_regex[0];
         $debug && print "Forcing use of only the first regex defined\n";
      }
      
      if ($execute) {
         if ($compare_regex) {
            $execute=0;
            if ($nagios_serviceoutput=~/$compare_regex/i) {
               $execute=1;
               print "Executing since Regex \"$compare_regex\" matches service output\n";
            } else {
               $debug && print "Not executing since Regex \"$compare_regex\" does not match service output\n";
            }
         } else {
            $debug && print "No regex defined for this command\n";
         }
      }

      # and finally actually execute the command if we are supposed to
      if ($execute) {
         print "Running Command#$command_number: $$opt_command[$command_number]\n";
         my $output=`$$opt_command[$command_number] 2>&1`;
         print "Command Output: $output\n";
      }
      $debug && print "------------- End of Command#$command_number -------------------\n";
      $command_number++;
   }
}

#==============================================================================
#================================== FUNCTIONS =================================
#==============================================================================

#-------------------------------------------------------------------------------
sub usage () {
print<<EOT;
A generic use, Nagios event handler. Runs a parameter driven command under various Nagios conditions.
Allows you to fully parameterise your event handlers so that you can simply your Nagios configuration.

Usage: $0 [-s [-n NUM]] [-h] [-l STATELIST] [-d FILE] [-t TIMEOUT] [-r REGEX] [-usefirstregex] [--usefirststatelist] [-e ENVTEST] -c COMMAND

where
-s          Specifies the command should be run during Nagios SOFT states

NUM         If -s is used, specifies the attempt number when the command will be executed
            Use L to specify that it should be the last SOFT state before it goes HARD

-h          Specifies the command should be run during Nagios HARD states
            If -s and/or -h is not provided -h is assumed

COMMAND     Is the complete command with arguments to be executed. Run multiple commands 
            by separating them with a semi-colon (;). For example:
            'date;id;uname -a'

STATELIST   The list of Nagios states the COMMAND will be executed under
            Use o for OK, w for WARNING, c for CRITICAL, u for UNKNOWN
            Specify multiple states simply by string them together eg cw or uow
            If STATELIST is not specfied it defaults to the single element c

FILE        The name of a file to dump debug info to. Needs to be Nagios writeable.
            A file is used since most of the time this event handler is run from within Nagios
            and its very handy to be able to to see what is going on.
            If FILE is the text string stdout then the debug output will be sent to STDOUT.
            If you want to make all checks that use this handler do debug, modify this script as follows:
            Change the line: my $debug='';
            to contain the name of your debug file eg my $debug='/tmp/event.log';

TIMEOUT     Specify a timeout for this event handler in seconds

REGEX       Only execute the command if the REGEX matches the output text of the service
            that the event handler is running for. The REGEX is case insensitive.

ENVTEST     A pipe delimited string which sets up fake environment variables to simulate being called from Nagios. 
            Used for testing only. Format is SERVICESTATE|ATTEMPT|MAXATTEMPTS|STATETYPE|SERVICEOUTPUT where
            SERVICESTATE = one of CRITICAL, WARNING, UNKNOWN, OK
            ATTEMPT = an integer. The number of times Nagios has found the service in this state.
            MAXATTEMPTS = an integer. The maximum number of ATTEMPTS before the service state goes HARD
            STATETYPE = SOFT or HARD
            SERVICEOUTPUT = the text the service displays. Only needs to be set if using a REGEX

--usefirstregex       Use the same REGEX for all commands ie the first REGEX defined on the command line
--usefirststatelist   Use the same STATELIST for all command ie the first STATELIST defined on the command line

NOTES:
======
-c COMMAND and -l STATELIST and -r REGEX can be used multiple times. In this case, the order of definition matters.
The first use of COMMAND will match the first use of STATELIST.
The second use of COMMAND will match the second use of STATELIST and so on.

For example, to run 2 commands on WARNING States use:
-c COMMAND1 -c COMMAND2  -l w  -l w

For example, to run 2 commands, one on WARNING state and the other on CRITICAL states use:
-c COMMAND_FOR_WARN -c COMMAND_FOR_CRIT  -l w  -l c

For example, to run 2 commands, one on WARNING state and the other on CRITICAL states use:
Remember that if you do not specify -l, it will default to c

EXAMPLES:
=========
The most basic usage is run a command on HARD CRITICAL states:
$0 -c "COMMAND" 

To run a command on the last SOFT CRITICAL state (ie just before it goes HARD):
$0 -c "COMMAND" -s -n L

To run a command on any SOFT CRITICAL or WARNING state:
$0 -c "COMMAND" -s -l cw

To run a 2 commands on any HARD CRITICAL or WARNING state:
$0 -c "COMMAND1" -c "COMMAND2" -l cw --usefirststatelist

To run a command if the output contains "really bad problem":
$0 -c "COMMAND1" -r "really bad problem"

To run a command if the output does not contain "timeout":
$0 -c "COMMAND1" -r '^(?!.*?timeout).*'

To test outside of Nagios you need to provide the information that Nagios would otherwise provide. 
So you might run it like this:
To simulate the first time a service has a problem -
$0 -d stdout -e "CRIT|1|3|SOFT|Service XX has a problem" -c "sleep 0"
Second time service has a problem -
$0 -d stdout -e "CRIT|2|3|SOFT|Service XX has a problem" -c "sleep 0"
Third time service has a problem (when the service goes to HARD state) -
$0 -d stdout -e "CRIT|3|3|HARD|Service XX has a problem" -c "sleep 0"
EOT
exit 1;
}
#-------------------------------------------------------------------------------

#!/usr/local/bin/perl
#
# usage: 
#    check_flexlm.pl license_file
#
# Check available flexlm license managers.
# Use lmstat to check the status of the license server
# described by the license file given as argument.
# Check and interpret the output of lmstat
# and create returncodes and output.
#
# Contrary to the nagios concept, this script takes
# a file, not a hostname as an argument and returns
# the status of hosts and services described in that
# file. Use these hosts.cfg entries as an example
#
#host[anchor]=any host will do;some.address.com;;check-host-alive;3;120;24x7;1;1;1;
#service[anchor]=yodel;24x7;3;5;5;unix-admin;60;24x7;1;1;1;;check_flexlm!/opt/lic/licfiles/yodel_lic
#service[anchor]=yeehaw;24x7;3;5;5;unix-admin;60;24x7;1;1;1;;check_flexlm!/opt/lic/licfiles/yeehaw_lic
#command[check_flexlm]=/some/path/libexec/check_flexlm.pl $ARG1$
#
# Notes:
# - you need the lmstat utility which comes with flexlm.
# - set the correct path in the variable $lmstat.
#
# initial version: 9-10-99 Ernst-Dieter Martin edmt@infineon.com
# current status: looks like working
#
# Copyright Notice: Do as you please, credit me, but don't blame me
#

# Just in case of problems, let's not hang Nagios
$SIG{'ALRM'} = sub {
	print "No Answer from Client\n";
	exit 2;
};
alarm(20);

$lmstat = "/opt/lic/sw/cadadm/default/bin/lmstat";

$licfile = shift;

#print "$licfile \n";

open CMD,"$lmstat -c $licfile |";

$serverup = 0;

while ( <CMD> ) {
  if ( /^License server status: [0-9]*@([-0-9a-zA-Z_]*),[0-9]*@([-0-9a-zA-Z_]*),[0-9]*@([-0-9a-zA-Z_]*)/ ) {
	$ls1 = $1;
	$ls2 = $2;
	$ls3 = $3;
	$lf1 = $lf2 = $lf3 = 0;
	$servers = 3;
  } elsif ( /^License server status: [0-9]*@([-0-9a-zA-Z_]*)/ ) {
	$ls1 = $1;
	$ls2 = $ls3 = "";
	$lf1 = $lf2 = $lf3 = 0;
	$servers = 1;
  } elsif ( / *$ls1: license server UP/ ) {
	print "$ls1 UP, ";
	$lf1 = 1
  } elsif ( / *$ls2: license server UP/ ) {
	print "$ls2 UP, ";
	$lf2 = 1
  } elsif ( / *$ls3: license server UP/ ) {
	print "$ls3 UP, ";
	$lf3 = 1
  } elsif ( / *([^:]*: UP .*)/ ) {
	print " license server for $1\n";
	$serverup = 1;
  }
}
if ( $serverup == 0 ) {
    print " license server not running\n";
    exit 2;	
}

exit 0 if ( $servers == $lf1 + $lf2 + $lf3 );
exit 1 if ( $servers == 3 && $lf1 + $lf2 + $lf3 == 2 );
exit 2;

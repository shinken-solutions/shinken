#!/usr/bin/perl -w

# check_digitemp.pl Copyright (C) 2002 by Brian C. Lane <bcl@brianlane.com>
#
# This is a NetSaint plugin script to check the temperature on a local 
# machine. Remote usage may be possible with SSH
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to
# deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
# sell copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.
#
# ===========================================================================
# Howto Install in NetSaint (tested with v0.0.7)
#
# 1. Copy this script to /usr/local/netsaint/libexec/ or wherever you have
#    placed your NetSaint plugins
#
# 2. Create a digitemp config file in /usr/local/netsaint/etc/
#    eg. digitemp -i -s/dev/ttyS0 -c /usr/local/netsaint/etc/digitemp.conf
#
# 3. Make sure that the webserver user has permission to access the serial
#    port being used.
#
# 4. Add a command to /usr/local/netsaint/etc/commands.cfg like this:
#    command[check-temp]=$USER1$/check_digitemp.pl -w $ARG1$ -c $ARG2$ \
#    -t $ARG3$ -f $ARG4$
#    (fold into one line)
#
# 5. Tell NetSaint to monitor the temperature by adding a service line like
#    this to your hosts.cfg file:
#    service[kermit]=Temperature;0;24x7;3;5;1;home-admins;120;24x7;1;1;1;; \
#    check-temp!65!75!1!/usr/local/netsaint/etc/digitemp.conf
#    (fold into one line)
#    65 is the warning temperature
#    75 is the critical temperature
#    1 is the sensor # (as reported by digitemp -a) to monitor
#    digitemp.conf is the path to the config file
#
# 6. If you use Centigrade instead of Fahrenheit, change the commands.cfg
#    line to include the -C argument. You can then pass temperature limits in
#    Centigrade in the service line.
#
# ===========================================================================
# Howto Install in Nagios (tested with v1.0b4)
#
# 1. Copy this script to /usr/local/nagios/libexec/ or wherever you have
#    placed your Nagios plugins
#
# 2. Create a digitemp config file in /usr/local/nagios/etc/
#    eg. digitemp -i -s/dev/ttyS0 -c /usr/local/nagios/etc/digitemp.conf
#
# 3. Make sure that the webserver user has permission to access the serial
#    port being used.
#
# 4. Add a command to /usr/local/nagios/etc/checkcommands.cfg like this:
#
#    #DigiTemp temperature check command
#    define command{
#        command_name    check_temperature
#        command_line    $USER1$/check_digitemp.pl -w $ARG1$ -c $ARG2$ \
#        -t $ARG3$ -f $ARG4$
#    (fold above into one line)
#        }
#
# 5. Tell NetSaint to monitor the temperature by adding a service line like
#    this to your service.cfg file:
#
#    #DigiTemp Temperature check Service definition
#    define service{
#        use                         generic-service
#        host_name                       kermit
#        service_description             Temperature
#        is_volatile                     0
#        check_period                    24x7
#        max_check_attempts              3
#        normal_check_interval           5
#        retry_check_interval            2
#        contact_groups                  home-admins
#        notification_interval           240
#        notification_period             24x7
#        notification_options            w,u,c,r
#        check_command                   check_temperature!65!75!1!  \
#        /usr/local/nagios/etc/digitemp.conf
#        (fold into one line)
#        }
#
#    65 is the warning temperature
#    75 is the critical temperature
#    1 is the sensor # (as reported by digitemp -a) to monitor
#    digitemp.conf is the path to the config file
#
# 6. If you use Centigrade instead of Fahrenheit, change the checkcommands.cfg
#    line to include the -C argument. You can then pass temperature limits in
#    Centigrade in the service line.
#
# ===========================================================================

# Modules to use
use strict;
use Getopt::Std;

# Define all our variable usage
use vars qw($opt_c $opt_f $opt_t $opt_w $opt_F $opt_C
	    $temperature $conf_file $sensor $temp_fmt
	    $crit_level $warn_level $null
            %exit_codes
            $percent $fmt_pct 
            $verb_err $command_line);


# Predefined exit codes for NetSaint
%exit_codes   = ('UNKNOWN' ,-1,
		      'OK'      , 0,
                      'WARNING' , 1,
                      'CRITICAL', 2,);

# Default to Fahrenheit input and result (use -C to change this)
$temp_fmt = 3;


# Get the options
if ($#ARGV le 0)
{
  &usage;
} else {
  getopts('f:t:FCc:w:');
}

# Shortcircuit the switches
if (!$opt_w or $opt_w == 0 or !$opt_c or $opt_c == 0)
{
  print "*** You must define WARN and CRITICAL levels!";
  &usage;
}

# Check if levels are sane
if ($opt_w >= $opt_c)
{
  print "*** WARN level must not be greater than CRITICAL when checking temperature!";
  &usage;
}


$warn_level   = $opt_w;
$crit_level   = $opt_c;

# Default sensor to read is #0
if(!$opt_t)
{
  $sensor = 0;
} else {
  $sensor = $opt_t;
}

# Default config file is /etc/digitemp.conf
if(!$opt_f)
{
  $conf_file = "/etc/digitemp.conf";
} else {
  $conf_file = $opt_f;
}

# Check for config file
if( !-f $conf_file ) {
  print "*** You must have a digitemp.conf file\n";
  &usage;
}


if($opt_C)
{
  $temp_fmt = 2;
}

# Read the output from digitemp
# Output in form 0\troom\tattic\tdrink
open( DIGITEMP, "/usr/local/bin/digitemp -c $conf_file -t $sensor -q -o $temp_fmt |" );

# Process the output from the command
while( <DIGITEMP> )
{
#  print "$_\n";
  chomp;

  if( $_ =~ /^nanosleep/i )
  {
    print "Error reading sensor #$sensor\n";
    close(DIGITEMP);
    exit $exit_codes{'UNKNOWN'};
  } else {
    # Check for an error from digitemp, and report it instead
    if( $_ =~ /^Error.*/i ) {
      print $_;
      close(DIGITEMP);
      exit $exit_codes{'UNKNOWN'};
    } else {
      ($null,$temperature) = split(/\t/);
    }
  }
}
close( DIGITEMP );

if( $temperature and $temperature >= $crit_level )
{
  print "Temperature CRITICAL - Sensor #$sensor = $temperature ";
  if( $temp_fmt == 3 ) { print "F\n"; } else { print "C\n"; }
  exit $exit_codes{'CRITICAL'};
} elsif ($temperature and $temperature >= $warn_level ) {
  print "Temperature WARNING - Sensor #$sensor = $temperature ";
  if( $temp_fmt == 3 ) { print "F\n"; } else { print "C\n"; }
  exit $exit_codes{'WARNING'};
} elsif( $temperature ) {
  print "Temperature OK - Sensor #$sensor = $temperature ";
  if( $temp_fmt == 3 ) { print "F\n"; } else { print "C\n"; }
  exit $exit_codes{'OK'};
} else {
    print "Error parsing result for sensor #$sensor\n";
    exit $exit_codes{'UNKNOWN'};  
}

# Show usage
sub usage()
{
  print "\ncheck_digitemp.pl v1.0 - NetSaint Plugin\n";
  print "Copyright 2002 by Brian C. Lane <bcl\@brianlane.com>\n";
  print "See source for License\n";
  print "usage:\n";
  print " check_digitemp.pl -t <sensor> -f <config file> -w <warnlevel> -c <critlevel>\n\n";
  print "options:\n";
  print " -f               DigiTemp Config File\n";
  print " -t               DigiTemp Sensor #\n";
  print " -F               Temperature in Fahrenheit\n";
  print " -C               Temperature in Centigrade\n";
  print " -w temperature   temperature >= to warn\n";
  print " -c temperature   temperature >= when critical\n";

  exit $exit_codes{'UNKNOWN'}; 
}

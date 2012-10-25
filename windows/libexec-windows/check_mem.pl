#!/usr/bin/perl -w
# $Id: check_mem.pl 2 2002-02-28 06:42:51Z egalstad $

# check_mem.pl Copyright (C) 2000 Dan Larsson <dl@tyfon.net>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# you should have received a copy of the GNU General Public License
# along with this program (or with Nagios);  if not, write to the
# Free Software Foundation, Inc., 59 Temple Place - Suite 330,
# Boston, MA 02111-1307, USA

# Tell Perl what we need to use
use strict;
use Getopt::Std;

use vars qw($opt_c $opt_f $opt_u $opt_w
	    $free_memory $used_memory $total_memory
	    $crit_level $warn_level
            %exit_codes @memlist
            $percent $fmt_pct 
            $verb_err $command_line);

# Predefined exit codes for Nagios
%exit_codes   = ('UNKNOWN' ,-1,
		 'OK'      , 0,
                 'WARNING' , 1,
                 'CRITICAL', 2,);

# Turn this to 1 to see reason for parameter errors (if any)
$verb_err     = 0;

# This the unix command string that brings Perl the data
$command_line = `vmstat | tail -1 | awk '{print \$4,\$5}'`;

chomp $command_line;
@memlist      = split(/ /, $command_line);

# Define the calculating scalars
$used_memory  = $memlist[0];
$free_memory  = $memlist[1];
$total_memory = $used_memory + $free_memory;

# Get the options
if ($#ARGV le 0)
{
  &usage;
}
else
{
  getopts('c:fuw:');
}

# Shortcircuit the switches
if (!$opt_w or $opt_w == 0 or !$opt_c or $opt_c == 0)
{
  print "*** You must define WARN and CRITICAL levels!" if ($verb_err);
  &usage;
}
elsif (!$opt_f and !$opt_u)
{
  print "*** You must select to monitor either USED or FREE memory!" if ($verb_err);
  &usage;
}

# Check if levels are sane
if ($opt_w <= $opt_c and $opt_f)
{
  print "*** WARN level must not be less than CRITICAL when checking FREE memory!" if ($verb_err);
  &usage;
}
elsif ($opt_w >= $opt_c and $opt_u)
{
  print "*** WARN level must not be greater than CRITICAL when checking USED memory!" if ($verb_err);
  &usage;
}

$warn_level   = $opt_w;
$crit_level   = $opt_c;

if ($opt_f)
{
  $percent    = $free_memory / $total_memory * 100;
  $fmt_pct    = sprintf "%.1f", $percent;
  if ($percent <= $crit_level)
  {
    print "Memory CRITICAL - $fmt_pct% ($free_memory kB) free\n";
    exit $exit_codes{'CRITICAL'};
  }
  elsif ($percent <= $warn_level)
  {
    print "Memory WARNING - $fmt_pct% ($free_memory kB) free\n";
    exit $exit_codes{'WARNING'};
  }
  else
  {
    print "Memory OK - $fmt_pct% ($free_memory kB) free\n";
    exit $exit_codes{'OK'};
  }
}
elsif ($opt_u)
{
  $percent    = $used_memory / $total_memory * 100;
  $fmt_pct    = sprintf "%.1f", $percent;
  if ($percent >= $crit_level)
  {
    print "Memory CRITICAL - $fmt_pct% ($used_memory kB) used\n";
    exit $exit_codes{'CRITICAL'};
  }
  elsif ($percent >= $warn_level)
  {
    print "Memory WARNING - $fmt_pct% ($used_memory kB) used\n";
    exit $exit_codes{'WARNING'};
  }
  else
  {
    print "Memory OK - $fmt_pct% ($used_memory kB) used\n";
    exit $exit_codes{'OK'};
  }
}

# Show usage
sub usage()
{
  print "\ncheck_mem.pl v1.0 - Nagios Plugin\n\n";
  print "usage:\n";
  print " check_mem.pl -<f|u> -w <warnlevel> -c <critlevel>\n\n";
  print "options:\n";
  print " -f           Check FREE memory\n";
  print " -u           Check USED memory\n";
  print " -w PERCENT   Percent free/used when to warn\n";
  print " -c PERCENT   Percent free/used when critical\n";
  print "\nCopyright (C) 2000 Dan Larsson <dl\@tyfon.net>\n";
  print "check_mem.pl comes with absolutely NO WARRANTY either implied or explicit\n";
  print "This program is licensed under the terms of the\n";
  print "GNU General Public License (check source code for details)\n";
  exit $exit_codes{'UNKNOWN'}; 
}

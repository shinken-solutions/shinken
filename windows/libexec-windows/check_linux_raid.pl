#!/usr/bin/perl -w

# Copyright (c) 2002 ISOMEDIA, Inc.
# originally written by Steve Milton
# later updates by sean finney <seanius@seanius.net>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
# Usage:   check_raid [raid-name]
# Example: check_raid md0
#	  WARNING md0 status=[UUU_U], recovery=46.4%, finish=123.0min

use strict;
use lib "/usr/local/nagios/libexec";
use utils qw(%ERRORS);

# die with an error if we're not on Linux
if ($^O ne 'linux') {
    print "This plugin only applicable on Linux.\n";
    exit $ERRORS{'UNKNOWN'};
}

sub max_state($$){
	my ($a, $b) = @_;
	if ($a eq "CRITICAL" || $b eq "CRITICAL") { return "CRITICAL"; } 
	elsif ($a eq "WARNING" || $b eq "WARNING") { return "WARNING"; }
	elsif ($a eq "OK" || $b eq "OK") { return "OK"; }
	elsif ($a eq "UNKNOWN" || $b eq "UNKNOWN") { return "UNKNOWN"; }
	elsif ($a eq "DEPENDENT" || $b eq "DEPENDENT") { return "DEPENDENT"; }
	return "UNKNOWN";
}

my $nextdev;
if(defined $ARGV[0]) { $nextdev = shift; }
else { $nextdev = "md[0-9]+"; }

my $code = "UNKNOWN";
my $msg = "";
my %status;
my %recovery;
my %finish;
my %active;
my %devices;

while(defined $nextdev){
	open (MDSTAT, "< /proc/mdstat") or die "Failed to open /proc/mdstat";
	my $device = undef;
	while(<MDSTAT>) {
		if (defined $device) {
			if (/(\[[_U]+\])/) {
				$status{$device} = $1;
			} elsif (/recovery = (.*?)\s/) {  
				$recovery{$device} = $1;
				($finish{$device}) = /finish=(.*?min)/;
				$device=undef;
			} elsif (/^\s*$/) {
				$device=undef;
			}
		} elsif (/^($nextdev)\s*:/) {
			$device=$1;
			$devices{$device}=$device;
			if (/\sactive/) {
				$status{$device} = ''; # Shall be filled later if available
				$active{$device} = 1;
			}
		}
	}
	$nextdev = shift;
}

foreach my $k (sort keys %devices){
	if (!exists($status{$k})) {
		$msg .= sprintf " %s inactive with no status information.",
			$devices{$k};
		$code = max_state($code, "CRITICAL");
	} elsif ($status{$k} =~ /_/) {
		if (defined $recovery{$k}) {
			$msg .= sprintf " %s status=%s, recovery=%s, finish=%s.",
				$devices{$k}, $status{$k}, $recovery{$k}, $finish{$k};
			$code = max_state($code, "WARNING");
		} else {
			$msg .= sprintf " %s status=%s.", $devices{$k}, $status{$k};
			$code = max_state($code, "CRITICAL");
		}
	} elsif ($status{$k} =~ /U+/) {
		$msg .= sprintf " %s status=%s.", $devices{$k}, $status{$k};
		$code = max_state($code, "OK");
	} else {
		if ($active{$k}) {
			$msg .= sprintf " %s active with no status information.",
				$devices{$k};
			$code = max_state($code, "OK");
		} else {
			# This should't run anymore, but is left as a catch-all
			$msg .= sprintf " %s does not exist.\n", $devices{$k};
			$code = max_state($code, "CRITICAL");
		}
	}
}

print $code, $msg, "\n";
exit ($ERRORS{$code});


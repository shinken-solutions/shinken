#!/usr/bin/perl -w
#
# check_snmp_procs.pl
#    Nagios script to check processes on remote host via snmp
#
# 
# Copyright (c) 2003 David Alden
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
# History
# -------
#  02-25-2003 - Dave Alden <alden@math.ohio-state.edu>
#    Initial creation
#
#
# TODO
# ----
#    make it work with snmp version 3
#    Suggestions???
#
#use strict;
use Getopt::Long;
use Net::SNMP qw (oid_lex_sort oid_base_match SNMP_VERSION_1);
use lib "/usr/local/nagios/libexec";
use utils qw(%ERRORS &print_revision &support &usage);

my $PROGNAME="check_snmp_procs";
my $REVISION="1.0";

#
my $opt_authprotocol;
my $opt_authpassword;
my $opt_community    = 'ma4read';
my $opt_critical;
my $opt_help;
my $opt_host         = 'euler';
my $opt_oidname      = 'hrSWRunName';
my $opt_port         = 161;
my $opt_privpassword;
my $opt_regexp       = 0;
my $opt_snmp_version = '2c';
my $opt_timeout      = $utils::TIMEOUT;
my $opt_username;
my $opt_verbose;
my $opt_version;
my $opt_wanted_procs;
my $opt_warning;

#
my $max_no_processes = 999999;
my $session;
my $error;
my $no_procs;
my $exit_status;

#
my @wanted_procs;
my %current_process_list;

#
my %OIDS = (hrSWRunName => '1.3.6.1.2.1.25.4.2.1.2',
	    hrSWRunPath => '1.3.6.1.2.1.25.4.2.1.4');

my %OIDS_L = (hrSWRunName => length($OIDS{hrSWRunName}),
	      hrSWRunPath => length($OIDS{hrSWRunPath}));

#
$ENV{'PATH'}='';
$ENV{'BASH_ENV'}=''; 
$ENV{'ENV'}='';

#
Getopt::Long::Configure('bundling');
if (GetOptions(
	"a:s" => \$opt_authprotocol,  "authprotocol:s"  => \$opt_authprotocol,
	"A:s" => \$opt_authpassword,  "authpassword:s"  => \$opt_authpassword,
	"C:s" => \$opt_community,     "community:s"     => \$opt_community,
        "c:s" => \$opt_critical,      "critical:s"      => \$opt_critical,
	"h"   => \$opt_help,          "help"	        => \$opt_help,
	"H:s" => \$opt_host,          "hostname:s"      => \$opt_host,
	"o:s" => \$opt_oidname,       "oidname:s"       => \$opt_oidname,
	"P=s" => \$opt_password,      "password=s"      => \$opt_password,
	"p=i" => \$opt_port,          "port=i"          => \$opt_port,
	"r"   => \$opt_regexp,        "regexp"          => \$opt_regexp,
	"S"   => \$opt_snmp_version,  "snmpversion"     => \$opt_snmp_version,
	"t=i" => \$opt_timeout,       "timeout=i"       => \$opt_timeout,
	"U=s" => \$opt_username,      "username=s"      => \$opt_username,
	"v"   => \$opt_verbose,       "verbose"         => \$opt_verbose,
	"V"   => \$opt_version,       "version"         => \$opt_version,
	"N=s" => \$opt_wanted_procs,  "names=s"         => \$opt_wanted_procs,
        "w:s" => \$opt_warning,       "warning:s"       => \$opt_warning)
    == 0) {
	print_usage();
	exit $ERRORS{'UNKNOWN'};
}

if ($opt_version) {
	print_revision($PROGNAME, "\$Revision: 1771 $REVISION \$");
	exit $ERRORS{'OK'};
}

if ($opt_help) {
	print_help();
	exit $ERRORS{'OK'};
}

if (! utils::is_hostname($opt_host)){
	usage();
	exit $ERRORS{'UNKNOWN'};
}

($longest_wanted, @wanted_procs) = parse_wanted_procs($opt_verbose, $opt_wanted_procs, $opt_warning, $opt_critical);

$SIG{'ALRM'} = sub {
	print "Timeout: No Answer from Client\n";
	exit $ERRORS{'UNKNOWN'};
};
alarm($opt_timeout);

($longest_current, %current_process_list) = get_process_list($opt_verbose, $opt_host, $opt_username, $opt_privpassword, $opt_authprotocol, $opt_authpassword, $opt_community, $opt_port, $opt_oidname, $opt_snmp_version);

$exit_status = compare_process_list($opt_regexp, \%current_process_list, @wanted_procs);

if ($opt_verbose) {
	print_info($longest_current, \%current_process_list, $longest_wanted, @wanted_procs);
}

exit($exit_status);


#
sub compare_process_list {

	my($regexp, $current_process_list, @wanted_procs) = @_;
	my($proc, $i, $no_running_procs, @warning, @critical);
	my $exit = $ERRORS{'OK'};

	for ($i = 0; $i <= $#wanted_procs; $i++) {

		$proc = $wanted_procs[$i];

		$no_running_procs = get_running_procs($regexp, $$proc{name}, $current_process_list);

		$$proc{no_matches} += $no_running_procs;

		if (($no_running_procs >= $$proc{warn_low}) &&
		    ($no_running_procs <= $$proc{warn_high})) {

			push(@warning, $$proc{name} . "($no_running_procs)");

			if ($exit != $ERRORS{'CRITICAL'}) {
				$exit = $ERRORS{'WARNING'};
			}

		} elsif (($no_running_procs < $$proc{minimum}) ||
			 ($no_running_procs >= $$proc{critical_low}) &&
			 ($no_running_procs <= $$proc{critical_high})) {

			push(@critical, $$proc{name} . "($no_running_procs)");

			$exit = $ERRORS{'CRITICAL'};
		}
	}

	print "SNMPPROC ";

	if ($#critical >= 0) {
		print "CRITICAL:";
	} elsif ($#warning >= 0) {
		print "WARNING:";
	} else {
		print "OK";
	}

	foreach $i (@critical) {
		print " $i";
	}

	if (($#critical >= 0) &&
	    ($#warning >= 0)) {
		print "  WARNING:";
	}

	foreach $i (@warning) {
		print " $i";
	}

	print "\n";

	return $exit;
}


#
sub get_running_procs {

	my($regex, $name, $process_list) = @_;
	my $count = 0;
	my $process;

	$count = 0;

	if ($regex) {

		foreach $process (keys %{$process_list}) {

			if ($process =~ /$name/) {
				$count += $$process_list{$process};
			}
		}


	} else {

		if (!defined($count = $$process_list{$name})) {
			$count = 0;
		}
	}

	return $count;
}


#
sub get_process_list {

	my($verbose, $host, $username, $privpassword, $authprotocol, $authpassword, $community, $port, $oidname, $snmp_version) = @_;
	my(%process_list, %process_pid_list, $result);
	my $process_list_longest = 1, $not_done = 1;
	my(@args, @oids, $oid, $name);

	($session, $error) = Net::SNMP->session(
		-hostname      =>  $host,
		-community     =>  $community,
		-port	       =>  $port,
		-version       =>  $snmp_version,
		defined($privpassword) ? (-privpassword  =>  $privpassword) : (),
		defined($authpassword) ? (-authpassword  =>  $authpassword) : (),
		defined($authprotocol) ? (-authprotocol  =>  $authprotocol) : (),
		defined($username)     ? (-username      =>  $username) : ());

	if (!defined($session)) {
		print ("UNKNOWN: $error\n");
		exit $ERRORS{'UNKNOWN'};
	}

	@args = (-varbindlist => [$OIDS{$oidname}]);

	if ($session->version == SNMP_VERSION_1) {

		while (defined($session->get_next_request(@args))) {

			$oid = (keys(%{$session->var_bind_list}))[0];

			last if (!oid_base_match($OIDS{$oidname}, $oid));

			$name = $session->var_bind_list->{$oid};
			$process_list{$name}++;

			if ($verbose && ($process_list_longest < length($name))) {
				$process_list_longest = length($name);
			}

			@args = (-varbindlist => [$oid]);
		}

	} else {

		push(@args, -maxrepetitions => 25);

		while ($not_done && defined($session->get_bulk_request(@args))) {

			@oids = oid_lex_sort(keys(%{$session->var_bind_list}));

			foreach $oid (@oids) {
				if (!oid_base_match($OIDS{$oidname}, $oid)) {

					$not_done = 0;

				} else {

					$name = $session->var_bind_list->{$oid};
					$process_list{$name}++;

					if ($verbose && ($process_list_longest < length($name))) {
						$process_list_longest = length($name);
					}

					if ($session->var_bind_list->{$oid} eq 'endOfMibView') {
						$not_done = 0;
					}
				}
			}

			if ($not_done) {
				@args = (-maxrepetitions => 25, -varbindlist => [pop(@oids)]);
			}
		}
	}

	if ($session->error() ne '') {
		print ("UNKNOWN: " . $session->error() . "\n");
		exit $ERRORS{'UNKNOWN'};
	}

	$session->close;

	return($process_list_longest, %process_list);
}


#
sub parse_wanted_procs {

	my($verbose, $wanted_procs, $warning, $critical) = @_;

	my(@procs, $process, $i, $critical_low, $critical_high, $warn_low, $warn_high, $process_name, $process_min);
	my(@process_array, @warn_array, @critical_array);
	my $exit = 0;
	my $longest_name = 1;

	if (defined($wanted_procs)) {
		@process_array = split(/,/, $wanted_procs);
	}

	if (defined($warning)) {
		@warn_array = split(/,/, $warning);
	}

	if (defined($critical)) {
		@critical_array = split(/,/, $critical);
	}

	if( defined($warning) && $#process_array != $#warn_array ) {

		print "Error: Number of entries in process list($#process_array) and warn list($#warn_array) don't match\n";
		exit $ERRORS{'UNKNOWN'};
	}

	if( defined($critical) && $#process_array != $#critical_array ) {

		print "Error: Number of entries in process list and critical list don't match\n";
		exit $ERRORS{'UNKNOWN'};
	}

	for ($i = 0; $i <= $#process_array; $i++) {

		if ((($process_name, $process_min) = split(/:/, $process_array[$i])) != 2) {

			$process_min = 1;
		}

		if ($verbose && ($longest_name < length($process_name))) {

			$longest_name = length($process_name);
		}

		if (defined($critical_array[$i])) {
			if ((($critical_low, $critical_high) = split(/:/, $critical_array[$i])) != 2) {

				$critical_high = $critical_low;

			} else {

				if ($critical_high eq "") {
					$critical_high = $max_no_processes;
				}

				if ($critical_low eq "") {
					$critical_low = 0;
				}
			}
		} else {

			$critical_low = -1;
			$critical_high = -1;
		}

		if (defined($warn_array[$i])) {
			if ((($warn_low, $warn_high) = split(/:/, $warn_array[$i])) != 2) {

				$warn_high = $warn_low;

			} else {

				if ($warn_high eq "") {
					$warn_high = $max_no_processes;
				}

				if ($warn_low eq "") {
					$warn_low = 0;
				}
			}
		} else {

			$warn_low = -1;
			$warn_high = -1;
		}

		if ($critical_low > $critical_high) {
			print "Error: $process_name critical low($critical_low) is larger than high($critical_high)\n";
			$exit = 1;
		}

		if ($warn_low > $warn_high) {
			print "Error: $process_name warn low($warn_low) is larger than high($warn_high)\n";
			$exit = 1;
		}

		if (@critical_array &&
		    ($process_min > $critical_low)) {
			print "Error: $process_name minimum($process_min) is larger than critical low($critical_low)\n";
			$exit = 1;
		}

		if (@warn_array &&
		    ($process_min > $warn_low)) {
			print "Error: $process_name minimum($process_min) is larger than warn low($warn_low)\n";
			$exit = 1;
		}

		if (@warn_array && @critical_array &&
		    ((($warn_low >= $critical_low) && ($warn_low <= $critical_high)) ||
		     (($warn_high >= $critical_low) && ($warn_high <= $critical_high)))) {

			print "Error: $process_name warn levels($warn_low:$warn_high) overlap with critical levels($critical_low:$critical_high)\n";
			$exit = 1;
		}

		push(@procs,{
			name          => $process_name,
			critical      => defined($critical),
			critical_low  => $critical_low,
			critical_high => $critical_high,
			minimum	      => $process_min,
			warning       => defined($warning),
			warn_low      => $warn_low,
			warn_high     => $warn_high});
	}

	if ($exit) {
		exit $ERRORS{'UNKNOWN'};
	}

	return($longest_name, @procs);
}


#
sub print_info {

	my ($longest_current, $current_process_list, $longest_wanted, @wanted_procs) = @_;

	if ($longest_wanted < 7) {
		$longest_wanted = 7;
	} else {
		$longest_wanted++;
	}

	printf("%s---------------------------------------------\n", "-" x $longest_wanted);
	printf("|%-" . $longest_wanted . "s |      |  Min |     Warn    |   Critical  |\n", "Process");
	printf("|%-" . $longest_wanted . "s | Qty  | Procs|  Low | High |  Low | High |\n", "Name");
	printf("%s---------------------------------------------\n", "-" x $longest_wanted);

	for (my $temp=0; $temp <= $#wanted_procs; $temp++) {

		printf("|%-" . $longest_wanted . "s |%6d|%6d|%6d|%6d|%6d|%6d|\n",
			$wanted_procs[$temp]{name},
			$wanted_procs[$temp]{no_matches},
			$wanted_procs[$temp]{minimum},
			$wanted_procs[$temp]{critical_low},
			$wanted_procs[$temp]{critical_high},
			$wanted_procs[$temp]{warn_low},
			$wanted_procs[$temp]{warn_high});
	}

	printf("%s---------------------------------------------\n\n", "-" x $longest_wanted);

	if ($longest_current < 7) {
		$longest_current = 7;
	} else {
		$longest_current++;
	}

	printf("%s----------\n", "-" x $longest_current);
	printf("|%-" . $longest_current . "s |  Qty |\n", "Process");
	printf("%s----------\n", "-" x $longest_current);

	foreach my $result (sort keys %{$current_process_list}) {

		printf("|%-" . $longest_current . "s |%6d|\n", $result,
			$current_process_list{$result});
	}
	printf("%s----------\n", "-" x $longest_current);

	return;
}


#
sub print_usage {
    print "Usage:
 $PROGNAME -H <host> [-r] [-v]
		  -N <processname>[:minimum][,<processname>[:minimum] ...]
		  [-a <authprotocol>] [-A <authpassword>]
		  [-U <username>] [-P <password>]
		  [-o <oidname>] [ -S <snmpversion> ]
		  [-C <snmp_community>] [-p <port>] [-t <timeout>]
		  [-w <low>:<high>[,<low>:<high> ...]
		  [-c <low>:<high>[,<low>:<high> ...]
       $PROGNAME (-h | --help) for detailed help
       $PROGNAME (-V | --version) for version information\n";
}


#
sub print_help {
	print_revision($PROGNAME, "\$Revision: 1771 $REVISION \$");
	print "Copyright (c) 2003 David Alden

Check if processes are running on a host via snmp

";

	print_usage();

	print "
-a, --authprotocol=<authprotocol>
   Set the authentication protocol used for authenticated SNMPv3 messages
-A, --authpassword=<authpassword>
   Set the authentication pass phrase used for authenticated SNMPv3 messages
-c, --critical=<low>:<high>[,<low>:<high> ...]
   exit with CRITICAL status if number of processes is between <low> and <high>
-C, --community=<snmp_community>
   SNMP read community (default: $opt_community)
-h, --help
   Show this help screen
-H, --host=<host>
   Check processes on the indiciated host
-o, --oidname=<oidname>
   Which oid tree to search, hrSWRunName or hrSWRunPath (default: $opt_oidname)
-p, --port=<port>
   Make connection on the indicated port (default: $opt_port)
-N, --names=<processname>[:<minimum>][,<processname>[:<minimum>] ...]
   Process names to check, (optional) minimum number of processes (default: 1)
-P, --password=<privpassword>
   Set the privacy pass phrase used for encrypted SNMPv3 messages
-r, --regex
   Use regular expression match for <process>
-S, --snmpversion
   Use snmp version specified (values: 1|2c|3, default: $opt_snmp_version)
-t, --timeout
   Plugin time out in seconds (default: $opt_timeout)
-U, --username=<securityname>
   Set the securityname used for encrypted SNMPv3 messages
-v, --verbose
   Print some extra debugging information (not advised for normal operation)
-V, --version
   Show version and license information
-w, --warning=<low>:<high>[,<low>:<high> ...]
   exit with WARNING status if number of processes is between <low> and <high>


A CRITICAL error will be indicated unless there are at least <minimum> number
of processes running (unless <minimum> is set to 0 -- useful if you don't
mind that there are none of the processes running).

If no processes are specified, the program will still connect to the remote
host and download the current list of running processes.  It will then exit
with an OK (unless it wasn't able to connect) -- useful if you want to make
sure that the remote snmpd process is running and returning a list of procs.


";
	support();
}

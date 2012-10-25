#!/usr/bin/perl -w

# chec_smart
# Check S.M.A.R.T. enabled disks status.
#
# This uses smartmontools to check for disk status.
# This is NOT compatible with smartsuite
# Please use smartctl --smart=on --offlineauto=on --saveauto=on /dev/something
# or similar to enable automatic data collection, and RTFM about it.
#
# this uses sudo to access the smartctl program, so please add a line in sudoers
# nagios  computername = NOPASSWD:/usr/sbin/smartctl
#
# CopyLeft Roy Sigurd Karlsbakk <roy@karlsbakk.net>
# Developed under Debian/SID
# No warranties what so ever. If this toasts your PC, or your wife
# runs away with your girlfriend, or even me, don't blame me.
#
# Licenced under GPL
#

use strict;
use Getopt::Long;

my (
	$s, $i, $out, $retcode, $errtxt, $exitcode,
	$device, $text_mode, $exitcode_mode, $help, $verbose, $type,
);
my $smartctl = "sudo /usr/sbin/smartctl";
my $e_commandline = 0;
my $e_devopen = 0;
my $e_chksum = 0;
my $e_disk_failing = 0;
my $e_prefail = 0;
my $e_mayprefail = 0;
my $e_errlog = 0;
my $e_selftestlog = 0;

sub end {
	$s = shift;
	$i = shift;
	if ($i == 0) {
		$s = "OK: $s";
	} elsif ($i == 1) {
		$s = "WARNNG: $s";
	} elsif ($i == 2) {
		$s = "CRITICAL: $s";
	} elsif ($i == 3) {
		$s = "UNKNOWN: $s";
	} else {
		$s = "OUT OF RANGE: $s";
	}
	print "$s\n";
	exit($i);
}

sub syntax {
	$s = shift or $s = 'Unknown';
	printf STDERR ("Error: $s\n") unless ($help);
	printf STDERR ("Syntax: %s (-t|-e) -d <device> [-vh]\n", $0);
	printf STDERR ("  --text-mode -t        check by parsing smartctl's output\n");
	printf STDERR ("  --exitcode-mode -e    check smartctl's exitcode (only works on IDE)\n");
	printf STDERR ("  --device -d           disk device to check\n");
	printf STDERR ("  --type -T             drive type. See the -d flag in the smartctl manual\n");
	printf STDERR ("  --verbose -v          verbose\n");
	printf STDERR ("  --help -h             this help\n");
	exit(0) if $help;
	exit(3);
}

Getopt::Long::Configure('bundling');
GetOptions(
	"d=s" => \$device, "device=s" => \$device,
	"T=s" => \$type, "type=s" => \$type,
	"t" => \$text_mode, "text-mode" => \$text_mode,
	"e" => \$exitcode_mode, "exitcode-mode" => \$exitcode_mode,
	"h" => \$help, "help" => \$help,
	"v" => \$verbose, "verbose" => \$verbose
) || syntax("RTFM!");

syntax if ($help);
syntax("Need device to check") unless ($device);
syntax("Conflicting modes") if ($text_mode && $exitcode_mode);
syntax("Need test mode") unless ($text_mode || $exitcode_mode);
syntax("Exitcode mode only works on ATA drives") if ($exitcode_mode && ! ($device =~ /\/dev\/hd./));

if ($type) {
	$type =~ s/[\r\n]*?//g;
	print "type: '$type'\n" if ($verbose);
	syntax("Valid --type entries include ata, scsi and 3ware,n")
		unless (($type =~ /^ata$/) || ($type =~ /^scsi$/) || ($type =~ /^3ware,\d+$/));
}
if (defined($type)) {
	$type = "--device=$type";
} else {
	$type = "";
}

if ($text_mode) {
	print "running $smartctl $type -H $device" if ($verbose);
	unless (open SMARTCTL,"$smartctl $type -H $device|") {
		print STDERR "Can't execute $smartctl: $!\n";
		exit(3);
	}
	while (<SMARTCTL>) {
		last if (/=== START OF READ SMART DATA SECTION ===/);
	}
	$out = <SMARTCTL>;
	print $out;
	exit(0) if ($out =~ /PASSED/);
	exit(2) if ($out =~ /SAVE ALL DATA/ || $out =~ /FAILED/);
	exit(3);
} elsif ($exitcode_mode) {
	print "Running $smartctl $type -q silent $device\n" if ($verbose);
	system("$smartctl $type -q silent $device");
	$retcode = $?;
	$e_commandline = 1 if ($retcode & 0x0100);
	$e_devopen = 1 if ($retcode & 0x0200);
	$e_chksum = 1 if ($retcode & 0x0400);
	$e_disk_failing = 1 if ($retcode & 0x0800);
	$e_prefail = 1 if ($retcode & 0x1000);
	$e_mayprefail = 1 if ($retcode & 0x2000);
	$e_errlog = 1 if ($retcode & 0x4000);
	$e_selftestlog = 1 if ($retcode & 0x8000);

	print "$e_commandline $e_devopen $e_chksum $e_disk_failing $e_prefail $e_mayprefail $e_errlog $e_selftestlog\n"
		if ($verbose);

	$exitcode = 0;
	$errtxt = "";
	if ($exitcode) {
		if ($e_commandline) {
			$errtxt .= "Commandline didn't parse, ";
			$exitcode = 3 if ($exitcode == 0);
		}
		if ($e_devopen) {
			$errtxt .= "Device could not be opened, ";
			$exitcode = 3 if ($exitcode == 0);
		}
		if ($e_chksum) {
			$errtxt .= "Checksum failure somewhere, ";
			$exitcode = 1 if ($exitcode != 2);
		}
		if ($e_disk_failing) {
			$errtxt .= "Disk is failing!, ";
			$exitcode = 2;
		}
		if ($e_prefail) {
			$errtxt .= "Disk is in prefail, ";
			$exitcode = 1 if ($exitcode != 2);
		}
		if ($e_mayprefail) {
			$errtxt .= "Disk is close to prefail. Please check manually, ";
			$exitcode = 1 if ($exitcode != 2);
		}
		if ($e_errlog) {
			$errtxt .= "The device error log contains records of errors, ";
			$exitcode = 1 if ($exitcode != 2);
		}
		if ($e_selftestlog) {
			$errtxt .= "The device self-test log contains records of errors, ";
			$exitcode = 1 if ($exitcode != 2);
		}
		if ($exitcode == 1) {
			$errtxt = "WARNNG: $errtxt";
		} elsif ($exitcode == 2) {
			$errtxt = "CRITICAL: $errtxt";
		} else {
			$errtxt = "UNKNOWN: $errtxt";
		}
	} else {
		$errtxt = "OK";
	}
	print "$errtxt\n";
	exit($exitcode);
} else {
	print STDERR "Something's strange is going on :~|\n";
	exit(3);
}
# vim:ts=4:sw=4:cindent

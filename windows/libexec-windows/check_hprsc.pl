#!/usr/bin/perl -wT
#
# Copyright (c) 2000 Hugo Gayosso
#
# Description:
#    Nagios plug-in that monitors the resources on an HP-UX machine
#    by querying the SNMP daemon
#
# License: General Public License (GPL)
#          http://www.gnu.org/copyleft/gpl.txt
#
# ChangeLog
#

# Requirements: Perl 5.005 or higher

# Variable initialization
$ENV{'PATH'}="";
$ENV{'ENV'}="";
$ENV{'BASH_ENV'}="";


if (-e "/usr/bin/snmpwalk") {
  $snmpwalk = "/usr/bin/snmpwalk";
} elsif (-e "/usr/local/bin/snmpwalk") {
  $snmpwalk = "/usr/local/bin/snmpwalk";
}


# HP-UX SNMP OIDs
$filesystemID1_OID   = ".1.3.6.1.4.1.11.2.3.1.2.2.1.1";
$mounted_OID         = ".1.3.6.1.4.1.11.2.3.1.2.2.1.3";
$totalspace_OID      = ".1.3.6.1.4.1.11.2.3.1.2.2.1.4";
$freespace_OID       = ".1.3.6.1.4.1.11.2.3.1.2.2.1.6";
$path_OID            = ".1.3.6.1.4.1.11.2.3.1.2.2.1.10";
$cpu_5min_OID        = ".1.3.6.1.4.1.11.2.3.1.1.4";

use Getopt::Long;

GetOptions( "check-filesystem"   => \$chk_fs,
	    "show-filesystems"   => \$show_fs,
	    "check-filesystemID" => \$chk_fsid,
	    "check-cpu"          => \$chk_cpu,
	    "host=s"             => \$target_host,
	    "community=s"        => \$target_community,
	    "filesystemID1=i"    => \$fsid1_opt,
	    "filesystem=s"       => \$fs_opt,
	    "protocol:s"          => \$proto_opt,
	    "warning=i"          => \$warning_opt,
            "critical=i"         => \$critical_opt);

$proto_opt = 1
  unless $proto_opt == 1	||
         $proto_opt == '2c'	||
         $proto_opt == 3;

if ($chk_fs) {
    walk_data($snmpwalk, $target_host, $target_community, $mounted_OID,$proto_opt );
    walk_data($snmpwalk, $target_host, $target_community, $totalspace_OID,$proto_opt );
    walk_data($snmpwalk, $target_host, $target_community, $freespace_OID,$proto_opt );    check_filesystem($fs_opt, $warning_opt, $critical_opt);
} elsif ($show_fs) {
    walk_data($snmpwalk, $target_host, $target_community, $filesystemID1_OID,$proto_opt);
    walk_data($snmpwalk, $target_host, $target_community, $mounted_OID,$proto_opt );
    walk_data($snmpwalk, $target_host, $target_community, $path_OID,$proto_opt);
    show_filesystem();
} elsif ($chk_fsid){
    $totalspace_fsID_OID = "$totalspace_OID.$fsid1_opt";
    $freespace_fsID_OID = "$freespace_OID.$fsid1_opt";
    walk_data($snmpwalk, $target_host, $target_community, $totalspace_fsID_OID,$proto_opt);
    walk_data($snmpwalk, $target_host, $target_community, $freespace_fsID_OID,$proto_opt);
    check_filesystemID1($fsid1_opt, $warning_opt, $critical_opt);
} elsif ($chk_cpu) {
    get_cpu_load($snmpwalk, $target_host, $target_community, $cpu_5min_OID,$proto_opt);
    check_cpu_5min($cpu, $warning_opt, $critical_opt);
} else {
    print "\n\nUsage:\n";
    print "Checking 5-min CPU Load:\n";
    print "     $0 --check-cpu -warning <threshold> --critical <threshold> --host <yourhost> --community <SNMP community> --protocol <SNMP version [1|2c|3]>\n\n";
    print "Checking local filesystem mounted on a host:\n";
    print "     $0 --show-filesystems --host <hostname> --community <SNMP community> --protocol <SNMP version [1|2c|3]>\n\n";
    print "Checking by filesystem name:\n";
    print "     $0 --check-filesystem --filesystem </dev/vg00/lvol1> --warning <% used space> --critical <% used space> --host <hostname> --community <SNMP community> --protocol <SNMP version [1|2c|3]>\n\n";
    print "Checking by filesystem ID:\n";
    print "     $0 --check-filesystemID --filesystemID <filesystemID1> --warning <% used space> --critical <% used space> --host <hostname> --community <SNMP community> --protocol <SNMP version [1|2c|3]>\n\n";
}

sub get_cpu_load {
    my ($snmpwalk, $target_host, $target_community, $OID,$vers) = @_;
    die "cannot fork: $!" unless defined($pid = open(SNMPWALK, "-|"));

    if ($pid) {   # parent
	while (<SNMPWALK>) {
	    my @snmpdata = split(/:/,$_);
	    $cpu = $snmpdata[1]/100;
	}
	close(SNMPWALK) or warn "kid exited $?";
    } else {      # child
	exec($snmpwalk,'-c',$target_community,'-v',$vers,$target_host,$OID)  or die "can't exec program: $!";
    }
}

sub walk_data {
#This function queries the SNMP daemon for the specific OID
    my ($snmpwalk, $target_host, $target_community, $OID,$vers) = @_;

    die "cannot fork: $!" unless defined($pid = open(SNMPWALK, "-|"));

    if ($pid) {   # parent
	while (<SNMPWALK>) {
	    $output = $_;
	    sort_walk_data($output);
	}
	close(SNMPWALK) or warn "kid exited $?";
    } else {      # child
	exec($snmpwalk,'-c',$target_community,'-v',$vers,$target_host,$OID)  or die "can't exec program: $!";
    }
}

sub sort_walk_data {
    my ($snmp_data) = @_;
    @fields = split(/\./,$snmp_data);
    $item = $fields[8];
    $filesystemID1 = $fields[9];
    @fields2 = split(/=/,$fields[10]);
#   $filesystemID2 = $fields2[0];
    $value = $fields2[1];
    chomp($value);
    if ($value =~ /"/) {
        @fields3 = split(/"/,$value);
        $value = $fields3[1];
    }
    if ($item == 3) {
	$mounted{$filesystemID1} = "$value";
    } elsif ($item == 4) {
	$totalspace{$filesystemID1} = "$value";
    } elsif ($item == 6) {
	$freespace{$filesystemID1} = "$value";
    } elsif ($item == 10) {
	$filesystempath{$filesystemID1} = "$value";
    }
}

sub show_filesystem {
    print "\n\nfilesystemID1\tmounted filesystem\tfilesystem path\n";
    foreach $element (keys %mounted) {
	print "$element\t$mounted{$element}\t\t$filesystempath{$element}\n";
    }
    print "\n\n";
}

sub check_filesystem {

# Warning  = percentage of used space >= $warning and < $critical
# Critical = percentage of used space > $warning and >= $critical
# OK       = percentage of used space < $warning and < $critical

    my ($mounted_filesystem, $warning, $critical) = @_;
    foreach $element (keys %mounted) {
	if ($mounted{$element} eq $mounted_filesystem) {
	    my $warning_result = $totalspace{$element}*(100-$warning)/100;
	    my $critical_result = $totalspace{$element}*(100-$critical)/100;
	    my $result_percent = $freespace{$element}*100/$totalspace{$element};
	    if (($freespace{$element} <= $warning_result) && ($freespace{$element} > $critical_result)) {
		printf "Only %d M (%d%s) free\n",$freespace{$element}/1024,$result_percent,"%";
		exit 1;
	    } elsif ($freespace{$element} <= $critical_result) {
		printf "Only %d M (%d%s) free\n",$freespace{$element}/1024,$result_percent,"%";
		exit 2;
	    } else {
		printf "Disk ok - %d M (%d%s) free\n",$freespace{$element}/1024,$result_percent,"%";
		exit 0;
	    }
	}
    }
    print "$mounted_filesystem doesn't exist in $target_host\n\n";
    exit -1;
}

sub check_filesystemID1{
# Warning  = percentage of used space >= $warning and < $critical
# Critical = percentage of used space > $warning and >= $critical
# OK       = percentage of used space < $warning and < $critical

    my ($fsid1, $warning, $critical) = @_;
    foreach $element (keys %totalspace) {
	if ($element eq  $fsid1) {
	    my $warning_result = $totalspace{$element}*(100-$warning)/100;
	    my $critical_result = $totalspace{$element}*(100-$critical)/100;
	    my $result_percent = $freespace{$element}*100/$totalspace{$element};
	    if (($freespace{$element} <= $warning_result) && ($freespace{$element} >= $critical_result)) {
		printf "Only %d M (%d%s) free\n",$freespace{$element}/1024,$result_percent,"%";
		exit 1;
	    } elsif ($freespace{$element} <= $critical_result) {
		printf "Only %d M (%d%s) free\n",$freespace{$element}/1024,$result_percent,"%";
		exit 2;
	    } else {
		printf "Disk ok - %d M (%d%s) free\n",$freespace{$element}/1024,$result_percent,"%";
		exit 0;
	    }
	}
    }
    print "$fsid1 doesn't exist in $target_host\n\n";
    exit -1;
}

sub check_cpu_5min {
    my ($cpu, $warn, $crit) = @_;
    if ($cpu >= $crit) {
	print "Critical- 5-min load: $cpu\n";
	exit 2;
    } elsif ($cpu >= $warn) {
	print "Warning - 5-min load: $cpu\n";
	exit 1;
    } else {
	print "Load ok - 5-min load: $cpu\n";
	exit 0;
    }
}




#!/usr/bin/perl -w
# nagios: -epn
use strict;
use warnings;
use Switch;
use lib "/usr/lib/nagios/plugins";
use utils qw(%ERRORS $TIMEOUT);
use Getopt::Long;
use vars qw/$opt_storage1 $opt_storage2 $opt_type $opt_name $opt_sec $opt_verbose $opt_wk $opt_ck $opt_wi $opt_ci $opt_help $opt_freshness/;
# Assuming performance data returned like:
# "Storage Subsystems ","Total IOs ","Read Percentage ","Cache Hit Percentage ","Current KB/second ","Maximum KB/second ","Current IO/second ","Maximum IO/second"

#### Main

get_options();
$TIMEOUT=60;
my $smcli	= '/opt/IBM_DS/client/SMcli';
my $runninguser = (getpwuid($<))[0];		# If script is run as root, nagios cannot overrite it so put username in temp file name :D
my $temp_file	= "/tmp/IBM_performance_$runninguser"."$opt_storage1.txt";
my $new_check	= 0;
my $sanname	= undef;
my @input;
my $command="sudo $smcli";
$command .= " $opt_storage1";
$command .= " $opt_storage2";
$command .= " -n $sanname" if(defined($sanname));

switch ($opt_type) {
	case 'logical'		{ $opt_type = 'Logical Drive'; $command .= " -c \"set session performanceMonitorInterval=$opt_sec performanceMonitorIterations=1; show logicalDrive [$opt_name] performanceStats;\"" }
	case 'controller'	{ $opt_type = 'CONTROLLER IN SLOT '.$opt_name; $command .= " -c \"set session performanceMonitorInterval=$opt_sec performanceMonitorIterations=1; show allLogicalDrives performanceStats;\"" }
	else			{ $command .= " -c \"set session performanceMonitorInterval=$opt_sec performanceMonitorIterations=1; show allLogicalDrives performanceStats;\"" }
}


# Code to avoid multiple SMCli commands on Storage - it seems that management controllers crash if too many scripts are run at the same time

if (-e $temp_file) {
	my $mod_time =  (stat($temp_file))[9] ;
	my $now_time =  time() ;
	if ( defined($opt_verbose) ) {
		print "Temp file updated at: ", scalar( localtime( ($mod_time)) ),"\n";;
		print "Now time: ",scalar( localtime( ($now_time) ) ),"\n";
		print "Time difference: ",scalar ( $now_time - $mod_time ) ,"\n";
	}
	if ( ($now_time - $mod_time) >= $opt_freshness*60 ) { 
		$new_check = 1;
	}

} 

if (! -e $temp_file || $new_check ) {
	open(DATA,"$command|") || die "CRITICAL Could not execute $command";
	open(FILE,'+>',$temp_file) or die "CRITICAL Could not write to /tmp";

	while(<DATA>) {
	    chomp;
	    print FILE "$_\n";
	    push(@input,$_);
	}
	close(FILE);
	close(DATA);
} else {
	if (-z $temp_file) { sleep(15); }	# in case another script started and didn't finished yet
	open(FILE,'<',$temp_file) or die "CRITICAL Could not open temp file";
	while(<FILE>) {
		chomp;
		push(@input,$_);
	}
	close(FILE);
}

# End Code to avoid..

my $some_data_found=0;
my ($resk, $resi, $res)=('','','');
my $nresult;
my ($ss,$tio,$rp,$chp,$ckbs,$mkbs,$cios,$mios);
foreach my $line (@input) {
	if ( $line =~ $opt_type ) {
		$some_data_found=1;
		($ss,$tio,$rp,$chp,$ckbs,$mkbs,$cios,$mios) = split ',',$line;
		$ckbs=~s/\"//g;$ckbs=int($ckbs);
		$cios=~s/\"//g;$cios=int($cios);
		if ( defined($opt_wk) ) { if ($ckbs < $opt_wk) {$resk='OK';} else {$resk='WARNING';} }
		if ( defined($opt_ck) && ($resk =~ 'WARNING'||!defined($opt_wk)) ) { if ($ckbs > $opt_ck) {$resk='CRITICAL';} }
		if ( defined($opt_wi) ) { if ($cios < $opt_wi) {$resi='OK';} else {$resi='WARNING';} }
		if ( defined($opt_ci) && ($resi =~ 'WARNING'||!defined($opt_wi)) ) { if ($cios > $opt_ci) {$resi='CRITICAL';} }
	if ( $resk =~ 'CRITICAL' or $resi =~ 'CRITICAL' ) {$res='CRITICAL';} else { 
		if ( $resk=~'WARNING' or $resi=~'WARNING' ) { $res='WARNING'; } else { $res='OK'; }
	}
	
	$nresult = "$res $opt_type ";
	$nresult .= "$opt_name " if (defined($opt_name));
	$nresult .= "'Current MB/s'=".int($ckbs/1024)." 'Current IO/second'=$cios";
	$nresult .= "| ";
	$nresult .= "'Current B/second'=".($ckbs*1024).";".($opt_wk*1024).";".($opt_ck*1024) if (defined($opt_wk) && defined($opt_ck));
	$nresult .= "'Current B/second'=".($ckbs*1024).";".($opt_wk*1024).";" if (defined($opt_wk) && !defined($opt_ck));
	$nresult .= "'Current B/second'=".($ckbs*1024).";".";".($opt_ck*1024) if (defined($opt_ck) && !defined($opt_wk));
	$nresult .= "'Current B/second'=".($ckbs*1024) if (!defined($opt_ck) && !defined($opt_wk));
	$nresult .= " 'Current IO/second'=$cios;$opt_wi;$opt_ci" if (defined($opt_wi) && defined($opt_ci));
	$nresult .= " 'Current IO/second'=$cios;$opt_wi;" if (defined($opt_wi) && !defined($opt_ci));
	$nresult .= " 'Current IO/second'=$cios;;$opt_ci" if (defined($opt_ci) && !defined($opt_wi));
	$nresult .= " 'Current IO/second'=$cios" if (!defined($opt_ci) && !defined($opt_wi));;
print ("$nresult\n");
	}
}

if ( !$some_data_found || $opt_verbose ) {
	print " CRITICAL No corresponding data has been found, please check name of the controller/lun\nDebugging data: \n" if(!defined($opt_verbose));
	print "$command\n";
	foreach my $line (@input) {print "$line\n";}
	exit $ERRORS{'CRITICAL'};
}
exit $ERRORS{"$res"};

#### END MAIN

sub get_options {
    Getopt::Long::Configure( 'bundling' );
      GetOptions(
		'i:s'		=> \$opt_storage1,	'storage1:s'	=> \$opt_storage1, 
		'j:s'		=> \$opt_storage2,	'storage2:s'    => \$opt_storage2,
		't:s'		=> \$opt_type,		'type:s'	=> \$opt_type,
		'n:s'		=> \$opt_name,		'name:s'	=> \$opt_name,
		'f:i'		=> \$opt_freshness,	'freshness:i'	=> \$opt_freshness,
		's:i'		=> \$opt_sec,		'seconds:i'	=> \$opt_sec,
		'v'		=> \$opt_verbose,	'verbose'	=> \$opt_verbose,
		'w:i'		=> \$opt_wk,		'warningkilo'	=> \$opt_wk,
		'c:i'		=> \$opt_ck,		'criticalkilo'	=> \$opt_ck,
		'x:i'		=> \$opt_wi,            'warningio'	=> \$opt_wi,
		'd:i'		=> \$opt_ci,            'criticalio'	=> \$opt_ci,
		'h'		=> \$opt_help,		'help'		=> \$opt_help,
                 );
	if ( defined($opt_help) ) { &print_help; exit $ERRORS{'CRITICAL'}; }
	if ( !defined($opt_storage1) ) { print "Define storage ips!!!\n"; &print_help; exit $ERRORS{'CRITICAL'}; }
	if ( !defined($opt_storage2) ) { print "Define storage ips!!!\n"; &print_help; exit $ERRORS{'CRITICAL'}; }
	if ( !defined($opt_type) || !defined($opt_name) || ($opt_type eq '') || ($opt_name eq '') ) { $opt_type='STORAGE SUBSYSTEM TOTALS'; $opt_name=''; }
	if ( defined($opt_wk) ) { if ( $opt_wk==0 ) { $opt_wk=undef; } }
	if ( defined($opt_ck) ) { if ( $opt_ck==0 ) { $opt_ck=undef; } }
	if ( defined($opt_wi) ) { if ( $opt_wi==0 ) { $opt_wi=undef; } }
        if ( defined($opt_ci) ) { if ( $opt_ci==0 ) { $opt_ci=undef; } }
	if ( defined($opt_sec) ) { if ( $opt_sec==0 ) { $opt_sec=undef; } }
	if ( !defined($opt_sec) ) { $opt_sec=5; }
	if ( defined($opt_type) ) { if ( !$opt_type =~ 'logical' || !$opt_type =~ 'controller' ) { &print_help(); exit 1;} }
	if ( !defined($opt_type) ) { $opt_type='STORAGE SUBSYSTEM TOTALS'; }
	if ( !defined($opt_freshness) ) { $opt_freshness = 1; }
  }
sub print_help {
print <<EOT;

Usage: check_IBM_performance -i <ip_cntrl1> <ip_cntrl2> [-t <logical,controller>] [-n <lun/controller name>] [-s <seconds>] [-w] [-c] [-x] [-d] [-s] [-v] [-h];
        -i  --storage1=<ip of the 1'st controllers>
		This must be defined
	-j --storage2=<ip of the 2'nd controller>
	-v, --verbose
                print extra debugging information
        -t, --type=(logical,controller)
                performance for logical dirve (-n must be suplied too) if not totals will be displayed
		performance for controller
		if -t not specified or null totals will be displayed
        -n, --name=<name>
		the name of the logical drive or the controller ( -n A  / -n B )
		MUST be specified if -t used to have a correct results or total will be displayed
	-f, --freshness=<int> (minutes)
		minutes for keeping temporary performance file until refresh data from Storage
		defaults to 1 minute (minimum)
        -s, --seconds=<int>
		sampling interval for the performance statistics (also see defined timeout)
	-w, --warningkilo  = <threshold in kb>
	-c, --criticalkilo = <threshold in kb>
	-x, --warningio  = <threshold iops>
	-d, --criticalio = <threshold iops>
	-h, --help	This help
Nagios command examples:

define command{
    command_name        check_IBM_DS4700
    command_line        /usr/lib64/nagios/plugins/check_IBM_performance -i "a.b.c.d" -j "a.b.c.e" -t \$ARG1\$ -n \$ARG2\$ -w \$ARG3\$ -c \$ARG4\$ -x \$ARG5\$ -d \$ARG6\$ 
}
Check command in action: (for the above defined command the following will give an WARNING on 500K and a CRITICAL at 10000K sampling on 10 seconds for the entire storage: no -t -n specified)
    check_command               check_IBM_DS4100!!!500!10000!!!10

New improvement from Martin Moebius (from -i "ip1 ip2" => -i "ip1" -j "ip2")
define command{
    command_name        check_IBM_DS4700
    command_line        /usr/lib64/nagios/plugins/check_IBM_performance -i \$HOSTADDRESS\$ -j \$ARG1\$ -t \$ARG2\$ -n \$ARG3\$ -w \$ARG4\$ -c \$ARG5\$ -x \$ARG6\$ -d \$ARG7\$ 
}

Martin: The syntax of the mod is “check_IBM_performance -i a.b.c.d –j a.b.c.e” and it also can be used as “check_IBM_performance -i \$HOSTADDRESS\$ –j \$ARG1\$”
So you can put the ip's in the check command not hardcoded in the definition of it

Command takes no arguments returns TOTAL KBPS and IOPS

Known issues:
	- If you have 2 controllers and specify only one ip the SMcli command will throw an error so no performance data is returned
	- pnp4nagios graps for KB/s makes y scale with k which is confusing, so I * 1024 => at input ( -w or -c ) you will specify values in KB and the output will be in Bytes !!!
	- you have to define the host with the ip of one controller (which will be pinged) but the check command must have both controller's ip's hardcoded	     - if you want to use -c you MUST use also -w or you will get CRITICAL any time
EOT
}	


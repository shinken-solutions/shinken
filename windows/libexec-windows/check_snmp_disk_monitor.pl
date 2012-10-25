#!/usr/local/bin/perl
# author: Al Tobey <albert.tobey@priority-health.com>
# what:    monitor diskspace using the host-resources mib
# license: GPL - http://www.fsf.org/licenses/gpl.txt
#
# Todo:

use strict;
require 5.6.0;
use lib qw( /opt/nagios/libexec );
use utils qw(%ERRORS $TIMEOUT &print_revision &support &usage);
use SNMP 5.0;
use Getopt::Long;
use vars qw( $exit $message $opt_version $opt_timeout $opt_help $opt_command $opt_host $opt_community $opt_verbose $opt_warning $opt_critical $opt_port $opt_mountpoint $opt_stats $snmp_session $PROGNAME $TIMEOUT %mounts );

$PROGNAME      = "snmp_disk_monitor.pl";
$opt_verbose   = undef;
$opt_host      = undef;
$opt_community = 'public';
$opt_command   = undef;
$opt_warning   = 99;
$opt_critical  = 100;
$opt_port      = 161;
$opt_stats     = undef;
$message       = undef;
$exit          = 'OK';
%mounts        = ();

sub process_options {
    my( $opt_crit, $opt_warn ) = ();
    Getopt::Long::Configure( 'bundling' );
    GetOptions(
        'V'     => \$opt_version,       'version'     => \$opt_version,
        'v'     => \$opt_verbose,       'verbose'     => \$opt_verbose,
        'h'     => \$opt_help,          'help'        => \$opt_help,
        's'     => \$opt_stats,         'statistics'  => \$opt_stats,
        'H:s'   => \$opt_host,          'hostname:s'  => \$opt_host,
        'p:i'   => \$opt_port,          'port:i'      => \$opt_port,
        'C:s'   => \$opt_community,     'community:s' => \$opt_community,
        'c:i'   => \$opt_crit,          'critical:i'  => \$opt_crit,
        'w:i'   => \$opt_warn,          'warning:i'   => \$opt_warn,
        't:i'   => \$TIMEOUT,           'timeout:i'   => \$TIMEOUT,    
        'm:s'   => \$opt_mountpoint,    'mountpoint:s'=> \$opt_mountpoint
    );
    if ( defined($opt_version) ) { local_print_revision(); }
    if ( defined($opt_verbose) ) { $SNMP::debugging = 1; }
    if ( !defined($opt_host) || defined($opt_help) || !defined($opt_mountpoint) ) {
        print_help();
        exit $ERRORS{UNKNOWN};
    }
    $opt_mountpoint = [ split(/,/, $opt_mountpoint) ];
}

sub local_print_revision {
        print_revision( $PROGNAME, '$Revision: 82 $ ' )
}

sub print_usage {
    print "Usage: $PROGNAME -H <host> -C <snmp_community> [-s] [-w <low>,<high>] [-c <low>,<high>] [-t <timeout>] -m <mountpoint>\n";
}

sub print_help {
    local_print_revision();
    print "Copyright (c) 2002 Al Tobey <albert.tobey\@priority-health.com>\n\n",
          "SNMP Disk Monitor plugin for Nagios\n\n";
    print_usage();
    print <<EOT;
-v, --verbose
   print extra debugging information
-h, --help
   print this help message
-H, --hostname=HOST
   name or IP address of host to check
-C, --community=COMMUNITY NAME
   community name for the host's SNMP agent
-m, --mountpoint=MOUNTPOINT
   a mountpoint, or a comma delimited list of mountpoints
-w, --warning=INTEGER
   percent of disk used to generate WARNING state (Default: 99)
-c, --critical=INTEGER
   percent of disk used to generate CRITICAL state (Default: 100)
-s, --statistics
   output statistics in Nagios format
EOT
}

sub verbose (@) {
    return if ( !defined($opt_verbose) );
    print @_;
}

sub check_for_errors {
    if ( $snmp_session->{ErrorNum} ) {
        print "UNKNOWN - error retrieving SNMP data: $snmp_session->{ErrorStr}\n";
        exit $ERRORS{UNKNOWN};
    }
}

# =========================================================================== #
# =====> MAIN
# =========================================================================== #
process_options();

alarm( $TIMEOUT ); # make sure we don't hang Nagios

$snmp_session = new SNMP::Session(
    DestHost => $opt_host,
    Community => $opt_community,
    RemotePort => $opt_port,
    Version   => '2c'
);

# retrieve the data from the remote host
my( $mps, $alloc, $size, $used ) = $snmp_session->bulkwalk( 0, 4, [['hrStorageDescr'],['hrStorageAllocationUnits'],['hrStorageSize'],['hrStorageUsed']] );
check_for_errors();

alarm( 0 ); # all done with the network connection

# move all the data into a nice, convenient hash for processing
foreach my $mp ( @$mps )   { $mounts{$mp->iid}->{mountpoint} = $mp->val; }
foreach my $a  ( @$alloc ) { $mounts{$a->iid}->{alloc_units} = $a->val; }
foreach my $si ( @$size ) {
    if ( exists($mounts{$si->iid}->{alloc_units}) ) {
        $mounts{$si->iid}->{size} = $si->val * $mounts{$si->iid}->{alloc_units};
    }
    else {
        $mounts{$si->iid}->{size} = $si->val;
    }
}
foreach my $us ( @$used ) {
    if ( exists($mounts{$us->iid}->{alloc_units}) ) {
        $mounts{$us->iid}->{used} = $us->val * $mounts{$us->iid}->{alloc_units};
    }
    else {
        $mounts{$us->iid}->{used} = $us->val;
    }
}

# now find the mountpoint or mountpoints that were actually requested and push onto an array for output
my @matches = ();
foreach my $mp ( @$opt_mountpoint ) {
    my $found = scalar(@matches); # count all matches
    foreach my $key ( keys(%mounts) ) {
        if ( $mounts{$key}->{mountpoint} eq $mp ) {

            # find the percentate - eval to avoid divide by zero errors
            eval { $mounts{$key}->{percent_used} = $mounts{$key}->{used} / $mounts{$key}->{size} };
            $mounts{$key}->{percent_used} =~ s/^0\.([0-9]{1,2})([0-9]?).*/\1/; # truncate
            if ( $2 >= 5 ) { $mounts{$key}->{percent_used}++ }; # round the number number

            verbose "mountpoint $mp has ", $mounts{$key}->{percent_used}, "% used, ",
                $mounts{$key}->{size}, " bytes and ",$mounts{$key}->{used}, " used\n"; 

            push( @matches, $mounts{$key} );
        }
    }
    if ( scalar(@matches) == $found ) {
        print "UNKNOWN - could not locate mountpoint $mp on host\n";
        exit $ERRORS{UNKNOWN};
    }
}

# now run through and check the thresholds
foreach my $mp ( @matches ) {
    if ( $mp->{percent_used} >= $opt_warning  ) {
        $exit = 'WARNING';
        if ( $mp->{percent_used} >= $opt_critical ) { $exit = 'CRITICAL'; }
    }
    $message .= $mp->{percent_used}.'% used on '.$mp->{mountpoint}.', ';
}
$message =~ s/,\s*$//;

# append statistics if requested
if ( defined($opt_stats) ) {
    my @tmp = ();
    foreach my $mp ( @matches ) {
        push( @tmp, join(',',$mp->{mountpoint},$mp->{size},$mp->{used}) );
    }
    $message .= '|'.join( ':', @tmp );
}

print "Disk $exit - $message\n";
exit $ERRORS{$exit};



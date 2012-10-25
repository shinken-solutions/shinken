#!/usr/local/bin/perl
# author: Al Tobey <albert.tobey@priority-health.com>
# what:   monitor a process using the host-resources mib
# license: GPL - http://www.fsf.org/licenses/gpl.txt
#
# Todo:
# * implement memory and cpu utilization checks
# * maybe cache pids in DBM files if snmp agents get overworked
###############################################################################
# to get a list of processes over snmp try this command:
# snmptable -v2c -c public hostname hrSWRunTable
# for just a list of valid arguments for the '-e' option:
# snmpwalk -v2c -c public hostname hrSWRunName |perl -pe 's:.*/::'
###############################################################################

use strict;
require 5.6.0;
use lib qw( /opt/nagios/libexec /usr/local/libexec );
use utils qw(%ERRORS $TIMEOUT &print_revision &support &usage);
use SNMP 5.0;
use Getopt::Long;
use Storable;
use vars qw( $exit $opt_version $opt_timeout $opt_help $opt_command $opt_host $opt_community $opt_verbose $opt_warning $opt_critical $opt_memory $opt_cpu $opt_port $opt_regex $opt_stats $opt_cache $opt_nocache $cache_exp $interpreters $snmp_session $PROGNAME $TIMEOUT );

$PROGNAME      = "snmp_process_monitor.pl";
$opt_verbose   = undef;
$opt_host      = undef;
$opt_community = 'public';
$opt_command   = undef;
$opt_warning   = [ 1, -1 ];
$opt_critical  = [ 1, -1 ];
$opt_memory    = undef;
$opt_cpu       = undef;
$opt_port      = 161;
$opt_cache     = 1;
$opt_nocache   = undef;
$cache_exp     = 600;
$exit          = $ERRORS{OK};
$interpreters  = '(perl|/bin/sh|/usr/bin/sh|/bin/bash|/bin/ksh|python)';
our $cachefile = '/var/opt/nagios/tmp/'; # completed later
our %processes = ();

sub process_options {
    my( $opt_crit, $opt_warn ) = ();
    Getopt::Long::Configure( 'bundling' );
    GetOptions(
        'V'     => \$opt_version,       'version'     => \$opt_version,
        'v'     => \$opt_verbose,       'verbose'     => \$opt_verbose,
        'h'     => \$opt_help,          'help'        => \$opt_help,
        's'     => \$opt_stats,         'statistics'  => \$opt_stats,
                                        'nocache'     => \$opt_nocache,
        'H:s'   => \$opt_host,          'hostname:s'  => \$opt_host,
        'p:i'   => \$opt_port,          'port:i'      => \$opt_port,
        'C:s'   => \$opt_community,     'community:s' => \$opt_community,
        'c:s'   => \$opt_crit,          'critical:s'  => \$opt_crit,
        'w:s'   => \$opt_warn,          'warning:s'   => \$opt_warn,
        't:i'   => \$TIMEOUT,           'timeout:i'   => \$TIMEOUT,    
        'e:s'   => \$opt_command,       'command:s'   => \$opt_command,
        'r:s'   => \$opt_regex,         'regex:s'     => \$opt_regex,
        'cpu:i' => \$opt_cpu,           'memory:i'    => \$opt_memory,
    );
    if ( defined($opt_version) ) { local_print_revision(); }
    if ( defined($opt_verbose) ) { $SNMP::debugging = 1; }
    if ( !defined($opt_host) || defined($opt_help) || (!defined($opt_command) && !defined($opt_regex)) ) {
        print_help();
        exit $ERRORS{UNKNOWN};
    }

    if ( defined($opt_crit) ) {
        if ( $opt_crit =~ /,/ ) {
            $opt_critical = [ split(',', $opt_crit) ];
        }
        else {
            $opt_critical = [ $opt_crit, -1 ];
        }
    }
    if ( defined($opt_warn) ) {
        if ( $opt_warn =~ /,/ ) {
            $opt_warning = [ split(',', $opt_warn) ];
        }
        else {
            $opt_warning = [ $opt_crit, -1 ];
        }
    }
    if ( defined($opt_memory) ) { $opt_memory = 0 }
    if ( defined($opt_cpu)    ) { $opt_cpu    = 0 }
    if ( defined($opt_nocache)) { $opt_cache  = 0 }

    # complete the cachefile's name
    $cachefile .= $opt_host . '.proc';
}

sub local_print_revision {
        print_revision( $PROGNAME, '$Revision: 84 $ ' )
}

sub print_usage {
    print "Usage: $PROGNAME -H <host> -C <snmp_community> -e <command> [-w <low>,<high>] [-c <low>,<high>] [-t <timeout>] [-s|--statistics] [--memory] [--cpu] [--nocache]\n";
}

sub print_help {
    local_print_revision();
    print "Copyright (c) 2002 Al Tobey <albert.tobey\@priority-health.com>\n\n",
          "SNMP Process Monitor plugin for Nagios\n\n";
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
-e, --command=COMMAND NAME (ps -e style)
   what command should be monitored?
-r, --regex=Perl RE
   use a perl regular expression to find your process
-w, --warning=INTEGER[,INTEGER]
   minimum and maximum number of processes before a warning is issued (Default 1,-1)
-c, --critical=INTEGER[,INTEGER]
   minimum and maximum number of processes before a critical is issued (Default 1,-1)
--memory
   combined with '-s', will print the number of bytes of real memory used by process
--cpu
   combined with '-s', will print the number of seconds of cpu time consumed by process
EOT
}

sub verbose (@) {
    return if ( !defined($opt_verbose) );
    print @_;
}

sub check_for_errors {
    if ( $snmp_session->{ErrorNum} ) {
        %processes = ();
        print "UNKNOWN - error retrieving SNMP data: $snmp_session->{ErrorStr}\n";
        exit $ERRORS{UNKNOWN};
    }
}

sub init_cache {
    if ( !defined($opt_cache) ) {
        %processes = ();
        return;
    }
    if ( -r $cachefile ) {
        eval {
            verbose "loading cache from $cachefile\n";
            %processes = %{ retrieve( $cachefile ) };
        };
        if ( $@ ) {
            verbose "cache loading failed - using blank cache: $@\n";
            %processes = ()
        }
    }
    else {
        %processes = ();
    }
}

sub snmpget {
    my $tmpvar = SNMP::Varbind->new( shift );
    $snmp_session->get( $tmpvar );
    check_for_errors();
    return $tmpvar->val;
}

sub update_cache {
    # expire the cache after $cache_exp seconds
    if ( $opt_cache != 0 && exists($processes{__last_update})
      && $processes{__last_update} >= time - $cache_exp )  {
        verbose "cache file is recent enough - using it\n";
        return 1;
    }

    verbose "retrieving full listing of processes from $opt_host\n";
    my $process_count = snmpget( ['hrSystemProcesses', 0] );

    # retrieve the data from the remote host
	my ($names) = $snmp_session->bulkwalk( 0, $process_count + 1, [['hrSWRunName']] );
	check_for_errors();

    # make sure the number of processes from the bulkwalk is close to hrSystemProcesses
    if ( scalar(@$names) + 10 < $process_count ) {
        print "UNKNOWN - only ", scalar(@$names), " of ",$process_count, " processes returned\n";;
        exit $ERRORS{UNKNOWN};
    }

    # sort through the process names and create a nice hash of processes
	foreach my $row ( @$names ) {
        my %hash = {};
	    $hash{name}     = $row->val;
        $hash{abs_name} = $row->val;
	    $hash{name}     =~ s#.*/##; # strip path
	
	    if ( defined($opt_regex) ||
	        ($row->val =~ m#$interpreters$#
	        && $opt_command !~ m#$interpreters$#) ) {
	
	        # fetch the runtime parameters of the process
            my $parameters = snmpget( ['hrSWRunParameters', $row->iid] );
	
	        # only strip if we're looking for a specific command
	        if ( defined($opt_command) ) {
	            verbose "process ",$row->iid," uses $1 as an interpreter - getting parameters\n";
	            $hash{name} = $parameters;
	            $hash{name} =~ s#.*/##;    # strip path name off the front
	            $hash{name} =~ s/\s+.*$//; # strip everything from the first space to the end
	        }
	        else {
	            # use the full 'ps -efl' style listing for regular expression matching
                my $path = snmpget( ['hrSWRunPath', $row->iid] );
	            $hash{name} = "$path $parameters";
	        }
	    }
        # store in the global hash
        $processes{$row->iid} = \%hash;
	}

    # update the timestamp so the cache can expire
    $processes{__last_update} = time;
    return 0;
}

# process the %processes hash and see if there any matches for our command or regex
sub check_for_matches {
    my $ret_match = 0;
	foreach my $key ( keys(%processes) ) {
        next if ( $key eq '__last_update' );
        my $match = 0;

        # static matches are letter-for-letter (-e)
	    if ( defined($opt_command)  && $processes{$key}->{name} eq  $opt_command ) { $match++; }
        # use /o to make sure the user-supplied regex (-r) is only compiled once
	    elsif ( defined($opt_regex) && $processes{$key}->{name} =~ /$opt_regex/o ) { $match++; }

        # verify the cache's entry by doing an snmpget
        if ( $match > 0 && $opt_cache != 0 ) {
            my $proc = snmpget( ['hrSWRunName', $key] );
            --$match if ( !$proc || $proc ne $processes{$key}->{abs_name} );
        }
        # get the process memory usage if requested
        if ( $match > 0 && defined($opt_memory) ) {
            $opt_memory += snmpget( ['hrSWRunPerfMem', $key] );
        }
        # get the process cpu usage if requested
        if ( $match > 0 && defined($opt_cpu) ) {
            $opt_cpu += snmpget( ['hrSWRunPerfCPU', $key] );
        }

	    verbose "process '$processes{$key}->{name}' has pid $processes{$key}->{pid} and index $key\n"
            if ( $match > 0 );

        $ret_match += $match;
	}
	return $ret_match;
}
# =========================================================================== #
# =====> MAIN
# =========================================================================== #
process_options();

alarm( $TIMEOUT ); # make sure we don't hang Nagios

# intialize the cache, if it's enabled
init_cache();

# create a session for conversing with the remote SNMP agent
$snmp_session = new SNMP::Session(
    DestHost => $opt_host,
    Community => $opt_community,
    RemotePort => $opt_port,
    Version   => '2c'
);

my $usage = update_cache();
my $count = check_for_matches();

# always try twice if caching is enabled - once with cache and once without
if ( $usage != 0 && $opt_cache != 0 && $count <= 0 ) {
    verbose "did not find process in cache - trying a refresh\n";
    %processes = ();
    update_cache();
    $count = check_for_matches();
}


# the default, OK message
my $message = "OK - $count process(es) found resembling '". ($opt_command || $opt_regex);

# warning, critical
if ( ($opt_warning->[0] > 0 && $opt_warning->[0]  >  $count)
  || ($opt_warning->[1] > 0 && $opt_warning->[1]  <= $count) ) {
    $message = "WARNING - no processes found resembling '". ($opt_command || $opt_regex);
    $exit = $ERRORS{WARNING};
}
if ( ($opt_critical->[0] > 0 && $opt_critical->[0]  >  $count)
  || ($opt_critical->[1] > 0 && $opt_critical->[1]  <= $count) ) {
    $message = "CRITICAL - no processes found resembling '". ($opt_command || $opt_regex);
    $exit = $ERRORS{CRITICAL};
}

# output the status message
print $message, "'";

# print the number of processes if statistics are requested
if ( defined($opt_stats) ) {
    print "|count=$count";
    if ( defined($opt_memory) ) {
        print ":memory=", $opt_memory;
    }
    if ( defined($opt_cpu) ) {
        $opt_cpu = $opt_cpu / 100;
        printf ":cpu=%.2f", $opt_cpu;
    }
}

# store a copy of the %processes hash if we're using caching
if ( $exit == $ERRORS{OK} && $opt_cache != 0 ) {
    eval {
        unlink( $cachefile ) if ( -e $cachefile );
        store( \%processes, $cachefile );
    };
}

print "\n";
exit $exit;



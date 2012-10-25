#!/usr/bin/perl

# check_inodes.pl for FreeBSD
# Designed on FreeBSD 4.6 (although this should not matter)
# parses df output, splits, and then takes variables
# df.pl -f mountpoint -w warningnumber -c critical number
# USE NUMBERS AND NOT PERCENTS FOR wanring and critical values
# -h is help
# -v is version
# Mountpoints:
# like / or /usr or /var (whatever you mount drives NOT the device names)
# Andrew Ryder - 20020804 - atr@mrcoffee.org


use strict;
use Getopt::Long;
use vars qw($opt_V $opt_h $opt_w $opt_c $opt_f $verbose $PROGNAME);
use lib "/usr/local/libexec/nagios" ;
use utils qw($TIMEOUT %ERRORS &print_revision &support);

my $df = "/bin/df";
my $grep = "/usr/bin/grep";

$PROGNAME="df.pl";

sub print_help ();
sub print_usage ();


$ENV{'PATH'}='';
$ENV{'BASH_ENV'}='';
$ENV{'ENV'}='';

Getopt::Long::Configure('bundling');
GetOptions
        ("V"   => \$opt_V, "version"    => \$opt_V,
         "h"   => \$opt_h, "help"       => \$opt_h,
         "w=s" => \$opt_w, "warning=s"  => \$opt_w, 
         "c=s" => \$opt_c, "critical=s" => \$opt_c,
	 "f=s" => \$opt_f, "filesystem=s" => \$opt_f);
	

if ($opt_V) {
        print_revision($PROGNAME,'$Revision: 72 $ ');
        exit $ERRORS{'OK'};
}

if ($opt_h) {
        print_help();
        exit $ERRORS{'OK'};
}

($opt_w) || ($opt_w = shift) || ($opt_w = 50);
my $warning = $1 if ($opt_w =~ /([0-9]+)/);

($opt_c) || ($opt_c = shift) || ($opt_c = 75);
my $critical = $1 if ($opt_c =~ /([0-9]+)/);

if ($opt_c < $opt_w) {
        print "Critical offset should be larger than warning offset\n";
        print_usage();
        exit $ERRORS{"UNKNOWN"};
}

($opt_f) || ($opt_f = "/");


unless (-e $df) {
	print "UNKNOWN: $df is not where df is\n";
	exit $ERRORS{'UNKNOWN'};
	}

unless (-e $grep) {
	print "UNKNOWN: $grep is not where grep is\n";
	exit $ERRORS{'UNKNOWN'};
	}

unless (-d $opt_f) {
	print "UNKNOWN: $opt_f is not a mount point\n"; 
	exit $ERRORS{'UNKNOWN'};
	}


my $state = $ERRORS{'UNKNOWN'};
my $answer;

open(DF, "$df -i $opt_f| $grep -v Filesystem |");

while (<DF>) {
	
		my ($fs,$onek,$used,$avail,$capacity,$iused,$ifree,$ipercent,$mounted) = split;
		$ipercent =~ s/%//s;

			if ($ipercent > $opt_w) {
				$state = $ERRORS{'WARNING'};
				$answer =  "WARNING: $ipercent percent inodes free on $opt_f\n";
			} elsif ($ipercent > $opt_w) {
				$state = $ERRORS{'CRITCAL'};
        			$answer =  "CRITICAL: $ipercent percent inodes free on $opt_f\n";
        		} elsif ($ipercent < $opt_w) {
				$state = $ERRORS{'OK'};
				$answer = "OK: $ipercent percent inodes free on $opt_f\n";
			}
}

close(DF);

print "$answer";
exit $state;

sub print_usage () {
        print "Usage: $PROGNAME <filesystem> [-w <warn>] [-c <crit>]\n";
	print "Example: $PROGNAME /dev/ad0s1a -w 50 -c 75\n";
}
                
sub print_help () {
        print_revision($PROGNAME,'$Revision: 72 $');
        print "Copyright (c) 2002 Andrew Ryder\n";
        print "\n";
        print_usage();
        print "\n";
        print "<warn> = Inode Percent at which a warning message is returned. Defaults to 50.\n";
        print "<crit> = Inode Percent at which a critical message is returned..\n        Defaults to 75.\n\n";
        support();
}
 


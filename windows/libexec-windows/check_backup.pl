#! /usr/bin/perl -wT

# (c)2001 Patrick Greenwell, Stealthgeeks, LLC. (patrick@stealthgeeks.net)
# Licensed under the GNU GPL
# http://www.gnu.org/licenses/gpl.html

# check_backup: Checks a directory to see if at least one file was
# created within a specified period of time that is of equal to or greater
# than a given size.

# Version 1.0
# Last Updated: 9/12/01


BEGIN {
	if ($0 =~ m/^(.*?)[\/\\]([^\/\\]+)$/) {
		$runtimedir = $1;
		$PROGNAME = $2;
	}
}

require 5.004;
use strict;
use Getopt::Long;
use vars qw($opt_H $opt_d $opt_s $opt_t $verbose $PROGNAME);
use lib $main::runtimedir;
use utils qw($TIMEOUT %ERRORS &print_revision &usage &support &is_error);

sub help ();
sub print_help ();
sub print_usage ();
sub version ();
sub display_res($$);
my ($filesize, $answer) = ();
my $state = $ERRORS{'UNKNOWN'};

# Directory to check.
my $dir = "/backup/";

# Time period(in seconds)
my $within = "3600";

# Minimum size of file (in bytes)
my $minsize = "40000000";

delete @ENV{'PATH', 'IFS', 'CDPATH', 'ENV', 'BASH_ENV'};

Getopt::Long::Configure('bundling', 'no_ignore_case');
GetOptions
	("V|version"     => \&version,
	 "h|help"        => \&help,
	 "v|verbose"     => \$verbose,
         "d|directory=s" => \$opt_d,
         "s|minsize=s"   => \$opt_s,
         "t|timeout=s"   => \$opt_t,
         );

($opt_s) || ($opt_s = shift) || usage("Minimum File size not specified\n");
usage("File size must be numeric value") unless ($opt_s =~ m/^[0-9]+$/);

(($opt_t) && ($TIMEOUT = $opt_t)) || ($TIMEOUT = 120);
usage("TIMEOUT must be numeric value") unless ($TIMEOUT =~ m/^[0-9]+$/);

# Don't hang if there are timeout issues
$SIG{'ALRM'} = sub {
	print ("ERROR: No response from ftp server (alarm)\n");
	exit $ERRORS{'UNKNOWN'};
};
alarm($TIMEOUT);

# Do stuff

my $time = time;
 
opendir(THISDIR, "$dir") or die "Can't open directory! $!";
my @allfiles = grep !/^\./, readdir THISDIR;
closedir THISDIR;
while (my $file = $dir . pop @allfiles){
        my ($size, $mtime) = (stat($file))[7,9];
        if  (((my $a = ($time - $mtime)) <= $within) and ($size >= $opt_s)){
                display_res("OK: File $file is <= $within and >=$opt_s bytes.\n","OK");        
        }
}
 
# If we got here nothing matched.... 
display_res("CRITICAL: No files in $dir are <= $within and >= $minsize.", "CRITICAL");

exit;

sub print_usage () {
	print "Usage: $PROGNAME -s <minimum file size in bytes> -t <timeout> \n";
}

sub print_help () {
	print_revision($PROGNAME,'$ Revision: 1.0 $ ');
	print_usage();
	support();
}

sub version () {
	print_revision($PROGNAME,'$ Revision: 1.0 $ ');
	exit $ERRORS{'OK'};
}

sub help () {
	print_help();
	exit $ERRORS{'OK'};
}

sub display_res ($$) {
        my ($answer, $state) = @_;
        print $answer;
        exit $ERRORS{$state};
}

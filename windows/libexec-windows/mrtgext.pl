#!/usr/bin/perl -w
#
#  mrtgext.pl  v0.3
#    (c)2000 Cliff Woolley, Washington and Lee University
#    jwoolley@wlu.edu
#
#  A UNIX counterpart to Jim Drews' MRTG Extension for netware servers
#  Mimics output of mrtgext.nlm using output of various standard UNIX
#  programs (df, uptime, and uname)
#
#  Dependencies:  I make some assumptions about the output format of
#  your df and uptime commands.  If you have nonstandard outputs for
#  any of these, either pick a different command that gives more
#  standard output or modify the script below.  Example: use /usr/bin/bdf
#  on HP-UX instead of /usr/bin/df, because bdf follows the output format
#  I expect while df does not.  This was written on Linux and tested on
#  HP-UX 10.20 (with changes to the subroutines at the bottom of the
#  program to reflect HP's command parameters); similar tweaking could
#  well be required to port this to other platforms.  If you get it
#  working on your platform, please send me any changes you had to
#  make so I can try to incorporate them.
#
#
#  Following is what I expect the programs' outputs to look like:
#  
#  ======= df ========
#  Filesystem           1k-blocks      Used Available Use% Mounted on
#  /dev/sda1              1014696    352708    609612  37% /
#  /dev/sda2              2262544    586712   1559048  27% /apps
#  /dev/sda3              4062912    566544   3286604  15% /share
#  /dev/sr0                651758    651758         0 100% /cdrom
#  ===================
#
#  ===== uptime ======
#  3:17pm  up 15 days,  4:40,  5 users,  load average: 0.12, 0.26, 0.33
#  ===================
#

###############################################################
#  Configuration section
###############################################################

$dfcmd          = "/bin/df 2>/dev/null";
$uptimecmd      = "/usr/bin/uptime";
%customcmds     = ( "PROCS"    => "numprocesses",
                    "ZOMBIES"  => "numzombies",
                    "MEMFREE"  => "memfree",
                    "SWAPUSED" => "swapused",
                    "TCPCONNS" => "tcpconns",
                    "CLIENTS"  => "ipclients" );
                           # These are functions that you can
                           # define and customize for your system.
                           # You probably need to change the provided
                           # subroutines to work on your system (if
                           # not Linux).

$rootfsnickname = "root";  # this is necessary as a kludge to
                           # better match the netware behavior.
                           # if you already have a _filesystem_
                           # mounted as /root, then you'll need
                           # to change this to something else
$DEBUG          = 0;
$recvtimeout    = 30;


###############################################################
#  Program section
###############################################################

require 5.004;

use Sys::Hostname;


$DEBUG = $ARGV[0] unless ($DEBUG);
$SIG{'ALRM'} = sub { exit 1; };

# some things never change
$hostname = hostname;


if ( $DEBUG ) {
    $| = 1;
    print scalar localtime,": mrtgext.pl started\n";
}

# timeout period 
alarm($recvtimeout);
my $items = <STDIN>;
alarm(0);

$items =~ s/[\r\n]//g;
( $DEBUG ) && print scalar localtime,": request: \"$items\"\n";
my @items = split (/\s+/,"$items");
( $DEBUG ) && print scalar localtime,": ",scalar @items," item(s) to process\n";

my $uptime = `$uptimecmd`;
my @df     = grep {/^\//} `$dfcmd`;

my $processed = 1;

foreach $_ (@items) {
    ( $DEBUG ) && print scalar localtime,": processing item #$processed: \"$_\"\n";
    $_ = uc; #convert $_ to upper case
    if    ( /^UTIL1$/ ) {
        $uptime =~ /load average: ([^,]+),/;
        print $1 * 100,"\n";
    }
    elsif ( /^UTIL5$/ ) {
        $uptime =~ /load average: [^,]+, ([^,]+)/;
        print $1 * 100,"\n";
    }
    elsif ( /^UTIL15$/ ) {
        $uptime =~ /load average: [^,]+, [^,]+, ([^,]+)/;
        print $1 * 100,"\n";
    }
    elsif ( /^CONNECT$/ ) {
        $uptime =~ /(\d+) users?,/;
        print "$1\n";
    }
    elsif ( /^NAME$/ ) {
        print "$hostname\n";
    }
    elsif ( /^UPTIME$/ ) {
        $uptime =~ /up (.*),\s+\d+\s+users?,/;
        print "$1\n";
    }
    elsif ( /^VOLUMES$/ ) {
        foreach $dfline (@df) {
            my $volname = (split(/\s+/, "$dfline"))[5];
            $volname =~ s/^\/$/$rootfsnickname/;
            $volname =~ s/^\///;
            $volname =~ s/\//_/g;
            print "$volname\n";
        }
    }
    elsif ( /^VF(\w*)$/ ) {
        my $volname = ("$1" eq uc("$rootfsnickname")) ? "/" : "$1";
        foreach $dfline (@df) {
            my @dfline = split(/\s+/, "$dfline");
            if ($dfline[5] =~ /^\/?$volname$/i ) {
                print (($dfline[1]-$dfline[2]) * 1024,"\n");
                goto done;
            }
        }
        ( $DEBUG ) && print scalar localtime,": ERROR: volume not found.\n";
        print "-1\n";
    }
    elsif ( /^VU(\w*)$/ ) {
        my $volname = ("$1" eq uc("$rootfsnickname")) ? "/" : "$1";
        foreach $dfline (@df) {
            my @dfline = split(/\s+/, "$dfline");
            if ($dfline[5] =~ /^\/?$volname$/i ) {
                print ($dfline[2] * 1024,"\n");
                goto done;
            }
        }
        ( $DEBUG ) && print scalar localtime,": ERROR: volume not found.\n";
        print "-1\n";
    }
    elsif ( /^VS(\w*)$/ ) {
        my $volname = ("$1" eq uc("$rootfsnickname")) ? "/" : "$1";
        foreach $dfline (@df) {
            my @dfline = split(/\s+/, "$dfline");
            if ($dfline[5] =~ /^\/?$volname$/i ) {
                print ($dfline[1] * 1024,"\n");
                goto done;
            }
        }
        ( $DEBUG ) && print scalar localtime,": ERROR: volume not found.\n";
        print "-1\n";
    }
    elsif ( /^VKF(\w*)$/ ) {
        my $volname = ("$1" eq uc("$rootfsnickname")) ? "/" : "$1";
        foreach $dfline (@df) {
            my @dfline = split(/\s+/, "$dfline");
            if ($dfline[5] =~ /^\/?$volname$/i ) {
                print (($dfline[1]-$dfline[2]),"\n");
                goto done;
            }
        }
        ( $DEBUG ) && print scalar localtime,": ERROR: volume not found.\n";
        print "-1\n";
    }
    elsif ( /^VKU(\w*)$/ ) {
        my $volname = ("$1" eq uc("$rootfsnickname")) ? "/" : "$1";
        foreach $dfline (@df) {
            my @dfline = split(/\s+/, "$dfline");
            if ($dfline[5] =~ /^\/?$volname$/i ) {
                print ($dfline[2],"\n");
                goto done;
            }
        }
        ( $DEBUG ) && print scalar localtime,": ERROR: volume not found.\n";
        print "-1\n";
    }
    elsif ( /^VKS(\w*)$/ ) {
        my $volname = ("$1" eq uc("$rootfsnickname")) ? "/" : "$1";
        foreach $dfline (@df) {
            my @dfline = split(/\s+/, "$dfline");
            if ($dfline[5] =~ /^\/?$volname$/i ) {
                print ($dfline[1],"\n");
                goto done;
            }
        }
        ( $DEBUG ) && print scalar localtime,": ERROR: volume not found.\n";
        print "-1\n";
    }
    elsif ( /^ZERO$/ ) {
        print "0\n";
    }
    elsif (exists( $customcmds{"$_"} )) {
        my $cmdsub = "$customcmds{$_}";
        print &$cmdsub."\n";
    }
    else {
        print "-1\n";
    }
    done: $processed++;
}
( $DEBUG ) && print scalar localtime,": done.\n";


###############################################################
#  CUSTOMIZED PROCEDURES
###############################################################

sub numprocesses {

    my $num = `/bin/ps -eaf | /usr/bin/tail -n +2 | /usr/bin/wc -l`;
    chomp ($num);
    $num =~ s/\s+//g;

    $num;
}

sub numzombies {

    my $num = `/bin/ps -afx | /usr/bin/awk '{print \$3}' | /usr/bin/grep Z | /usr/bin/tail -n +2 | /usr/bin/wc -l`;
    chomp ($num);
    $num =~ s/\s+//g;

    $num;
}

sub tcpconns {

    my $num = `/bin/netstat -nt | /usr/bin/tail -n +3 | /usr/bin/wc -l`;
    chomp ($num);
    $num =~ s/\s+//g;

    $num;
}

sub ipclients {

    my $num = `/bin/netstat -nt | /usr/bin/tail -n +3 | /usr/bin/awk '{print \$5}' | /bin/cut -d : -f 1 | /usr/bin/sort -nu | /usr/bin/wc -l`;
    chomp ($num);
    $num =~ s/\s+//g;

    $num;
}

sub memfree {

    open( FP, "/proc/meminfo" );
    my @meminfo = <FP>;
    close(FP);

    #         total:    used:    free:  shared: buffers:  cached:
    # Mem:  994615296 592801792 401813504 91193344 423313408 93118464
    # Swap: 204791808        0 204791808
    my ($total,$free,$buffers,$cache) = (split(/ +/,$meminfo[1]))[1,3,5,6];
    
    int(($free+$buffers+$cache)/$total*100);
}

sub swapused {

    open( FP, "/proc/meminfo" );
    my @meminfo = <FP>;
    close(FP);

    #         total:    used:    free:  shared: buffers:  cached:
    # Mem:  994615296 592424960 402190336 89821184 423313408 93077504
    # Swap: 204791808        0 204791808

    my ($total,$used) = (split(/ +/,$meminfo[2]))[1,2];
    
    int($used/$total*100);
}

#!/usr/bin/perl
# ------------------------------------------------------------------------------
# File Name:            check_dns_random.pl
# Author:               Richard Mayhew - South Africa
# Date:                 2000/01/26
# Version:              1.0
# Description:          This script will check to see if dns resolves hosts
#                       randomly from a list using the check_dns plugin. 
# Email:                netsaint@splash.co.za
# ------------------------------------------------------------------------------
# Copyright 1999 (c) Richard Mayhew
# Credits go to Ethan Galstad for coding Nagios
# If any changes are made to this script, please mail me a copy of the
# changes :)
# License GPL
# ------------------------------------------------------------------------------
# Date          Author          Reason
# ----          ------          ------
# 1999/09/26    RM              Creation
# ------------------------------------------------------------------------------

# -----------------------------------------------------------------[ Require ]--
require 5.004;

# --------------------------------------------------------------------[ Uses ]--
use Socket;
use strict;

# --------------------------------------------------------------[ Enviroment ]--
$ENV{PATH} = "/bin";
$ENV{BASH_ENV} = "";
$|=1;

my $host = shift || &usage;

my $domainfile = "/usr/local/nagios/etc/domains.list";
my $wc = `/usr/bin/wc -l $domainfile`;
my $check = "/usr/local/nagios/libexec/check_dns";
my $x = 0;
my $srv_file = "";
my $z = "";
my $y = "";

open(DOMAIN,"<$domainfile") or die "Error Opening $domainfile File!\n";
        while (<DOMAIN>) {
          $srv_file .= $_;
}
        close(DOMAIN);
                my @data = split(/\n/,$srv_file);

chomp $wc;
$wc =~ s/ //g;
$wc =~ s/domains//g;

$x = rand $wc;
($z,$y) = split(/\./,$x);

system($check, $data[$z], $host);
exit ($? / 256);

sub usage
{
        print "Minimum arguments not supplied!\n";
        print "\n";
        print "Perl Check Random DNS plugin for Nagios\n";
        print "Copyright (c) 2000 Richard Mayhew\n";
        print "\n";
        print "Usage: check_dns_random.pl <host>\n";
        print "\n";
        print "<host> = DNS server you would like to query.\n";
        exit -1;

}


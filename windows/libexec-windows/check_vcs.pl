#!/usr/bin/perl
#
# Veritas Cluster System monitor for Nagios.
# Written by Aaron Bostick (abostick@mydoconline.com)
# Last modified: 05-22-2002
#
# Usage: check_vcs {-g <vcs_group> | -r <vcs_resource> } -s <vcs_system> [-n]
#
# Description:
#
# This plugin is just a perl wrapper to the vcs commands hagrp and hares. 
# You specify what group/resource and system you want the status for, and
# the plugin returns a status code based on the output of either hagrp or 
# hares.
#
# Normal hagrp/hares status codes are ONLINE and OFFLINE depending on where the 
# cluster service currently lives.  I have added an option, -n, which makes
# the expected state to be OFFLINE rather than ONLINE so you can run the 
# plugin on both sides of the cluster and will receive critical alerts when
# the cluster fails over i.e.  a proper failover will make the standby node
# go from OFFLINE to ONLINE for the group, so an ONLINE status should alert
# you! (You do want to know when the cluster fails over, right? :))
#
# Output:
#
# This plugin returns OK when hagrp/hares -state <grp> -sys <system> returns 
# ONLINE (or OFFLINE if -n is specified).  Any other hagrp/hares string returns 
# CRITICAL...  Would a WARNING ever be justified???  UNKNOWN is returned if 
# hagrp/hares cannot run for some reason.
# 
# Examples:
#
# Make sure group oracle is ONLINE on server dbserver1:
#   check_vcs -g oracle -s dbserver1
#
# Make sure group oracle is OFFLINE on server dbserver2:
#   check_vcs -g oracle -s dbserver2 -n
#
# Make sure resource oraip is ONLINE on server dbserver1:
#   check_vcs -r oraip -s dbserver1
#
# Make sure resource oraip is OFFLINE on server dbserver2:
#   check_vcs -r oraip -s dbserver2 -n
#


BEGIN {
    if ($0 =~ s/^(.*?)[\/\\]([^\/\\]+)$//) {
        $prog_dir = $1;
        $prog_name = $2;
    }
}

require 5.004;

use lib $main::prog_dir;
use utils qw($TIMEOUT %ERRORS &print_revision &support);
use Getopt::Long;

sub print_usage ();
sub print_version ();
sub print_help ();

    # Initialize strings
    $vcs_bin = '/opt/VRTSvcs/bin';
    $vcs_command = '';
    $vcs_arg = '';
    $vcs_group = '';
    $vcs_resource = '';
    $vcs_system = '';
    $vcs_negate = '';
    $vcs_result = '';
    $vcs_expected_result = 'ONLINE';
    $plugin_revision = '$Revision: 33 $ ';

    # Grab options from command line
    GetOptions
    ("g|group:s"        => \$vcs_group,
     "r|resouce:s"      => \$vcs_resource,
     "s|system=s"       => \$vcs_system,
     "n|negate"         => \$vcs_negate,
     "v|version"        => \$version,
     "h|help"           => \$help);
 
    (!$version) || print_version ();
    (!$help) || print_help ();
    (!$vcs_negate) || ($vcs_expected_result = 'OFFLINE');

    # Make sure group and resource is not specified
    !($vcs_group && $vcs_resource) || usage("Please specify either a group or a resource, but not both.\n");
    # Make sure group or resource is specified
    ($vcs_group || $vcs_resource) || usage("HA group or resource not specified.\n");
    # Make sure system is specified
    ($vcs_system) || usage("HA system not specified.\n");

    # Specify proper command
    if ($vcs_group) {
        $vcs_command = 'hagrp';
        $vcs_arg = $vcs_group;
    } else {
        $vcs_command = 'hares';
        $vcs_arg = $vcs_resource;
    }

    # Run command and save output
    $vcs_result = `$vcs_bin/$vcs_command -state $vcs_arg -sys $vcs_system`;
    chomp ($vcs_result);

    # If empty result, return UNKNOWN
    if (!$vcs_result) {
        print "UNKNOWN: Problem running $vcs_command...\n";
        exit $ERRORS{'UNKNOWN'};
    }
        
    # If result is expected, return OK
    # If result is not expected, return CRITICAL
    if ($vcs_result eq $vcs_expected_result) {
        print "OK: $vcs_command $vcs_arg is $vcs_result\n";
        exit $ERRORS{'OK'};
    } else {
        print "CRITICAL: $vcs_command $vcs_arg is $vcs_result\n";
        exit $ERRORS{'CRITICAL'};
    }
        

#
# Subroutines
#

sub usage () {
    print @_;
    print_usage();
    exit $ERRORS{'OK'};
}

sub print_usage () {
    print "\nUsage: $prog_name { -g <vcs_group> | -r <vcs_resource> } -s <vcs_system> [-n]\n";
    print "Usage: $prog_name [ -v | --version ]\n";
    print "Usage: $prog_name [ -h | --help ]\n";
}

sub print_version () {
    print_revision($prog_name, $plugin_revision);
    exit $ERRORS{'OK'};
}

sub print_help () {
    print_revision($prog_name, $plugin_revision);
    print "\n";
    print "Validate output from hagrp/hares command.\n";
    print "\n";
    print_usage();
    print "\n";
    print "-g, --group=<vcs_group>\n";
    print "    The HA group to be validated\n";
    print "-r, --resource=<vcs_resource>\n";
    print "    The HA resource to be validated\n";
    print "-s, --system=<vcs_system>\n";
    print "    The HA system where the group/resource lives\n";
    print "-n, --negate=<negate>\n";
    print "    Set expected result to OFFLINE instead of ONLINE\n";
    print "\n";
    support();
    exit $ERRORS{'OK'};
}

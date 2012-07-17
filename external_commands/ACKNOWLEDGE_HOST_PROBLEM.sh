#!/bin/sh
#
# This is a sample shell script showing how you can submit the
# CHANGE_HOST_CHECK_COMMAND command to Nagios. Adjust variables to fit
# your environment as necessary.

now=$(date +%s)
commandfile='/usr/local/shinken/var/rw/nagios.cmd'

printf "[%lu] ACKNOWLEDGE_HOST_PROBLEM;dc01;1;1;1;Jean Gabes;Some Acknowledgement Comment\n" $now > $commandfile

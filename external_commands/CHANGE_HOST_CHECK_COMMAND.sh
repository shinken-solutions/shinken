#!/bin/sh
#
# This is a sample shell script showing how you can submit the
# CHANGE_HOST_CHECK_COMMAND command to Nagios. Adjust variables to fit
# your environment as necessary.

now=$(date +%s)
commandfile='/home/nap/shinken/src/var/rw/nagios.cmd'

printf "[%lu] CHANGE_HOST_CHECK_COMMAND;dc1;check_http\n" $now > $commandfile

#!/bin/sh
#
# This is a sample shell script showing how you can submit the
# CHANGE_HOST_CHECK_COMMAND command to Nagios. Adjust variables to fit
# your environment as necessary.

now=$(date +%s)
commandfile='/usr/local/shinken/var/rw/nagios.cmd'

printf "[111] ADD_SIMPLE_POLLER;All;newpoller;localhost;8771\n" > $commandfile

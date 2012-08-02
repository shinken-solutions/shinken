#!/bin/sh
#
# This is a sample shell script showing how you can submit the
# CHANGE_CONTACT_HOST_NOTIFICATION_TIMEPERIOD command to Nagios.
# Adjust variables to fit your environment as necessary.

now=$(date +%s)
commandfile='/usr/local/shinken/var/rw/nagios.cmd'

printf "[%lu] CHANGE_CONTACT_HOST_NOTIFICATION_TIMEPERIOD;dbrosseau;24x7\n" $now > $commandfile

#!/usr/bin/perl -w
#
# =============================== SUMMARY =====================================
#
# Program : check_netint.pl or check_snmp_netint.pl
# Version : 2.4 alpha 9
# Date    : Nov 30, 2012
# Maintainer: William Leibzon - william@leibzon.org,
# Authors : See "CONTRIBUTORS" documentation section
# Licence : GPL - summary below, full text at http://www.fsf.org/licenses/gpl.txt
#
#  ********************* IMPORTANT NOTE ABOUT THIS VERSION ********************
#  *** THIS IS AN ALPHA/DEVELOPMENT RELEASE WHICH HAS NOT BEEN FULLY TESTED ***
#  *** IF YOU NEED A STABLE VERSION, PLEASE GET 2.36 VERSION OF THIS PLUGIN ***
#  *** AT HTTP://william.leibzon.org/nagios/ or http://exchange.nagios.org/ ***
#  ****************************************************************************
# 
# =========================== PROGRAM LICENSE =================================
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
#
# ===================== INFORMATION ABOUT THIS PLUGIN =========================
#
#  This is a plugin for nagios to check network interfaces (network ports)
#  on servers switches & routers. It is based on check_snmp_int.pl plugin
#  by Patrick Ploy with extensive rewrites for performance improvements
#  and additions to support Cisco and other switches (plugin can query and
#  cache cisco port names, port link data and switch STP status and more)
#  The plugin can use nagios-stored previous performance data to give port
#  traffic & utilization without creation of temporary files. This new 2.4
#  version supports checking interface on a local linux server without SNMP. 
#
# ======================  SETUP AND PLUGIN USE NOTES  =========================
#
# Help : ./check_snmp_netint.pl -h
#   above will tell you most you probalby need for this to make this plugin work
#
# Patrick's Site: http://nagios.manubulon.com/snmp_int.html
#   documentation reproduced below for options shared with check_snmp_int
#
# If you're using -P option to pass performance data back to plugin then
# you may (depending on version of nagios) also need to modify nagios.cfg
# and remove ' from illegal_macro_output_chars=`~$&|'"<> line, i.e. change to
#   illegal_macro_output_chars=`~$&|"<>
#
# ------------------------------------------------------------------------------
# Checks by snmp (v1, v2c or v3) host interface state and usage.
# Interfaces can be selected by regexp ('eth' will check eth0,eth1,eth2, ...).
# If multiple interfaces are selected, all must be up to get an OK result
#
# Standard checks:
#   The script will check interface operational status using the MIB-II table.
#   To see how interface looks like in snmp, you can list all with the '-v'.
#
#   The interfaces are selected by their description in the MIB-II table.
#   The interface is/are selected by the -n option. This option will be treated
#   as a regular expression (eth will match eth0,eth1,eth2...). You can disable
#   this with the -r option : the interface will be selected if it's description
#   exactly matches the name given by -n
# 
#   The script will return OK if ALL interfaces selected are UP, or CRITICAL
#   if at least one interface is down. You can make the script return a OK
#   value when all interfaces are down (and CRITICAL when at least one is up)
#   with the -i option. You can make the same tests on administrative status
#   instead with the -a option. If you have ISDN interface, and want that
#   DORMANT state returns ok, put -D.
#
#   To make output shorter, specially when you have many interfaces, you can put
#   the -s option. It will get only the first <n> characters of the interface
#   description. If the number is negative then get the last <n> characters. 
#   Ex : EL20005 3Com Gigabit NIC (3C2000 Family)
#      -s 4 will output : "EL20".
#      -s -4 will output : "ily)".
#
# Performance output
#   -f option : performance output (default the In/out octet as a counter).
#   -e option : in/out errors and discarded packets. -f must also be set.
#   -S option : Include speed in performance output in bits/s as '<interface_name>_speed_bps'
#   -y option : output performance data in % of interface speed
#   -Y option : output performance data in bits/s or Bytes/s (depending on -B)
#   Note : -y and -Y options need the usage check to ba active (-k)
#   Warning : the counters needed by -e are not available on all devices
#
# Usage check
#   -k : activates the standard usage feature
#   -q : activates the extended usage
#   -d : delta in seconds (default is 300s)
#   -w : warning levels
#   -c : critical levels
# 
#   If you specify '-k' a temporary file will be created in "/tmp" by default
#   (unless -P option is also used, see below). Directory and start of filename 
#   can be set with '-F' option with result file being like
#     tmp_Nagios_int.<host IP>.<Interface name>, one file per interface
#   
#   If you do "-k -P \$SERVICEPERFDATA\$ -T \$LASTSERVICECHECK\$" then no file
#   is created and instead data from previous check is feed back into plugin.
#
#   The status UNKNOWN is returned when the script doesn't have enough
#   information (see -d option). You will have to specify the warning and
#   critical levels, separated with "," and you can use decimal (ex : 10.3).
#   For standard checks (no "-q") :
#     -w <In warn>,<Out warn> -c <In warn>,<Out warn>
#        In warn : warning level for incomming traffic
#        Out warn : warning level for outgoing traffic
#        In crit : critical level for incomming traffic
#        Out crit : critical level for outgoing traffic
#
#   Use 0 if you do not want to specify any warning or critical threshold
#   You can also use '-z' option which makes specifying -w and -c optional
#   but still allows to see all the values in status or use them for graphing
#
#   The unit for the check depends on the -B, -M and -G option :
#   	                B set    -B not set
#     ----------------+--------+-------------
#    -M & -G not set  |  Kbps  |   KBps
#    -M set           |  Mbps  |   MBps
#    -G set 	      |  Gbps  |   GBps
#   
#   It is possible to put warning and critical levels with -b option.
#   0 means no warning or critical level checks
#
#   When the extended checks are activated (-q option), the warning levels are
#     -w <In bytes>,<Out bytes>,<In error>,<Out error>,<In disc>,<Out disc>
#     -c <In warn>,<Out warn>, .....
#        In error : warn/crit level in inboud error/minute
#        Out error : warn/crit level in outbound error/minute
#        In disc : warn/crit level in inboud discarded packets/minute
#        Out disc : warn/crit level in outbound discarded packets/minute
#
#  -d: delta time
#     You can put the delta time as an option : the "delta" is the prefered time
#     between two values that the script will use to calculate the average
#     Kbytes/s or error/min. The delta time should (not must) be bigger than
#     the check interval.
#     Here is an example : Check interval of 2 minutes and delta of 4min
#        T0 : value 1 : can't calculate usage
#        T0+2 : value 2 : can't calculate usage
#        T0+4 : value 3 : usage=(value3-value1)/((T0+4)-T0)
#        T0+6 : value 4 : usage=(value4-value2)/((T0+6)-T0+2)
#        (Yes I know TO+4-T0=4, it's just to explain..)
#     The script will allow 10% less of the delta and 300% more than delta
#     as a correct interval. For example, with a delta of 5 minutes, the
#     acceptable interval will be between 4'30" and 15 minutes.
#
# Msg size option (-o option)
#     In case you get a "ERROR: running table: Message size exceeded maxMsgSize"
#     error, you may need to adjust the maxMsgSize, i.e. the maximum size of
#     snmp message with the -o option. Try a value with -o AND the -v option, 
#     the script will output the actual value so you can add some octets to it
#     with the -o option.
#
# --label option
#     This option will put label before performance data value: 
#        Without : eth1:UP (10.3Kbps/4.4Kbps), eth0:UP (10.9Kbps/16.4Kbps):2 UP: OK
#        With : eth1:UP (in=14.4Kbps/out=6.2Kbps), eth0:UP (in=15.3Kbps/out=22.9Kbps):2 UP: OK
#
# Note: Do not rely on this option meaning same thing in the future, it may be
#       changed to specify label to put prior to plugin output with this
#       option changing to something else...
#
# ----------------------------------------------------------------------------- 
# Below is documentation for options & features unique to check_snmp_netint
# that were not part of check_snmp_int:
#
# I. Plugin execution time and performance and optimization options:
#   1. [default] By default this plugin will first read full
#      'ifindex description' table and from that determine which interfaces
#      are to be checked by doing regex with name(s) given at -n. It will
#      then issue several SNMP queries - one for operational or admin status
#      and 2nd one for "performance" data. If '--cisco' and '--stp' options
#      are given then several more queries are done to find mapping from
#      cisco ports to ifindex and separate mapping between ifindex and stp,
#      only then can queries be done for additional cisco & stp status data.
#   2. ['minimize_queries'] If you use '-m' ('--minimize_queries') option then
#      all queries for status data are done together but the original ifindex
#      snmp table is still read separately. By itself this brings about 30%
#      speed improvement
#   3. ['minimize_queries' and -P] When using '-f -m -P "$SERVICEPERFDATA$"'
#      as options, your nagios config performance data is feed back and
#      used as a placeholder to cache information on exactly which
#      interfaces need to be queried. So no aditional description table
#      lookup is necessary. Similarly data for '--cisco' and '--stp'
#      maps is also cached and reused. There is only one SNMP query done
#      together for all data OIDs (status & performance data) and 
#      for all interfaces; this query also includes query for specific
#      description OID (but not reading entire table) which is then
#      compared against cached result to make sure ifindex has not changed.
#      Once every 12 hours full check is done and description data is recached.
#      65% to 90% or more speed improvements are common with this option.
#   4. ['minimum_queries' and -P] Using '-f -mm -P "$SERVICEPERFDATA$"'
#      is almost the same as "-m" but here extra check that interface
#      description is still the same is not done and recaching is every
#      3 days instead of 12 hours. Additionally port speed data is also
#      cached and not checked every time. These provide marginal extra
#      plugin execution time impovements over '-m' (75%-100% improvement
#      over not doing -m) but is not safe for devices where port ifindex
#      may change (i.e. switches with removeable interface modules).
#      But in 99% of the cases it should be ok do to use this option.
#
# II. As mentioned previously when you want to see current traffic in/out &
#     utilization data (-k option) for interface this requires previous octet
#     count data to calculate average and so normally this requires temporary
#     file (see -F option). But when you feed nagios performance data back to
#     plugin as per above that means you already provide with at least one set
#     of previous data, so by also adding '-T $LASTSERVICECHECK$' (which is time
#     of last check when this data was cached) you can have this plugin report
#     current traffic in Mb (or kb, etc) without any temporary files.
#
#     As of version 2.1 its possible to also have short history as part of
#     performance data output  i.e. plugin will output not only the
#     most current data but also one or more sets of previous data.
#     Bandwidth calculations are then less "bursty". Total number of such
#     sets is controlled with '--pcount' option and by default is 2.
#     If you have only one interface checked with this plugin its probably
#     safe to increase this to 3 or 4, but larger values or more interfaces
#     are an issue unless you increased size of nagios buffer used to
#     store performance data. 
#
# III.For those of you with Cisco switches you may have noticed that they
#     do not provide appropriate port names at standard SNMP ifdescr table.
#     There are two options to help you:
#   1. If you set custom port names ('set port 1/xx name zzz") you can use
#      those names with "--cisco=use_portnames" option.
#   2. Another option is specify custom description table with
#       "-N 1.3.6.1.2.1.31.1.1.1.1"
#       and optionally display "set port name" as a comment. 
#   Its recommended you try both:
#       "-N 1.3.6.1.2.1.31.1.1.1.1 --cisco=show_portnames" and
#       "-O 1.3.6.1.2.1.31.1.1.1.1 --cisco=use_portnames"
#   and see which works best in your case 
#
#   Additionally when using "--cisco" option the plugin will attempt to
#   retrieve port status information from 3 cisco-specific tables (see below).
#   If any "unusual" status is listed there the output is provided back - this
#   can be useful to diagnose if you have faulty cable or if the equipment
#   on the other end is bad, etc. The tables retrieved are:
#    --cisco=oper	portOperStatus = 1.3.6.1.4.1.9.5.1.4.1.1.6
#    --cisco=linkfault  portLinkFaultStatus = 1.3.6.1.4.1.9.5.1.4.1.1.22
#    --cisco=addoper	portAdditionalOperStatus = 1.3.6.1.4.1.9.5.1.4.1.1.23
#    --cisco=noauto	special option - none of the above
#   You can mix-match more then one table (together with show_portnames) or not
#   specify at all (i.e. just '--cisco') in which case plugin will attempt to
#   retrieve data from all 3 tables first time (stop with '--cisco=noauto')
#   but if you use caching (-m) it will output and cache which table actually
#   had usable data and will not attempt to retrieve from tables that did
#   not exist on subsequent calls. 
#
# IV. Support is also provided to query STP (Spanning Tree Protocol) status
#     of the port. Although only tested with cisco switches, this is
#     standartized SNMP data and should be supported by few other vendors
#     so separate '--stp' option will work without '--cisco' option.
#     The plugin will report single WARNING alert if status changes so
#     be prepared for some alerts if your network is undergoing reorganization
#     due to some other switch getting unplugged. Otherwise STP status is also
#     very useful diagnostic data if you're looking as to why no traffic is
#     passing through particular interface...
#
# ============================ EXAMPLES =======================================
#
# First set of examples is from Patrick's site:
#
# check_snmp_netint using snmpv1:
#   define command{
#     command_name check_snmp_int_v1
#     command_line $USER1$/check_snmp_netint.pl -H $HOSTADDRESS$ $USER7$ -n $ARG1$ $ARG2$
#   }
# Checks FastEthernet 1 to 6 are up (snmpv1):
#   define service {
#     name check_int_1_6
#     check_command check_snmp_int_v1!"FastEthernet-[1-6]"
#   }
# Checks input bandwith on eth1 is < 100 KBytes/s and output is < 50 Kbytes/s
# (critical at 0,0 means no critical levels). (snmpv3):
#   define service {
#     name check_int_eth0_bdw
#     check_command check_snmp_int_v3!eth0!-k -w 100,50 -c 0,0
#   }
# ----------------------------------------------------------------
#
# Linux server with one or more eth? and one or more bond? interface:
#   define command {
#        command_name check_snmp_network_interface_linux
#        command_line $USER1$/check_snmp_int.pl -2 -f -e -C $USER6$ -H $HOSTADDRESS$
# -n $ARG1$ -w $ARG2$ -c $ARG3$ -d 200 -q -k -y -M -B 
# -m -P "$SERVICEPERFDATA$" -T "$LASTSERVICECHECK$"
#   }
#   define service{
#       use                             std-service
#       servicegroups                   snmp,netstatistics
#       hostgroup_name                  linux
#       service_description             Network Interfaces
#       check_command                   check_snmp_network_interface_linux!"eth|bond"!50,50,0,0,0,0!100,100,0,0,0,0
#   }
#
# Alteon switch - really funky device that does not like snmp v2 queries
# (so no -2) and no good interface names table. Therefore normal ifindex
# is used instead with index->names translation somewhat "guessed" manually
# with snmpwalk based on data (for those who want to know more, the first
# 255 ids are reserved for VLANs):
#   define command {
#       command_name check_snmp_network_interface_alteon
#       command_line $USER1$/check_snmp_netint.pl -f -C $USER5$ -H $HOSTADDRESS$
# -N 1.3.6.1.2.1.2.2.1.1 -n $ARG1$ -w $ARG2$ -c $ARG3$ -d 200 -k -y 
# -M -B -m -P "$SERVICEPERFDATA$" -T "$LASTSERVICECHECK$"
#   }
#   define service{
#        use                             std-switch-service
#        servicegroups                   snmp,netstatistics
#        hostgroup_name                  alteon184
#        service_description             Alteon Gigabit Port 1
#        check_command                   check_snmp_network_interface_alteon!"257"!0,0!0,0
#   }
#
# Cisco CatOS switch (will work for 5500 and many others), full set of possible options is given: 
#   define command {
#      command_name check_snmp_network_interface_catos
#      command_line $USER1$/check_snmp_netint.pl -2 -f -C $USER5$
# -H $HOSTADDRESS$ -N 1.3.6.1.2.1.31.1.1.1.1 --cisco=show_portnames --stp
# -n $ARG1$ -w $ARG2$ -c $ARG3$ -d 200 -e -q -k -y -M -B -mm
# -P "$SERVICEPERFDATA$" -T "$LASTSERVICECHECK$"
#   }
#   define service{
#       use                             std-switch-service
#       servicegroups                   snmp,netstatistics
#       hostgroup_name                  cs2948
#       service_description             GigabitEthernet2/1
#       check_command                   check_snmp_network_interface_catos!"2/1$"!0,0,0,0,0,0!0,0,0,0,0,0
#   }
#
# Cisco 2960 (IOS) switch (has only portOperStatus extended port state table):
#   define command {
#      command_name check_snmp_network_interface_cisco2960
#      command_line $USER1$/check_snmp_netint.pl -2 -f -C $USER5$
# -H $HOSTADDRESS$ --cisco=oper,show_portnames --stp -n $ARG1$ -w $ARG2$
# -c $ARG3$ -d $USER8$ -e -q -k -y -M -B -mm -P "$SERVICEPERFDATA$"
# -T "$LASTSERVICECHECK$" --label
#   }
#   define service{
#       use                             std-switch-service
#       servicegroups                   snmp,netstatistics
#       hostgroup_name                  cs2960
#       service_description             GigabitEthernet0/1
#       check_command                   check_snmp_network_interface_cisco2960!"GigabitEthernet0/1$"!0,0,0,0,0,0!0,0,0,0,0,0
#   }
#
# Other ports on above switches are defined similarly as separate services - 
# you don't have to do it this way though, but all 48 ports is too much for
# one check to handle so if you have that many split checks into groups of
# no more then 12 ports
#
# ======================= VERSIONS and CHANGE HISTORY =========================
#
# [1.4] This plugin is based on (with now about 60% rewrite or new code)
#       release 1.4 (somewhere around May 2007) of the check_snmp_int
#       plugin by Patrick Ploy. This is info provided with 1.4 version:
#       ----------------------------------------------------------
#       Version : 1.4.1
#       Date : Jul 9 2006
#       Author  : Patrick Proy ( patrick at proy.org )
#       Help : http://www.manubulon.com/nagios/
#       Licence : GPL - http://www.fsf.org/licenses/gpl.txt
#       Contrib : J. Jungmann, S. Probst, R. Leroy, M. Berger
#       TODO :
#         Check isdn "dormant" state
#         Maybe put base directory for performance as an option
#       ----------------------------------------------------------
#
#  The first changes for performance improvements were started in around
#  October 2006 with code base at version 1.4.1 of Patrick's check_snmp_int
#  plugin. Patricks's latest code from about May 2007 was ported back into
#  code maintained by WL (exact 1.4.x version of this port is unclear).  
#  Those early performance improvement code changes are now invoked with
#  'minimize_queries' (but without -P) option and allow to do query
#  for status data for all ports together. Additionally -N option to
#  specify different port names table OID was added in 2006 as well.
#  Also -F option from above TODO was added too.
#
# [1.5] 06/01/07 - Main code changes by William to allow the plugin to reuse
#       its previous performance data (passed with $SERVICEPERFDATA$ macro).
#       The changes were extensive and allow to reuse this data in way similar
#       to maintaining history file and result in traffic rate (per Mb/Gb etc)
#       being reported in the output. Additionally of paramout importance was
#       saving list of ports to check (i.e. result of regex) which means that
#       port/interface names table do not need to be checked with SNMP every
#       time and instead specific ports OIDs can be retrieved with bulk request
#       (this is what results in up to 75% performance improvement). 
#       About 30-40% of the original code was rewritten for these changes and
#       '--minimize_queries' (or '-m') option added - back then it acted more
#       like '--minimum_queries' or '-mm' in 2.0 release
# [1.5.5] 07/15/07 - Code additions to support cisco-specific data given
#       with '--cisco' option. Support is both for using cisco port names
#       for regex matching of ports and for using different table for regex
#       matching but adding cisco port name as additional comment/description.
#       Also cisco-specific port status data (info on if cable is attached,
#       etc) are also retrieved & added as additional commentary to port
#       UP/DOWN status. Additional coding work on performance improvements
#       was also done somewhere between June and July 2007 which in part resulted
#       in separation of "--minimize_queries" and "--minimum_queries" options.
# [1.5.7] 07/22/07 - This is when code to support retrieval of STP data
#       and '--stp' option were added. Also some more code cleanup related
#       to 1.5.x to better support cisco switches.
#        
#       A code from locally maintained but never released to public 1.5.7
#       branch was sent by William to Patrick sometime in early August 2007.
#       He briefly responded back that he'll look at it later but never
#       responded further and did not incorporate this code into his main
#       branch releasing newer version of 1.4.x. As a result since there is
#       public benefit in new code due to both performance and cisco-specific
#       improvements, this will now be released as new plugin 'check_snmp_netint"
#       with branch version startint at 2.0. The code will be maintained
#       by William unless Patrick wants to merge it into his branch later.
#       There is about 50% code differences (plugin header documentation you're
#       reading are not counted) between this release and check_snmp_int 1.4
#       which is where this plugin started from.
#
# [2.0] 12/20/07 - First public release as check_snmp_netint plugin. Primary
#       changes from 1.5.7 are the "header" with history and documentation
#       which are necessary for such public release, copyright notice changed
#       (W. Leibzon was listed only as contributor before), etc. 
#
# [2.1] 12/26/07 - Support for more then one set of previous data in
#       performance output to create short history for better bandwidth
#       check results. New option '--pcount' controls how many sets.
#       12/27/07 - Finally looked deeper into code that calculates bandwidth
#       and speed data and saw that it was really only using one result and
#       not some form or average. I rewrote that and it will now report back
#	average from multiple successful consequitive checks which should give
#       much smoother results. It also means that --pcount option will now
# 	be used to specify how many sets of data will be used for average
#	even if temporary file is used to store results.
#       01/08/08 - Bug fixes in new algorithm
# [2.15] 01/12/08 - Fixed so that port speed table is not retrieved unless
#       options -Y or -u or -S are given. Also fixed to make sure portpseed
#	performance variable is only reported when '-S' option is given
#	(however for caching speed data is also in 'cache_int_speed')
# [2.16] 02/03/08 - Bug fixed in how timestamp array is saved by new algorithm,
#       it would have resulted in only up to 2 previous data being used properly
#       even if > 2 are actually available
# [2.17] 04/02/08 - Bug fixes related to STP and Cisco port data extensions for
#        cases when no data is returned for some or all of the ports
# [2.18] 04/03/08 - Rewrite of cisco additional port status data extensions.
#        Now 3 tables: portOperStatus=1.3.6.1.4.1.9.5.1.4.1.1.6
#		       portLinkFaultStatus = 1.3.6.1.4.1.9.5.1.4.1.1.22
#		       portAdditionalOperStatus = 1.3.6.1.4.1.9.5.1.4.1.1.23 
#	 are supported but user can specify as option to --cisco= which one
#        is to be retrieved. When its not specified the plugin defaults to
#	 "auto" mode (unless --cisco=noauto is used) and will try to retrieve
#	 data for all 3 tables, check which data is available and then
#	 cache these results and in the future only retrieve tables that
#	 returned some data. This behavior should work with all cisco switches
#	 and not only with cisco catos models. But be warned about bugs in
#        complex behavior such as this...
# [2.19] 04/06/08 - For STP port changes previous state is now reported in
#                   the output (instead of just saying STP changed)
# 
# [2.20] 04/10/08 - Releasing 2.2 version as stable. No code changes but
#                   documentation above has been updated
# [2.201] 04/15/08 - Minor results text info issue (',' was not added before operstatus)
# [2.21] 06/10/08 - Minor fixes. Some documentation cleanup.
#		    Option -S extended to allow specifying expected interface
#		    speed with critical alert if speed is not what is specified
# [2.22] 10/20/08 - Added support for "-D" option (dormant state of ISDN)
# [2.23] 10/22/08 - Code fixes submitted or suggested by Bryan Leaman:
#                    - Fix to write data to new file, for those using file
#                      (instead of perfdata MACRO) for previous data
#                    - _out_bps fixes for those who want to use that directly
#                      for graphing instead of octet counter
#                    - New option '-Z' to have octet count in performance data
#                      instead of having this data by default (though this data
#                      is required and added automaticly with -P option)
#
# [2.3]  12/15/10 - Various small fixes. Plus a patch sent by Tristan Horn to better
#                   support minimum and maximum warning and critical thresholds
# [2.31] 01/10/11 - Bug fix when reporting in_prct/out_prct performance metric 
# [2.32] 12/22/11 - Fixes for bugs reported by Joe Trungale and Nicolas Parpandet
#		    Updates to check on existance of utils.pm and use but not require it
#		    Patch by Steve Hanselman that adds "-I" option:
#		      "I’ve attached a patch that adds an option to ignore interface status
# 		       (this is useful when you’re monitoring a switch with user devices
#		       attached that randomly power on and off but you still want
#		       performance stats and alerts on bandwidth when in use)."
# [2.34] 12/25/11 - Based on comments/requests on nagiosexchange, -z option has been added.
#		    This option makes specifying thresholds with -w and/or -c optional
#		    for those who want to use plugin primarily for data collection
#		    and graphing. This was (and still can be) accomplished before by
#		    specifying threshold value as 0 and then its not checked. Also the
#		    use of -w and -c is unnecessary if you do not use -k or -q options.
# [2.35] 04/19/12 - Added patch by Sébastien PRUD'HOMME which incorporates changes
#                   and bug fixes in revsions 1.23 and 1.19 of check_snmp_int (done
#                   after this plugin deverged from it) into this plugin as well.
#                   The changes add proper support for 64-bit counters when -g
#                   option is used and fix a bug when output is in % / perf in Bytes.
# [2.36] 06/15/12 - 1) Added fixes suggested in modified version of this plugin created
#		       by Yannick Charton to remove ^@ (NULL ?) and other not-ASCII
#		       characters at the end of the interface description. This allows
#		       to correctly match the network interface on some Windows servers.
#		    2) Extended '-v' (debug/verbose) option so that instead of writing
#		       to STDOUT people could specify a file to write debug output to.
#		    3) Using of quotewords() in prev_perf as suggested by Nicholas Scott
#		       allows to work with interfaces that have space in their name.
#		       Due to this plugin now require Text::ParseWords perl library.
#		    4) List of contributors created as a separate header section below.
#
# [2.4] alpha/beta  This version will support getting data from network interfaces on
#		    the local machine rather than just by SNMP. It will also support
#		    gettind data on average traffic (50-percentalile) and being able
#		    to specify threshold based on deviation from this average. There
#		    will be several alpha and beta versions before official 2.4 release.
#
# Specific info on each alpha/beta release will be removed in the future and only
# summary of below will appear in documentation on features and updated in 2.4 release
# 
# 2.4a1 - 07/07/12 - Implemented in this release:
#		    1) The plugin has been renamed "check_netint" from "check_snmp_netint".
#		       It can now check interfaces on a local Linux system and in the
#		       future FreeBSD, Sun and other systems maybe supported too.
#		       Checking of local interfaces happens if you do not specify -H and
#		       snmp (-O, -C, etc) options and if plugin name does not start with
#		       "check_snmp". For local interfaces options like --stp and --cisco
#		       are not valid, and optimization options -m and -mm also do not
#		       work same way since plugin will always get all data locally.
#		    2) The plugin no longer requires -n (interface name) option
#		       though it is still recommended you use it. When interface
#		       name is not specified, all interfaces will be checked.
#		    3) If with -F option directory is given instead of a file this
#		       will become base directory to write temporary file to.
#		    4) Many doc and code fixes and cleanups all over
# 2.4a2 - 08/15/12 - Fixed bug with cache of previous data for SNMP queries that came
#		     around due to change in logic and introduction of non-SNMP.
#		     Added experimental support for future Nagios SAVEDDATA feature
#		     (plugin output after || after perfdata) enabled with --nagios_with_saveddata
# 2.4a3 - 09/13/12 - Patch/contrib by Franky Van Liedekerke:
#		     1) Added option --admindown_ok: when checking for operational UP
#                       interfaces, the interfaces that are administratively down are OK
#                    2) The '-z' option now also prevents tmp files of being written
#                       and removes the 'no usable data' warning because of missing perf data
# 2.4a4 - 09/28/12 - Additional patch by FVL for --admindown_ok. Option also got -K one-letter alias.
#		     Also added determining interface speed on linux with ethtool and iwconfig..
# 2.4a5 - 10/10/12 - Interface speed can now be specified with -S/--intspeed option for use when
#                    plugin can not find speed by itsef or when what it finds is wrong. Previously
#		     this option was used to warn if speed is not what is expected, To do this now
#                    requires using prefix WARNING<> or CRITICAL<> before actual speed which is
#		     an incompatible change to preious format of this option.
# 2.4a6 - 11/17/12 - Changed ok interval from 0.9*delta - 3*delta to 0.75*delta - 4*delta.
#		     Fixed bug that would not output interface speed percent data in
#                    perf unless both -y and -u were used together. This bug was introduced
#		     somewhere around 2.2 and apparently 2.31 did not entirely fix it
# 2.4a7 - 11/18/12 - Added support for SNMP bulk requests and --bulk_snmp_queries option
# 2.4a8 - 11/21/12 - Another major code refactoring work to separate snmp-specific query
#                    code into its own function (as well as new ifconfig processing
#                    for linux local checks into its own function).
# 2.4a9 - 11/30/12 - prev_perf() function added in place of directly accessing prev_perf hash
#		     message size is reset to 5 times the default with --bulk_snmp_queries
#
# ============================ LIST OF CONTRIBUTORS ===============================
#
# The following individuals have contributed code, patches, bug fixes and ideas to
# this plugin (listed in last-name alphabetical order):
#
#    M. Berger
#    Yannick Charton
#    Steve Hanselman
#    Tristan Horn
#    J. Jungmann
#    Bryan Leaman
#    William Leibzon
#    R. Leroy
#    S. Probst
#    Patrick Proy
#    Sébastien PRUD'HOMME
#    Nicholas Scott
#    Franky Van Liedekerke
#
# Open source community is grateful for all your contributions.
#
# ============================ START OF PROGRAM CODE =============================

use strict;
use Getopt::Long;
use Text::ParseWords;

# Nagios specific
use lib "/usr/local/nagios/libexec";
our $TIMEOUT;
our %ERRORS;
eval 'use utils qw(%ERRORS $TIMEOUT)';
if ($@) {
 $TIMEOUT = 10;
 %ERRORS = ('OK'=>0,'WARNING'=>1,'CRITICAL'=>2,'UNKNOWN'=>3,'DEPENDENT'=>4);
}

our $do_snmp=1;
eval 'use Net::SNMP';
if ($@) {
  $do_snmp=0;
}

# Version 
my $Version='2.4';

############### BASE DIRECTORY FOR TEMP FILE (override this with -F) ########
my $o_base_dir="/tmp/tmp_Nagios_int.";
my $file_history=200;   # number of lines of data to keep in file

# SNMP OID Datas
my $inter_table= '.1.3.6.1.2.1.2.2.1';
my $index_table = '1.3.6.1.2.1.2.2.1.1';
my $descr_table = '1.3.6.1.2.1.2.2.1.2';
my $oper_table = '1.3.6.1.2.1.2.2.1.8.';
my $admin_table = '1.3.6.1.2.1.2.2.1.7.';
my $speed_table = '1.3.6.1.2.1.2.2.1.5.';
my $speed_table_64 = '1.3.6.1.2.1.31.1.1.1.15.';
my $in_octet_table = '1.3.6.1.2.1.2.2.1.10.';
my $in_octet_table_64 = '1.3.6.1.2.1.31.1.1.1.6.';
my $in_error_table = '1.3.6.1.2.1.2.2.1.14.';
my $in_discard_table = '1.3.6.1.2.1.2.2.1.13.';
my $out_octet_table = '1.3.6.1.2.1.2.2.1.16.';
my $out_octet_table_64 = '1.3.6.1.2.1.31.1.1.1.10.';
my $out_error_table = '1.3.6.1.2.1.2.2.1.20.';
my $out_discard_table = '1.3.6.1.2.1.2.2.1.19.';

# WL: I reversed hash array meaning so that human-redable name can be used to assign status instead
#     of numeric value. Second array is used for reversing it back when doing status line output
my %status=('UP'=>1,'DOWN'=>2,'TESTING'=>3,'UNKNOWN'=>4,'DORMANT'=>5,'NotPresent'=>6,'lowerLayerDown'=>7);
my %status_print=(1=>'UP',2=>'DOWN',3=>'TESTING',4=>'UNKNOWN',5=>'DORMANT',6=>'NotPresent',7=>'lowerLayerDown');

# WL: These are in use for Cisco CATOS special hacks, enable use with "--cisco"
my $cisco_port_name_table='1.3.6.1.4.1.9.5.1.4.1.1.4';     # table of port names (the ones you set with 'set port name')
my $cisco_port_ifindex_map='1.3.6.1.4.1.9.5.1.4.1.1.11';   # map from cisco port table to normal SNMP ifindex table
my $cisco_port_linkfaultstatus_table='1.3.6.1.4.1.9.5.1.4.1.1.22.'; # see table below for possible codes
my $cisco_port_operstatus_table='1.3.6.1.4.1.9.5.1.4.1.1.6.' ;;   # see table below for possible values
my $cisco_port_addoperstatus_table='1.3.6.1.4.1.9.5.1.4.1.1.23.'; # see table below for possible codes
# codes are as of July 2007 (just in case cisco updates MIB and somebody is working with this plugin later)
my %cisco_port_linkfaultstatus=(1=>'UP',2=>'nearEndFault',3=>'nearEndConfigFail',4=>'farEndDisable',5=>'farEndFault',6=>'farEndConfigFail',7=>'otherFailure');
my %cisco_port_operstatus=(0=>'operstatus:unknown',1=>'operstatus:other',2=>'operstatus:ok',3=>'operstatus:minorFault',4=>'operstatus:majorFault');
my %cisco_port_addoperstatus=(0=>'other',1=>'connected',2=>'standby',3=>'faulty',4=>'notConnected',5=>'inactive',6=>'shutdown',7=>'dripDis',8=>'disable',9=>'monitor',10=>'errdisable',11=>'linkFaulty',12=>'onHook',13=>'offHook',14=>'reflector');

# STP Information (only tested with Cisco but should work with other vendor switches too)
my $stp_dot1dbase_ifindex_map='1.3.6.1.2.1.17.1.4.1.2';	   # map from dot1base port table to SNMP ifindex table
my $stp_dot1dbase_portstate='1.3.6.1.2.1.17.2.15.1.3.';	   # stp port states
my %stp_portstate=('0'=>'unknown',1=>'disabled',2=>'blocking',3=>'listening',4=>'learning',5=>'forwarding',6=>'broken');
my %stp_portstate_reverse=(); # becomes reverse of above, i.e. 'disabled'=>1, etc

# Standard options
my $o_host = 		undef; 	# hostname
my $o_timeout=  	undef;  # Timeout (Default 10) 
my $o_descr = 		undef; 	# description filter
my $o_help=		undef; 	# wan't some help ?
my $o_admin=		undef;	# admin status instead of oper
my $o_inverse=  	undef;	# Critical when up
my $o_ignorestatus=     undef;  # Ignore interface NAK status, always report OK
my $o_dormant=        	undef;  # Dormant state is OK
my $o_verb=		undef;	# verbose mode/debug file name
my $o_version=		undef;	# print version
my $o_noreg=		undef;	# Do not use Regexp for name
my $o_short=		undef;	# set maximum of n chars to be displayed
my $o_label=		undef;	# add label before speed (in, out, etc...).
my $o_admindown_ok=	undef;  # admin down is ok (usefull when checking operational status)

# Speed/error checks
my $o_warn_opt=         undef;  # warning options
my $o_crit_opt=         undef;  # critical options
my @o_warn_min=         undef;  # warning levels of perfcheck
my @o_warn_max=         undef;  # warning levels of perfcheck
my @o_crit_min=         undef;  # critical levels of perfcheck
my @o_crit_max=         undef;  # critical levels of perfcheck
my $o_checkperf=	undef;	# checks in/out/err/disc values
my $o_delta=		300;	# delta of time of perfcheck (default 5min)
my $o_ext_checkperf=	undef;  # extended perf checks (+error+discard) 
my $o_highperf=         undef;  # Use 64 bits counters
my $o_meg=              undef;  # output in MBytes or Mbits (-M)
my $o_gig=              undef;  # output in GBytes or Gbits (-G)
my $o_prct=             undef;  # output in % of max speed  (-u)
my $o_kbits=	        undef;	# Warn and critical in Kbits instead of KBytes
my $o_zerothresholds=	undef;  # If warn/crit are not specified, assume its 0

# Average Traffic Calculation Options (new option for upcoming 2.4 beta)
my $o_timeavg_opt=	undef;  # New option that allows to keep track of average traffic
				# (50 percentile) over longer period and to set
				# threshold based on deviation from this average
my $o_atime_nchecks_opt= undef;	# Minimum number of samples for threshold to take affect
				# (2 numbers: one fo take affect in addition to regular
			        #  threshold, 2nd number is to take

# Performance data options
my $o_perf=             undef;  # Output performance data
my $o_perfe=            undef;  # Output discard/error also in perf data
my $o_perfp=            undef;  # output performance data in % of max speed (-y)
my $o_perfr=            undef;  # output performance data in bits/s or Bytes/s (-Y)
my $o_perfo=            undef;  # output performance data in octets (-Z)
my $o_intspeed=         undef;  # include speed in performance output (-S), specify speed

# WL: These are for previous performance data that nagios can send data to the plugin
# with $SERVICEPERFDATA$ macro (and $SERVICESAVEDDATA$ for future naios versions).
# This allows to calculate traffic without temporary file and also used to cache
# SNMP table info so as not to retreive it every time 
my $o_prevperf=		undef;	# performance data given with $SERVICEPERFDATA$ macro
my $o_prevtime=         undef;  # previous time plugin was run $LASTSERVICECHECK$ macro
my @o_minsnmp=		();     # see below
my $o_minsnmp=		undef;	# minimize number of snmp queries
my $o_maxminsnmp=	undef;  # minimize number of snmp queries even futher (slightly less safe in case of switch config changes)
my $o_bulksnmp=		undef;	# do snmp bulk request
my $o_filestore=        "";  # path of the file to store cached data in - overrides $o_base_dir
my $o_pcount=		2;	# how many sets of previous data should be in performance data
my $o_nagios_saveddata=	undef;	# enabled SAVEDDATA special output after ||

# These are unrelated WL's contribs to override default description OID 1.3.6.1.2.1.2.2.1.2 and for stp and cisco m[a|y]stery
my $o_descroid=         undef;  # description oid, overrides $descr_table
my $o_commentoid=	undef;  # comment text oid, kind-of like additional label text
my $o_ciscocat=		undef;	# enable special cisco catos hacks
my %o_cisco=		();	# cisco options
my $o_stp=		undef;	# stp support option

# Login and other options specific to SNMP
my $o_port =		161;    # SNMP port
my $o_octetlength=	undef;	# SNMP Message size parameter (Makina Corpus contrib)
my $o_community =	undef; 	# community
my $o_version2	=	undef;	# use snmp v2c
my $o_login=		undef;	# Login for snmpv3
my $o_passwd=		undef;	# Pass for snmpv3
my $v3protocols=	undef;	# V3 protocol list.
my $o_authproto=	'md5';	# Auth protocol
my $o_privproto=	'des';	# Priv protocol
my $o_privpass= 	undef;	# priv password

# Readable names for counters (M. Berger contrib)
my @countername = ( "in=" , "out=" , "errors-in=" , "errors-out=" , "discard-in=" , "discard-out=" );
my $checkperf_out_desc;

## Additional global variables
my %prev_perf_data=();  # array that is populated with previous performance data
my @prev_time=	();     # timestamps if more then one set of previois performance data
my $perfcache_time=undef;  # time when data was cached
my $perfcache_recache_trigger=43200;  # How many seconds to use cached data for (default 12 hours for -m)
my $perfcache_recache_max=259200; # and 3 days for -mm (minmize most)
my $timenow=time(); 	# This used to be defined later but easier if moved to the top
my $stp_warntime=900;	# Warn in case of change in STP state in last 15 minutes
my $check_speed=0;      # If '-Y', '-u' or '-S' options are given this is set to 1
my $specified_speed=0;	# if -S has interface speed specified, this is set to speed specified there
my $speed_alert=undef; 	# if -S has alert specified, this is alert to issue if interface speed is not what is expected
my $shell_pid=undef;	# defined only if run locally
my $snmp_session_v=0;   # if no snmp session, its 0, otherwise 1 2 or 3 depending on version of SNMP session opened
my $num_int = 0;	# number of interfaces that have matched
my @interfaces=();	# main array for interfaces data
# separated arrays that existed before that were replaced by above common array of structure/hash
# my @descr = (); --> $descr[$i] is now $interfaces[$i]{'descr'}
# my @portspeed=(); --> $portspeed[$i] is now $interfaces[$i]{'portspeed'}
my $perf_out='';	# performance data accumulator
my $saved_out='';	# saved data accumulator (added to perf)

# Functions
sub read_file { 
	# Input : File, items_number
	# Returns : array of value : [line][item] 
  my ($traffic_file,$items_number)=@_;
  my ($ligne,$n_rows)=(undef,0);  
  my (@last_values,@file_values,$i);
  open(FILE,"<".$traffic_file) || return (1,0,0); 
  
  while($ligne = <FILE>)
  {
    chomp($ligne);
    @file_values = split(":",$ligne);
    #verb("@file_values");
    if ($#file_values >= ($items_number-1)) { 
	# check if there is enough data, else ignore line
      for ( $i=0 ; $i< $items_number ; $i++ ) {$last_values[$n_rows][$i]=$file_values[$i];}
      $n_rows++;
    } 
  }
  close FILE;
  if ($n_rows != 0) { 
    return (0,$n_rows,@last_values);
  } else {
    return (1,0,0);
  }
}

sub write_file { 
  # Input : file , rows, items, array of value : [line][item]
  # Returns : 0 / OK, 1 / error
  my ($file_out,$rows,$item,@file_values)=@_;
  my $start_line= ($rows > $file_history) ? $rows -  $file_history : 0;
  if ( open(FILE2,">".$file_out) ) {
    for (my $i=$start_line;$i<$rows;$i++) {
      for (my $j=0;$j<$item;$j++) {
	print FILE2 $file_values[$i][$j];
	if ($j != ($item -1)) { print FILE2 ":" };
      }
      print FILE2 "\n";
    }
    close FILE2;
    return 0;
  } else {
    return 1;
  }
}

sub p_version { print "check_snmp_netint version : $Version\n"; }

sub print_usage {
    print "Usage: $0 [-v [debugfilename]] -H <host> (-C <snmp_community> [-2]) | (-l login -x passwd [-X pass -L <authp>,<privp>)  [-p <port>] [-N <desc table oid>] -n <name in desc_oid> [-O <comments table OID>] [-I] [-i | -a | -D | -K] [-r] [-f[eSyYZ] [-P <previous perf data from nagios \$SERVICEPERFDATA\$>] [-T <previous time from nagios \$LASTSERVICECHECK\$>] [--pcount=<hist size in perf>]] [-k[qBMGu] [-S [intspeed]] -g [-w<warn levels> -c<crit levels> [-z]| -z] -d<delta>] [-o <octet_length>] [-m|-mm] [-t <timeout>] [-s] [--label] [--cisco=[oper,][addoper,][linkfault,][use_portnames|show_portnames]] [--stp[=<expected stp state>]] [-V]\n";
}

sub isnnum { # Return true if arg is not a number
  my $num = shift;
  if ( $num =~ /^(\d+\.?\d*)|(^\.\d+)$/ ) { return 0 ;}
  return 1;
}

sub ascii_to_hex { # Convert each ASCII character to a two-digit hex number [WL]
  (my $str = shift) =~ s/(.|\n)/sprintf("%02lx", ord $1)/eg;
  return $str;
}

sub help {
   print "\nNetwork Interfaces Monitor Plugin for Nagios (check_netint/check_snmp_netint) v. ",$Version,"\n";
   print "GPL 2.0 or 3.0 licence, (c)2004-2007 Patrick Proy, (c)2007-2012 William Leibzon\n";
   print "Please see documentation for a full list of authors and contributors\n\n";
   print_usage();
   print <<EOT;

-h, --help
   print this help message
-V, --version
   prints plugin version number (required of all nagios plugins)
-t, --timeout=INTEGER
   timeout in seconds (Default: 5). if SNMP this is timeout for SNMP response
-v, --verbose[=FILENAME], --debug=FILENAME
   Print extra debugging information (including interface list on the system)
   If filename is specified instead of STDOUT the debug data is written to that file

Interface Selection and Status Output options:

-n, --name=NAME
   Name of the interface (eth0, ppp0 ...).
   This is treated as a regexp : -n eth will match eth0,eth1,...
   Test it before, because there are known bugs (ex : trailling /)
-r, --noregexp
   Do not use regexp to match NAME
-i, --inverse
   Return status CRITICAL when UP instead
-a, --admin
   Use administrative status instead of default operational
-D, --dormant
   Dormant state is an OK state (mainly for ISDN interfaces)
-I, --ignorestatus
   Ignore the interface status and return OK regardless
-s, --short=int
   Make the output shorter : only the first <n> chars of the interface(s)
   If the number is negative, then get the <n> LAST characters.
-K, --admindown_ok
   Indicate that administrative down status is OK for operational
   interfaces that are down

Note : when multiple interfaces are selected with regexp,
       all must be up (or down with -i) to get an OK result.

Threshold Checks and Performance Data options:

-f, --perfparse
   Perfparse compatible output (no output when interface is down).
-e, --error
   Add error & discard to Perfparse output
-S, --intspeed[=[OK|WARNING|CRITICAL<>]1000000Kb|100000000Kb|100000000Kb|10Mb|100Mb|1000Mb]
   If -S is used by itself, this adds speed in performance output in bits/s.
   This option also allows to specify speed of the interface if it can not be found by plugin
   or if what plugin determined is wrong. Be carefull, if you're checking multiple interfaces,
   this will override and set speed for all of them. Additionally if you prefix speed with
   WARNING<> or CRITICAL<> the alert will be issued if speed is not what is expected.
      IMPORTANT: Prior to version 2.4 of this plugin if you specified speed after --intspeed=
                 then instead of overriding it would issue a critical alert if speed is not
                 the same (CRITICAL<> behavior). You must specify alert type before speed now.
-y, --perfprct ; -Y, --perfspeed ; -Z, --perfoctet
   -y : output performance data in % of max speed 
   -Y : output performance data in bits/s or Bytes/s (depending on -B)
   -Z : output performance data in octets i.e. bytes (always so with -P)
-k, --perfcheck ; -q, --extperfcheck 
   -k check the input/ouput bandwidth of the interface
   -q also check the error and discard input/output
--label
   Add label before speed in output : in=, out=, errors-out=, etc...
-B, --kbits
   Make the warning and critical levels in K|M|G Bits/s instead of K|M|G Bytes/s
-G, --giga ; -M, --mega ; -u, --prct
   -G : Make the warning and critical levels in Gbps (with -B) or GBps
   -M : Make the warning and critical levels in Mbps (with -B) or MBps
   -u : Make the warning and critical levels in % of reported interface speed.
-w, --warning=input,output[,error in,error out,discard in,discard out]
   warning level for input / output bandwidth (0 for no warning)
     unit depends on B,M,G,u options
   warning for error & discard input / output in error/min (need -q)
-c, --critical=input,output[,error in,error out,discard in,discard out]
   critical level for input / output bandwidth (0 for no critical)
     unit depends on B,M,G,u options
   critical for error & discard input / output in error/min (need -q)
-z, --zerothresholds
   if warning and/or critical thresholds are not specified, assume they are 0
   i.e. do not check thresholds, but still give input/ouput bandwidth for graphing
   This option also prevents tmp files of being writtena.

Options for saving results of previous checks to calculate Traffic & Utilization:

-P, --prev_perfdata
   Previous performance data (normally put '-P \$SERVICEPERFDATA\$' in nagios
   command definition). This is used in place of temporary file that otherwise
   could be needed when you want to calculate utilization of the interface
   Also used to cache data about which OIDs to lookup instead of having
   to check interface names table each time.
-T, --prev_checktime
   This is used with -P and is a previous time plugin data was obtained,
   use it as '-T \$LASTSERVICECHECK\$'. This is now optional as plugin
   will also save time as part of performance variables and get it with -P
--pcount=INTEGER 
   Default: 2
   How many sets of previus data to keep as performance data. By keeping
   at least couple sets allows for more realistic and less 'bursty' results
   but nagios has buffer limits so very large output of performance data
   would not be kept.
-d, --delta=seconds
   Default: 300 seconds = 5 minutes
   Expected time between checks in seconds. Used for making sure traffic
   can be calculated properly. If plugin receives is run more often than
   0.75 of specified value, it'll not use results but keep previous data
   for later check. If it is run and receives results more than 4 times
   later then this value, it'll discard all previous performance data
   and start calculation again next time it is run.
-F, --filestore[=<filename>|<directory>]
   When you use -P option that causes plugin to use previous performance data 
   that is passed as an argument to plugin to calculate in/out bandwidth
   instead of storing data in temporary file. This option is an alternative
   to -P and causes results of previous check to be saved in a file.
   If this option has a parameter and it is a directory, then temporary 
   file will be saved in this directory, otherwise /tmp is used.
   If parameter is a filename then it is used as a first part in
   how temporary file is named.
--nagios_with_saveddata
   Enables experimental support for future Nagios SAVEDATA (output after ||)
   where cached data for next plugin use goes to special buffer and not PERFDATA
   [THIS IS AN EXPERIMENTAL OPTION THAT MAY BE REMOVED OR RENAMED IN THE FUTURE]

SNMP Authentication options and options valid only with SNMP:

-H, --hostname=HOST
   name or IP address of host to check
-C, --community=COMMUNITY NAME
   community name for the SNMP agent (used with v1 or v2c protocols)
-2, --v2c
   use snmp v2c (can not be used with -l, -x)
-l, --login=LOGIN ; -x, --passwd=PASSWD
   Login and auth password for snmpv3 authentication 
   If no priv password exists, implies AuthNoPriv 
-X, --privpass=PASSWD
   Priv password for snmpv3 (AuthPriv protocol)
-L, --protocols=<authproto>,<privproto>
   <authproto> : Authentication protocol (md5|sha : default md5)
   <privproto> : Priv protocols (des|aes : default des) 
-p, --port=PORT
   SNMP port (Default 161)
-o, --octetlength=INTEGER
   Max-size of the SNMP message. Usefull in case of too long responses.
   Be carefull with network filters. Range 484 - 65535, default are
   usually 1472,1452,1460 or 1440.     
-N, --descrname_oid=OID
   SNMP OID of the description table (optional for non-standard equipment)
-O, --optionaltext_oid=OID
   SNMP OID for additional optional commentary text name for each interface
   This is added into output as interface "label" (but it is not matched on).
-g, --64bits
   Use 64 bits counters instead of the standard counters when checking
   bandwidth & performance data for interface >= 1Gbps.
   You must use snmp v2c or v3 to get 64 bits counters.
-m, --minimize_queries | -mm, --minimum_queries 
   Optimization options to minimize number of SNMP queries. 
   This is done by saving table ids in performance data (see -P above) and doing
   all SNMP checks together. When "-mm" or "--minimum_queries" option is used
   the number of queries is even smaller but there are no checks done to make
   sure ifindex description is still the same (not safe only if you add vlans)
--bulk_snmp_queries
   Enables using GET_BULK_REQUEST (SNMP v2 and v3 only) to get data
   While this may work and be faster on some systems, it fails on others 
--cisco=[oper,][addoper,][linkfault,][use_portnames|show_portnames]
   This enables special cisco snmp additions which:
   1) Provide extra detail on operational and fault status for physical ports.
      There are 3 tables that are available: 'operStatus','AdditionalOperStatus',
      'LinkFaultStatus' (some switches have one, some may have all 3), if you do
      not specify an attempt will be made for all tables but if caching is used
      what is found available will be cached for future requests.
   2) Optional "use_portnames" argument means that instead of using normal SNMP
      description OID table (or the one you could supply with -N) it would match
      names with port description names that you set with with 'set port name',
      this does however restrict to only cisco module ports (ifindex maybe larger
      and include also non-port interfaces such as vlan).
   3) Optional "show_portname" causes port names to go as comments (do not use with -O)
--stp[=disabled|blocking|listening|learning|forwarding|broken]
   This enables reporting of STP (Spanning Tree Protocol) switch ports states.
   If STP port state changes then plugin for period of time (default 15 minutes)
   reports WARNING. Optional parameter after --stp= is expected STP state of
   the port and plugin will return CRITICAL error if its anything else. 
EOT
}

# For verbose output (updated 06/06/12 to write to debug file if specified)
sub verb {
    my $t=shift;
    if (defined($o_verb)) {
	if ($o_verb eq "") {
		print $t, "\n";
	}
	else {
	    if (!open (DEBUGFILE, ">>$o_verb")) {
		print $t, "\n";
	    }
	    else {
		print DEBUGFILE $t,"\n";
		close DEBUGFILE;
	    }
	}
    }
}

# Load previous performance data
# 05/20/12: modified to use quotewords as suggested by Nicholas Scott
sub process_perf {
   my %pdh;
   my ($nm,$dt);
   use Text::ParseWords;
   foreach (quotewords('\s+',1,$_[0])) {
       if (/(.*)=(.*)/) {
           ($nm,$dt)=($1,$2);
           verb("prev_perf: $nm = $dt");
           # in some of my plugins time_ is to profile how long execution takes for some part of plugin
           # $pdh{$nm}=$dt if $nm !~ /^time_/;
           $pdh{$nm}=$dt;
           $pdh{$nm}=$1 if $dt =~ /(\d+)c/; # 'c' is added as designation for octet
           push @prev_time,$1 if $nm =~ /.*\.(\d+)/ && (!defined($prev_time[0]) || $prev_time[0] ne $1); # more then one set of previously cached performance data
       }
   }
   return %pdh;
}

# this is normal way check_snmp_int does it
# (function written by WL but based on previous code) 
sub perf_name {
  my ($iname,$vtype) = @_;
  $iname =~ s/'\/\(\)/_/g; #' get rid of special characters in performance description name
  return "'".$iname."_".$vtype."'";
}

# alternative function used by WL
sub perf_name2 {
  my ($iname,$vtype) = @_;
  $iname =~ s/'\/\(\)/_/g; #'
  $iname =~ s/\s/_/g;
  return $iname."_".$vtype;
} 

# This is used to lookup previous perf data.
# If only one argument is given, it is used as is. 
# Otherwise perf_name is called with these two arguments to get the name
# so function does something similar to $prev_perf{perf_name($iname,$vtype)} 
sub prev_perf {
 my ($name, $vtype) = @_;

 $name = perf_name($name,$vtype) if defined($vtype);
 return $prev_perf_data{$name} if exists($prev_perf_data{$name});
 # also lets check in case nagios stripped quotes out of perf
 if ($name =~ /^'(.*)`$/) {
    return $prev_perf_data{$1} if exists($prev_perf_data{$1});
 }
 return undef;
}

sub check_options {
    Getopt::Long::Configure ("bundling");
	GetOptions(
   	'v:s'	=> \$o_verb,		'verbose:s' => \$o_verb, "debug:s" => \$o_verb, 
        'h'     => \$o_help,    	'help'        	=> \$o_help,
        'H:s'   => \$o_host,		'hostname:s'	=> \$o_host,
        'p:i'   => \$o_port,   		'port:i'	=> \$o_port,
	'n:s'   => \$o_descr,           'name:s'        => \$o_descr,
        'C:s'   => \$o_community,	'community:s'	=> \$o_community,
	 '2'	=> \$o_version2,	'v2c'		=> \$o_version2,
	'l:s'	=> \$o_login,		'login:s'	=> \$o_login,
	'x:s'	=> \$o_passwd,		'passwd:s'	=> \$o_passwd,
	'X:s'	=> \$o_privpass,	'privpass:s'	=> \$o_privpass,
	'L:s'	=> \$v3protocols,	'protocols:s'	=> \$v3protocols,
        't:i'   => \$o_timeout,    	'timeout:i'	=> \$o_timeout,
	'i'	=> \$o_inverse,		'inverse'	=> \$o_inverse,
	'a'	=> \$o_admin,		'admin'		=> \$o_admin,
	'D'     => \$o_dormant,         'dormant'       => \$o_dormant,
        'I'     => \$o_ignorestatus,    'ignorestatus'  => \$o_ignorestatus,
	'K'	=> \$o_admindown_ok,	'admindown_ok'	=> \$o_admindown_ok,
	'r'	=> \$o_noreg,		'noregexp'	=> \$o_noreg,
	'V'	=> \$o_version,		'version'	=> \$o_version,
        'f'     => \$o_perf,            'perfparse'     => \$o_perf,
        'e'     => \$o_perfe,           'error'     	=> \$o_perfe,
        'k'     => \$o_checkperf,       'perfcheck'   	=> \$o_checkperf,
        'q'     => \$o_ext_checkperf,   'extperfcheck'  => \$o_ext_checkperf,
        'w:s'   => \$o_warn_opt,       	'warning:s'   	=> \$o_warn_opt,
        'c:s'   => \$o_crit_opt,      	'critical:s'   	=> \$o_crit_opt,
	'z'	=> \$o_zerothresholds,	'zerothresholds' => \$o_zerothresholds,
        'B'     => \$o_kbits,           'kbits'         => \$o_kbits,
        's:i'   => \$o_short,      	'short:i'   	=> \$o_short,
        'g'   	=> \$o_highperf,      	'64bits'   	=> \$o_highperf,
        'S:s'   => \$o_intspeed,      	'intspeed:s'   	=> \$o_intspeed,
        'y'   	=> \$o_perfp,      	'perfprct'   	=> \$o_perfp,
        'Y'   	=> \$o_perfr,      	'perfspeed'   	=> \$o_perfr,
	'Z'     => \$o_perfo,           'perfoctet'     => \$o_perfo,
        'M'   	=> \$o_meg,      	'mega'   	=> \$o_meg,
        'G'   	=> \$o_gig,      	'giga'   	=> \$o_gig,
        'u'   	=> \$o_prct,      	'prct'   	=> \$o_prct,
	'o:i'   => \$o_octetlength,    	'octetlength:i' => \$o_octetlength,
	'label'   => \$o_label,    	
        'd:i'   => \$o_delta,           'delta:i'     	=> \$o_delta,
	'N:s'	=> \$o_descroid,	'descrname_oid:s' => \$o_descroid,
	'O:s'	=> \$o_commentoid,	'optionaltext_oid:s' => \$o_commentoid,
	'P:s'	=> \$o_prevperf,	'prev_perfdata:s' => \$o_prevperf,
	'T:s'   => \$o_prevtime,        'prev_checktime:s'=> \$o_prevtime,
	'pcount:i' => \$o_pcount,
	'm'	=> \@o_minsnmp,		'minimize_queries' => \$o_minsnmp, 
	'minimum_queries' => \$o_maxminsnmp, 'bulk_snmp_queries' => \$o_bulksnmp,
	'F:s'   => \$o_filestore,       'filestore:s' => \$o_filestore,
	'cisco:s' => \$o_ciscocat,	'stp:s' =>	\$o_stp,
	'nagios_with_saveddata' => \$o_nagios_saveddata
    );
    if (defined ($o_help) ) { help(); exit $ERRORS{"UNKNOWN"}};
    if (defined($o_version)) { p_version(); exit $ERRORS{"UNKNOWN"}};

    # check snmp information
    # 06/25/12: this is now required only if plugin name starts with check_snmp or if host is specified)
    if ($0 =~ /^check_snmp/ || defined($o_host)) {
	if ($do_snmp==0) { print "Can't locate Net/SNMP.pm\n"; exit $ERRORS{"UNKNOWN"}}
	if (defined($o_descroid)) { $descr_table = $o_descroid; }
	if (!defined($o_descr) && !defined($o_community) && (!defined($o_login) || !defined($o_passwd)) )
	    { print "Specify community and put snmp login info!\n"; print_usage(); exit $ERRORS{"UNKNOWN"}}
	if ((defined($o_login) || defined($o_passwd)) && (defined($o_community) || defined($o_version2)) )
	    { print "Can't mix snmp v1,2c,3 protocols!\n"; print_usage(); exit $ERRORS{"UNKNOWN"}}
	if (defined ($v3protocols)) {
	    if (!defined($o_login)) { print "Put snmp V3 login info with protocols!\n"; print_usage(); exit $ERRORS{"UNKNOWN"}}
	    my @v3proto=split(/,/,$v3protocols);
	    if ((defined ($v3proto[0])) && ($v3proto[0] ne "")) {$o_authproto=$v3proto[0];  }	# Auth protocol
	    if (defined ($v3proto[1])) {$o_privproto=$v3proto[1];	}	# Priv  protocol
	    if ((defined ($v3proto[1])) && (!defined($o_privpass)))
	      { print "Put snmp V3 priv login info with priv protocols!\n"; print_usage(); exit $ERRORS{"UNKNOWN"}}
	}
        if (defined($o_minsnmp[1])) {
	    $o_maxminsnmp=1;
        }
	elsif (defined($o_minsnmp[0])) {
	    $o_minsnmp=1;
	}
	if (defined($o_maxminsnmp)) { 
	    if (defined($o_minsnmp)) {
		print "You dont need to use -m when you already specified -mm."; print_usage(); exit $ERRORS{"UNKNOWN"};
	    }
	    else {
		$o_minsnmp=1;
		# $o_bulksnmp=1;
	    }
	}
	# Check snmpv2c or v3 with 64 bit counters
	if (defined ($o_highperf) && (!defined($o_version2) && defined($o_community)))
	  { print "Can't get 64 bit counters with snmp version 1\n"; print_usage(); exit $ERRORS{"UNKNOWN"}}
	if (defined ($o_highperf)) {
	  if (eval "require bigint") {
	    use bigint;
	  } else  { print "Need bigint module for 64 bit counters\n"; print_usage(); exit $ERRORS{"UNKNOWN"}}
	}
	$perfcache_recache_trigger=$perfcache_recache_max if defined($o_maxminsnmp);
	if (defined($o_commentoid)) {
	    if ($o_commentoid !~ /\./) {
		print "Comment OID is not specified or is not valid\n"; print_usage(); exit $ERRORS{"UNKNOWN"};
	    }
	    $o_commentoid.='.' if $o_commentoid !~ /\.$/;
	}
	#### octet length checks
	if (defined ($o_octetlength) && (isnnum($o_octetlength) || $o_octetlength > 65535 || $o_octetlength < 484 )) {
	    print "octet length must be < 65535 and > 484\n";print_usage(); exit $ERRORS{"UNKNOWN"};
	}
    }
    else {
	$do_snmp=0;
	if (defined($o_octetlength) || defined($o_highperf) || defined($o_maxminsnmp) || defined($o_minsnmp) ||
	    defined($v3protocols) || defined($o_login) || defined($o_passwd) || defined($o_version2) || defined($o_community) ||
	    defined($o_ciscocat) || defined($o_stp) || defined($o_commentoid) || defined($o_descroid)) {
	   print "Option you specified is only valid with SNMP. Maybe you forgot to specify hostname with -h?\n";print_usage(); exit $ERRORS{"UNKNOWN"};
	}
    }
    if (defined($o_timeout) && (isnnum($o_timeout) || ($o_timeout < 2) || ($o_timeout > 60))) 
	{ print "Timeout must be >1 and <60 !\n"; print_usage(); exit $ERRORS{"UNKNOWN"}}
    if (!defined($o_timeout)) {$o_timeout=5;}

    # check if -e without -f
    if ( defined($o_perfe) && !defined($o_perf))
        { print "Cannot output error without -f option!\n"; print_usage(); exit $ERRORS{"UNKNOWN"}}		
	if (defined ($o_perfr) && defined($o_perfp) )  {
	    print "-Y and -y options are exclusives\n"; print_usage(); exit $ERRORS{"UNKNOWN"}}
	if ((defined ($o_perfr) || defined($o_perfp) || defined($o_perfo)) && !defined($o_checkperf))  {
	    print "Cannot put -Y or -y or -Z options without perf check option (-k) \n"; print_usage(); exit $ERRORS{"UNKNOWN"}}
    if (defined ($o_short)) {
      #TODO maybe some basic tests ? characters return empty string
    }
    if (defined($o_prevperf)) {
	if (defined($o_perf)) {
		%prev_perf_data=process_perf($o_prevperf);
		# put last time nagios was checked in timestamp array
		if (defined($prev_perf_data{'ptime'})) {
			push @prev_time, $prev_perf_data{'ptime'};
		}
		elsif (defined($o_prevtime)) {
			push @prev_time, $o_prevtime;
			$prev_perf_data{'ptime'}=$o_prevtime;
		}
		else {
			@prev_time=();
		}
		# numeric sort for timestamp array (this is from lowest time to highiest, i.e. to latest)
		my %ptimes=();
		$ptimes{$_}=$_ foreach @prev_time;
 	        @prev_time = sort { $a <=> $b } keys(%ptimes);
	}
	else {
		print "need -f option first \n"; print_usage(); exit $ERRORS{"UNKNOWN"};
	}
    }
    if (defined($o_prevtime) && !defined($o_prevperf))
    { 
	print "Specifying previous servicecheck is only necessary when you send previous performance data (-T)\n"; 
	print_usage(); exit $ERRORS{"UNKNOWN"};
    }
    if (defined ($o_checkperf)) {
      my @o_warn=();
      @o_warn=split(/,/,$o_warn_opt) if defined($o_warn_opt);
      if (!defined($o_zerothresholds) && defined($o_ext_checkperf) && (!defined($o_warn_opt) || $#o_warn != 5)) {
        print "Add '-z' or specify 6 warning levels for extended checks \n"; print_usage(); exit $ERRORS{"UNKNOWN"};
      } 
      if (!defined($o_zerothresholds)&& !defined($o_ext_checkperf) && (!defined($o_warn_opt) || $#o_warn !=1 )){
	print "Add 'z' or specify 2 warning levels for bandwidth checks \n"; print_usage(); exit $ERRORS{"UNKNOWN"};
      }
      my @o_crit=();
      @o_crit=split(/,/,$o_crit_opt) if defined($o_crit_opt);
      #verb(" $o_crit_opt :: $#o_crit : @o_crit"); 
      if (!defined($o_zerothresholds) && defined($o_ext_checkperf) && (!defined($o_crit_opt) || $#o_crit != 5)) {
        print "Add '-z' or specify 6 critical levels for extended checks \n"; print_usage(); exit $ERRORS{"UNKNOWN"};
      } 
      if (!defined($o_zerothresholds) && !defined($o_ext_checkperf) && (!defined($o_crit_opt) || $#o_crit !=1 )) {
	print "Add '-z' or specify 2 critical levels for bandwidth checks \n"; print_usage(); exit $ERRORS{"UNKNOWN"};
      }
      for (my $i=0;$i<=$#o_warn;$i++) { 
        if ($o_warn[$i] =~ /^\d+$/) {
          $o_warn_max[$i] = $o_warn[$i];
        } elsif ($o_warn[$i] =~ /^(\d+)?-(\d+)?$/) {
          $o_warn_min[$i] = $1 if $1;
          $o_warn_max[$i] = $2 if $2;
        } else {
          print "Can't parse warning level: $o_warn[$i]\n"; print_usage(); exit $ERRORS{"UNKNOWN"};
        }
      }
      for (my $i=0;$i<=$#o_crit;$i++) {
        if ($o_crit[$i] =~ /^\d+$/) {
          $o_crit_max[$i] = $o_crit[$i];
        } elsif ($o_crit[$i] =~ /^(\d+)?-(\d+)?$/) {
          $o_crit_min[$i] = $1 if $1;
          $o_crit_max[$i] = $2 if $2;
        } else {
          print "Can't parse critical level: $o_crit[$i]\n"; print_usage(); exit $ERRORS{"UNKNOWN"};
        }
      }
      for (my $i=0;$i<=$#o_warn;$i++) {
        if (defined($o_crit_max[$i]) && defined($o_warn_max[$i]) &&
	  $o_crit_max[$i] && $o_warn_max[$i] && $o_warn_max[$i] > $o_crit_max[$i]) {
            print "Warning max must be < Critical max level \n"; print_usage(); exit $ERRORS{"UNKNOWN"};
        }
        if (defined($o_crit_min[$i]) && defined($o_warn_min[$i]) &&
	  $o_warn_min[$i] && $o_crit_min[$i] && $o_warn_min[$i] < $o_crit_min[$i]) {
            print "Warning min must be > Critical min level \n"; print_usage(); exit $ERRORS{"UNKNOWN"};
        }
      }
      if ((defined ($o_meg) && defined($o_gig) ) || (defined ($o_meg) && defined($o_prct) )|| (defined ($o_gig) && defined($o_prct) )) {
	print "-M -G and -u options are exclusives\n"; print_usage(); exit $ERRORS{"UNKNOWN"};
      }
    }
    # cisco hacks to use or show user-specified port names (WL)
    if (defined($o_ciscocat)) {
	if (!defined($o_host)) {
	    print "Cisco option is only valid with SNMP when checking remote host\n";print_usage(); exit $ERRORS{"UNKNOWN"};
	}
	$o_cisco{$_}=$_ foreach (split ',',$o_ciscocat);
        if (defined($o_cisco{use_portnames})) {
	    if (defined($o_descroid)) {
		print "Can not use -N when --cisco=use_portnames option is used\n"; print_usage(); exit $ERRORS{'UNKNOWN'};
	    }
	    else {
		$descr_table = $cisco_port_name_table; 
	    }
        }
        elsif (defined($o_cisco{show_portnames})) {
            if (defined($o_commentoid)) {
                print "Can not use -O when --cisco=show_portnames option is used\n"; print_usage(); exit $ERRORS{'UNKNOWN'};
            }
            else {
		$o_commentoid = $cisco_port_name_table;
	    }
        }
	$o_cisco{auto}='auto' if (!defined($o_cisco{oper}) && !defined($o_cisco{addoper}) && !defined($o_cisco{linkfault}) &&!defined($o_cisco{noauto}));
	verb("Cisco Options: ".join(',',keys %o_cisco));
    }
    # stp support
    if (defined($o_stp) && $o_stp ne '') {
	if (!defined($o_host)) {
	    print "STP option is currently only valid with SNMP when checking remote host\n";print_usage(); exit $ERRORS{"UNKNOWN"};
	}
	$stp_portstate_reverse{$stp_portstate{$_}}=$_ foreach keys %stp_portstate;
	if (!defined($stp_portstate_reverse{$o_stp})) {
		print "Incorrect STP state specified after --stp=\n"; print_usage(); exit $ERRORS{'UNKNOWN'};
	}
    }
    # interface speed
    $check_speed = 1 if defined($o_prct) || defined($o_perfp);
    if (defined($o_intspeed) && $o_intspeed =~ /(\d+)/) {
	$specified_speed = $1;
	$specified_speed = $specified_speed*1024 if $o_intspeed =~ /Kb?$/;
	$specified_speed = $specified_speed*1024*1024 if $o_intspeed =~ /Mb?$/;
	if ($o_intspeed =~ /^(.*)<>/) {
	    $speed_alert = $1;
	    $check_speed = 1;
	    if (!exists($ERRORS{$speed_alert})) {
		print "Incorrect alert type $speed_alert specified at --intspeed=\n"; print_usage(); exit $ERRORS{'UNKNOWN'};
	    }
	    if ($specified_speed==0) {
		print "Must specify speed after alert type with --intspeed\n"; print_usage(); exit $ERRORS{"UNKNOWN"};
	    }
	}
	else {
	    $check_speed = 0; # since we specified speed here, we don't need to check it
	}
    }
}

# new function from code that checks if interface name matches name given with -n option
sub int_name_match {
    my $name = shift;

    return 1 if !defined($o_descr);
    # test by regexp or exact match
    return ($name eq $o_descr) if defined($o_noreg);
    return ($name =~ /$o_descr/);
}

# new function that cleans interface name as it may appear in SNMP into what we use
sub clean_int_name {
    my $name = shift;

    # below chop line is based on code by Y. Charton to remove ^@ (NULL ?) and other
    # non-ASCII characters at the end of the interface description, this allows to
    # correctly match interfaces for Windows servers, since they have buggy snmp
    chop($name) if (ord(substr($name,-1,1)) > 127 || ord(substr($name,-1,1)) == 0 );

    $name =~ s/[[:cntrl:]]//g;
    chomp $name;
    return $name;
}

# function that opens proper session for SNMP v1/2/3
sub create_snmp_session {
  my ($session,$error);

  if ( defined($o_login) && defined($o_passwd)) {
    # SNMPv3 login
    if (!defined ($o_privpass)) {
    verb("SNMPv3 AuthNoPriv login : $o_login, $o_authproto");
      ($session, $error) = Net::SNMP->session(
	-hostname   	=> $o_host,
	-version	=> '3',
	-port      	=> $o_port,
	-username	=> $o_login,
	-authpassword	=> $o_passwd,
	-authprotocol	=> $o_authproto,
	-timeout        => $o_timeout
      );  
    } else {
      verb("SNMPv3 AuthPriv login : $o_login, $o_authproto, $o_privproto");
      ($session, $error) = Net::SNMP->session(
	-hostname   	=> $o_host,
	-version	=> '3',
	-username	=> $o_login,
	-port      	=> $o_port,
	-authpassword	=> $o_passwd,
	-authprotocol	=> $o_authproto,
	-privpassword	=> $o_privpass,
	-privprotocol     => $o_privproto,
	-timeout          => $o_timeout
      );
    }
    $snmp_session_v = 3;
  } else {
    if (defined ($o_version2)) {
      # SNMPv2c Login
      verb("SNMP v2c login");
      ($session, $error) = Net::SNMP->session(
	-hostname  => $o_host,
	-version   => 2,
	-community => $o_community,
	-port      => $o_port,
	-timeout   => $o_timeout
      );
      $snmp_session_v = 2;
    } else {
      # SNMPV1 login
      verb("SNMP v1 login");
      ($session, $error) = Net::SNMP->session(
	-hostname  => $o_host,
	-community => $o_community,
	-port      => $o_port,
	-timeout   => $o_timeout
      );
      $snmp_session_v = 1;
    }
  }
  if (!defined($session)) {
   printf("ERROR opening session: %s.\n", $error);
   exit $ERRORS{"UNKNOWN"};
  }
  if (defined($o_octetlength) || defined($o_bulksnmp)) {
	my $oct_resultat=undef;
	my $oct_test=$session->max_msg_size();
	verb(" actual max octets:: $oct_test");
	if (defined($o_octetlength)) {
	    $oct_resultat = $session->max_msg_size($o_octetlength);
	}
	else { # for bulksnmp we set message size to 5 times its default
	    $oct_resultat = $session->max_msg_size($oct_test * 5);
	}
	if (!defined($oct_resultat)) {
		 printf("ERROR: Session settings : %s.\n", $session->error);
		 $session->close;
		 exit $ERRORS{"UNKNOWN"};
	}
	$oct_test= $session->max_msg_size();
	verb(" new max octets:: $oct_test");
  }
  return $session;
}

# function that does snmp get request for a list of OIDs
# 1st argument is session, 2nd is ref to list of OIDs,
# 3rd is optional text for error & debug info
# 4th argument is optional hash of array to be filled with results
sub snmp_get_request {
  my ($session, $oids_ref, $table_name, $results) = @_;
  my $result = undef;

  verb("Doing snmp request on ".$table_name." OIDs: ".join(' ',@{$oids_ref}));
  if (defined($o_bulksnmp) && $snmp_session_v > 1) {
    my @oids_bulk=();
    my ($oid_part1,$oid_part2);
    foreach(@{$oids_ref}) {
	if (/^(.*)\.(\d+)$/) {
		$oid_part1=$1;
		$oid_part2=$2;
		$oid_part2-- if $oid_part2 ne '0';
		$oid_part1.='.'.$oid_part2;
		push @oids_bulk,$oid_part1;
	}
    }
    verb("Converted to bulk request on OIDs: ".join(' ',@oids_bulk));
    $result = $session->get_bulk_request(
      -nonrepeaters => scalar(@oids_bulk),
      -maxrepetitions => 0,
      -varbindlist => \@oids_bulk,
    );
  }
  else {
    $result = $session->get_request(
      -varbindlist => $oids_ref
    );
  }
  if (!defined($result)) {
    printf("SNMP ERROR getting %s : %s.\n", $table_name, $session->error); 
    $session->close;
    exit $ERRORS{"UNKNOWN"};
  }

  verb("Finished SNMP request. Result contains ".scalar(keys %$result)." entries:");
  foreach(keys %$result) { 
      $results->{$_} = $result->{$_} if defined($results);
      verb(" ".$_." = ".$result->{$_});
  }

  return $result;
}

# executes shell command, returns results blob file pointer
sub exec_shell_command {
  my $shell_command = shift;
  
  verb("Executing: $shell_command");
  $shell_pid=open(SHELL_DATA, "$shell_command 2>&1 |");
  if (!$shell_pid) {
      print "UNKNOWN ERROR - could not execute $shell_command - $!";
      exit $ERRORS{'UNKNOWN'};
  }
  return \*SHELL_DATA;
}

# closes blob/file pointer, end of shell command execution
sub finish_shell_command {
  my $file_ref = shift;
  close $file_ref;
  $shell_pid = undef;
}

# this function gets all interface data on localhost
# by executing ifconfig and other commands as necessary
# for the machine and architecture its being run on
sub getdata_localhost {
   my $linux_ifconfig = "/sbin/ifconfig";
   my $linux_ethtool = "/sbin/ethtool";
   my $linux_iwconfig = "/sbin/iwconfig";

   # first find architecture we're running on
   my $shell_command;
   my $shell_ref = undef;
   my $os = `uname`;
   chomp $os;

   # Linux output of "ifconfig":
   #
   # wlan0 Link encap:Ethernet  HWaddr a0:88:b4:97:9b:d4  
   #       inet addr:192.168.1.31  Bcast:192.168.1.255  Mask:255.255.255.0
   #       inet6 addr: fe80::a288:b4ff:fe97:9bd4/64 Scope:Link
   #       UP BROADCAST RUNNING MULTICAST  MTU:1500  Metric:1
   #       RX packets:3610846 errors:0 dropped:0 overruns:0 frame:0
   #       TX packets:3054674 errors:0 dropped:0 overruns:0 carrier:0
   #       collisions:0 txqueuelen:1000 
   #       RX bytes:2637787245 (2.6 GB)  TX bytes:604337476 (604.3 MB)
   # 
   # Linux output of "netstat -n -i": 
   # 
   #  Kernel Interface table
   #  Iface        MTU Met  RX-OK RX-ERR  RX-DRP RX-OVR    TX-OK TX-ERR TX-DRP TX-OVR Flg
   #  eth0       1500 0         0      0      0       0        0      0      0      0 BMU
   #  lo        16436 0    221065      0      0       0   221065      0      0      0 LRU
   #  wlan0      1500 0   3657422      0      0       0  3100992      0      0      0 BMRU
   #
   # (these are packets, so should multiply by MTU but size may actually different)
   #
   # Linux output of "ip link show" :
   #
   # 1: lo: <LOOPBACK,UP,LOWER_UP> mtu 16436 qdisc noqueue state UNKNOWN 
   #    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
   # 2: eth0: <NO-CARRIER,BROADCAST,MULTICAST,UP> mtu 1500 qdisc pfifo_fast state DOWN qlen 1000
   #    link/ether f0:de:f1:76:83:df brd ff:ff:ff:ff:ff:ff
   # 3: wlan0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc mq state UP qlen 1000
   #    link/ether a0:88:b4:97:9b:d4 brd ff:ff:ff:ff:ff:ff
   # 4: virbr0: <NO-CARRIER,BROADCAST,MULTICAST,UP> mtu 1500 qdisc noqueue state DOWN 
   #    link/ether 86:cd:48:f1:05:ad brd ff:ff:ff:ff:ff:ff

   # FREEBSD output of "ifconfig" :
   #
   # plip0: flags=8810<POINTOPOINT,SIMPLEX,MULTICAST> metric 0 mtu 1500
   # lo0: flags=8049<UP,LOOPBACK,RUNNING,MULTICAST> metric 0 mtu 16384
   #     options=3<RXCSUM,TXCSUM>
   #     inet6 fe80::1%lo0 prefixlen 64 scopeid 0x4
   #     inet6 ::1 prefixlen 128
   #     inet 127.0.0.1 netmask 0xff000000
   #     nd6 options=3<PERFORMNUD,ACCEPT_RTADV>
   # 
   # FREEBSD output of netstat:
   #
   # vpn8# netstat -w 1
   #          input        (Total)           output
   #  packets  errs      bytes    packets  errs      bytes colls
   #  145159     0   82485349     153321     0  117743533     0
   #  136895     0   79084654     145018     0  111877348     0
   #  146279     0   81710082     153952     0  116857455     0
   #  143634     0   80602950     152005     0  116127801     0
   #  144205     0   81175701     151892     0  115836499     0
   #  146342     0   83031415     153968     0  118093209     0
   #  143365     0   80564430     151508     0  115702643     0
   #  145253     0   82320881     153062     0  116675147     0
   #  146909     0   81998714     155485     0  117155601     0
   #   91507     0   76590439      79098     0   35481375     0
   #  145148     0   81429871     153728     0  116617071     0
   #
   # Note: I think it should have been "netstat -bni -I <interface>" ...
   #
   # Script for bandwidth from http://www.unix.com/unix-dummies-questions-answers/9528-commnad-getting-bandwidth-usage.html:
   # open(NETSTAT, "/usr/bin/netstat -I vr0 1|") || die "$!";
   # 
   # for ($lineCount = 1; $lineCount <= 3; $lineCount++) {
   #    $inputLine = <NETSTAT>;
   #    chomp($inputLine);
   #     if ($lineCount == 3) {
   #          $inputLine =~ s/\s+/-/g;
   #          my @column = split(/-/, $inputLine);
   #          $throughPut = ($column[6]*8)/1024;
   #          print "$throughPut\n";
   #      };
   #};
   # #close(NETSTAT);

   # AIX ('entstat -d ent0' equivalent to ethtool
   # San Solaris (link_speed will return 0 for 10mbit and 1 for 100mbit
   #              link_mode will return 0 for half duplex and 1 for full duplex)
   #              Example: if you want the speed for /dev/hme2, you issue:  
   #                  /usr/sbin/ndd -set /dev/hme instance 2
   #                  /usr/sbin/ndd /dev/hme link_speed
   # Also see: https://cfengine.com/forum/read.php?3,27223

   if ($os ne "Linux") {
	printf("Only Linux is currently supported for local interfaces\n");
	exit $ERRORS{"UNKNOWN"};
   }
   # This is for linux, may want to move to separate function later
   else {
        $shell_ref = exec_shell_command("$linux_ifconfig -a");

	$num_int=0;
	my $int_lines=0;
	while (<$shell_ref>) {
	    chomp;
	    verb("got line: $_");
	    my @words = split;
	    if (!$int_lines && scalar(@words)>2 && $words[1] eq 'Link') {
		if (int_name_match($words[0])) {
		    $interfaces[$num_int] = { 
			  'descr' => $words[0], 'admin_up'=> $status{'DOWN'}, 'oper_up'=> $status{'DOWN'}, # considered common between SNMP and local checks
			  'in_bytes' => 0, 'out_bytes' => 0, 'in_packets' => 0, 'out_packets' => 0,  # considered common, but packets are not used
			  'in_errors' => 0, 'out_errors' => 0, 					     # considered common
			  'in_dropped' => 0, 'out_dropped' => 0,				     # common, same as discards for SNMP
			  'in_overruns' => 0, 'out_overruns' => 0,  				     # added to errors if not 0
			  'collisions' => 0, 'txqueuelen' => 0, 'metric' => 0, 'MTU'=>0		     # linux-specific names, not really used
		    };
		    $int_lines=1;
		}
	    }
	    elsif ($int_lines && scalar(@words)<2) {
		$int_lines=0;
		$num_int++;
	    }
	    elsif ($int_lines) {
		my $prefix="";
		foreach(@words) {
		    if ($_ eq "RX") { $prefix = "in_"; }
		    elsif ($_ eq "TX") { $prefix = "out_"; }
		    elsif ($_ eq "UP") { $interfaces[$num_int]{'admin_up'} = $status{'UP'}; }
		    elsif ($_ eq "RUNNING") { $interfaces[$num_int]{'oper_up'} = $status{'UP'}; }
		    elsif ($_ =~ /^(.*):(\d+)/) { 
			verb("   interface #".$num_int." (".$interfaces[$num_int]{'descr'}.") : ".$prefix.$1." = ".$2);
			$interfaces[$num_int]{$prefix.$1} = $2;
			$interfaces[$num_int]{$prefix.'errors'} += $2 if ($1 eq 'overruns');
		    }
		}
	    }
	}
	finish_shell_command($shell_ref);
	if ($check_speed) {
	    if (-f $linux_iwconfig) {
		my %wint = ();
		my $cint = undef;
		$shell_ref = exec_shell_command($linux_iwconfig);
		while (<$shell_ref>) {
		    chomp;
		    verb("got line: $_");
		    if ($_ eq "") {
			verb("   end interface $cint") if defined($cint);
			$cint = undef if defined($cint);
		    }
		    elsif (/^(\w+)\s+IEEE/) {
			verb("   start interface $1");
			$cint = $1;
		    }
		    elsif (/\s+Bit\sRate\=(\d+\.?\d?)\s+Mb/) {
			verb("   speed of ".$cint." is ".$1." Mb/s") if defined($cint);
			$wint{$cint} = $1 if defined($cint);
		    }
		}
		finish_shell_command($shell_ref);
		if (scalar(keys %wint)>0) {
		    for (my $i=0;$i<$num_int;$i++) {
			if (exists($wint{$interfaces[$i]{'descr'}})) {
			    $interfaces[$i]{'portspeed'} = $wint{$interfaces[$i]{'descr'}} *1024*1024;
			    verb("   speed of interface ".$interfaces[$i]{'descr'}." is ".$interfaces[$i]{'portspeed'}." bps");
			}
		    }
		}
	    }
	    if (-f $linux_ethtool) {
		for (my $i=0;$i < $num_int; $i++) {
		    if ($interfaces[$i]{'admin_up'} == $status{'UP'} && $interfaces[$i]{'oper_up'} == $status{'UP'}) {
			$shell_ref = exec_shell_command("$linux_ethtool ".$interfaces[$i]{'descr'});
			while(<$shell_ref>) {
			    if (/Speed:\s(\d+)Mb/) {
				$interfaces[$i]{'portspeed'} = $1 *1024*1024;
				verb("   speed of interface ".$interfaces[$i]{'descr'}." is ".$interfaces[$i]{'portspeed'}." bps");
			    }
			}
			finish_shell_command($shell_ref);
		    }
		}
	    }
	}
   }
}

# code that retrieves data by SNMP and populates interfaces array is now in this function
# instead of directly directly part of non-function main code below
sub getdata_snmp {
   # global arrays of interface data used used for snmp retrieval
   my $session = undef;
   my @tindex = ();
   my @oids = undef;
   my @oids_admin = undef;
   my @oid_descr=(); # this is actually only used with '-m' to double-check that cached index is correct
   my @oid_speed=();
   my @oid_speed_high=();
   my @oid_commentlabel=();
   my @oid_ciscostatus=();
   my @oid_ciscofaultstatus=();
   my @oid_ciscooperstatus=();
   my @oid_ciscoaddoperstatus=();
   my @oid_stpstate=();
   my %cisco_timap=();
   my %stp_ifmap=();
   my @stpport=();
   my @cport=();
   my @portspeed=();
   my @descr=();
   my %copt=();
   my %copt_next=();
   my $results = {};
   my (@oid_perf,@oid_perf_outoct,@oid_perf_inoct,@oid_perf_inerr,@oid_perf_outerr,@oid_perf_indisc,@oid_perf_outdisc)= (undef,undef,undef,undef,undef,undef,undef);
   my ($result1,$result2,$data1) = (undef,undef,undef);
   my $int_status_extratext="";

   # Create SNMP session
   $session = create_snmp_session();

   if (defined($o_minsnmp) && %prev_perf_data) {
      # load old-style arrays
      @tindex = split(',', prev_perf('cache_descr_ids')) if defined(prev_perf('cache_descr_ids'));
      @cport = split(',', prev_perf('cache_descr_cport')) if defined(prev_perf('cache_descr_cport'));
      @stpport = split(',', prev_perf('cache_descr_stpport')) if defined(prev_perf('cache_descr_stpport'));
      @portspeed = split(',', prev_perf('cache_int_speed')) if defined(prev_perf('cache_int_speed')) && $specified_speed==0;
      @descr = split(',', prev_perf('cache_descr_names')) if defined(prev_perf('cache_descr_names'));

      # clear old index if anything seems wrong with cached data
      my %tindex_hash = map { $_ => 1 } @tindex;
      @tindex = () if (scalar(@tindex) != scalar(keys %tindex_hash)) || # make sure no duplicates
		   (scalar(@tindex) != scalar(@descr)) ||
		   (defined($o_ciscocat) && (!defined(prev_perf('cache_descr_cport')) || scalar(@tindex) != scalar(@cport))) ||
		   (defined($o_stp) && (!defined(prev_perf('cache_descr_stpport')) || scalar(@tindex) != scalar(@stpport))) ||
		   (defined(prev_perf('cache_int_speed')) && scalar(@tindex) != scalar(@portspeed)) ||
		   # this checks that time of last saved indeces is not way too long ago, in which case we check them again
		   (!defined($perfcache_time) || $timenow < $perfcache_time || ($timenow - $perfcache_time) > $perfcache_recache_trigger);

      # load into our new array
      for (my $i=0;$i<scalar(@tindex);$i++) {
	 $interfaces[$i]={'descr' => $descr[$i]};
	 $interfaces[$i]{'speed'} = $portspeed[$i] if defined(prev_perf('cache_int_speed'));
      }
      if (defined(prev_perf('cache_cisco_opt'))) {
	 $copt{$_}=$_ foreach(split ',',prev_perf('cache_cisco_opt'));
      }

      if (scalar(@tindex)>0) {
	  $num_int = scalar(@tindex);
	  verb("Using cached data:");
	  verb("  tindex=".join(',',@tindex));
	  verb("  descr=".join(',',@descr));
	  verb("  speed=".join(',',@portspeed)) if scalar(@portspeed)>0;
	  verb("  copt=".join(',',keys %copt)) if scalar(keys %copt)>0;
	  if (scalar(@cport)>0) {
	     verb("  cport=".join(',',@cport));
	     @cport=() if $cport[0]==-1; # perf data with previous check done with --cisco but no cisco data was found
	  }
	  if (scalar(@stpport)>0) {
	     verb("  stpport=".join(',',@stpport));
	     @stpport=() if $stpport[0]==-1; # perf data with previous check done with --stp but no stp data was found
	  }
      }
   }

   if (scalar(@tindex)==0) {
      # WL: Get cisco port->ifindex map table
      if (defined($o_ciscocat)) {
	 $result2 = $session->get_table(
		-baseoid => $cisco_port_ifindex_map 
	 );
	 if (!defined($result2)) {
		printf("ERROR: Cisco port-index map table : %s.\n", $session->error);
		$session->close;
		exit $ERRORS{"UNKNOWN"};
	 }
	 foreach (keys %$result2) {
		$cisco_timap{$result2->{$_}}=$1 if /$cisco_port_ifindex_map\.(.*)/;
	 }
      }
      # WL: Get stp port->ifindex map table
      if (defined($o_stp)) {
         $result1 = $session->get_table(
                -baseoid => $stp_dot1dbase_ifindex_map
         );
         if (!defined($result1)) {
                printf("ERROR: STP port-index map table : %s.\n", $session->error);
                $session->close;
                exit $ERRORS{"UNKNOWN"};
         }
         foreach (keys %$result1) {
                $stp_ifmap{$result1->{$_}}=$1 if /$stp_dot1dbase_ifindex_map\.(.*)/;
         }
      }
      $perfcache_time = $timenow;
      verb("Getting Interfaces Description Table ($descr_table):");
      # Get description table
      $result1 = $session->get_table(
	 -baseoid => $descr_table
      );
      if (!defined($result1)) {
	 printf("ERROR: Description table : %s.\n", $session->error);
	 $session->close;
	 exit $ERRORS{"UNKNOWN"};
      }
      # Select interface by regexp of exact match and put the oid to query in an array
      foreach my $key (keys %$result1) {
	 $data1 = clean_int_name($result1->{$key});
	 verb(" OID : $key, Clean Desc : $data1, Raw Desc: ".$result1->{$key});

	 if (int_name_match($data1) && $key =~ /$descr_table\.(.*)/) {
	    $interfaces[$num_int] = { 'descr' => '', 'admin_up' => 0, 'oper_up' => 0, 'in_bytes' => 0, 'out_bytes' => 0, 
				   'in_packets' => 0, 'out_packets' => 0, 'in_errors' => 0, 'out_errors' => 0 };
	    # WL: get the index number of the interface (using additional map in case of cisco) 
	    if (defined($o_ciscocat)) {
		if (defined($o_cisco{'use_portnames'}) && defined($result2->{$cisco_port_ifindex_map.'.'.$1})) {
			$cport[$num_int] = $1;
			$tindex[$num_int] = $result2->{$cisco_port_ifindex_map.'.'.$1};
		}
		elsif (defined($cisco_timap{$1})) {
			$cport[$num_int] = $cisco_timap{$1};
			$tindex[$num_int] = $1;
		}
		else {
			$tindex[$num_int] = $1;
		}
	    }
	    else {
		$tindex[$num_int] = $1;
	    }
	    # WL: find which STP port to retrieve data for that corresponds to this ifindex port
	    if (defined($o_stp)) {
		$stpport[$num_int] = $stp_ifmap{$tindex[$num_int]} if exists($stp_ifmap{$tindex[$num_int]});
	    }
	    # get the full description and get rid of special characters (specially for Windows)
	    $interfaces[$num_int]{'descr'}=$data1;
	    $num_int++;
	 }
      }
   }

   if ($num_int == 0) {
      $session->close;
   }
   else {
      # Change to 64 bit counters if option is set : 
      if (defined($o_highperf)) {
	 $out_octet_table=$out_octet_table_64;
	 $in_octet_table=$in_octet_table_64;
      }

      # WL: Prepare list of all OIDs to be retrieved for interfaces we want to check
      for (my $i=0;$i<$num_int;$i++) {
	 verb("Name : $interfaces[$i]{'descr'}, Index : $tindex[$i]");

	 # put the admin or oper oid in an array
	 $oids[$i]= defined ($o_admin) ? $admin_table . $tindex[$i] : $oper_table . $tindex[$i] ;
	 $oids_admin[$i]= $admin_table . $tindex[$i];
	 # this is for verifying cached description index is correct
	 # (just in case ifindex port map or cisco port name changes)
	 if (defined($o_minsnmp) && !defined($o_maxminsnmp)) {
	    if (defined($o_cisco{'use_portnames'})) {
	       $oid_descr[$i] = $descr_table .'.'.$cport[$i];
	    }
	    else {
	       $oid_descr[$i] = $descr_table .'.'.$tindex[$i];
	    }
	 }
	 if (defined($o_ciscocat) && $cport[$i]) {
	    if (exists($o_cisco{'oper'}) || exists($copt{'oper'}) || 
		(scalar(keys %copt)==0 && exists($o_cisco{'auto'}))) {
		    $oid_ciscooperstatus[$i] = $cisco_port_operstatus_table . $cport[$i];
	    }
	    if (exists($o_cisco{'addoper'}) || exists($copt{'addoper'}) ||
		(scalar(keys %copt)==0 && exists($o_cisco{'auto'}))) {
		    $oid_ciscoaddoperstatus[$i] = $cisco_port_addoperstatus_table . $cport[$i];
	    }
	    if (exists($o_cisco{'linkfault'}) || exists($copt{'linkfault'}) ||
		(scalar(keys %copt)==0 && exists($o_cisco{'auto'}))) {
		    $oid_ciscofaultstatus[$i] = $cisco_port_linkfaultstatus_table . $cport[$i];
	    }
	 }
	 if (defined($o_stp)) {
	    $oid_stpstate[$i] = $stp_dot1dbase_portstate . $stpport[$i] if $stpport[$i];
	 }
	 # Put the performance oid 
	 if (defined($o_perf) || defined($o_checkperf)) {
	    $oid_perf_inoct[$i]= $in_octet_table . $tindex[$i];
	    $oid_perf_outoct[$i]= $out_octet_table . $tindex[$i];
	    if (defined($o_ext_checkperf) || defined($o_perfe)) {
	       $oid_perf_indisc[$i]= $in_discard_table . $tindex[$i];
	       $oid_perf_outdisc[$i]= $out_discard_table . $tindex[$i];
	       $oid_perf_inerr[$i]= $in_error_table . $tindex[$i];
	       $oid_perf_outerr[$i]= $out_error_table . $tindex[$i];
	    }
	 }
	 if ($check_speed && (!defined($interfaces[$i]{'portspeed'}) || !defined($o_maxminsnmp))) {
	    $oid_speed[$i]=$speed_table . $tindex[$i];
	    $oid_speed_high[$i]=$speed_table_64 . $tindex[$i];
	 }
	 if (defined($o_commentoid)) {
	    if (defined($o_ciscocat) && defined($o_cisco{'show_portnames'})) {
	       $oid_commentlabel[$i]=$o_commentoid .'.'. $cport[$i] if $cport[$i]; 
	    }
	    else {
	       $oid_commentlabel[$i]=$o_commentoid . $tindex[$i];
	    }
	 }
      }

      # put them all together and do as one query when -m option is used 
      if (defined($o_perf) || defined($o_checkperf) || defined($o_intspeed)) {
	 @oid_perf=(@oid_perf_outoct,@oid_perf_inoct,@oid_speed);
	 if (defined($o_highperf)) {
	    @oid_perf=(@oid_perf,@oid_speed_high);
	 }
	 if (defined ($o_ext_checkperf) || defined($o_perfe)) {
	    @oid_perf=(@oid_perf,@oid_perf_inerr,@oid_perf_outerr,@oid_perf_indisc,@oid_perf_outdisc);
	 }
      }
      if (defined($o_ciscocat)) {
	 @oid_ciscostatus=(@oid_ciscofaultstatus,@oid_ciscooperstatus,@oid_ciscoaddoperstatus);
      }
      if (defined($o_admindown_ok)) {
	 push @oids, @oids_admin if scalar(@oids_admin)>0;
      }
      if (defined($o_minsnmp)) {
	 push @oids, @oid_perf if scalar(@oid_perf)>0;
	 push @oids, @oid_descr if scalar(@oid_descr)>0;
	 push @oids, @oid_commentlabel if defined($o_commentoid) && scalar(@oid_commentlabel)>0;
	 push @oids, @oid_ciscostatus if defined($o_ciscocat) && scalar(@oid_ciscostatus)>0;
	 push @oids, @oid_stpstate if defined($o_stp) && scalar(@oid_stpstate)>0;
      }

      # Get the requested oid values
      snmp_get_request($session, \@oids, "status table", $results);

      # If not doing it as one query, do additional queries
      # to get the perf value if -f (performance) option defined or -k (check bandwidth)
      if ((defined($o_perf) || defined($o_checkperf) || defined($o_intspeed)) && !defined($o_minsnmp)) {
	 snmp_get_request($session, \@oid_perf, "statistics table", $results);
      }
      # and additional cisco status tables
      if (defined($o_ciscocat) && !defined($o_minsnmp) && scalar(@oid_ciscostatus)>0) {
	 snmp_get_request($session, \@oid_ciscostatus, "cisco status tables", $results);
      }
      # and stp state table if --stp option is given
      if (defined($o_stp) && !defined($o_minsnmp) && scalar(@oid_stpstate)>0) {
	 snmp_get_request($session, \@oid_stpstate, "stp state table", $results);
      }
      # and additional comments / port description table
      if (defined($o_commentoid) && !defined($o_minsnmp) && scalar(@oid_commentlabel)>0) {
	 snmp_get_request($session, \@oid_commentlabel, "comments table", $results);
      }

      $session->close;

      # Now go through the results and populate our interfaces array
      for (my $i=0;$i<$num_int;$i++) {
	 $int_status_extratext="";

	 # First verify description is correct when -m option (but not --mm) is used
	 if (defined($o_minsnmp) && !defined($o_maxminsnmp)) {
	    my $dsc=undef;
	    if (defined($o_cisco{'use_portnames'})) {
		$dsc=$results->{$descr_table.'.'. $cport[$i]} if $cport[$i];
	    }
	    else {
		$dsc=$results->{$descr_table.'.'. $tindex[$i]};
	    }
	    $dsc = clean_int_name($dsc) if defined($dsc);
	    if (!defined($dsc) || $dsc ne $interfaces[$i]{'descr'}) {
		# WL: Perhaps this is not quite right and there should be "goto" here forcing to retrieve all tables again
		if (!defined($dsc)) {
		    printf("ERROR: Cached port description is %s while retrieved port name is not available\n", $interfaces[$i]{'descr'});
		}
		else {
		    printf("ERROR: Cached port description %s is different then retrieved port name %s\n", $interfaces[$i]{'descr'}, $dsc);
		}
		exit $ERRORS{"UNKNOWN"};
	    }
	    verb("Name : $dsc [confirmed cached name for port $i]");
	 }

	 # Admin and Oper Status
	 $interfaces[$i]{'admin_up'} = $results->{$admin_table.$tindex[$i]} if exists($results->{$admin_table.$tindex[$i]});
	 $interfaces[$i]{'oper_up'} = $results->{$oper_table.$tindex[$i]} if exists($results->{$oper_table.$tindex[$i]});

	 # IN and OUT traffic counters, Errors and Dropped counters
	 if (defined($results->{$oid_perf_inoct[$i]}) && defined($results->{$oid_perf_outoct[$i]})) {
	     $interfaces[$i]{'in_bytes'}=$results->{$oid_perf_inoct[$i]};
	     $interfaces[$i]{'out_bytes'}=$results->{$oid_perf_outoct[$i]};
	     $interfaces[$i]{'in_errors'}=0;
	     $interfaces[$i]{'out_errors'}=0;
	     $interfaces[$i]{'in_dropped'}=0;
	     $interfaces[$i]{'out_dropped'}=0;
	     if (defined($o_ext_checkperf)) { # Add other values (error & disc)
		$interfaces[$i]{'in_errors'}=$results->{$oid_perf_inerr[$i]} if defined($results->{$oid_perf_inerr[$i]});
		$interfaces[$i]{'out_errors'}=$results->{$oid_perf_outerr[$i]} if defined($results->{$oid_perf_outerr[$i]});
		$interfaces[$i]{'in_dropped'}=$results->{$oid_perf_indisc[$i]} if defined($results->{$oid_perf_indisc[$i]});
		$interfaces[$i]{'out_dropped'}=$results->{$oid_perf_outdisc[$i]} if defined($results->{$oid_perf_outdisc[$i]});
	     }
	 }

	 # Additional description data / Comments OID
	 if (defined($o_commentoid)) {
	    if (defined($o_cisco{'show_portnames'})) {
                $interfaces[$i]{'descr_extra'} ='('.$results->{$o_commentoid.'.'.$cport[$i]}.')' if $cport[$i] && $results->{$o_commentoid.'.'.$cport[$i]};
	    }
	    else {
                $interfaces[$i]{'descr_extra'} ='('.$results->{$o_commentoid.$tindex[$i]}.')' if $results->{$o_commentoid.$tindex[$i]};
	    }
	 }

	 # Cisco status data
	 if (defined($o_ciscocat) && $cport[$i]) {
	    my ($int_status_cisco,$operstat,$addoperstat)=(undef,undef,undef);
	    my $cisco_status_extratext="";

	    if (exists($o_cisco{'linkfault'}) || exists($copt{'linkfault'}) ||
	       (scalar(keys %copt)==0 && exists($o_cisco{'auto'}))) {
		 if (defined($results->{$cisco_port_linkfaultstatus_table.$cport[$i]})) {
		    $int_status_cisco=$results->{$cisco_port_linkfaultstatus_table.$cport[$i]};
		    if (defined($int_status_cisco) && $int_status_cisco !~ /\d+/) {
                	verb("Received non-integer value for cisco linkfault status when checking port $i: $int_status_cisco");
               		 $int_status_cisco=undef;
		    }
		    if (defined($int_status_cisco) && $int_status_cisco!=1) {
			$cisco_status_extratext.=',' if $cisco_status_extratext;
			$cisco_status_extratext.=$cisco_port_linkfaultstatus{$int_status_cisco};
		    }
		 }
		 if (defined($int_status_cisco) && (
                        (!defined($o_inverse) && $int_status_cisco!=1) || (defined($o_inverse) && $int_status_cisco==1))) {
		    $interfaces[$i]{'nagios_status'}=$ERRORS{'CRITICAL'};
		 }
	    }
	    if (exists($o_cisco{'oper'}) || exists($copt{'oper'}) ||
		(scalar(keys %copt)==0 && exists($o_cisco{'auto'}))) {
		if (defined($results->{$cisco_port_operstatus_table.$cport[$i]})) {
		    $operstat=$results->{$cisco_port_operstatus_table.$cport[$i]};
		    if (defined($operstat) && $operstat !~ /\d+/) {
                        verb("Received non-integer value for cisco operport status when checking port $i: $operstat");
                         $operstat=undef;
		    }
		    if (defined($operstat) && $operstat!=2) {
			$cisco_status_extratext.=',' if $cisco_status_extratext;
                        $cisco_status_extratext.=$cisco_port_operstatus{$operstat};
		    }
		}
		if (defined($operstat) && (
                        (!defined($o_inverse) && $operstat!=2) || (defined($o_inverse) && $operstat==2))) {
		    $interfaces[$i]{'nagios_status'}=$ERRORS{'CRITICAL'};
		}
	    }
	    if (exists($o_cisco{'addoper'}) || exists($copt{'addoper'}) ||
	      (scalar(keys %copt)==0 && exists($o_cisco{'auto'}))) {
		if (defined($results->{$cisco_port_addoperstatus_table.$cport[$i]})) {
		    $addoperstat=$results->{$cisco_port_addoperstatus_table.$cport[$i]};
		}
		if (defined($addoperstat) && ($addoperstat eq 'noSuchInstance' || $addoperstat eq 'noSuchObject')) {
		    verb("Received invalid value for cisco addoper status when checking port $i: $addoperstat");
		    $addoperstat=undef;
		}
		if (defined($addoperstat)) {
		    if ($addoperstat !~ /0x.*/) {$addoperstat = hex ascii_to_hex($addoperstat);} else {$addoperstat = hex $addoperstat;}
		    for (my $j=0; $j<=15;$j++) { # WL: SNMP BITS type - yak!
			if ($addoperstat & (1<<(15-$j))) {
			   $cisco_status_extratext.=',' if $cisco_status_extratext;
			   $cisco_status_extratext.=$cisco_port_addoperstatus{$j} if $cisco_port_addoperstatus{$j} ne 'connected';
			}
		    }
		}
	    }
	    if (scalar(keys %copt)==0 && exists($o_cisco{'auto'})) {
		$copt_next{'linkfault'}=1 if defined($int_status_cisco);
		$copt_next{'oper'}=1 if defined($operstat);
		$copt_next{'addoper'}=1 if defined($addoperstat);
	    }
	    if ($cisco_status_extratext) {
		$int_status_extratext.=", " if $int_status_extratext;
		$int_status_extratext.="CISCO: ".$cisco_status_extratext;
	    }
	 }

	 # STP state data
	 if (defined($o_stp) && $stpport[$i]) {
	    my ($int_stp_state,$prev_stp_state,$prev_stp_changetime)=(undef,undef,undef);
	    $int_stp_state=$results->{$stp_dot1dbase_portstate.$stpport[$i]};
	    if ($int_stp_state !~ /\d+/) {
		verb("Received non-numeric status for STP for port $i: $int_stp_state");
		$int_stp_state=undef;
	    }
	    $prev_stp_state=prev_perf($interfaces[$i]{'descr'},"stp_state");
	    $prev_stp_changetime=prev_perf($interfaces[$i]{'descr'},"stp_changetime");
	    if (defined($int_stp_state)) {
		$int_status_extratext.=',' if $int_status_extratext;
		$int_status_extratext.='STP:'.$stp_portstate{$int_stp_state};
		$perf_out .= " ".perf_name($interfaces[$i]{'descr'},"stp_state")."=".$int_stp_state;
		$perf_out .= " ".perf_name($interfaces[$i]{'descr'},"prev_stp_state")."=".$prev_stp_state if defined($prev_stp_state);
		if (defined($prev_stp_changetime) && defined($prev_stp_state) && $prev_stp_state == $int_stp_state) {
			$perf_out .= " ".perf_name($interfaces[$i]{'descr'},'stp_changetime').'='.$prev_stp_changetime;
		}
		elsif (!defined($prev_stp_state) || !defined($prev_stp_changetime)) {
			$perf_out .= " ".perf_name($interfaces[$i]{'descr'},'stp_changetime').'='.($timenow-$stp_warntime);
		}
		else {
			$perf_out .= " ".perf_name($interfaces[$i]{'descr'},'stp_changetime').'='.$timenow;
		}
		if ($o_stp ne '' && $int_stp_state != $stp_portstate_reverse{$o_stp}) {
			$int_status_extratext.=":CRIT";
			$interfaces[$i]{'nagios_status'} = $ERRORS{'CRITICAL'};
		}
		elsif ((defined($prev_stp_changetime) && ($timenow-$prev_stp_changetime)<$stp_warntime) ||
		       (defined($prev_stp_state) && $prev_stp_state != $int_stp_state)) {
			$int_status_extratext.=":WARN(change from ".
			         $stp_portstate{$prev_stp_state}.")";
		        $interfaces[$i]{'nagios_status'} = $ERRORS{'WARNING'};
		}
	    }
	 }

	 # Get the speed in normal or highperf speed counters
	 if (defined($oid_speed[$i]) && defined($results->{$oid_speed[$i]})) {
	     if ($results->{$oid_speed[$i]} == 4294967295) { # Too high for this counter (cf IF-MIB)
		if (!defined($o_highperf) && $check_speed) {
		  print "Cannot get interface speed with standard MIB, use highperf mib (-g) : UNKNOWN\n";
		  exit $ERRORS{"UNKNOWN"}
	        }
	        if (defined ($results->{$oid_speed_high[$i]}) && $results->{$oid_speed_high[$i]} != 0) {
		  $interfaces[$i]{'portspeed'}=$results->{$oid_speed_high[$i]} * 1000000;
	        } 
	        elsif ($specified_speed==0) {
		  print "Cannot get interface speed using highperf mib : UNKNOWN\n";
		  exit $ERRORS{"UNKNOWN"}
	        }
	     } else {
		$interfaces[$i]{'portspeed'}=$results->{$oid_speed[$i]};
	     }
	 }

	 # Finished with getting data. Now save extra text for interface status info
	 if ($int_status_extratext ne '') {
	     $interfaces[$i]{'status_extratext'} = '' if !exists($interfaces[$i]{'status_extratext'});
	     $interfaces[$i]{'status_extratext'} .= ', ' if $interfaces[$i]{'status_extratext'};
	     $interfaces[$i]{'status_extratext'} .= $int_status_extratext;
	 }

	 # Prepare index table and desc data for performance output / saved data caching and reuse
	 if (defined($o_minsnmp) && defined($o_prevperf)) {
	     @descr=();
	     @portspeed=();
	     for(my $iii=0;$iii<scalar(@tindex);$iii++) {
		  $descr[$iii]=$interfaces[$iii]{'descr'};
		  $portspeed[$iii]=$interfaces[$iii]{'portspeed'} if defined($interfaces[$iii]{'portspeed'});
	     }
	     $saved_out.= " cache_descr_ids=". join(',',@tindex) if scalar(@tindex)>0;
	     $saved_out.= " cache_descr_names=".join(',',@descr) if scalar(@descr)>0;
	     $saved_out.= " cache_descr_time=".$perfcache_time if defined($perfcache_time);
	     $saved_out.= " cache_int_speed=". join(',',@portspeed) if $check_speed && scalar(@portspeed)>0 && defined($o_maxminsnmp) && $specified_speed==0;
	     if (defined($o_ciscocat)) {
		 $cport[0]=-1 if scalar(@cport)==0;
		 $saved_out.= " cache_descr_cport=".join(',',@cport);
		 if (scalar(keys %copt)>0) {
		    $saved_out.= " cache_cisco_opt=".join(',',keys %copt);
		 }
		 elsif (scalar(keys %copt_next)>0) {
		    $saved_out.= " cache_cisco_opt=".join(',',keys %copt_next);
		 }
	     }
	     if (defined($o_stp)) {
		 $stpport[0]=-1 if scalar(@stpport)==0;
		 $saved_out.= " cache_descr_stpport=".join(',',@stpport);
	     }
	 }
      }
  }

  return $results;
}

########## MAIN #######

check_options();

# Check gobal timeout if snmp screws up
if (defined($TIMEOUT)) {
  verb("Alarm at $TIMEOUT + 5");
  alarm($TIMEOUT+5);
} else {
  verb("no timeout defined : $o_timeout + 10");
  alarm ($o_timeout+10);
}

$SIG{'ALRM'} = sub {
 if (defined($o_host)) {
      print "ERROR: alarm timeout. No answer from host $o_host\n";
 }
 else {
      print "ERROR: alarm timeout\n";
      kill 9, $shell_pid if defined($shell_pid);
 }
 exit $ERRORS{"UNKNOWN"};
};

#Select interface by regexp of exact match
verb("Filter : $o_descr") if defined($o_descr);

# WL: check if '-m' option is passed and previous description ids & names are available from
#     previous performance data (caching to minimize SNMP lookups and only get specific data
#     instead of getting description table every time)
$perfcache_time = prev_perf('cache_descr_time') if defined(prev_perf('cache_descr_time'));

# Get data from local machine about its interfaces or from SNMP
if ($do_snmp==0) {
   getdata_localhost();
}
else {
   getdata_snmp();
}

if ($num_int == 0) {
   if (defined($o_descr)) {
	  print "ERROR : Unknown interface $o_descr\n";
   }
   else {
	  print "ERROR : can not find any network interfaces\n";
   }
   exit $ERRORS{"UNKNOWN"};
}

# some more global variables, some should possibly move further up to main vars definition
my $num_ok=0;
my $num_admindown=0;
my $ok_val= defined ($o_inverse) ? 2 : 1;  # define the OK value depending on -i option
my $final_status = 0;
my $print_out='';
my $temp_file_name;
my @prev_values=();
my @checkperf_out_raw=undef;
my @checkperf_out=undef;
my $checkval_out=undef;
my $checkval_in=undef;
my $checkval_tdiff=undef;
my $usable_data=0;
my $n_rows=0;
my $n_items_check=(defined($o_ext_checkperf))?7:3;
my $trigger=$timenow - ($o_delta - ($o_delta/4));
my $trigger_low=$timenow - 4*$o_delta;
my $old_value=undef;
my $old_time=undef;
my $speed_unit=undef;
my $speed_metric=undef;

# make all checks and output for all interfaces
for (my $i=0;$i < $num_int; $i++) { 
  $print_out.=", " if ($print_out);
  $perf_out .= " " if ($perf_out);
  my $usable_data=1; # 0 is OK, 1 means its not OK

  # Get the status of the current interface
  my $int_status = $ok_val;
  my $admin_int_status = $ok_val;
  my $int_status_extratext = "";
  if (!defined($o_ignorestatus)) {
     if (!exists($interfaces[$i]{'up_status'})) {
	if (defined($o_admin) && exists($interfaces[$i]{'admin_up'})) {
	   $interfaces[$i]{'up_status'} = $interfaces[$i]{'admin_up'};
	}
	elsif (exists($interfaces[$i]{'oper_up'})) {
	   $interfaces[$i]{'up_status'} = $interfaces[$i]{'oper_up'};
	}
	else {
	    printf("ERROR: Can not find up status for interface ".$interfaces[$i]{'descr'});
	    exit $ERRORS{"UNKNOWN"};
	}
     }
     if (defined($o_admindown_ok) && exists($interfaces[$i]{'admin_up'})) {
        $admin_int_status = $interfaces[$i]{'admin_up'};
	$int_status_extratext.="ADMIN:".$status_print{$admin_int_status} if $admin_int_status ne $interfaces[$i]{'up_status'}; 
     }
     $int_status = $interfaces[$i]{'up_status'} if exists($interfaces[$i]{'up_status'});
  }
  if (exists($interfaces[$i]{'status_extratext'})) {
     $int_status_extratext.=", " if $int_status_extratext;
     $int_status_extratext.=$interfaces[$i]{'status_extratext'};
  }

  # Get the final output interface description ready
  my $int_desc="";
  my $descr=$interfaces[$i]{'descr'};
  if (defined ($o_short)) {
     if ($o_short < 0) {
        $int_desc=substr($descr,$o_short);
     }
     else {
        $int_desc=substr($descr,0,$o_short);
     }
  }
  else {
     $int_desc = $descr;
  }
  if (exists($interfaces[$i]{'descr_extra'})) {
     $int_desc .=  $interfaces[$i]{'descr_extra'};
  }
  $interfaces[$i]{'full_descr'}=$int_desc;

  # Interface Speed
  if ($specified_speed!=0 && !exists($interfaces[$i]{'portspeed'})) {
      $interfaces[$i]{'portspeed'} = $specified_speed;
  }
  if (defined($speed_alert) && defined($interfaces[$i]{'portspeed'}) && $interfaces[$i]{'portspeed'}!=$specified_speed) {
      $int_status_extratext.=',' if $int_status_extratext;
      $int_status_extratext.="$speed_alert: Speed=".$interfaces[$i]{'portspeed'}." bps";
      $int_status_extratext.=" (should be $specified_speed bps)";
      $interfaces[$i]{'nagios_status'}=$ERRORS{$speed_alert} if !exists($interfaces[$i]{'nagios_status'}) || $ERRORS{$speed_alert} > $interfaces[$i]{'nagios_status'};
  }
  verb ("Interface $i speed : ".$interfaces[$i]{'portspeed'}) if defined($interfaces[$i]{'portspeed'});

  $final_status = $interfaces[$i]{'nagios_status'} if exists($interfaces[$i]{'nagios_status'}) && $final_status < $interfaces[$i]{'nagios_status'};

  # Make the bandwidth & error checks if necessary 
  if (defined ($o_checkperf) && $int_status==$status{'UP'}) {

    # WL: checks if previous performance data & time last check was run are available
    if ($o_filestore || !defined($o_prevperf)) {
        if ($o_filestore && length($o_filestore)>1 && ! -d $o_filestore) {
	  $temp_file_name = $o_filestore;
        }
        else {
	  $temp_file_name = $descr;
	  $temp_file_name =~ s/[ ;\/]/_/g;
	  $temp_file_name = (length($o_filestore)>1 && -d $o_filestore ? $o_filestore : $o_base_dir) . (defined($o_host)?$o_host.".":"") . $temp_file_name; 
        }
        # First, read entire file
        my @ret_array=read_file($temp_file_name,$n_items_check);
        $usable_data = shift(@ret_array);
        $n_rows = shift(@ret_array);
        if ($n_rows != 0) { @prev_values = @ret_array };
        verb ("File read returns : $usable_data with $n_rows rows");
    }
    # WL: if one or more sets of previous performance data is available
    #      then put it in prev_values array and use as history data
    # [TODO] this code is still a bit buggy as far as checking for bad
    #        or missing values in previous performance data
    else {
	my $j=0;
	my $jj=0;
	my $data_ok;
	my $timeref='';
	for (;$j<$o_pcount && exists($prev_time[$j]); $j++) {
		$data_ok=1;
		$timeref='.'.$prev_time[$j];
		$timeref='' if prev_perf('ptime') eq $prev_time[$j];
		$prev_values[$jj]=[ $prev_time[$j],
				    prev_perf($descr,'in_octet'.$timeref),
				    prev_perf($descr,'out_octet'.$timeref),
				    prev_perf($descr,'in_error'.$timeref),
				    prev_perf($descr,'out_error'.$timeref),
				    prev_perf($descr,'in_discard'.$timeref),
				    prev_perf($descr,'out_discard'.$timeref) ];
		# this checks if data is ok and not, this set of values would not be used
		# and next set put in its place as $jj is not incrimented
		for (my $k=1;$k<(defined($o_ext_checkperf)?7:3);$k++) { 
			if (!defined($prev_values[$jj][$k]) || $prev_values[$jj][$k] !~ /\d+/) {
				$prev_values[$jj][$k]=0;
				$data_ok=0 if $k<3;
			}
		}
		if ($data_ok && $prev_values[$jj][1]!=0 && $prev_values[$jj][2]!=0) {
			$jj++;
		}
		else {
			$prev_values[$jj][0]=0;
		}
	}
	$n_rows = $jj;
	if ($jj==0) { $usable_data=1 } #NAK
	  else { $usable_data=0; } # OK
    }
    verb("Previous data array created: $n_rows rows");

    # Put the new values in the array
    if (defined($interfaces[$i]{'in_bytes'}) && defined($interfaces[$i]{'out_bytes'})) {
        $prev_values[$n_rows]=[ $timenow, $interfaces[$i]{'in_bytes'}, $interfaces[$i]{'out_bytes'}, 
					  $interfaces[$i]{'in_errors'}, $interfaces[$i]{'out_errors'},
					  $interfaces[$i]{'in_dropped'}, $interfaces[$i]{'out_dropped'} ];
	$n_rows++;
    }
    #make the checks if the file is OK  
    if ($usable_data==0) {
      my $j;
      my $jj=0;
      my $n=0;
      my $overfl;
      @checkperf_out=(0,0,0,0,0,0);
      @checkperf_out_raw=();
      $checkval_in=undef;
      $checkval_out=undef;
      $checkval_tdiff=undef;

      # check if the counter is back to 0 after 2^32 / 2^64.
      # First set the modulus depending on highperf counters or not
      my $overfl_mod = defined ($o_highperf) ? 18446744073709551616 : 4294967296;

      # Define the speed metric ( K | M | G ) (Bits|Bytes) or %
      if (defined($o_prct)) { # in % of speed
	# Speed is in bits/s, calculated speed is in Bytes/s
	if (defined($interfaces[$i]{'portspeed'})) {
	    $speed_metric=$interfaces[$i]{'portspeed'}/800;
	    $speed_unit='%';
	}
      } else {
	if (defined($o_kbits)) { # metric in bits
	    if (defined($o_meg)) { # in Mbit/s = 1000000 bit/s
		$speed_metric=125000; #  (1000/8) * 1000
		$speed_unit="Mbps";
	    } elsif (defined($o_gig)) { # in Gbit/s = 1000000000 bit/s
		$speed_metric=125000000; #  (1000/8) * 1000 * 1000
		$speed_unit="Gbps";
	    } else { # in Kbits
		$speed_metric=125; #  ( 1000/8 )
		$speed_unit="Kbps";
	    }
	} else { # metric in byte
	    if (defined($o_meg)) { # in Mbits
		$speed_metric=1048576; # 1024^2
		$speed_unit="MBps";
	    } elsif (defined($o_gig)) { # in Mbits
		$speed_metric=1073741824; # 1024^3
		$speed_unit="GBps";
	    } else {
		$speed_metric=1024; # 1024^1
		$speed_unit="KBps";
	    }		    
	}
      }

      # Calculate averages & metrics
      $j=$n_rows-1;
      do {
	if ($prev_values[$j][0] < $trigger) {
	  if ($prev_values[$j][0] > $trigger_low) {
	    if (($checkval_tdiff=$prev_values[$j+1][0]-$prev_values[$j][0])!=0) {
              # check_perf_out_raw is array used to store calculations from multiple counts
              $checkperf_out_raw[$jj] = [ 0,0,0,0,0 ];

	      # Check counter (s)
	      if ($prev_values[$j+1][1]!=0 && $prev_values[$j][1]!=0) {
	        $overfl = ($prev_values[$j+1][1] >= $prev_values[$j][1] ) ? 0 : $overfl_mod;
	        $checkval_in = ($overfl + $prev_values[$j+1][1] - $prev_values[$j][1]) / $checkval_tdiff ;
	        $checkperf_out_raw[$jj][0] = $checkval_in / $speed_metric;
	      }
	      if ($prev_values[$j+1][2]!=0 && $prev_values[$j][2]!=0) {
	    	$overfl = ($prev_values[$j+1][2] >= $prev_values[$j][2] ) ? 0 : $overfl_mod;
	        $checkval_out = ($overfl + $prev_values[$j+1][2] - $prev_values[$j][2]) / $checkval_tdiff;
	        $checkperf_out_raw[$jj][1] = $checkval_out / $speed_metric;
	      }
	      if (defined($o_ext_checkperf)) {
	        $checkperf_out_raw[$jj][2] = ( ($prev_values[$j+1][3] - $prev_values[$j][3])/ $checkval_tdiff )*60;
	        $checkperf_out_raw[$jj][3] = ( ($prev_values[$j+1][4] - $prev_values[$j][4])/ $checkval_tdiff )*60;
	        $checkperf_out_raw[$jj][4] = ( ($prev_values[$j+1][5] - $prev_values[$j][5])/ $checkval_tdiff )*60;
	        $checkperf_out_raw[$jj][5] = ( ($prev_values[$j+1][6] - $prev_values[$j][6])/ $checkval_tdiff )*60;
	      }
	      $jj++ if $checkperf_out_raw[$jj][0]!=0 || $checkperf_out_raw[$jj][1]!=0;
	    }
	  }
	}
	$j--;
      } while ( $j>=0 && $jj<$o_pcount );

      # Calculate total as average
      if ($jj>0) {
        for (my $k=0;$k<5;$k++) {
          $n=0;
          for ($j=0;$j<$jj;$j++) {
	    if ($checkperf_out_raw[$j][$k]!=0) {
	      $n++;
	      $checkperf_out[$k]+=$checkperf_out_raw[$j][$k];
            }
          }
	  if ($n>0) {
	    $checkperf_out[$k]=$checkperf_out[$k]/$n;
	  }
        }
      }
      else {
        $usable_data=1;
      }
    }

    # WL: modified to not write the file if both -P and -T options are used
    # -z option used: don't write the tmp file
    if (defined($temp_file_name) && !defined($o_zerothresholds) && ($o_filestore || !$o_prevperf || !$o_prevtime)) {
      if (($_=write_file($temp_file_name,$n_rows,$n_items_check,@prev_values))!=0) {
        $final_status=3;
        $print_out.= " !!Unable to write file ".$temp_file_name." !! ";
        verb ("Write file returned : $_");
      }
    }
    # Print the basic status
    $print_out.=sprintf("%s:%s",$int_desc, $status_print{$int_status});
    $print_out.=' ['.$int_status_extratext.']' if $int_status_extratext;
    # print the other checks if it was calculated
    if ($usable_data==0 && defined($checkperf_out[0])) {
      $print_out.= " (";
      # check 2 or 6 values depending on ext_check_perf
      my $num_checkperf=(defined($o_ext_checkperf))?6:2;
      for (my $l=0;$l < $num_checkperf;$l++) {
	    # Set labels if needed
	    $checkperf_out_desc= (defined($o_label)) ? $countername[$l] : "";
	    verb("Interface $i, threshold check $l : $checkperf_out[$l]");
	    $print_out.="/" if $l!=0;
	    if ((defined($o_crit_max[$l]) && $o_crit_max[$l] && ($checkperf_out[$l]>$o_crit_max[$l])) ||
                (defined($o_crit_min[$l]) && $o_crit_min[$l] && ($checkperf_out[$l]<$o_crit_min[$l]))) { 
		$final_status=2;
		$print_out.= sprintf("CRIT %s%.1f",$checkperf_out_desc,$checkperf_out[$l]);
	    } elsif ((defined($o_warn_max[$l]) && $o_warn_max[$l] && ($checkperf_out[$l]>$o_warn_max[$l])) ||
	             (defined($o_warn_min[$l]) && $o_warn_min[$l] && ($checkperf_out[$l]<$o_warn_min[$l]))) { 
		$final_status=($final_status==2)?2:1;
		$print_out.= sprintf("WARN %s%.1f",$checkperf_out_desc,$checkperf_out[$l]);
	    } else {
		$print_out.= sprintf("%s%.1f",$checkperf_out_desc,$checkperf_out[$l]);
	    }
	    $print_out.= $speed_unit if defined($speed_unit) && ($l==0 || $l==1);
      }
      $print_out .= ")";
    } 
    elsif (!defined($o_zerothresholds)) {
      $print_out.= " (no usable data - ".$n_rows." rows) ";
      # WL: I've removed return of UNKNOWN if no data is available, though when plugin is first run that may still happen
      # $final_status=3;
    }
  }
  else {
    $print_out.=sprintf("%s:%s",$int_desc, $status_print{$int_status});
    $print_out.=' ['.$int_status_extratext.']' if $int_status_extratext;
  }
  if ((($int_status == $ok_val) || (defined($o_dormant) && $int_status == $status{'DORMANT'}))) { 
    # used to also be: "&& $int_status_opt==0" but I removed it in 2.4 so only main (admin/oper) status is counted for up/down 
    $num_ok++;
  } elsif (defined($o_admindown_ok) && $ok_val==1 && !$o_admin && $int_status == $status{'DOWN'} && $admin_int_status == $status{'DOWN'}) {
    # we want to check for operational UP interfaces, so don't check those that are supposed to be down (administratively down)
    $num_admindown++;
  }
  # Don't return performance data for interfaces that are down and are supposed to be down
  if (!(defined($o_admindown_ok) && $ok_val==1 && $int_status == $status{'DOWN'} && $admin_int_status == $status{'DOWN'}) && defined($interfaces[$i]{'descr'}) && (defined($o_perf) || defined($o_intspeed) || defined($o_perfr) || defined($o_perfp) || defined($o_checkperf))) {
    if (defined ($o_perfp)) { # output in % of speed
	if ($usable_data==0 && defined($checkperf_out[0]) && defined($checkperf_out[1])) {
	    if (defined($o_prct)) {
		$perf_out .= " ".perf_name($descr,"in_prct")."=";
		$perf_out .= sprintf("%.0f",$checkperf_out[0]) . '%;';
		$perf_out .= (defined($o_warn_max[0]) && $o_warn_max[0]) ? $o_warn_max[0] . ";" : ";";
		$perf_out .= (defined($o_crit_max[0]) && $o_crit_max[0]) ? $o_crit_max[0] . ";" : ";"; 
		$perf_out .= "0;100 ";
		$perf_out .= " ".perf_name($descr,"out_prct")."=";
		$perf_out .= sprintf("%.0f",$checkperf_out[1]) . '%;';
		$perf_out .= (defined($o_warn_max[1]) && $o_warn_max[1]) ? $o_warn_max[1] . ";" : ";";
		$perf_out .= (defined($o_crit_max[1]) && $o_crit_max[1]) ? $o_crit_max[1] . ";" : ";"; 
		$perf_out .= "0;100 ";
	    }
	    elsif (defined($interfaces[$i]{'portspeed'}) && $interfaces[$i]{'portspeed'} != 0) {
		$perf_out .= " ".perf_name($descr,"in_prct")."=";
		$perf_out .= sprintf("%.0f", $checkperf_out[0]*$speed_metric/$interfaces[$i]{'portspeed'}*800). '%';
		$perf_out .= " ".perf_name($descr,"out_prct")."=";
		$perf_out .= sprintf("%.0f", $checkperf_out[1]*$speed_metric/$interfaces[$i]{'portspeed'}*800). '%';
	    }
	    else {
		verb("we do not have information on speed of interface $i (".$interfaces[$i]{'descr'}.")");
	    }
	}
    } elsif (defined ($o_perfr)) { # output in bites or Bytes /s
	if ($usable_data==0) {
  	    if (defined($o_kbits)) { # bps
		  # put warning and critical levels into bps or Bps
		  my $warn_factor=undef;
		  if (defined($o_prct)) { # warn&crit in % -> put warn_factor to 1% of speed in bps
			$warn_factor=$interfaces[$i]{'portspeed'}/100 if defined($interfaces[$i]{'portspeed'});
                  } else { # just convert from K|M|G bps
			$warn_factor = (defined($o_meg)) ? 1000000 : (defined($o_gig)) ? 1000000000 : 1000;
		  }
		  if (defined($warn_factor)) {
			$perf_out .= " ".perf_name($descr,"in_bps")."=";
			$perf_out .= sprintf("%.0f",$checkperf_out[0] * 8 * $speed_metric) .";" if defined($checkperf_out[0]);
			$perf_out .= (defined($o_warn_max[0]) && $o_warn_max[0]) ? $o_warn_max[0]*$warn_factor . ";" : ";";
			$perf_out .= (defined($o_crit_max[0]) && $o_crit_max[0]) ? $o_crit_max[0]*$warn_factor . ";" : ";";
			$perf_out .= "0;". $interfaces[$i]{'portspeed'} ." " if defined($interfaces[$i]{'portspeed'});
			$perf_out .= " ".perf_name($descr, "out_bps"). "=";
			$perf_out .= sprintf("%.0f",$checkperf_out[1] * 8 * $speed_metric) .";" if defined($checkperf_out[1]);
			$perf_out .= (defined($o_warn_max[1]) && $o_warn_max[1]) ? $o_warn_max[1]*$warn_factor . ";" : ";";
			$perf_out .= (defined($o_crit_max[1]) && $o_crit_max[1]) ? $o_crit_max[1]*$warn_factor . ";" : ";";
			$perf_out .= "0;". $interfaces[$i]{'portspeed'} ." " if defined($interfaces[$i]{'portspeed'});
		  }
	    } else { # Bps
		  my $warn_factor = undef;
		  if (defined($o_prct)) { # warn&crit in % -> put warn_factor to 1% of speed in Bps
			$warn_factor=$interfaces[$i]{'portspeed'}/800 if defined($interfaces[$i]{'portspeed'});
		  } else { # just convert from K|M|G bps
			$warn_factor = (defined($o_meg)) ? 1048576 : (defined($o_gig)) ? 1073741824 : 1024;
		  }
		  if (defined($warn_factor)) {
			$perf_out .= " ".perf_name($descr,"in_Bps")."=" . sprintf("%.0f",$checkperf_out[0] * $speed_metric) .";" if defined($checkperf_out[0]);
			$perf_out .= (defined($o_warn_max[0]) && $o_warn_max[0]) ? $o_warn_max[0]*$warn_factor . ";" : ";";
			$perf_out .= (defined($o_crit_max[0]) && $o_crit_max[0]) ? $o_crit_max[0]*$warn_factor . ";" : ";";
			$perf_out .= "0;". $interfaces[$i]{'portspeed'} / 8 ." " if defined($interfaces[$i]{'portspeed'});
			$perf_out .= " ".perf_name($descr,"out_Bps")."=" . sprintf("%.0f",$checkperf_out[1] * $speed_metric) .";" if defined($checkperf_out[1]);
			$perf_out .= (defined($o_warn_max[1]) && $o_warn_max[1]) ? $o_warn_max[1]*$warn_factor . ";" : ";";
			$perf_out .= (defined($o_crit_max[1]) && $o_crit_max[1]) ? $o_crit_max[1]*$warn_factor . ";" : ";";
			$perf_out .= "0;". $interfaces[$i]{'portspeed'} / 8 ." " if defined($interfaces[$i]{'portspeed'});
		  }
	    }
	}
    }
    # output in octet counter
    if (defined($o_perfo) || (defined($o_prevperf) && !defined($o_nagios_saveddata))) {
	# we add 'c' for graphing programs to know its a COUNTER
        $perf_out .= " ".perf_name($descr,"in_octet")."=". $interfaces[$i]{'in_bytes'}."c";
        $perf_out .= " ".perf_name($descr,"out_octet")."=". $interfaces[$i]{'out_bytes'}."c";
    }
    if (defined($o_prevperf) && defined($o_nagios_saveddata)) {
        # we don't need to add 'c' if saved data is separate from perfdata
        $saved_out .= " ".perf_name($descr,"in_octet")."=". $interfaces[$i]{'in_bytes'};
        $saved_out .= " ".perf_name($descr,"out_octet")."=". $interfaces[$i]{'out_bytes'};
    }
    if (defined ($o_perfe) && defined($o_ext_checkperf)) {
	# these are techinically counters too, but its better to have them graphed as total
        $perf_out .= " ".perf_name($descr,"in_error")."=". $interfaces[$i]{'in_errors'};
        $perf_out .= " ".perf_name($descr,"out_error")."=". $interfaces[$i]{'out_errors'};
        $perf_out .= " ".perf_name($descr,"in_discard")."=". $interfaces[$i]{'in_dropped'} if defined ($interfaces[$i]{'in_dropped'});
        $perf_out .= " ".perf_name($descr,"out_discard")."=". $interfaces[$i]{'out_dropped'} if defined ($interfaces[$i]{'out_dropped'});
    }
    if (defined($interfaces[$i]{'portspeed'}) && defined($o_perf) && defined($o_intspeed)) {
        $perf_out .= " ".perf_name($descr,"speed_bps")."=".$interfaces[$i]{'portspeed'};
    }
  } 
}

# Add additional sets of previous performance data
# do it at the very end so that if nagios does cut performance data
# due to limits in its buffer space then what is cut is part of this data
my ($pcount,$loop_time);
if (defined($o_prevperf) && $o_pcount>0) {
  for (my $i=0; $i<$num_int; $i++) {
    $pcount=0;
    foreach $loop_time (reverse sort(@prev_time)) {
      if (defined($interfaces[$i]{'descr'}) && $pcount<($o_pcount-1)) {
        my $timeref='.'.$loop_time;
        $timeref='' if defined(prev_perf('ptime')) && prev_perf('ptime') eq $loop_time;
        if (defined(prev_perf($interfaces[$i]{'descr'},'in_octet'.$timeref)) &&
	    defined(prev_perf($interfaces[$i]{'descr'},'in_octet'.$timeref))) {
	  $saved_out .= " ".perf_name($interfaces[$i]{'descr'},'in_octet.'.$loop_time).'='.prev_perf($interfaces[$i]{'descr'},'in_octet'.$timeref);
	  $saved_out .= " ".perf_name($interfaces[$i]{'descr'},'out_octet.'.$loop_time).'='.prev_perf($interfaces[$i]{'descr'},'out_octet'.$timeref);
        }
        if (defined ($o_perfe) &&
	    defined(prev_perf($interfaces[$i]{'descr'},'in_error'.$timeref)) &&
	    defined(prev_perf($interfaces[$i]{'descr'},'out_error'.$timeref)) &&
	    defined(prev_perf($interfaces[$i]{'descr'},'in_discard'.$timeref)) &&
	    defined(prev_perf($interfaces[$i]{'descr'},'out_discard'.$timeref))) {
	  $saved_out .= " ".perf_name($interfaces[$i]{'descr'},'in_error.'.$loop_time).'='.prev_perf($interfaces[$i]{'descr'},'in_error'.$timeref);
	  $saved_out .= " ".perf_name($interfaces[$i]{'descr'},'out_error.'.$loop_time).'='.prev_perf($interfaces[$i]{'descr'},'out_error'.$timeref);
	  $saved_out .= " ".perf_name($interfaces[$i]{'descr'},'in_discard.'.$loop_time).'='.prev_perf($interfaces[$i]{'descr'},'in_discard'.$timeref);
	  $saved_out .= " ".perf_name($interfaces[$i]{'descr'},'out_discard.'.$loop_time).'='.prev_perf($interfaces[$i]{'descr'},'out_discard'.$timeref);
        }
        $pcount++;
      }
    }
  }
  $saved_out .= " ptime=".$timenow;
}

# Only a few ms left...
alarm(0);

# WL: partially rewritten these last steps to minimize amount of code
# Check if all interface are OK
my $exit_status="UNKNOWN";
if (($num_ok == $num_int) || (defined($o_admindown_ok) && $num_ok+$num_admindown == $num_int) ) {
  $exit_status="OK" if $final_status==0;
  $exit_status="WARNING" if $final_status==1;
  $exit_status="CRITICAL" if $final_status==2;
  if (defined($o_admindown_ok)) {
     print $print_out," ($num_ok UP, $num_admindown ADMIN DOWN): $exit_status";
  } else {
     print $print_out," ($num_ok UP): $exit_status";
  }
}
# print the not OK interface number and exit (return is always critical if at least one int is down)
else {
  $exit_status="CRITICAL";
  print $print_out,": ", $num_int-$num_ok-$num_admindown, " int NOK : CRITICAL";
}
print " | ",$perf_out if defined($perf_out) && $perf_out;
if (defined($saved_out) && $saved_out) {
	print " ||" if defined($o_nagios_saveddata);
	print $saved_out;
}
print "\n";
exit $ERRORS{$exit_status};
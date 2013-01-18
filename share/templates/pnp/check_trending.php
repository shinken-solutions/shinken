<?php
#
# Copyright (c) 2006-2008 Joerg Linge (http://www.pnp4nagios.org)
# Plugin: check_http
# $Id: check_http.php 367 2008-01-23 18:10:31Z pitchfork $
#


# Trend
#
$opt[1] = "--vertical-label \"$UNIT[1]\" --title \"Trending & Current - $hostname / $servicedesc\" ";
#
#
#

$def[1] =  "DEF:var2=$RRDFILE[2]:$DS[2]:AVERAGE " ;
$def[1] .= "AREA:var2#07FA0A:\"$NAME[2] \" " ;
$def[1] .= "LINE1:var2#000000 " ;
$def[1] .= "GPRINT:var2:LAST:\"%3.4lf$UNIT[2] last\" " ;
$def[1] .= "GPRINT:var2:AVERAGE:\"%3.4lf$UNIT[2] avg\" " ;
$def[1] .= "GPRINT:var2:MAX:\"%3.4lf$UNIT[2] max\\n\" ";


$def[1]  .=  "DEF:var1=$RRDFILE[1]:$DS[1]:AVERAGE " ;
#$def[1] .= "AREA:var1#07FA0A:\"$NAME[1] \" " ;
$def[1] .= "LINE1:var1#FF0000:\"$NAME[1] \" " ;
$def[1] .= "GPRINT:var1:LAST:\"%3.4lf$UNIT[1] last\" " ;
$def[1] .= "GPRINT:var1:AVERAGE:\"%3.4lf$UNIT[1] avg\" " ;
$def[1] .= "GPRINT:var1:MAX:\"%3.4lf$UNIT[1] max\\n\" ";


#
# Scenario Echoue
#
#$opt[2] = "--vertical-label \"$UNIT[2]\" --title \"Current - $hostname / $servicedesc\" ";
#
#
#

#
# Scenario NoSteps
#
$opt[2] = "--lower-limit -100 --upper-limit 100 --rigid --vertical-label \"$UNIT[3]\" --title \"Trend variation - $hostname / $servicedesc\" ";
#
#
#
$def[2] =  "DEF:var1=$RRDFILE[3]:$DS[3]:AVERAGE " ;
$def[2] .= "AREA:var1#FF00FF:\"$NAME[3] \" " ;
$def[2] .= "LINE1:var1#000000 " ;
$def[2] .= "GPRINT:var1:LAST:\"%3.4lf$UNIT[3] last\" " ;
$def[2] .= "GPRINT:var1:AVERAGE:\"%3.4lf$UNIT[3] avg\" " ;
$def[2] .= "GPRINT:var1:MAX:\"%3.4lf$UNIT[3] max\\n\" ";


?>

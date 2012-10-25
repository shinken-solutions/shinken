#!/usr/bin/perl 
##############################################################################
# This plugin uses df to gather filesystem statistics and check the percent  #
# used of inodes.  I've put a switch in here since i've got both aix and     #
# linux systems...adjust for your syntax's results.                          #
# Note: the percentages passed in MUST NOT have % after them                 #
# No warranty is either implied, nor expressed herein.                       #
#                                                                            #
##############################################################################

$filesystem = $ARGV[0];
$warnpercent = $ARGV[1];
$critpercent = $ARGV[2];

#------Find out what kind of syntax to expect
$systype=`uname`;
chomp($systype);

#------Make sure we got called with the right number of arguments
#------you could also put a check in here to make sure critical level is
#------greater than warning...but what the heck.
die "Usage: check_inodes filesystem warnpercent critpercent" unless @ARGV;

if ($#ARGV < 2) {
  die "Usage: check_inodes filesystem warnpercent critpercent";
}#end if

#------This gets the data from the df command
$inputline = `df -i $filesystem|grep -v "Filesystem"`;

#------replaces all spaces with a single :, that way we can use split
$inputline =~ y/ /:/s;

#------different oses give back different sets of columns from the df -i
#------(at least mine do).  This way I can use this plugin on all my hosts
#------if neither of these work, add your own in, or if you've got one that
#------just flat out reports something different...well...perl is your friend.
SWITCH: {
  if ($systype eq "Linux") {
    ($fs,$inodes,$iused,$ifree,$ipercent,$mntpt) = split(/:/,$inputline); 
    last SWITCH;
  }#end if
  if ($systype eq "AIX") {
    ($fs,$blks,$free,$percentused,$iused,$ipercent,$mntpt) = split(/:/,$inputline); 
    last SWITCH;
  }#end if
}#end switch

#------First we check for critical, since that is, by definition and convention
#------going to exceed the warning threshold
$ipercent =~ y/%//ds;

if ($ipercent > $critpercent) {
  print "CRITICAL: $filesystem inode use exceeds critical threshold $critpercent ($ipercent)";
  exit 1;
}# end if

#------Next we check the warning threshold
if ($ipercent > $warnpercent) {
  print "WARNING: $filesystem inode use exceeds warning threshold $warnpercent ($ipercent)";
  exit 2;
}# end if


#------thanks to the magic of procedural programming, we figure if we got here,
#------everything MUST be fine.
print "$filesystem inode use within limits ($ipercent)";
exit 0;


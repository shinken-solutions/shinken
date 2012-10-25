#!/usr/bin/perl

# Plugin to test signal strength on Breezecom wireless equipment
# Contributed by Jeffrey Blank

$Host=$ARGV[0];
$sig_crit=$ARGV[1];
$sig_warn=$ARGV[2];
$sig=0;
$sig = `snmpget $Host public .1.3.6.1.4.1.710.3.2.3.1.3.0`;
@test=split(/ /,$sig);
$sig=@test[2];
$sig=int($sig);
if ($sig>100){$sig=100}

print "Signal Strength at: $sig%\n";
if ($sig<$sig_crit)
  {exit(2)}
if ($sig<$sig_warn)
  {exit(1)}

exit(0);

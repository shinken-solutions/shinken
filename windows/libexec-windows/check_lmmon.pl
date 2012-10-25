#!/usr/bin/perl
# NetSaint Temp warning script
# Written by: Nathan LeSueur

if ($#ARGV < 1) {
print "Usage: $0 <critical temp> <warning temp> <normal temp>\n";
exit; } $crit = shift; $warn = shift; $norm = shift; if ($warn >
$crit) {    print "Warning level cannot be greater than critical
level!\n"; exit; } @b = qx{/usr/local/bin/lmmon -s}; foreach(@b) { @c
= split(/ \/ /, $_); $d = $c[1]; } @e = split(/F/, $d); $f = $e[0];

$status = "$f degrees F\n";

if($f >= $crit) {print "CRITICAL - $status"; exit 2;}
if($f >= $warn) {print "WARNING - $status"; exit 1;}
if($f <= $norm && $f != 0) {print "OK - $status"; exit 0;}
else{print "UNKNOWN - unable to access smb\n"; exit (-1);}



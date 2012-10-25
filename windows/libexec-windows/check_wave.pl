#!/usr/bin/perl

# CHECK_WAVE.PL
# Plugin to test signal strength on Speedlan wireless equipment
# Contributed by Jeffry Blank

$Host=$ARGV[0];
$sig_crit=$ARGV[1];
$sig_warn=$ARGV[2];




$low1 = `snmpget $Host public .1.3.6.1.4.1.74.2.21.1.2.1.8.1`;
@test=split(/ /,$low1);
$low1=@test[2];


$med1 = `snmpget $Host public .1.3.6.1.4.1.74.2.21.1.2.1.9.1`;
@test=split(/ /,$med1);
$med1=@test[2];


$high1 = `snmpget $Host public .1.3.6.1.4.1.74.2.21.1.2.1.10.1`;
@test=split(/ /,$high1);
$high1=@test[2];

sleep(2);



$snr = `snmpget $Host public .1.3.6.1.4.1.762.2.5.2.1.17.1`;
@test=split(/ /,$snr);
$snr=@test[2];
$snr=int($snr*25);
$low2 = `snmpget $Host public .1.3.6.1.4.1.74.2.21.1.2.1.8.1`;
@test=split(/ /,$low2);
$low2=@test[2];


$med2 = `snmpget $Host public .1.3.6.1.4.1.74.2.21.1.2.1.9.1`;
@test=split(/ /,$med2);
$med2=@test[2];


$high2 = `snmpget $Host public .1.3.6.1.4.1.74.2.21.1.2.1.10.1`;
@test=split(/ /,$high2);
$high2=@test[2];



$low=$low2-$low1;
$med=$med2-$med1;
$high=$high2-$high1;

$tot=$low+$med+$high;


if ($tot==0)
  {
   $ss=0;
  }
else
  {
   $lowavg=$low/$tot;
   $medavg=$med/$tot;
   $highavg=$high/$tot;
   $ss=($medavg*50)+($highavg*100);
  }
printf("Signal Strength at: %3.0f%,  SNR at $snr%",$ss);
#print "Signal Strength at: $ss%,  SNR at $snr%";
if ($ss<$sig_crit)
  {exit(2)}
if ($ss<$sig_warn)
  {exit(1)}

exit(0);

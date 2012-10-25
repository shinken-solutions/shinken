#! /usr/bin/perl -w
#
# Marko Riedel, EDV Neue Arbeit gGmbH, mriedel@neuearbeit.de 
#
#
#
#
use POSIX qw(strtol);

my $command_file = '/usr/local/nagios/var/rw/nagios.cmd';

my $hour = (60*60);
my $next_day = (24*60*60);

my $downtimes = 
  [
   { 
    host => 'somehost',
    service => 'SERVICE',
    times => [ ["00:00", 9], ["18:00", 6] ]
   }
  ];

foreach my $entry (@$downtimes) {
  my ($secstart, $secend, $cmd, $current);

  $current = `/bin/date +"%s"`;
  chomp $current;

  foreach my $tperiod (@{ $entry->{times} }){
    $secstart = strtol(`/bin/date -d "$tperiod->[0]" +"%s"`);
    $secend   = $secstart+$tperiod->[1]*$hour;

    $secstart += $next_day;
    $secend   += $next_day;

    $cmd  = "[$current] SCHEDULE_SVC_DOWNTIME;";
    $cmd .= "$entry->{host};$entry->{service};";
    $cmd .= "$secstart;$secend;";
    $cmd .= "1;0;$0;automatically scheduled;\n";

    print STDERR $cmd;

    system "echo \"$cmd\" >> $command_file";
  }
}  


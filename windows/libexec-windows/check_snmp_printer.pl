#!/usr/local/bin/perl -w

# check_snmp_printer - check for printer status via snmp
#  Supports both standard PRINT-MIB (RFC-1759) and HP Enterprise print-mib
#  that is supported by some of the older JetDirect interfaces

# Acknowledgements:
# the JetDirect code is taken from check_hpjd.c by Ethan Galstad
#   
#   The idea for the plugin (as well as some code) were taken from Jim
#   Trocki's pinter alert script in his "mon" utility, found at
#   http://www.kernel.org/software/mon
#

# Notes:
# 'JetDirect' is copyrighted by Hewlett-Packard
#
#
# License Information:
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
############################################################################
#
# TODO: Query HOST-RESOURCE MIB for a quick status
#
# hrPrinterStatus = .1.3.6.1.2.1.25.3.5.1;
# hrPrinterDetectedErrorState = .1.3.6.1.2.1.25.3.5.1.2
#
# hrPrinterStatus OBJECT-TYPE
#    SYNTAX     INTEGER {
#                   other(1),
#                   unknown(2),
#                   idle(3),
#                   printing(4),
#                   warmup(5)
#               }
#
# hrPrinterDetectedErrorState OBJECT-TYPE
#    SYNTAX     OCTET STRING
#    MAX-ACCESS read-only
#    STATUS     current
#    DESCRIPTION
#        "This object represents any error conditions detected
#        by the printer.  The error conditions are encoded as
#        bits in an octet string, with the following
#        definitions:
#
#             Condition         Bit #
#
#             lowPaper              0
#
#             noPaper               1
#             lowToner              2
#             noToner               3
#             doorOpen              4
#             jammed                5
#             offline               6
#             serviceRequested      7
#             inputTrayMissing      8
#             outputTrayMissing     9
#             markerSupplyMissing  10
#             outputNearFull       11
#             outputFull           12
#             inputTrayEmpty       13
#             overduePreventMaint  14
#
#  
#
use strict;
use Getopt::Long;
use vars qw($opt_V $opt_h $opt_H $opt_P $opt_t $opt_d $session $error $answer $key
   $response $PROGNAME $port $hostname );
use lib  "utils.pm";
use utils qw(%ERRORS &print_revision &support &usage );
use Net::SNMP;

sub print_help ();
sub print_usage ();

$ENV{'PATH'}='';
$ENV{'BASH_ENV'}=''; 
$ENV{'ENV'}='';

# defaults 
my $ptype = 1;  						# to standard RFC printer type
my $state = $ERRORS{'UNKNOWN'};
my $community = "public";
my $snmp_version = 1;
my $port = 161;

Getopt::Long::Configure('bundling');
GetOptions
	("d"   => \$opt_d, "debug"			=> \$opt_d,
	 "V"   => \$opt_V, "version"		=> \$opt_V,
	 "P=s" => \$opt_P, "Printer=s"      => \$opt_P,    # printer type - HP or RFC
	 "v=i" => \$snmp_version, "snmp_version=i"  => \$snmp_version,
	 "p=i" => \$port, "port=i" => \$port,
	 "C=s" => \$community,"community=s" => \$community,
	 "h"   => \$opt_h, "help"		=> \$opt_h,
	 "H=s" => \$opt_H, "hostname=s"		=> \$opt_H);



$PROGNAME = "check_snmp_printer";

if ($opt_V) {
	print_revision($PROGNAME,'$Revision: 795 $');
	exit $ERRORS{'OK'};
}

if ($opt_h) {print_help(); exit $ERRORS{'OK'};}

unless (defined $opt_H) {
	print "No target hostname specified\n";
	exit $ERRORS{"UNKNOWN"};
}
$hostname = $opt_H;
if (! utils::is_hostname($hostname)){
	usage(" $hostname did not match pattern\n");
	exit $ERRORS{"UNKNOWN"};
}

if (defined $opt_P) {
	if ($opt_P eq "HP" ) {
		$ptype = 2;
	}elsif ($opt_P eq "RFC" ) {
		$ptype = 1;
	}else{
		print "Only \"HP\" and \"RFC\" are supported as printer options at this time.\n";
		exit $ERRORS{"UNKNOWN"};
	}
}


if ( $snmp_version =~ /[12]/ ) {
		
	($session, $error) = Net::SNMP->session(
	      -hostname  => $hostname,
	      -community => $community,
	      -port      => $port,
		  -version	=> $snmp_version
		   );

	if (!defined($session)) {
	      $state='UNKNOWN';
	      $answer=$error;
	      print ("$state: no session - $answer\n");
	      exit $ERRORS{$state};
	}

	print "Opened session|" if (defined ($opt_d));
		
}elsif ( $snmp_version =~ /3/ ) {
	$state='UNKNOWN';
	print ("$state: No support for SNMP v3 yet\n");
	exit $ERRORS{$state};
}else{
	$state='UNKNOWN';
	print ("$state: No support for SNMP v$snmp_version yet\n");
	exit $ERRORS{$state};
}






### main logic

if ( $ptype == 1 ) {   # STD MIB
	print "STD-MIB|" if (defined ($opt_d));

	my %snmp_response;
	my $snmp_index;
	my $col_oid;
	my %std_mib_inst_count ;
	my %std_mib_instances;
	my $display;
	my $inst;
	my $group;
	

	#### RFC1759 MIB OIDS

	# sub-unit status - textual convention
	my $subunit_status;   # integer from 0-126						
						

	# column oid - not instances
	my %std_mib = (
		std_mib_input_status => 				".1.3.6.1.2.1.43.8.2.1.11",  # 2 element index
		std_mib_input_name   => 				".1.3.6.1.2.1.43.8.2.1.13",
		std_mib_output_remaining_capacity => 	".1.3.6.1.2.1.43.9.2.1.5", 
		std_mib_output_status =>				".1.3.6.1.2.1.43.9.2.1.6",
		std_mib_marker_tech =>					".1.3.6.1.2.1.43.10.2.1.2",
		std_mib_marker_counter_unit =>	".1.3.6.1.2.1.43.10.2.1.3",
		std_mib_marker_life_count =>		".1.3.6.1.2.1.43.10.2.1.4",
		std_mib_marker_status =>				".1.3.6.1.2.1.43.10.2.1.15",
		std_mib_supplies_type =>				".1.3.6.1.2.1.43.11.1.1.5",
		std_mib_supplies_level =>				".1.3.6.1.2.1.43.11.1.1.9",
		std_mib_media_path_type =>				".1.3.6.1.2.1.43.13.4.1.9",
		std_mib_media_path_status =>			".1.3.6.1.2.1.43.13.4.1.11",

		std_mib_status_display => 				".1.3.6.1.2.1.43.16.5.1.2",  # 2 element index

		std_mib_alert_sev_level =>				".1.3.6.1.2.1.43.18.1.1.2",
		std_mib_alert_grp =>					".1.3.6.1.2.1.43.18.1.1.4",
		std_mib_alert_location => 				".1.3.6.1.2.1.43.18.1.1.5",

	);

	my %std_mib_marker_tech = (
					1 => "other",
					2 => "unknown",
					3 => "electrophotographicLED",
					4 => "electrophotographicLaser",
					5 => "electrophotographicOther",
					6 => "impactMovingHeadDotMatrix9pin",
					7 => "impactMovingHeadDotMatrix24pin",
					8 => "impactMovingHeadDotMatrixOther",
					9 => "impactMovingHeadFullyFormed",
					10 => "impactBand",
					11 => "impactOther",
					12 => "inkjectAqueous",
					13 => "inkjetSolid",
					14 => "inkjetOther",
					15 => "pen",
					16 => "thermalTransfer",
					17 => "thermalSensitive",
					18 => "thermalDiffusion",
					19 => "thermalOther",
					20 => "electroerosion",
					21 => "electrostatic",
					22 => "photographicMicrofiche",
					23 => "photographicImagesetter",
					24 => "photographicOther",
					25 => "ionDeposition",
					26 => "eBeam",
					27 => "typesetter",
	);
	
	my %std_mib_marker_counter_units = (
					3 => "tenThousandthsOfInches",
					4 => "micrometers",
					5 => "characters",
					6 => "lines",
					7 => "impressions",
					8 => "sheets",
					9 => "dotRow",
					11 => "hours",
					16 => "feet",
					17 => "meters",
	);

	my %std_mib_alert_groups = (
		1 => "unspecifiedOther",
		3 => "printerStorageMemory",  # hostResourcesMIBStorageTable
		4 => "internalDevice",			# hostResourcesMIBDeviceTable
		5 => "generalPrinter",
		6 => "cover",
		7 => "localization",
		8 => "input",
		9 => "output",
		10 => "marker",
		11 => "markerSupplies",
		12 => "markerColorant",
		13 => "mediaPath",
		14 => "connectionChannel",
		15 => "interpreter",
		16 => "consoleDisplayBuffer",
		17 => "consoleLights",
	);

		
	my %std_mib_prt_alert_code = (
		1 => "other",                      # ok if on power save
		2 => "unknown",
    	# -- codes common to serveral groups
		3 => "coverOpen",
		4 => "coverClosed",
		5 => "interlockOpen",
		6 => "interlockClosed",
		7 => "configurationChange",
		8 => "jam",                        # critical
		# -- general Printer group
		501 => "doorOpen",
		502 => "doorClosed",
		503 => "powerUp",
		504 => "powerDown",
		# -- Input Group
		801 => "inputMediaTrayMissing",
		802 => "inputMediaSizeChange",
		803 => "inputMediaWeightChange",
		804 => "inputMediaTypeChange",
		805 => "inputMediaColorChange",
		806 => "inputMediaFormPartsChange",
		807 => "inputMediaSupplyLow",
		808 => "inputMediaSupplyEmpty",
		# -- Output Group
		901 => "outputMediaTrayMissing",
		902 => "outputMediaTrayAlmostFull",
		903 => "outputMediaTrayFull",
		# -- Marker group
		1001 => "markerFuserUnderTemperature",
		1002 => "markerFuserOverTemperature",
		# -- Marker Supplies group
		1101 => "markerTonerEmpty",
		1102 => "markerInkEmpty",
		1103 => "markerPrintRibbonEmpty",
		1104 => "markerTonerAlmostEmpty",
		1105 => "markerInkAlmostEmpty",
		1106 => "markerPrintRibbonAlmostEmpty",
		1107 => "markerWasteTonerReceptacleAlmostFull",
		1108 => "markerWasteInkReceptacleAlmostFull",
		1109 => "markerWasteTonerReceptacleFull",
		1110 => "markerWasteInkReceptacleFull",
		1111 => "markerOpcLifeAlmostOver",
		1112 => "markerOpcLifeOver",
		1113 => "markerDeveloperAlmostEmpty",
		1114 => "markerDeveloperEmpty",
		# -- Media Path Device Group
		1301 => "mediaPathMediaTrayMissing",
		1302 => "mediaPathMediaTrayAlmostFull",
		1303 => "mediaPathMediaTrayFull",
		# -- interpreter Group	
		1501 => "interpreterMemoryIncrease",
		1502 => "interpreterMemoryDecrease",
		1503 => "interpreterCartridgeAdded",
		1504 => "interpreterCartridgeDeleted",
		1505 => "interpreterResourceAdded",
		1506 => "interpreterResourceDeleted",
	);

	## Need multiple passes as oids are all part of tables	
	foreach $col_oid (sort keys %std_mib ){ 

		if ( !defined( $response = $session->get_table($std_mib{$col_oid}) ) ) {
			print "Error col_oid $col_oid|" if (defined ($opt_d));

			if (! ($col_oid =~ m/std_mib_alert/ ) ) {             # alerts don't have to exist all the time!
				$answer=$session->error;
				$session->close;
				$state = 'CRITICAL';
				print ("$state: $answer for $std_mib{$col_oid}\n");
				exit $ERRORS{$state};
			}
		}
		
		print "NoError col_oid $col_oid|" if (defined ($opt_d));
		
		foreach $key (keys %{$response}) {
			$key =~ /.*\.(\d+)\.(\d+)$/;     # all oids have a two part index appended
			$snmp_index = $1 . "." . $2;   
			print "\n$key => $col_oid.$snmp_index  = $response->{$key} \n" if (defined ($opt_d));
			$snmp_response{$key} = $response->{$key} ;
			
			$std_mib_inst_count{$col_oid} += 1 ;   # count how many instances
			$std_mib_instances{$col_oid} .= $snmp_index .":" ;

		}
	
	}

	#foreach $key ( keys %std_mib_inst_count) {
	#	print "$key = $std_mib_inst_count{$key} $std_mib_instances{$key}  \n";
	#}
	# get (total) "page count" - perfdata
	#print "\n \n $std_mib_instances{'std_mib_marker_tech'} \n";	
	# how many marker technologies are in use?
	my ($pg, $pt, $pfd);
	my @mark_tech = split(/:/, $std_mib_instances{'std_mib_marker_tech'});
	foreach $inst (sort @mark_tech){
		$pfd = $std_mib_marker_tech{$snmp_response{$std_mib{'std_mib_marker_tech'}."." .$inst}} ;
		$pfd .= ",".$snmp_response{$std_mib{'std_mib_marker_life_count'}.".".$inst};
		$pfd .=	",".$std_mib_marker_counter_units{$snmp_response{$std_mib{'std_mib_marker_counter_unit'}.".".$inst}};
		$pfd .= ";"; #perf data separator for multiple marker tech


		print "pfd = $pfd\n" if (defined ($opt_d));
	};

	# combine all lines of status display into one line
	#$std_mib_instances{'std_mib_status_display'} = substr($std_mib_instances{'std_mib_status_display'}, 1);
	my @display_index = split(/:/,	$std_mib_instances{'std_mib_status_display'} );
	
	foreach $inst ( sort @display_index) {
		$display .= $snmp_response{$std_mib{'std_mib_status_display'} . "." . $inst} . " ";
	}



	# see if there are any alerts
	if (defined ( $std_mib_inst_count{'std_mib_alert_sev_level'} )  ) {
		
		if ( ( lc($display) =~ /save/  || lc($display) =~ /warm/ ) &&	$std_mib_inst_count{'std_mib_alert_sev_level'} == 1 ) {
			$state='OK';
			$answer = "Printer ok - $display";
			print $answer . "|$pfd\n";
			exit $ERRORS{$state};
		}
		
		# sometime during transitions from power save to warming there are 2 alerts
		# if the 2nd alert is for something else it should get caught in the
		# next call since warmup typically is much smaller than check time
		# interval.
		if (  lc($display) =~ /warm/  &&	$std_mib_inst_count{'std_mib_alert_sev_level'} == 2 )   {
			$state='OK';
			$answer = "$state: Printer - $display";
			print $answer . "|$pfd\n";
			exit $ERRORS{$state};
		}

		
		# We have alerts and the display does not say power save or warming up
		$std_mib_instances{'std_mib_alert_sev_level'} = substr($std_mib_instances{'std_mib_alert_sev_level'}, 1);
		@display_index = split(/:/,	$std_mib_instances{'std_mib_alert_sev_level'} );
		$answer = "Alert location(s): ";
		
		for $inst (@display_index) {
			$state = 'WARNING';
			if ( $snmp_response{$std_mib{'std_mib_alert_location'} . "." . $inst} < 1) {
				$answer .= "unknown location ";
			}else{
				$answer .= $std_mib_prt_alert_code{$snmp_response{$std_mib{'std_mib_alert_location'} . "." . $inst} } . " ";
			
				#print $std_mib_prt_alert_code{$snmp_response{$std_mib{'std_mib_alert_location'}. "." . $inst}} ;
			}
		}

		print "$state: $answer|$pfd\n";
		exit $ERRORS{$state};
		
	}else{
		$state='OK';
		$answer = "$state: Printer ok - $display ";
		print $answer . "|$pfd\n";
		exit $ERRORS{$state};

	}
	
	
	

}
elsif( $ptype == 2 ) {  # HP MIB - JetDirect
	
	#### HP MIB OIDS - instance OIDs
	my $HPJD_LINE_STATUS=			".1.3.6.1.4.1.11.2.3.9.1.1.2.1.0";
	my $HPJD_PAPER_STATUS=			".1.3.6.1.4.1.11.2.3.9.1.1.2.2.0";
	my $HPJD_INTERVENTION_REQUIRED=	".1.3.6.1.4.1.11.2.3.9.1.1.2.3.0";
	my $HPJD_GD_PERIPHERAL_ERROR=	".1.3.6.1.4.1.11.2.3.9.1.1.2.6.0";
	my $HPJD_GD_PAPER_JAM=			".1.3.6.1.4.1.11.2.3.9.1.1.2.8.0";
	my $HPJD_GD_PAPER_OUT=			".1.3.6.1.4.1.11.2.3.9.1.1.2.9.0";
	my $HPJD_GD_TONER_LOW=			".1.3.6.1.4.1.11.2.3.9.1.1.2.10.0";
	my $HPJD_GD_PAGE_PUNT=			".1.3.6.1.4.1.11.2.3.9.1.1.2.11.0";
	my $HPJD_GD_MEMORY_OUT=			".1.3.6.1.4.1.11.2.3.9.1.1.2.12.0";
	my $HPJD_GD_DOOR_OPEN=		 	".1.3.6.1.4.1.11.2.3.9.1.1.2.17.0";
	my $HPJD_GD_PAPER_OUTPUT=		".1.3.6.1.4.1.11.2.3.9.1.1.2.19.0";
	my $HPJD_GD_STATUS_DISPLAY=		".1.3.6.1.4.1.11.2.3.9.1.1.3.0";
	#define ONLINE		0
	#define OFFLINE		1

	my @hp_oids = ( $HPJD_LINE_STATUS,$HPJD_PAPER_STATUS,$HPJD_INTERVENTION_REQUIRED,$HPJD_GD_PERIPHERAL_ERROR,
				$HPJD_GD_PAPER_JAM,$HPJD_GD_PAPER_OUT,$HPJD_GD_TONER_LOW,$HPJD_GD_PAGE_PUNT,$HPJD_GD_MEMORY_OUT,
				$HPJD_GD_DOOR_OPEN,$HPJD_GD_PAPER_OUTPUT,$HPJD_GD_STATUS_DISPLAY);



	
	$state = $ERRORS{'OK'};

	if (!defined($response = $session->get_request(@hp_oids))) {
		$answer=$session->error;
		$session->close;
		$state = 'CRITICAL';
		print ("$state: $answer \n");
		exit $ERRORS{$state};
	}

	# cycle thru the responses and set the appropriate state
	
	if($response->{$HPJD_GD_PAPER_JAM} ) {
		$state='WARNING';
		$answer = "Paper Jam";
	}
	elsif($response->{$HPJD_GD_PAPER_OUT} ) {
		$state='WARNING';
		$answer = "Out of Paper";
	}
	elsif($response->{$HPJD_LINE_STATUS} ) {
		if ($response->{$HPJD_LINE_STATUS} ne "POWERSAVE ON" ) {
			$state='WARNING';
			$answer = "Printer Offline";
		}
	}
	elsif($response->{$HPJD_GD_PERIPHERAL_ERROR} ) {
		$state='WARNING';
		$answer = "Peripheral Error";
	}
	elsif($response->{$HPJD_INTERVENTION_REQUIRED} ) {
		$state='WARNING';
		$answer = "Intervention Required";
	}
	elsif($response->{$HPJD_GD_TONER_LOW} ) {
		$state='WARNING';
		$answer = "Toner Low";
	}
	elsif($response->{$HPJD_GD_MEMORY_OUT} ) {
		$state='WARNING';
		$answer = "Insufficient Memory";
	}
	elsif($response->{$HPJD_GD_DOOR_OPEN} ) {
		$state='WARNING';
		$answer = "Insufficient Memory";
	}
	elsif($response->{$HPJD_GD_PAPER_OUTPUT} ) {
		$state='WARNING';
		$answer = "OutPut Tray is Full";
	}
	elsif($response->{$HPJD_GD_PAGE_PUNT} ) {
		$state='WARNING';
		$answer = "Data too slow for Engine";
	}
	elsif($response->{$HPJD_PAPER_STATUS} ) {
		$state='WARNING';
		$answer = "Unknown Paper Error";
	}
	else		# add code to parse STATUS DISPLAY here
	{
		$state='OK';
		$answer = "Printer ok - $response->{$HPJD_GD_STATUS_DISPLAY} ";
	}

	# print and exit

	print "$state: $answer \n";
	exit $ERRORS{$state};


}
else{  # 3rd printer type - not yet supported
	
	print "Printer type $opt_P has not been implemented\n";
	$state='UNKNOWN';
	exit $ERRORS{$state};

}



#### subroutines
sub unit_status {
	my $stat = shift;
	

}

sub print_usage () {
	print "Usage: $PROGNAME -H <host> [-C community] [-P HP or RFC] [-p port]  [-v snmp_version] [-h help]  [-V version]\n";
}

sub print_help () {
	print_revision($PROGNAME,'$Revision: 795 $');
	print "Copyright (c) 2002 Subhendu Ghosh/Ethan Galstad.

This plugin reports the status of an network printer with an SNMP management
module.

";
	print_usage();
	print "
-H, --hostname=HOST
   Name or IP address of host to check
-C --community
   snmp community string (default: public)
-P --Printer
   supported values are \"HP\" for Jetdirect printers and
   \"RFC\" for RFC 1759 Print MIB based implementations (default: RFC)
-p --port
   Port where snmp agent is listening (default: 161)
-v --snmp_version
   SNMP version to use (default: version 1)
-h --help
   This screen
-V --version
   Plugin version

";
	support();
}




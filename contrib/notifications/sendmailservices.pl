#!/usr/bin/perl
use MIME::QuotedPrint;
use HTML::Entities;
use Mail::Sendmail 0.75; # doesn't work with v. 0.74!

$NOTIFICATIONTYPE=$ARGV[0];
$SERVICEDESC=$ARGV[1];
$HOSTNAME=$ARGV[2];
$HOSTADDRESS=$ARGV[3];
$SERVICESTATE=$ARGV[4];
$SHORTDATETIME=$ARGV[5];
$SERVICEOUTPUT=$ARGV[6];
$TO=$ARGV[7];
#$HOSTNAME=$ARGV[8];

$boundary = "====" . time() . "====";

$text = "***** Notification Shinken *****\n\n"
	. "Notification : $NOTIFICATIONTYPE\n\n"
	. "Impacted service : $SERVICEDESC\n"
	. "State : $SERVICESTATE\n\n"
	. "Related host : $HOSTNAME\n"
	. "Address : $HOSTADDRESS\n"
	. "Date/Time : $SHORTDATETIME\n\n"
	. "Service output : $SERVICEOUTPUT";

$texthtml = " <center><strong>***** Shinken Notification *****</strong></center>\n";

$color="blue";
$colorstate="black";

if ($NOTIFICATIONTYPE =~ /RECOVERY/ | $NOTIFICATIONTYPE =~ ACKNOWLEDGEMENT) {
	$color="#339933";
	if ($SERVICESTATE =~ /OK/){
		$colorstate="#339933";
	}
}

if ($NOTIFICATIONTYPE =~ /PROBLEM/) {
	$color="#FF0000";

	if ($SERVICESTATE =~ /CRITICAL/) {
       		$colorstate="#FF0000";
    	}
    	if ($SERVICESTATE =~ /WARNING/) {
        	$colorstate="#FF9900";
    	}
    	if ($SERVICESTATE =~ /UNKNOWN/) {
        	$colorstate="#999999";
    	}
}

$SERVICEOUTPUT =~ s/=/&#61;/g;

if ($NOTIFICATIONTYPE =~ /RECOVERY/){
	if ($SERVICESTATE =~ /OK/){
		$colorstate="#339933";
	}
}

$texthtml = $texthtml  . "<strong>Notification : <span style='color:$color'>$NOTIFICATIONTYPE</span></strong>\n\n"
	. "<strong>Impacted service : <i>$SERVICEDESC</i></strong>\n"
	. "<strong>State : <span style='color:$colorstate'>$SERVICESTATE</span></strong>\n\n";

$texthtml = $texthtml  . "<strong>Host</strong> : $HOSTNAME\n"
	. "<strong>Address</strong> : <i>$HOSTADDRESS</i>\n"
	. "<strong>Date/Time</strong> : <i>$SHORTDATETIME</i>\n\n"
	. "<strong>Service output</strong> : $SERVICEOUTPUT\n\n\n\n";

%mail = (
	 from => 'Monitoring Agent <monitor-agent@invaliddomain.org>',
         to => $TO,
         subject => "$SERVICEDESC $SERVICESTATE on $HOSTNAME",
         'content-type' => "multipart/alternative; boundary=\"$boundary\"",
         'Auto-Submitted' => "auto-generated"
        );

$plain = encode_qp $text;

#$html = encode_entities($texthtml);
$html = $texthtml;
#$html =~ s/\n\n/\n\n<p>/g;
$html =~ s/\n/<br>\n/g;
#$html = "<p>" . $html . "</p>";

$boundary = '--'.$boundary;


$mail{body} = <<END_OF_BODY;
$boundary
Content-Type: text/plain; charset="utf-8"
Content-Transfer-Encoding: quoted-printable

$plain

$boundary
Content-Type: text/html; charset="utf-8"

$html

$boundary--
END_OF_BODY

sendmail(%mail) || print "Error: $Mail::Sendmail::error\n";


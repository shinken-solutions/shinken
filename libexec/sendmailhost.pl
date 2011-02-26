#!/usr/bin/perl
use MIME::QuotedPrint;
use HTML::Entities;
use Mail::Sendmail 0.75; # doesn't work with v. 0.74!

$NOTIFICATIONTYPE=$ARGV[0];
$HOSTNAME=$ARGV[1];
$HOSTSTATE=$ARGV[2];
$HOSTADDRESS=$ARGV[3];
$HOSTOUTPUT=$ARGV[4];
$SHORTDATETIME=$ARGV[5];
$TO=$ARGV[6];
#$HOSTNAME=$ARGV[7];
#$DOWNTIME=$ARGV[8];

$boundary = "====" . time() . "====";

$text = "***** Notification Shinken *****\n\n"
        . "Notification : $NOTIFICATIONTYPE\n\n"
        . "Host : $HOSTNAME\n\n"
        . "Address : $HOSTADDRESS\n"
        . "State : $HOSTSTATE\n\n"
        . "Date/Time : $SHORTDATETIME\n\n"
        . "Host output : $HOSTOUTPUT";

$texthtml = " <center><table border='11><th><strong>***** Notification Shinken *****</strong></th></table></center>\n";

$color="blue";
if ($NOTIFICATIONTYPE =~ /RECOVERY/) {
	$color="#339933";
}
if ($NOTIFICATIONTYPE =~ /PROBLEM/) {
	$color="#FF0000";
}

$HOSTOUTPUT =~ s/=/&#61;/g;

$texthtml = $texthtml  . "<strong>Notification type : <span style='ccolor:$color> $NOTIFICATIONTYPE </span></strong>\n\n";

if ($DOWNTIME != 0) {
        $color="#3333FF";
	$texthtml = $texthtml . "<strong><i><span style='ccolor:$color>This device is actually in maintenance.</span></i></strong>\n\n";
}

if ($HOSTSTATE =~ /DOWN/) {
	$color="#FF0000";
}
if ($HOSTSTATE =~ /UP/) {
	$color="#339933";
}
if ($HOSTSTATE =~ /UNREACHABLE/) {
	$color="#00CCCC";
}

$texthtml = $texthtml  . "<strong>Impacted host</strong> : $HOSTNAME\n"
	. "<strong>Address</strong> : <i>$HOSTADDRESS</i> \n"
	. "<strong>Host State : <span style='ccolor:$color> $HOSTSTATE </span></strong>\n"
	. "<strong>Date/Time</strong> : <i>$SHORTDATETIME</i> \n\n"
	. "<strong>Host Output</strong> : $HOSTOUTPUT \n\n\n\n";


%mail = (
         from => 'Monitoring Agent <monitor-agent@invaliddomain.org>',
         to => $TO,
         subject => "$HOSTNAME is $HOSTSTATE !",
         'content-type' => "multipart/alternative; boundary=\"$boundary\"",
         'Auto-Submitted' => "auto-generated"
        );

$plain = encode_qp $text;

#$html = encode_entities($texthtml);
$html = $texthtml;
$html =~ s/\n\n/\n\n<p>/g;
$html =~ s/\n/<br>\n/g;
$html = "<p>" . $html . "</p>";

$boundary = '--'.$boundary;

$mail{body} = <<END_OF_BODY;
$boundary
Content-Type: text/plain; charset="utf-8"
Content-Transfer-Encoding: quoted-printable

$plain

$boundary
Content-Type: text/html; charset="utf-8"
Content-Transfer-Encoding: quoted-printable

<html>$html</html>
$boundary--
END_OF_BODY

sendmail(%mail) || print "Error: $Mail::Sendmail::error\n";


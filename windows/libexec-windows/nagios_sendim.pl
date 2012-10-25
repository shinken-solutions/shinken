#!/usr/bin/perl -w
#
# SENDIM 1.0 by Sergio Freire (sergio-s-freire@ptinovacao.pt)
# Nagios plugin to send notifications using instant messages through a jabber server
# 
# Note:  a) you can send messages to several different IM systems like ICQ,AIM,MSN,etc...
#        b) to test this plugin you can execute it with the arguments needed and write the message followed by a CTRL+D
#
# Please check http://www.jabber.org and http://www.jabberstudio.org for more information on Jabber Instant Messaging
 

use Net::Jabber qw(Client);
use Getopt::Std;

my $tmp;
my $mensagem="";
getopts("u:p:t:");
if ( (!defined($opt_u)) || (!defined($opt_p)) || (!defined($opt_t)))
	{
		print "USE: sendim -u user_JID -p password -t destination_JID\n";
		print 'EXAMPLE: sendim -u nagios@jabber.org -p nagios -t bitcoder@nagios.org'."\n";
		print "        (send an instant message as user nagios\@jabber.org to bitcoder\@jabber.org)\n";
		exit;
	}

my @buf=split('@',$opt_u);
my $login=$buf[0];
@buf=split('/',$buf[1]);
my $server=$buf[0];
my $resource=$buf[1] || "nagios";
my $password=$opt_p;
my $jid_dest=$opt_t;
my $debug=0; # Set debug=1 to enable output of debug information

while ($tmp=<STDIN>)
{
 $mensagem.=$tmp;
}

print "LOGIN: $login\nSERVER: $server\nRESOURCE: $resource\n" if $debug;
print "TO: $jid_dest\n" if $debug;

$Con1 = new Net::Jabber::Client();
$Con1->Connect(hostname=>$server);

           if ($Con1->Connected()) {
             print "CON1: We are connected to the server...\n" if $debug;
           } 

           @result1 = $Con1->AuthSend(username=>$login,
                                    password=>$password,
                                    resource=>$resource);


$Con1->PresenceSend();
$Con1->Process(1);

@result1=$Con1->MessageSend( to=>$jid_dest,
                             subject=>"nagios",
                             body=>$mensagem,
			     type=>"chat",
                             priority=>1);

$Con1->Process(1);
$Con1->Disconnect();
exit;

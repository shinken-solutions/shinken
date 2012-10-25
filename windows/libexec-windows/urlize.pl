#!/usr/bin/perl
#
# urlize.pl
#   jcw, 5/12/00
#
# A wrapper around Nagios plugins that provides a URL link in the output
#
#
# Pay close attention to quoting to ensure that the shell passes the
# expected data to the plugin. For example, in:
#
#    urlize http://example.com/ check_http -H example.com -r 'two words'
#
# the shell will remove the single quotes and urlize will see:
#
#    urlize http://example.com/ check_http -H example.com -r two words
#
# You probably want:
#
#    urlize http://example.com/ \"check_http -H example.com -r 'two words'\"
#
($#ARGV < 1) && die "Incorrect arguments";
my $url = shift;

chomp ($result = `@ARGV`);
print "<A HREF=\"$url\">$result</A>\n";

# exit with same exit value as the child produced
exit ($? >> 8);

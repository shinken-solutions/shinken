#!/bin/sh
# script to make a manpage from the text-based help of check_wmi_plus.pl
# the formatting part is taken from txt2man
# txt2man is largely left intact with some additional scripting to get the text help from check_wmi_plus
# and run man with the generated manpage
# the txt2man command line options that we use are hardcoded
# we do it like this since, if you make your own ini files then the help text changes and this allows you to
# read your own help text because the manpage is generated dynamically

# first parameter is the location of check_wmi_plus so that we can get the text-based help
check_wmi_plus_text_help="$1"

# dir where we store the man page we create
manpage_dir="$2"

# dir under $manpage_dir where the manpage is really stored
mkdir -p "$manpage_dir/man1"

# the full path to the manpage file
manfile="$manpage_dir/man1/check_wmi_plus.1"

# if we are not running in a terminal then only show the text-based help
if [ ! -t 0 ]; then
   # we are not running in a terminal
   echo "Not running in a terminal - showing text-based help"
   echo
   exec $check_wmi_plus_text_help
fi


usage()
{
cat << EOT
This is the original usage for txt2man. Left here to assist with formatting information.
NAME
  txt2man - convert flat ASCII text to man page format
SYNOPSIS
  txt2man [-hpTX] [-t mytitle] [-P pname] [-r rel] [-s sect]
          [-v vol] [-I txt] [-B txt] [-d date] [ifile]
DESCRIPTION
  txt2man converts the input text into nroff/troff standard man(7)
  macros used to format Unix manual pages. Nice pages can be generated
  specially for commands (section 1 or 8) or for C functions reference
  (sections 2, 3), with the ability to recognize and format command and
  function names, flags, types and arguments.

  txt2man is also able to recognize and format sections, paragraphs,
  lists (standard, numbered, description, nested), cross references and
  literal display blocks.

  If input file ifile is omitted, standard input is used. Result is
  displayed on standard output.

  Here is how text patterns are recognized and processed:
  Sections    These headers are defined by a line in upper case, starting
              column 1. If there is one or more leading spaces, a
	      sub-section will be generated instead.
  Paragraphs  They must be separated by a blank line, and left aligned.
  Tag list    The item definition is separated from the item description
              by at least 2 blank spaces, even before a new line, if
              definition is too long. Definition will be emphasized
              by default.
  Bullet list  
              Bullet list items are defined by the first word being "-"
	      or "*" or "o".
  Enumerated list  
	      The first word must be a number followed by a dot.
  Literal display blocks  
	      This paragraph type is used to display unmodified text,
	      for example source code. It must be separated by a blank
	      line, and be indented. It is primarily used to format
	      unmodified source code. It will be printed using fixed font
	      whenever possible (troff).
  Cross references  
	      A cross reference (another man page) is defined by a word
	      followed by a number in parenthesis.

  Special sections:
  NAME      The function or command name and short description are set in
            this section.
  SYNOPSIS  This section receives a special treatment to identify command
            name, flags and arguments, and propagate corresponding
            attributes later in the text. If a C like function is recognized
	    (word immediately followed by an open parenthesis), txt2man will
	    print function name in bold font, types in normal font, and
	    variables in italic font. The whole section will be printed using
	    a fixed font family (courier) whenever possible (troff).

  It is a good practice to embed documentation into source code, by using
  comments or constant text variables. txt2man allows to do that, keeping
  the document source readable, usable even without further formatting
  (i.e. for online help) and easy to write. The result is high quality
  and standard complying document.
OPTIONS
  -h          The option -h displays help.
  -d date     Set date in header. Defaults to current date.
  -P pname    Set pname as project name in header. Default to uname -s.
  -p          Probe title, section name and volume.
  -t mytitle  Set mytitle as title of generated man page.
  -r rel      Set rel as project name and release.
  -s sect     Set sect as section in heading, ususally a value from 1 to 8.
  -v vol      Set vol as volume name, i.e. "Unix user 's manual".
  -I txt      Italicize txt in output. Can be specified more than once.
  -B txt      Emphasize (bold) txt in output. Can be specified more than once.
  -T          Text result previewing using PAGER, usually more(1).
  -X          X11 result previewing using gxditview(1).
ENVIRONMENT
  PAGER    name of paging command, usually more(1), or less(1). If not set
           falls back to more(1).
EXAMPLE
  Try this command to format this text itself:

      $ txt2man -h 2>&1 | txt2man -T
HINTS
  To obtain an overall good formating of output document, keep paragraphs
  indented correctly. If you have unwanted bold sections, search for
  multiple spaces between words, which are used to identify a tag list
  (term followed by a description). Choose also carefully the name of
  command line or function parameters, as they will be emphasized each
  time they are encountered in the document.
SEE ALSO
  man(1), mandoc(7), rman(1), groff(1), more(1), gxditview(1), troff(1).
BUGS
  - Automatic probe (-p option) works only if input is a regular file (i.e.
  not stdin).
AUTHOR
  Marc Vertes <mvertes@free.fr>
EOT
}

sys=$(uname -s)
rel=
volume=
section=
title=untitled
doprobe=
itxt=
btxt=
post=cat

# txt2man options ignored - we have hardcoded the ones we want
#while getopts :d:hpTXr:s:t:v:P:I:B: opt
#do
#	case $opt in
#	d) date=$OPTARG;;
#	r) rel=$OPTARG;;
#	t) title=$OPTARG;;
#	s) section=$OPTARG;;
#	v) volume=$OPTARG;;
#	P) sys=$OPTARG;;
#	p) doprobe=1;;
#	I) itxt="$OPTARG§$itxt";;
#	B) btxt=$OPTARG;;
#	T) post="groff -mandoc -Tlatin1 | ${PAGER:-more}";;
#	X) post="groff -mandoc -X";;
#	*) usage; exit;;
#	esac
#done
#shift $(($OPTIND - 1))

# hardcoded txt2man option values
title="Check_WMI_Plus"

date=${date:-$(date +'%d %B %Y')}

if test "$doprobe"
then
	title=${1##*/}; title=${title%.txt}
	if grep -q '#include ' $1
	then
		section=${section:-3}
		volume=${volume:-"$sys Programmer's Manual"}
	else
		section=${section:-1}
		volume=${volume:-"$sys Reference Manual"}
	fi
	# get release from path
	rel=$(pwd | sed 's:/.*[^0-9]/::g; s:/.*::g')
fi

head=".\\\" Text automatically generated by txt2man
.TH $title $section \"$date\" \"$rel\" \"$volume\""

# see if we can run man
# try and run man, relying on $PATH
man > /dev/null 2>&1
manexit=$?

if [ "$manexit" = "127" ]; then
   # can not find man - just show the check_wmi_plus text help
   echo "Warning: Can not find 'man' in \$PATH to show manpage - showing text-based help"
   echo
   exec $check_wmi_plus_text_help
fi

# now we belive than man will run, so generate the man page

# run check_wmi_plus text-based help
echo "Generating Manpage ..."
$check_wmi_plus_text_help |
# gawk is needed because use of non standard regexp
gawk --re-interval -v head="$head" -v itxt="$itxt" -v btxt="$btxt" '
BEGIN {
	print head
	avar[1] = btxt; avar[2] = itxt
	for (k in avar) {
		mark = (k == 1) ? "\\fB" : "\\fI"
		split(avar[k], tt, "§")
		for (i in tt)
			if (tt[i] != "")
				subwords["\\<" tt[i] "\\>"] = mark tt[i] "\\fP"
		for (i in tt)
			delete tt[i]
	}
	for (k in avar)
		delete avar[k]
}
{
	# to avoid some side effects in regexp
	sub(/\.\.\./, "\\.\\.\\.")
	# remove spaces in empty lines
	sub(/^ +$/,"")
}
/^[[:upper:][:space:]]+$/ {
	# Section header
	if ((in_bd + 0) == 1) {
		in_bd = 0
		print ".fam T\n.fi"
	}
	if (section == "SYNOPSIS") {
		print ".fam T\n.fi"
		type["SYNOPSIS"] = ""
	}
	if ($0 ~/^[^[:space:]]/)
		print ".SH " $0
	else
		print ".SS" $0
	sub(/^ +/, "")
	section = $0
	if (section == "SYNOPSIS") {
		print ".nf\n.fam C"
		in_bd = 1
	}
	ls = 0		# line start index
	pls = 0		# previous line start index
	pnzls = 0	# previous non zero line start index
	ni = 0		# indent level
	ind[0] = 0	# indent offset table
	prevblankline = 0
	next
}
{
	# Compute line start index, handle start of example display block
	pls = ls
	if (ls != 0)
		pnzls = ls
	match($0, /[^ ]/)
	ls = RSTART
	if (pls == 0 && pnzls > 0 && ls > pnzls && $1 !~ /^[0-9\-\*\o]\.*$/) {
		# example display block
		if (prevblankline == 1) {
			print ".PP"
			prevblankline = 0
		}
		print ".nf\n.fam C"
		in_bd = 1
		eoff = ls
	}
	if (ls > 0 && ind[0] == 0)
		ind[0] = ls
}
(in_bd + 0) == 1 {
	# In block display
	if (section == "SYNOPSIS")
		;
	else if (ls != 0 && ls < eoff) {
		# End of litteral display block
		in_bd = 0
		print ".fam T\n.fi"
	} else { print; next }
}
section == "NAME" {
	$1 = "\\fB" $1
	sub(/ \- /, " \\fP- ")
}
section == "SYNOPSIS" {
	# Identify arguments of fcts and cmds
	if (type["SYNOPSIS"] == "") {
		if ($0 ~ /\(/)
			type["SYNOPSIS"] = "fct"
		else if ($1 == "struct" || $2 == "struct")
			type["SYNOPSIS"] = "struct"
		else if ($1 && $1 !~ /^#|typedef|struct|union|enum/)
			type["SYNOPSIS"] = "cmd"
	}
	if (type["SYNOPSIS"] == "cmd") {
		# Line is a command line
		if ($1 !~ /^\[/) {
			b = $1
			sub(/^\*/, "", b)
			subwords["\\<" b "\\>"] = "\\fB" b "\\fP"
		}
		for (i = 2; i <= NF; i++) {
			a = $i
			gsub(/[\[\]\|]/, "", a)
			if (a ~ /^[^\-]/)
				subwords["\\<" a "\\>"] = "\\fI" a "\\fP"
		}
	} else if (type["SYNOPSIS"] == "fct") {
		# Line is a C function definition
		if ($1 == "typedef") {
			if ($0 !~ /\(\*/)
				subwords["\\<" $2 "\\>"] = "\\fI" $2 "\\fP"
		} else if ($1 == "#define")
			subwords["\\<" $2 "\\>"] = "\\fI" $2 "\\fP"
		for (i = 1; i <= NF; i++) {
			if ($i ~ /[\,\)]\;*$/) {
				a = $i
				sub(/.*\(/, "", a)
				gsub(/\W/, "", a)
				subwords["\\<" a "\\>"] = "\\fI" a "\\fP"
			}
		}
	}
}
{
	# protect dots inside words
	while ($0  ~ /\w\.\w/)
		sub(/\./, "_dOt_")
	# identify func calls and cross refs
	for (i = 1; i <= NF; i++) {
		b = $i
		sub(/^\*/, "", b)
		if ((a = index(b, ")(")) > 3) {
			w = substr(b, 3, a - 3)
			subwords["\\<" w "\\>"] = "\\fI" w "\\fP"
		}
		if ((a = index(b, "(")) > 1) {
			w = substr(b, 1, a - 1)
			subwords["\\<" w "\\("] = "\\fB" w "\\fP("
		}
	}
	# word attributes
	for (i in subwords)
		gsub(i, subwords[i])
	# shell options
	gsub(/\B\-+\w+(\-\w+)*/, "\\fB&\\fP")
	# unprotect dots inside words
	gsub(/_dOt_/, ".")

	if (section == "SYNOPSIS") {
		sub(/^  /, "")
		print
		next
	}
	if (match($0, /[^ ]  +/) > 0) {
		# tag list item
		adjust_indent()
		tag = substr($0, 1, RSTART)
		sub(/^ */, "", tag)
		if (RSTART+RLENGTH < length())
			$0 = substr($0, RSTART + RLENGTH)
		else
			$0 = ""
		print ".TP\n.B"
		print tag
		prevblankline = 0
		if (NF == 0)
			next
	} else if ($1 == "-"||$1 == "o"||$1 == "*") {
		# bullet list item
		adjust_indent()
		print ".IP \\(bu 3"
		prevblankline = 0
		$1 = ""
	} else if ($1 ~ /^[0-9]+[\).]$/) {
		# enum list item
		adjust_indent()
		print ".IP " $1 " 4"
		prevblankline = 0
		$1 = ""
	} else if (pls == 0) {
		# new paragraph
		adjust_indent()
	} else if (NF == 0) {
		# blank line
		prevblankline = 1
		next
	} else
		prevblankline = 0
	# flush vertical space
	if (prevblankline == 1) {
		print ".PP"
		prevblankline = 0
	}
	if (section != "SYNOPSIS" || $0 ~ /^ {1,4}/)
		sub(/ */,"")
	print
}

function adjust_indent()
{
	if (ls > ind[ni]) {
		ind[++ni] = ls
		print ".RS"
	} else if (ls < ind[ni]) {
		while (ls < ind[ni]) {
			ni--
			print ".RE"
		}
	}
}
' > $manfile

# this should work
# we tested it before generating the manpage
# we must -M to point to our own man directory - this works for Fedora we assume it does for other systems as well!!!
man -M "$manpage_dir" check_wmi_plus

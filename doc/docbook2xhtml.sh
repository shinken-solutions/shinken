#!/bin/bash

cp style.css xhtml/
rsync -avP --exclude=.svn images xhtml/
xmllint --xinclude --postvalid  nagios.xml --output nagios-big.xml
xsltproc --output xhtml/ --xinclude xhtml.xsl nagios-big.xml
rm nagios-big.xml

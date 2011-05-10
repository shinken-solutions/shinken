#!/bin/bash

SCRIPTPATH=$(dirname $(readlink -f $0))
for file in $(find $SCRIPTPATH -type f -name *.pyc)
do
	echo "removing : "$file
	rm $file
done
rm -Rf $SCRIPTPATH/var/web/nagiosadmin

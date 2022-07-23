#!/bin/sh

DIR=$(cd $(dirname "$0"); pwd)
if [ -z "${PYTHON}" ]; then
    PYTHON=python3
fi
cd $DIR
echo "$PWD"

if [ ! -f test.history ]; then
	touch test.history
fi

for ii in $(ls -1 test_*py) ; do
	if grep -q $ii test.history; then
    	echo "Skipping already tested $ii"
		continue
	fi
    echo "Launching Test $ii"
    ${PYTHON} $ii
	if [ $? -eq 0 ]; then
		echo $ii >> test.history
	else
		echo "Failed test $ii"
		exit 1
	fi
done

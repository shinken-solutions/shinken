#!/bin/bash
for fic in $(find . -type f -name "*.pyc")
do
	rm -f $fic
done

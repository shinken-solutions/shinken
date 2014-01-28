#!/bin/bash

cd ../source/12_references


echo ".. _shinken_class_reference:
Shinken Class Reference
=======================

.. toctree::
   :maxdepth: 1
" > index.rst
  


for d in `find ../../../shinken/ -maxdepth 1 -type d`
do
    dirname=`basename $d`
    if [ "$dirname" == "shinken" ]
    then
        dirname=""
        submodule=""
        l=0
    else
        l=`expr length $dirname`
        mkdir -p ./$dirname
        submodule=".$dirname"
    fi


    echo ${dirname^} > ./$dirname/index.rst
    title=''
    for j in `seq $l`
    do
        title="$title="
    done
    echo $title >> ./$dirname/index.rst
    echo "" >> ./$dirname/index.rst
    echo "" >> ./$dirname/index.rst
    echo ".. toctree::" >> ./$dirname/index.rst
    echo "   :maxdepth: 1" >> ./$dirname/index.rst
    echo "" >> ./$dirname/index.rst

    echo "   $dirname/index" >> ./index.rst
    for i in `ls ../../../shinken/$dirname/*.py -1`i
    do
        name=`basename $i |cut -d "." -f 1`;
        filename=./$dirname/${name}.rst
        echo "${name^}" > $filename
        l=`expr length $name`
        title=''
        for j in `seq $l`
        do
            title="$title="
        done
        echo $title >> $filename
        echo "" >> $filename
        echo "" >> $filename
        echo ".. automodule:: shinken${submodule}.${name}" >> $filename
        echo "   :members:" >> $filename
        echo "   :undoc-members:" >> $filename
        echo "   $name" >> ./$dirname/index.rst
        sed -i '/__init__/d' ./$dirname/index.rst
    done
    
done

rm __init__.rst
rm */__init__.rst
sed -i '/ \/index/d' ./index.rst

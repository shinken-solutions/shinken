#!/usr/bin/env bash

MODE="$1"
DF="$2"


mkdir /tmp/share 2>/dev/null

if [ $MODE == "test" ]; then
   # -p 8000:8000
   docker run  --rm=true --privileged --cap-add ALL  -v /tmp/share:/tmp/share --tty --interactive --entrypoint=/bin/bash `docker build -q -f test/docker-files/$DF .| cut -d':' -f2`
   exit $?
fi


if [ $MODE == "run" ]; then
   docker run --rm=true --privileged --cap-add ALL  -v /tmp/share:/tmp/share --tty --interactive  `docker build -q -f test/docker-files/$DF .| cut -d':' -f2`
   exit $?
fi


if [ $MODE == "build" ]; then
   docker build -f test/docker-files/$DF .
   exit $?
fi
#!/usr/bin/env bash


# Travis: only need to run the installation once, it it not link to a specific python version. They don't need to use CPU for nothing ;)
if [ "$TEST_SUITE" == "PYTHON" ]; then
   echo "Installing dependencies for Python Unit tests"
   cd ..
   ./test/setup_test.sh
   # Get back in test to exec unit tests
   cd test

   #pip install -r ../dependencies
   #pip install coveralls
   #pip install nose-cov
   #pip install unittest2

   echo "Test launch for Python"
   # Now all is launched via
   ./quick_tests.sh
   #if [[ $TRAVIS_PYTHON_VERSION == '2.6' ]]; then pip install ordereddict; fi
   # notice: the nose-cov is used because it is compatible with --processes, but produce a .coverage by process
   # so we must combine them in the end
   # * -x : stop at first error
   # * --exe : allow to launch test py that are executable
   # * --process : use 1 sub process
   # * --process-timeout: at max 5min for a test to run
   # * --process-resttartworker: one sub process by test, to avoid mix between libs
   # NOTE: I don't kow why, byt process options are failing, with endless run
   #nosetests -xv --processes=1 --process-timeout=300 --process-restartworker --with-cov --cov=opsbro --exe
   exit $?
fi

echo "Test installations for SUITE  $TEST_SUITE"
# If not python, launch installations, and only a sub part if possible
./test_installation.sh

exit $?
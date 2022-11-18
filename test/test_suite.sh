#!/usr/bin/env bash

# Travis: only need to run the installation once, it it not link to a specific python version. They don't need to use CPU for nothing ;)
if [ "$TEST_SUITE" == "UNIT-TEST" ]; then
    echo "Installing dependencies for Python Unit tests"

    if "$TRAVIS_PYTHON_VERSION" == "2.7"; then
        sudo apt-get install -y  python-pip
        sudo apt-get install -y  python-pycurl
        sudo apt-get install -y  python-nose
        sudo pip install -r requirements.txt
        #sudo pip install coveralls
        #sudo pip install nose-cov

        echo "Test launch for Python2"
        # notice: the nose-cov is used because it is compatible with --processes, but produce a .coverage by process
        # so we must combine them in the end
        # * -x : stop at first error
        # * --exe : allow to launch test py that are executable
        # * --process : use 1 sub process
        # * --process-timeout: at max 5min for a test to run
        # * --process-resttartworker: one sub process by test, to avoid mix between libs
        # NOTE: I don't kow why, byt process options are failing, with endless run
        nosetests -xv --processes=1 --process-timeout=300 --process-restartworker test
        exit $?
    else
        sudo apt-get install -y  python3-pip
        sudo apt-get install -y  python3-pycurl
        sudo apt-get install -y  python3-nose
        sudo pip3 install -r requirements.txt
        #sudo pip install coveralls
        #sudo pip install nose-cov

        echo "Test launch for Python3"
        # notice: the nose-cov is used because it is compatible with --processes, but produce a .coverage by process
        # so we must combine them in the end
        # * -x : stop at first error
        # * --exe : allow to launch test py that are executable
        # * --process : use 1 sub process
        # * --process-timeout: at max 5min for a test to run
        # * --process-resttartworker: one sub process by test, to avoid mix between libs
        # NOTE: I don't kow why, byt process options are failing, with endless run
        nosetests3 -xv --processes=1 --process-timeout=300 --process-restartworker test
        exit $?
    fi
else
    echo "Test installations for SUITE  $TEST_SUITE"
    # If not python, launch installations, and only a sub part if possible
    ./test/test_installation.sh
    exit $?
fi

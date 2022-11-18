#!/usr/bin/env bash

# Tests Shinken installation on different distributions to test dependencies
# are satisfied and the services run correctly.


###############################################################################
#
# Utility functions
#

# Color codes
declare -A COLORS
COLORS[black]=30
COLORS[red]=31
COLORS[green]=32
COLORS[yellow]=33
COLORS[blue]=34
COLORS[magenta]=35
COLORS[cyan]=36
COLORS[white]=37

declare -A WEIGHT
WEIGHT[normal]=0
WEIGHT[bold]=1
WEIGHT[underline]=4
WEIGHT[blinking]=5
WEIGHT[reverse]=7


function print_color {
    local mesg=$1
    local color=$2
    local weight=$3
    if [ -z "$weght" ]; then
        weight=normal
    fi
    echo -e "\e[${WEIGHT[$weight]};${COLORS[$color]}m$mesg\e[0m"
}


function try_installation {
    FULL_PATH=$1
    DOCKER_FILE=$(basename $FULL_PATH)
    TAG=$(echo $DOCKER_FILE | sed 's/\.txt$//'|tr '[:upper:]' '[:lower:]')
    NOW=$(date +"%H:%M:%S")
    print_color "$DOCKER_FILE : starting at $NOW \n" magenta
    docker build -t $TAG -f $FULL_PATH .
    if [ $? != 0 ]; then
        print_color "ERROR:$DOCKER_FILE" red bold
        echo $DOCKER_FILE >> $FAIL_FILE
        return 1
    fi
    docker run --rm $TAG
    if [ $? != 0 ]; then
        print_color "ERROR: $DOCKER_FILE" red bold
        echo $DOCKER_FILE >> $FAIL_FILE
        return 1
    fi
    NOW=$(date +"%H:%M:%S")
    print_color "OK: $DOCKER_FILE at $NOW" green bold
    echo $DOCKER_FILE >> $SUCCESS_FILE
}

###############################################################################

echo "Launching installations tests for SUITE: $TEST_SUITE"

SUCCESS_FILE=/tmp/shinken.test.installation.success
FAIL_FILE=/tmp/shinken.test.installation.fail

# Clean results files
> $SUCCESS_FILE
> $FAIL_FILE

# Only do the test suite we must do
for DOCKER_FILE in test/docker-files/docker-file-$TEST_SUITE-*txt; do
    try_installation $DOCKER_FILE
done

printf "Some tests are OK:\n"
cat $SUCCESS_FILE

ALL_ERRORS=$(cat $FAIL_FILE)
if [ "X$ALL_ERRORS" == "X" ]; then
    echo "OK, no errors."
    exit 0
else
    echo "ERRORS: some tests did fail:"
    cat $FAIL_FILE
    exit 1
fi

#!/bin/bash

#########################################################
#
#   Check state of IBM DS4x00 / 5x00 Health Status
#   
#   uses IBM SMclient package, tested with version 10.70 
#
#   created by Martin Moebius
#   Modified by Forlot Romain
#
#   05.10.2011 - 1.0 * initial version
#
#   28.11.2011 - 1.1 * added Status "Warning" instead of "Critical" in case of Preferred Path error
#                    * changed filtering of SMcli output to string based sed instead of position based awk
#                    * moved filtering of SMcli output to remove redundant code
#                    * more comments on code
#
#   06.02.2012 - 1.2 * added patch from user "cseres", better SMcli output parsing
#   13.07.2012 - 1.3 * call to sudo to execute SMcli.
#
#########################################################

#SMcli location
COMMAND="sudo /opt/IBM_DS/client/SMcli"
ARG=""

# Define Nagios return codes
#
STATE_OK=0
STATE_WARNING=1
STATE_CRITICAL=2
STATE_UNKNOWN=3


#Help output
#
print_help() {

        echo ""
        echo "IBM DS4x00/5x00 Health Check"
        echo "the script requires IP of at least one DS4x00/5x00 Controller, second is optional"
        echo "or check by the storage array name. If both controller IP addresses and storage array"
        echo "are provided then storage array name is choosen"
        echo ""
        echo "Usage     check_IBM_DS_health.sh [-a X.X.X.X -b X.X.X.X] | [-n storage-array-name ]"
        echo ""
        echo "          -h  Show this page"
        echo "          -a  IP of Controller A"
        echo "          -b  IP of Controller B"
        echo "          -n  Storage array name"
        echo ""
    exit 0	
}

# Make sure the correct number of command line arguments have been supplied
#
if [ $# -lt 1 ]; then
    echo "At least one argument must be specified"
    print_help
    exit $STATE_UNKNOWN
fi

# Grab the command line arguments
#
while [ $# -gt 0 ]; do
    case "$1" in
        -h | --help)
            print_help
            exit $STATE_OK
            ;;
        -a | --ctrla)
               shift
               ARG=$ARG" $1"
                ;;
        -b | --ctrlb)
               shift
               ARG=$ARG" $1"
               ;;
        -n | --name)
               shift
               ARG=$ARG' -n '$1
               ;;
        *) 
               echo "Unknown argument: $1"
               print_help
               exit $STATE_UNKNOWN
            ;;
        esac
shift
done


# Check the health status via SMcli
#

##execute SMcli
<<<<<<< HEAD
RESULT=$($COMMAND $ARG -S -c "show storageSubsystem healthStatus;")
=======
RESULT=$($COMMAND $CTRLA_IP $CTRLB_IP -c "show storageSubsystem healthStatus;")

##filter unnecessary SMcli output
RESULT=$(echo $RESULT |sed 's/Performing syntax check...//g' | sed 's/Syntax check complete.//g' | sed 's/Executing script...//g' | sed 's/Script execution complete.//g'| sed 's/SMcli completed successfully.//g' )
>>>>>>> upstream/master

##check SMcli output to identfy error and report back to Nagios
case "$RESULT" in
 *optimal*)
  echo $RESULT
  echo "OK"
  exit $STATE_OK
  ;;
 *failure*)
  case "$RESULT" in
    *failed*|*Failed*)
      echo $RESULT
      echo "CRITICAL"
      exit $STATE_CRITICAL
    ;;
    *preferred*|*Preferred*)
      echo $RESULT
      echo "WARNING"
      exit $STATE_WARNING
    ;;
  esac
  ;;
 *)
  echo "Unkown response from SMcli: \" $RESULT \""
  echo "UNKNOWN"
  exit $STATE_UNKNOWN
 ;;
esac

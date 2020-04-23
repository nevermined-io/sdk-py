#!/bin/bash

# Run this in the root of the squid-py repo
# (to get paths of ./artifacts and the scripts themselves)
# Set the environment variable export TEST_NILE=1 for testing vs. deployed Nile
# Set the environment variable export TEST_NILE=0 for testing vs. local Spree network
# Default (no environment variable) is Spreej

#usage="$(basename) [-h] -- testing
#
#where:
#    -h  show this help text
#
#Run this in the root of the squid-py repo
#(to get paths of ./artifacts and the scripts themselves)
#Set the environment variable export TEST_NILE=1 for testing vs. deployed Nile
#Set the environment variable export TEST_NILE=0 for testing vs. local Spree network
#Default (no environment variable) is Spree"


RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

let passes=0
let fails=0
let total=0
unset summarystring
let summarystring=""

runtest() {
#    conda env list
    SCRIPT_PATH=$1
    SCRIPT_NAME=$2
    echo "\n*********************************************************"
    echo -e " Running test: " $2
    echo "*********************************************************\n"

    python $SCRIPT_PATH$SCRIPT_NAME

    exit_status=$?
    if [ $exit_status -eq 0 ]; then
        MESSAGE="Success, (exit code "$exit_status")"
        passes=$((passes + 1))
        total=$((total + 1))
        summarystring="$summarystring${GREEN}     ✔ $SCRIPT_NAME  \n"
    else
        MESSAGE="Fail, (exit code "$exit_status")"
        fails=$((fails + 1))
        total=$((total + 1))
        summarystring="$summarystring${RED}     ✗ $SCRIPT_NAME    \n"
    fi

    echo "\n********* TEST COMPLETE *********************************"
    echo " $SCRIPT_NAME: $MESSAGE"
    echo "*********************************************************\n"
}

runtest ./squid_py/examples/ register_asset.py
runtest ./squid_py/examples/ resolve_asset.py
runtest ./squid_py/examples/ search_assets.py
runtest ./squid_py/examples/ sign_agreement.py
runtest ./squid_py/examples/ buy_asset.py

SQUID_VERSION=$(pip freeze | grep squid)

echo "\n********* SUMMARY OF $total TESTS ***************************"

echo -e "\n"
echo "     Squid version:"
echo "     "$SQUID_VERSION

echo -e "\n"
if [ $TEST_NILE -eq 1 ]; then
    echo "     Summary of $total tests against deployed Nile network"
else
    echo "     Summary of $total tests against local Spree network"
fi

echo "\n"
echo "     "$passes" scripts passed"
echo "     "$fails" scripts failed"

echo "\n"

echo $summarystring
echo ${NC}

echo "*********************************************************\n"
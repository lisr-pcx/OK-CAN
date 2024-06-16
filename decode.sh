#!/bin/bash

# Name:     decode.sh
# Author:   lisr-pcx
# Update:   2024 June 11
# MIT License (c) 2024 lisr-pcx

# Note: to make executable permission, run the following chmod command:
# $ chmod -v +x decode.sh

Help()
{
    echo "[O]verrated [K]it-CAN"
    echo "Decode an input CAN trace into corresponding packets."
    echo "Please make sure to have Python3 installed on your system."
    echo ""
    echo "Syntax: decode.sh <TRACE_FILE> <JSON_PKT_DESCRIPTION>"
    echo ""
    echo "At the end of the decoding process two files will be available:"
    echo "  <TRACE_FILE>.dt     : list of decode messages"
    echo "  <TRACE_FILE>.dt.dp  : list of decode packet, based on JSON description"
    echo ""
    echo "Note1: <JSON_PKT_DESCRIPTION> is optional"
    echo "Note2: debug logs are available, see files:"
    echo "    dt.log"
    echo "    dp.log"
}

Help
echo "Start..."

if [ "$1" != "" ] 
then
    python3 ./can_trace_decoder.py $1 > dt.log 2>&1
    if [ "$2" != "" ]
    then
        python3 ./can_packet_decoder.py $1.dt $2 > dp.log 2>&1
    fi
fi

echo "Done!"
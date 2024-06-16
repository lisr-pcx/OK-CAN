#!/bin/bash

# Name:     decode.sh
# Author:   lisr-pcx
# Update:   2024 June 11

# Usage:
# $ ./decode <TRACE_FILE> <JSON_PACKET_DESCRIPTION>
#              |            |
#              |          (Optional) how to decode CAN messages
#              |
#             Input file containing all CAN segments sniffed from bus
#
# Two specific log files are created for debugging purpose.
#   decode.sh.trace.log
#   decode.sh.packet.log
#
# Please make sure to have Python 3.x installed on your system
#
# Note: to make executable permission, run the following chmod command:
# $ chmod -v +x decode.sh

echo "[O]verrated [K]it-CAN"
echo "Decode an input CAN trace into corresponding packets"
echo ""

if [ "$1" != "" ] 
then
    python3 ./can_trace_decoder.py $1 > decode.sh.trace.log 2>&1
    if [ "$2" != "" ]
    then
        python3 ./can_packet_decoder.py $1.TRACE.txt $2 > decode.sh.packet.log 2>&1
    fi
fi

echo "Done!"
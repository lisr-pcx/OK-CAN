# Name:     can_trace_decoder.py
# Author:   lisr-pcx
# Update:   2024 June 11
# MIT License (c) 2024 lisr-pcx

"""Decode a CAN trace (raw 8 bytes) composing the final CAN message

This script is compatible with following CAN trace format:

ASCII Trace IXXAT MiniMon V3  Version: 1.1.4.4533
Date: 5/9/2024
Start time: 2:37:37 PM
Stop time: 2:37:37 PM
Overruns:                                                            
Baudrate: 500 kbit/s
"Time","Identifier (hex)","Format","Flags","Data (hex)"
"00:30:06.866","184","Std","","00 06 00 16 75 EE 00 3C"
"00:30:06.866","184","Std","","28 84 00 00 00 00 00 00"
"00:30:06.866","184","Std","","30 00 00 00 00 00 00 00"
"00:30:06.866","184","Std","","5C 00 00 00 00 00 00 00"
"00:30:06.867","300","Std","","00 09 00 07 20 03 00 00"
"00:30:06.867","300","Std","","4B 01 83 49 00 00 00 00"
"00:30:06.882","374","Std","","00 01 00 1A 02 C9 08 0A"
"00:30:06.883","374","Std","","28 02 02 02 02 02 02 00"
"00:30:06.883","374","Std","","30 00 02 02 02 00 00 1C"
"00:30:06.883","374","Std","","38 02 1F 00 00 00 00 00"
"00:30:06.883","374","Std","","41 00 00 00 00 00 00 00"
...

The payload structure of each segment is the following:

______________
SINGLE SEGMENT

byte 0      xxx-----        CS  Command Specifier
                                011 : one segment
            ---00---        X   Always set to value zero
            -----xxx        VB  Number of byte of data in the segment payload, 0..6
byte 1                      Message number
byte 2..7                   Payload (filling with zero)

________________
MULTIPLE SEGMENT

byte 0      xxx-----        CS  Command Specifier
                                000 : first segment
                                001 : middle segment
                                010 : end segment
            ---xx---        SN  Serial Number of the segment (cyclic)
            -----000        For 'first' and 'middle' segment is always set to zero
            -----xxx        For 'end' segment is the number of byte of data in the segment payload, 0..6
byte 1                      For 'first' segment is the Message number
byte 1                      For 'middle' and 'end' segment contains payload
byte 2..3                   For 'first' segment is the length of data
byte 2..3                   For 'middle' and 'end' segment contains payload
byte 4..7                   Payload (filling with zero)

"""

import os.path
import argparse
import re
import math
from collections import deque

re_basic_hex = "[0-9aAbBcCdDeEfF]"
re_basic_hex_with_spaces = "[0-9aAbBcCdDeEfF ]"
re_parsing_can_trace = r'^"(.*)","(' + re_basic_hex + '{3})","(.*)","(.*)","(' + re_basic_hex_with_spaces + '{23})"$'
re_parsing_data_hex = r'^"(' + re_basic_hex + '{2}) \
                          (' + re_basic_hex + '{2}) \
                          (' + re_basic_hex + '{2}) \
                          (' + re_basic_hex + '{2}) \
                          (' + re_basic_hex + '{2}) \
                          (' + re_basic_hex + '{2}) \
                          (' + re_basic_hex + '{2}) \
                          (' + re_basic_hex + '{2})"$'

# Store decoded packets
packet_list = deque()

# store in-progress packets because composed of multiple segments
# (key is the COB)
packet_in_progress_list = dict()

class CanPacket:

    def Append(self, data: str):
        self.rx_data += data
        self.rx_len = len(self.rx_data) / 2

    def Info(self):
        info = "{0:<14} ; {1:<4} ; {2:<6} ; {3:<6d} ; {4:<}"
        return info.format(self.rx_time, self.rx_cob, self.rx_msg_number, int(self.rx_len), self.rx_data)
    
    def __init__(self, time: str, cob: str, data: str, msg_number: int):
        self.rx_time = time
        self.rx_cob = cob
        self.rx_data = data
        self.rx_len = len(data) / 2
        self.rx_msg_number = msg_number

def first_segment(time: str, cob: str, data: str):
    MSG_NUM_field = int(data[2:4], 16)
    MSG_LEN_field = int(data[4:8], 16)
    # TODO check message sequence
    if cob in packet_in_progress_list:
        print("ERR: previous msg was incomplete, discarded and start with a new one")
    else:
        packet_in_progress_list[cob] = CanPacket(time, cob, data[8:], MSG_NUM_field)

def middle_segment(time: str, cob: str, data: str):
    if cob in packet_in_progress_list:
        packet_in_progress_list[cob].Append(data[2:])
    else:
        print("ERR: first segment is missing, middle segment discarded")

def end_segment(time: str, cob: str, data: str, VB: str):
    if cob in packet_in_progress_list:
        packet_in_progress_list[cob].Append(data[2:2+2*int(VB, 2)])
        if arguments_list.verbose:
            print(packet_in_progress_list[cob].Info())
        packet_list.append(packet_in_progress_list.pop(cob))
    else:
        print("ERR: first and middle segments are missing, end segment discarded")

def single_segment(time: str, cob: str, data: str, VB: str):
    MSG_NUM_field = int(data[2:4], 16)
    # TODO check message sequence
    message = CanPacket(time, cob, data[4:4+2*int(VB, 2)], int(MSG_NUM_field))
    if arguments_list.verbose:
        print(message.Info())
    packet_list.append(message)

def manage_can_segment(time: str, cob: str, data: str):
    data = data.replace(" ","")
    byte0 = "{0:08b}".format(int(data[0:2], 16))    
    CS_field = byte0[:3]
    SN_field = byte0[3:5:1]
    VB_field = byte0[-3:]
    
    if CS_field == "000" :
        first_segment(time, cob, data)        
    elif CS_field == "001" :
        middle_segment(time, cob, data)        
    elif CS_field == "010" :
        end_segment(time, cob, data, VB_field)        
    elif CS_field == "011" :
        single_segment(time, cob, data, VB_field)
    else :
        print("ERR: invalid CS for value " + CS_field)

def write_decoded_packets():
    output_file = open(arguments_list.tracefilepath + ".DECODED", "w")
    for elem in packet_list:
        output_file.write(elem.Info() + "\n")
    output_file.close()   

def create_arg_parser():
    # Creates and returns the ArgumentParser object
    parser = argparse.ArgumentParser(
                        prog='python can_trace_decoder.py',
                        description='Decode CAN trace extracting packets of each COB id.',
                        epilog='This is free software and it comes with absolutely no warranty.')
    parser.add_argument('tracefilepath',
                        type=str,
                        help='Path to CAN trace')
    parser.add_argument('-v', '--verbose',
                        action='store_true',
                        help='Show detailed logging (default is false).')
    return parser

if __name__ == "__main__":
    arguments = create_arg_parser()
    arguments_list = arguments.parse_args()
    
    # Check file existence
    if os.path.isfile(arguments_list.tracefilepath):
        print("Opening file: " + arguments_list.tracefilepath)
        print("Start analyze trace...")

        # Analyze line by line
        with open(arguments_list.tracefilepath, 'r') as file:
            for line in file:
                # Extract info using regex - FIXME make it compatible to all formats
                decoded_values = re.search(re_parsing_can_trace, line)
                if decoded_values:

                    time_info = str(decoded_values.group(1))
                    cob_hex_info = str(decoded_values.group(2))
                    data_hex_info = str(decoded_values.group(5))

                    # Debug
                    if arguments_list.verbose:
                        print(time_info + " " + cob_hex_info + " " + data_hex_info)

                    manage_can_segment(time_info, cob_hex_info, data_hex_info)

            print("Writing decoded packets...")
            write_decoded_packets()                    

        print("End\n")
    else:
        print("File not found!")
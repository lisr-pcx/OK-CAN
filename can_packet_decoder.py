# Name:     can_packet_decoder.py
# Author:   lisr-pcx
# Update:   2024 June 10
# MIT License (c) 2024 lisr-pcx

"""Decode a CAN packet based on JSON file description

__________
INPUT FILE
This script is compatible with following input data format:

<datetime> ; <cob id hex> ; <sequence number> ; <msg len> ; <msg data hex>

Example:
2024-06-07 00:30:31.999 ; 111  ; 247 ; 36     ; F70000000000F1B3D801780288025806FA03FEC4D1E80090FECCD1E400A8FEE8D20400B8
2024-06-07 00:30:32.015 ; 208  ; 85  ; 11     ; 54CB3CFFFEFFFFFFFFFF00
2024-06-07 00:30:33.025 ; 1FA  ; 123 ; 11     ; 020022041122334402000A1719000D2123
2024-06-07 00:30:32.042 ; 301  ; 227 ; 6      ; 30E20000E2B8

___________________
MESSAGE DESCRIPTION
The payload is usually described in documents as SwID (software interface description).
These documents describe the protocol, the list of exchanged messages, parameters, ...

Example:
(to describe the logic behind and the corresponding JSON packet configuration for msg cob id:1FA )

TAB.1
+----------+---------------+----------+-------------------+----------------------------------------+
| Position | name          | Size     | Range and Units   | Description                            |
|----------|---------------|----------|-------------------|----------------------------------------|
| 0        | CODE          | 1 byte   | enumerative       | 00 : ack                               |
|          |               |          |                   | 01 : sensor status                     |
|          |               |          |                   | 02 : odometry info                     |
|----------|---------------|----------|-------------------|----------------------------------------|
| 1        | LEN           | 2 bytes  | 3..1024           | Total length of message (bytes)        |
|----------|---------------|----------|-------------------|----------------------------------------|
| 3        | TIME_LEN      | 1 byte   | 1..4              | Length of field TIME (following)       |
|----------|---------------|----------|-------------------|----------------------------------------|
| 4        | TIME          | -        | .. ms             | Time from power up in ms               |
|----------|---------------|----------|-------------------|----------------------------------------|
| -        | N_DATA_GROUP  | 1 byte   | 0..7              | N of groups containing specific info.  |
|          |               |          |                   | Each group has a specific subfields.   |
|----------|---------------|----------|-------------------|----------------------------------------|
| -        | DATA_GROUP_x  | -        | -                 | Collection of data as described TAB.2  |
+----------+---------------+----------+-------------------+----------------------------------------+

TAB.2 (Data groups)
+------------+---------------+----------+-------------------+--------------------------------------+
| Position   | name          | Size     | Range and Units   | Description                          |
| (relative) |               |          |                   |                                      |
|------------|---------------|----------|-------------------|--------------------------------------|
| 0          | POSITION      | 2bytes   | -5000 .. +5000 Km | Object position                      |
|------------|---------------|----------|-------------------|--------------------------------------|
| 2          | TILT_X        | 1 byte   | -90° .. +90°      | Rotation on X axis                   |
|------------|---------------|----------|-------------------|--------------------------------------|
| 4          | TILT_Y        | 1 byte   | -90° .. +90°      | Rotation on Y axis                   |
+------------+---------------+----------+-------------------+--------------------------------------+

________________________________
HOW TO MANUALLY DECODE A MESSAGE
Manual decode starts considering only message with the right cob id.
...
2024-06-07 00:30:33.025 ; 1FA  ; 123 ; 11     ; 020022041122334402000A1719000D2123
...

Then the payload is extracted:
020022041122334402000A1719000D2123

And based on tables above each field is converted:

    02              -> message CODE is "odometry info"
    0022            -> message LEN is ....
    04              -> field TIME is expressed on 4 bytes
    11223344        -> value of TIME is 287454020 ms
    02              -> there are 2 data groups
    000A1719        -> Group_1 : POSITION is +10 Km
                               : TILT_X is 23°
                               : TILT_Y is 25°
    000D2123        -> Group_2 : POSITION is +13 Km
                               : TILT_X is 33°
                               : TILT_Y is 35°

_____________________________________________
HOW TO CREATE AN AUTOMATIC JSON DECODING FILE
In oder to get information above but automatically running this script a JSON file
containing the packet description shall be passed as argument.

{
    "cob" : "1FA",
    "endianess" : "BIG",
    "min_length" : 3,
    "max_length" : 1024,
    "decode" : 
        [
            {
                "type" : "FIXED",
                "length" : 1,
                "name" : "CODE"
            },
            {
                "type" : "FIXED",
                "length" : 2,
                "name" : "LEN"
            },
            {
                "type" : "DYNAMIC",
                "length" : 1,
                "name" : "TIME"
            },
            {
                "type" : "BLOCK",
                "length" : 1,
                "name" : "GROUP",
                "subfields" : 
                    [
                        {
                            "type" : "FIXED",
                            "length" : 2,
                            "name" : "POSITION"
                        },
                        {
                            "type" : "FIXED",
                            "length" : 1,
                            "name" : "TILT_X"
                        },
                        {
                            "type" : "FIXED",
                            "length" : 1,
                            "name" : "TILT_Y"
                        }
                    ]
            }
        ]
}

"""

import os.path
import argparse
import re
import json
from types import SimpleNamespace
from collections import deque

re_parsing_can_msg = r'^ *([^;]*) *; *([0-9aAbBcCdDeEfF]{3}) *; *([0-9]{1,}) *; *([0-9]+) *; *([0-9aAbBcCdDeEfF]+) *$'

# Please note:
# for any date format use regex:
#     r'^ *([^;]*) *;'
# for specific date format like YYYY-MM-dd HH:mm:ss.xxx use something like:
#     r'^ *([0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{3}) *;'

# Store decoded packets
packet_list = deque()

class TerminalColors:
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    END = '\033[0m'

class CanMessage:
    
    def __decode_payload(self, structure, value_name_prefix: str):
        # Please note: 
        # this is a recursive function and the variable "structure" is 
        # specific to current level of JSON hierarchy
        for elem in structure:

            if elem["type"] == "FIXED":
                # store decoded value
                start_char = 2 * self.decoding_index
                end_char = start_char + 2 * elem["length"]
                self.value[value_name_prefix + elem["name"]] = str(self.data_hex[start_char:end_char])
                # move index to next field
                self.decoding_index = self.decoding_index + elem["length"]

            elif elem["type"] == "DYNAMIC":
                # get length of data
                start_char = 2 * self.decoding_index
                end_char = start_char + 2 * elem["length"]
                tmp_len = int(self.data_hex[start_char:end_char], 16)
                # move index to get data
                self.decoding_index = self.decoding_index + elem["length"]
                # store decoded value
                start_char = 2 * self.decoding_index
                end_char = start_char + 2 * tmp_len
                self.value[value_name_prefix + elem["name"]] = str(self.data_hex[start_char:end_char])
                # move index to next field
                self.decoding_index = self.decoding_index + tmp_len

            elif elem["type"] == "BLOCK":
                # get the number of blocks
                start_char = 2 * self.decoding_index
                end_char = start_char + 2 * elem["length"]
                tmp_nblocks = int(self.data_hex[start_char:end_char], 16)
                # move index to get blocks
                self.decoding_index = self.decoding_index + elem["length"]
                for nb in range (0, tmp_nblocks):
                    self.__decode_payload(elem["subfields"], elem["name"] + "_" + str(nb + 1) + "_")
            else: 
                print("ERR: Invalid type (" + str(elem["type"]) + ") in JSON decoding. Stop decoding!")
                break;            

    def Decode(self):
        # decode payload, byte after byte, based on JSON structure
        self.__decode_payload(self.decoding_structure, "")

    def Info(self):
        info = f"Packet: {self.datetime} ({self.cob_id_hex}) {self.data_hex}"
        info = info + "\nValues:\n"
        for v in self.value:
            info = info + f"{str(v):>25} - {str(self.value[v]):<}\n"
        info = info + "\n\n"
        return info
    
    def __init__(self, datetime: str, cob_id_hex: str, seq_num: int, len: int, data_hex: str, decoding_structure):
        self.datetime = str(decoded_values.group(1))
        self.cob_id_hex = str(decoded_values.group(2))
        self.seq_num = int(decoded_values.group(3))
        self.len = int(decoded_values.group(4))
        self.data_hex = str(decoded_values.group(5))
        self.decoding_structure = decoding_structure
        self.decoding_index = 0 # byte index
        self.value = dict()

def write_decoded_packets():
    output_file = open(arguments_list.datafilepath + ".dp", "w")
    for elem in packet_list:
        output_file.write(elem.Info() + "\n")
    output_file.close() 

def create_arg_parser():
    # Creates and returns the ArgumentParser object
    parser = argparse.ArgumentParser(
                        prog='python3 can_packet_decoder.py',
                        description='Generic can decoder.',
                        epilog='This script is part of OK-CAN utilities (MIT license) and it comes with absolutely no warranty.')
    parser.add_argument('datafilepath',
                        type=str,
                        help='Path to CAN messages')
    parser.add_argument('jsonfilepath',
                        type=str,
                        help='Path to JSON decoding file')
    parser.add_argument('-v', '--verbose',
                        action='store_true',
                        help='Show detailed logging (default is false).')
    return parser

if __name__ == "__main__":
    arguments = create_arg_parser()
    arguments_list = arguments.parse_args()
    
    # Check file existence
    if os.path.isfile(arguments_list.datafilepath):
        print("Opening DATA file: " + arguments_list.datafilepath)
        if os.path.isfile(arguments_list.jsonfilepath):
            print("Opening JSON file: " + arguments_list.jsonfilepath)
            print("\nGetting configuration...")

            # Get Decoding structure
            with open(arguments_list.jsonfilepath) as json_file:
                try:
                    json_msg_decode = json.load(json_file)
                    # Debug
                    if arguments_list.verbose:
                        print(json_msg_decode)
                except json.decoder.JSONDecodeError as e:
                    print("ERR: invalid JSON : " + str(e))

            print("\nStart decoding messages ...\n")

            print(f"{TerminalColors.CYAN}   COB:{json_msg_decode['cob']}")
            print(f"   min length:{str(json_msg_decode['min_length'])}")
            print(f"   max length:{str(json_msg_decode['max_length'])}{TerminalColors.END}\n")

            # Analyze line by line
            with open(arguments_list.datafilepath, 'r') as file:
                for line in file:
                    # Extract info using regex
                    decoded_values = re.search(re_parsing_can_msg, line)
                    if decoded_values:

                        msg = CanMessage(str(decoded_values.group(1)), 
                                         str(decoded_values.group(2)),
                                         int(decoded_values.group(3)),
                                         int(decoded_values.group(4)),
                                         str(decoded_values.group(5)),
                                         json_msg_decode["decode"])

                        # Check validity
                        if (msg.cob_id_hex != json_msg_decode["cob"]):
                            continue
                        if (json_msg_decode["min_length"] > 0 ) and (msg.len < json_msg_decode["min_length"]):
                            continue
                        if (json_msg_decode["max_length"] > 0 ) and (msg.len > json_msg_decode["max_length"]):
                            continue

                        msg.Decode()
                        print(f"{TerminalColors.GREEN}{msg.Info()}{TerminalColors.END}")
                        packet_list.append(msg)

            print("Writing decoded packets into .dp file")
            write_decoded_packets()
            print("End\n")
        else:
            print("ERR: JSON File not found!")    
    else:
        print("ERR: DATA File not found!")
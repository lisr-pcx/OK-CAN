# OK-CAN

**O**verrated **K**it for CAN bus analysis.  
Just a collection of scripts mainly for decoding and related stuff ...

## How to run

Please download or clone locally the repository.

For decoding a CAN trace just to run the *decode* script via Linux shell or Windows prompt, passing the filepath and (optionally) the JSON file which describes the structure of the packet.

On Linux:  
```shell
./decode.sh TRACE_FILE JSON_PKT_DESCRIPTION
```

At the end of the decoding process two files will be created:
 - **TRACE_FILE.dt**: the list of decode messages obtained from trace
 - **TRACE_FILE.dt.dp**: the list of decode packets, based on JSON description

## Demo

A sample CAN trace and JSON description is also provided as example.  
Run the command below:

```shell
./decode.sh sample_trace.csv odometry_packet.json
```

## Documentation

**TODO** explain workflow

Detailed comments are provide on the source code. Please read them carefully before apply any change.

For command line usage and options refer to *help page*:

```shell
python3 <SCRIPT NAME> --help
```

### can_trace_decoder.py

**TODO** show usage

As output of the process a new file containing decoded segments will be created with extension .dt (it means **d**ecoded **t**race) on the same directory.

### can_packet_decoder.py

**TODO** show usage

As output of the process a new file containing decoded packets will be created with extension .dp (it means **d**ecoded **p**ackets) on the same directory.

## Licensing

The **OK-CAN** software is licensed under the [MIT License](https://choosealicense.com/licenses/mit/).  
Please refer to LICENSE file for further details.

## TODO

- [ ] Fill documentation chapter  
- [ ] Add conversion from generic sample trace format to your specific
- [ ] Move python scripts into dedicated folder
- [x] Add JSON structure for decoding
- [ ] Add JSON field-data conversion (make it optional)
- [ ] Add conversion from ODBC to your generic JSON (maybe next year..)
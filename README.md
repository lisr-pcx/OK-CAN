# OK-CAN

**O**verrated **K**it for CAN bus management.  
Just a collection of scripts for packets decoding, analysis ...

## Documentation

For command line usage and option please refer to *man page* of the script:

On Linux:  
```shell
python3 <SCRIPT NAME> --help
```

### SCRIPT: can_packet_decoder.py

To get a quick overview just run the sample files:

On Linux:  
```shell
python3 can_packet_decoder.py input.txt odometry_packet.json
```

## Licensing

The **OK-CAN** software is licensed under the [MIT License](https://choosealicense.com/licenses/mit/). Please refer to LICENSE file for details.

## TODO

-[ ] Import can trace decoder
-[ ] Add check and clean up the mess
-[ ] Fill documentation chapter
-[ ] Add bat for automatic 3-steps workflow (adapt trace log, decode trace, decode packet)
:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:: Name:     decode.bat
:: Author:   lisr-pcx
:: Update:   2024 June 11
:: MIT License (c) 2024 lisr-pcx
:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

@ECHO OFF
ECHO --------------------------------------------------------------------------------
ECHO [O]verrated [K]it-CAN
ECHO Decode an input CAN trace into corresponding packets.
ECHO Please make sure to have Python3 installed on your system.
ECHO:
ECHO Syntax: decode.sh ^<TRACE_FILE^> ^<JSON_PKT_DESCRIPTION^>
ECHO:
ECHO At the end of the decoding process two files will be available:
ECHO   ^<TRACE_FILE^>.dt     : list of decode traces
ECHO   ^<TRACE_FILE^>.dt.dp  : list of decode packet, based on JSON description
ECHO:
ECHO Note1: ^<JSON_PKT_DESCRIPTION^> is optional
ECHO Note2: debug logs are available, see dp.log, dt.log files
ECHO --------------------------------------------------------------------------------
ECHO:

IF [%1]==[] goto noexecution
ECHO Start decoding traces
python code\can_trace_decoder.py %1 > dp.log 2>&1
IF [%2]==[] goto noexecution
ECHO Start decoding packets
python code\can_packet_decoder.py %1.dt %2 > dt.log 2>&1
ECHO Done
:noexecution
# cf_networktest

This tool lets a user run several network commands from the application.
It can be used to test network connectivity.

cf push cf_networktest


If you get an exception in any of these calls, like a timeout exception, you are dropped into the python debugger.
cf log <appname> -recent 
will give you the pin number to enter this debugger.

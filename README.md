# Nginx Alias Generator

This script runs a small webserver that automatically generates an alias file. 

The file is obtained by performing a request on the specified url, and is written to
a configuration file. Then, a reload command is performed. The configuration is 
obtained by the environment variable. An example run script is provided in 
```run-server.sh```.



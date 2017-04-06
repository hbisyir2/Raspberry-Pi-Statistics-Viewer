For our setup, we have the rabbitmq server set up on one raspberry pi, two hosts, and a monitor pi on the other end.

In order for this setup to be successful, we had to have a couple of things installed. First of all, we installed rabbitmq-server
on all the raspberry pis, as well as installing pika in order to connect to rabbitmq. The monitor pi also installed MongoDB to store the data from each message. In order to setup command line arguments, our monitor raspberry pi imported argparse, as opposed to our host pis, which simply parse the sys args.

When starting the server, the command run on the server pi is simply "sudo rabbitmq-server start" and the server is then up and running.
From here, the server administration tool can be opened in order to monitor the proper operation of rabbitmq.
This will be on port 15672 of the server pi.

For clients to connect to the server pi, they must use pika.BlockingConnection(), with the proper host connection parameters,
either specified by the command line arguments or defaulting to virtual host "/" with username:password being "guest:guest".

Since the guest account is only enabled for the local device, we had to create a config file for rabbitmq to connect to it.

Once clients are connected to the server, they can either publish data they want sent out to an exchange, or they can read in data
by subscribing to the same exchange as the one declared by the routing key. 

When publishing to the exchange, the host will publish it to the exchange with a given routing key and the monitor pi will create a queue
with the same routing key. The server pi will route messages into the open queue and will deliver them to the monitor pi over port 5672.
#! /usr/bin/env python3

import socket

soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
soc.connect(("127.0.0.1", 12345))

import random
data = zip([random.randint(1,1000) for i in range(1000)],
 [random.randint(1, 1000) for i in range(1000)])

for x, y in data:
    # send x and y separated by tab
    data = "{}\t{}".format(x,y)
    soc.sendall(data.encode("utf8"))

    # wait for response from server, so we know
    # that server has enough time to process the
    # data. Without this it can make problems

    if soc.recv(4096).decode("utf8") == "-":
        pass

# end connection by sending this string
soc.send(b'--ENDOFDATA--')

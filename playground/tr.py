import socket

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.bind(("localhost", 5084))
while 1:
    datagram = s.recv(1024)
    if not datagram:
    	break
    print repr(datagram)

s.close()

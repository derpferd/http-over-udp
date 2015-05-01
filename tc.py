import socket

target = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
target.connect(("localhost", 9090))
print 'sending:', target.send("HEY")
s_id = target.recv(1000)
print 'recving:', s_id
print 'sending:', target.send(s_id+" SET_DEST d.umn.edu 80")
# print 'sending:', target.send(s_id+" SET_DEST google.com 80")
print 'recving:', target.recv(1000)
print 'sending:', target.send(s_id+" SEND GET http://d.umn.edu/~beau0307/\r\n\r\n")
# print 'sending:', target.send(s_id+" SEND GET /\r\n\r\n")
print 'recving:', target.recv(10000000)

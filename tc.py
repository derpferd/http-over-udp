import socket

class ProxyHTTP(object):
	def __init__(self, dest, proxy):
		self.proxy = proxy
		self.host = dest[0]
		self.port = dest[1]

	def get(self, page):
		target = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		target.connect(self.proxy)
		print 'Sending Hey',
		target.send("HEY")
		s_id = target.recv(1000)
		print "Received id:", s_id

		print 'Sending destination',
		target.send(s_id+" SET_DEST " + str(self.host) + " " + str(self.port))
		print 'Received:', target.recv(1000)

		print 'Sending request'
		target.send(s_id+" SEND GET "+page+"\r\n\r\n")
		pack = target.recv(10000)
		cur_p = pack.split()[0]
		total_p = pack.split()[1]
		pack = pack[pack.index(" ", 2)+1:]
		page = [None for i in range(int(total_p))]
		page[int(cur_p)-1] = pack
		for i in range(int(total_p)-1):
			pack = target.recv(10000)
			cur_p = pack.split()[0]
			total_p = pack.split()[1]
			pack = pack[pack.index(" ", 2)+1:]
			page[int(cur_p)-1] = pack
		
		print "GOT:",page
		# TODO: implement a resend
		print 'Sending resend'
		target.send(s_id+" RESEND 2 3")
		print 'recving:', target.recv(10000000)
		print 'recving:', target.recv(10000000)
		print 'recving:', target.recv(10000000)



# target = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# target.connect(("131.212.205.152", 9090))
# print 'sending:', target.send("HEY")
# s_id = target.recv(1000)
# print 'recving:', s_id
# print 'sending:', target.send(s_id+" SET_DEST d.umn.edu 80")
# # print 'sending:', target.send(s_id+" SET_DEST google.com 80")
# print 'recving:', target.recv(1000)
# print 'sending:', target.send(s_id+" SEND GET http://d.umn.edu/~beau0307/\r\n\r\n")
# # print 'sending:', target.send(s_id+" SEND GET /\r\n\r\n")
# print 'recving:', target.recv(10000000)

ProxyHTTP(("d.umn.edu", 80), ("127.0.0.1", 9090)).get("http://d.umn.edu/~beau0307/book.txt")

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

        target2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        target2.connect(self.proxy)
        
        print 'Sending Hey',
        target2.send("HEY")
        s_id2 = target2.recv(1000)
        print "Received id:", s_id2
        
        from http import HTTPRequest
        
        r = HTTPRequest("GET", "http://www.google.com/", "HTTP/1.0", body="Give me your website!!!", headers={"HOST": "www.google.com"})
        msg = r.packToPack()
        
        target.send(s_id+" 1 1 SEND " + msg)
        print "GOT:", target.recv(100000)
        print "GOT:", target.recv(100000)
        target.send(s_id+" GOOD")
        
        r = HTTPRequest("GET", "http://inishia.com/", "HTTP/1.0", body="Give me your website!!!", headers={"HOST": "www.inishia.com"})
        msg = r.packToPack()
        
        target2.send(s_id2+" 1 1 SEND " + msg)
        print "GOT:", target2.recv(100000)
        print "GOT:", target2.recv(100000)
        target2.send(s_id2+" GOOD")

        # target.send(s_id+ " 1 1 Blabla bla")
        # target.send(s_id+ " 1 3 This ")
        # target.send(s_id+ " 2 3 is ")
        # target.send(s_id+ " 3 3 a Test.")


# 		print 'Sending request'
# 		target.send(s_id+" SEND GET "+page+"\r\n\r\n")
# 		pack = target.recv(10000)
# 		cur_p = pack.split()[0]
# 		total_p = pack.split()[1]
# 		pack = pack[pack.index(" ", 2)+1:]
# 		page = [None for i in range(int(total_p))]
# 		page[int(cur_p)-1] = pack
# 		for i in range(int(total_p)-1):
# 			pack = target.recv(10000)
# 			cur_p = pack.split()[0]
# 			total_p = pack.split()[1]
# 			pack = pack[pack.index(" ", 2)+1:]
# 			page[int(cur_p)-1] = pack
        
# 		print "GOT:",page
# 		# TODO: implement a resend
# 		print 'Sending resend'
# 		target.send(s_id+" RESEND 2 3")
# 		print 'recving:', target.recv(10000000)
# 		print 'recving:', target.recv(10000000)
# 		print 'recving:', target.recv(10000000)

# 		target.send(s_id+" BYE")

# 		return ''.join(page)


ProxyHTTP(("d.umn.edu", 80), ("127.0.0.1", 9090)).get("http://d.umn.edu/~beau0307/book.txt")

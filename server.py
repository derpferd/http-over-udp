#!/usr/bin/python
import socket
import select
import time
import sys
import threading
import httplib
import getopt
from http import HTTPRequest
from http import HTTPResponse


# Buffer size for receiving and sending data
BUFFER_SIZE = 4096
# Set this lower for production, like 0.0001
DELAY = 0.5

def show_help():
    print """\
Syntax: python %s <options>
 -p <port>         listen port  (default 8080)
""" % sys.argv[0]

# This function is used for spliting a string into an array of
# string with the specified length. The last string may not be
# of the same length
def chunkstring(string, length):
    return [string[0+i: length+1] for i in range(0, len(string), length)]


# This class is a thread used of handling a single "connection"
class SessionThread(threading.Thread):
    def __init__(self, channel, addr, sock):
        super(SessionThread, self).__init__()
        self.addr = addr
        self.sock = sock
        self.channel = channel
        
        # FOR TCP Unter v
        self.peer = False
        self.keepalive = False
        self.target = None

        # Just for debugging
        self.counter = 0
        self._host = None
        self._port = 0

    def recv(self):
        print "Receiving data"
        pack = self.recv_frame()
        cur_p = pack.split()[1]
        total_p = pack.split()[2]

        pack = ' '.join(pack.split(' ')[3:])
        page = [None for i in range(int(total_p))]
        page[int(cur_p)-1] = pack

        for i in range(int(total_p)-1):
            pack = self.recv_frame()
            cur_p = pack.split()[1]
            total_p = pack.split()[2]
            pack = pack[pack.index(" ", 4)+1:]
            page[int(cur_p)-1] = pack

        msg = ''.join(page)

        self.send_frame("0 GOOD")

        print "GOT RECV:", msg

        return msg
        
    #Splits data into packets, communicates with client if it is necessary to resend data, keeps a log of all the 
    #packets that are being sent so we can resend
    def send(self, data):
        print "Sending data"
        # split data into packets
        self.packets = []
        for i in range(0, len(data), BUFFER_SIZE):
            self.packets.append(data[i: i+BUFFER_SIZE])

        for i, packet_msg in enumerate(self.packets):
            self.send_pack(packet_msg, i+1, len(self.packets))

        # listen for a conformation or need for retransmission
        need_resend = True
        while need_resend:
            print "In resend loop"
            msg = self.recv_frame()
            print "Got Msg"
            if not len(msg.split()) > 1:
                continue
            if msg.split()[1] == "RESEND":
                print "Needed RESEND:", msg
                # TODO: implement
                pass
            elif msg.split()[1] == "GOOD":
                need_resend = False

        print "Data sent"

    #creates message, then sends message with length off too the send_frame
    def send_pack(self, data, num, total):
        msg = "0 " + str(num) + " " + str(total) + " " + data
        length = len(msg)
        sent = self.send_frame(msg)

        if length != sent:
            print "Length not equal", length, "!=", sent, "packet not sent, we are not retrying"

    #recv_frame waits for an incoming packet then returns a new channel
    def recv_frame(self, blocking=True):
        while blocking:
            if len(self.channel) > 0:
                return self.channel.pop()
            time.sleep(DELAY)
        if len(self.channel) > 0:
            return self.channel.pop()

    #sends data off to the client
    def send_frame(self, data):
        # sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        print "Sending frame to:", self.addr
        return self.sock.sendto(str(data), self.addr)

    #Waits for packet and processes requests
    def run(self):
        while True:
            msg = self.recv()
            if msg.split()[0] == "SEND":
                print "Good send command"
                data = msg[msg.index(" ")+1:]
                req = HTTPRequest.buildWithPack(data)
                print req
                print "Handling request"

                res = None
                
                if req.getMethod() == HTTPRequest.METHOD_GET:
                    host, port = req.getHost()
                    res = self.doGET(host, port, req)
                elif req.getMethod() == HTTPRequest.METHOD_POST:
                    host, port = req.getHost()
                    res = self.doPOST(host, port, req)
                elif req.getMethod() == HTTPRequest.METHOD_CONNECT:
                    print "Setting SSL to True"
                    self.peer = True
                    self.send("GOOD")
                    # res = self.doCONNECT(host, port, req)
                # TODO: add POST and CONNECT
                
                if res:
                    print "Got res", res
                    self.send(res.packToPack())
                
                print "Res sent"
            elif msg.split()[0] == "BYE":
                print "Closing connection"
                return
    
    #This is a marker. All functions before are for the TCP connect.
    
    def createConnection(self, host, port):

        if self.target and self._host == host:
            return self.target

        try:
            # If a SSL tunnel was established, create a HTTPS connection to the server
            if self.peer:
                conn = httplib.HTTPSConnection(host, port)
            else:
                # HTTP Connection
                conn = httplib.HTTPConnection(host, port)
        except HTTPException as e:
            print "It Broke line 131 server python"
        # If we need a persistent connection, add the socket to the dictionary
        if self.keepalive:
            self.target = conn

        self._host = host
        self._port = port
            
        return conn

    def _request(self, conn, method, path, params, headers):
        conn.putrequest(method, path, skip_host = True, skip_accept_encoding = True)
        for header,v in headers.iteritems():
            # auto-fix content-length
            if header.lower() == 'content-length':
                conn.putheader(header, str(len(params)))
            else:
                for i in v:
                    conn.putheader(header, i)
        conn.endheaders()

        if len(params) > 0:
            conn.send(params)

    def doRequest(self, conn, method, path, params, headers):
        try:
            self._request(conn, method, path, params, headers)
            return True
        except IOError as e:
            return False

    def doGET(self, host, port, req):
        conn = self.createConnection(host, port)
        if not self.doRequest(conn, "GET", req.getPath(), '', req.headers): return ''
        res = self._getresponse(conn)
        return res

    def doPOST(self, host, port, req):
        conn = self.createConnection(host, port)
        params = urllib.urlencode(req.getParams(HTTPRequest.METHOD_POST))
        if not self.doRequest(conn, "POST", req.getPath(), params, req.headers): return ''
        res = self._getresponse(conn)
        return res

    def _getresponse(self, conn):
        try:
            res = conn.getresponse()
        except httplib.HTTPException as e:
            # FIXME: check the return value into the do* methods
            return None

        body = res.read()
        if res.version == 10:
            proto = "HTTP/1.0"
        else:
            proto = "HTTP/1.1"

        code = res.status
        msg = res.reason

        res = HTTPResponse(proto, code, msg, res.msg.headers, body)

        return res

#Handles requests, makes new threads for new connections
class TheServer:
    def __init__(self, host, port):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((host, port))
        print "Server listening on", (host, port)
        self.server.setblocking(1)
        self.newid = 1
        self.channels = {}
        self.threads = []
 
    def main_loop(self):
        while 1:
            try:
                data, addr = self.server.recvfrom(BUFFER_SIZE+20)
                host, port = addr
                print "Received from", addr, "over UDP:", data
            except socket.error:
                pass
            else:
                if data.strip() == "HEY":
                    self.channels[self.newid] = list()
                    self.server.sendto(str(self.newid), (host, port))
                    new_thread = SessionThread(self.channels[self.newid], (host, port), self.server)
                    new_thread.setDaemon(True)
                    new_thread.start()
                    self.threads.append(new_thread)
                    self.newid += 1
                else:
                    s_id = -1
                    channel = None
                    try:
                        s_id = int(data.split()[0])
                        channel = self.channels[s_id]
                    except:
                        print "No Session"
                        continue
                    #TODO: implement bye
                    
                    self.channels[s_id].insert(0, data)

#MAIN METHOD
if __name__ == '__main__':
    try:
        opts, args = getopt.getopt(sys.argv[1:], "a:d:hp:r:vx:")
    except getopt.GetoptError, e:
        print str(e)
        show_help()
        exit(1)
    
    opts = dict([(k.lstrip('-'), v) for (k,v) in opts])
    
    port = 9090
    if 'p' in opts:
        port = int(opts['p'])
    
    server = TheServer('', port)
    try:
        server.main_loop()
    except KeyboardInterrupt:
        print "Ctrl C - Stopping server"
        sys.exit(1)

"""
  This file has been modified by:
      Jonathan Beaulieu
      Alekander Straumann
      
  Changes Made:
    Almost all the code has been changed however the general structure has been
    kept.

  Copyright notice
  ================
  
  Copyright (C) 2011
      Roberto Paleari     <roberto.paleari@gmail.com>
      Alessandro Reina    <alessandro.reina@gmail.com>
  
  This program is free software: you can redistribute it and/or modify it under
  the terms of the GNU General Public License as published by the Free Software
  Foundation, either version 3 of the License, or (at your option) any later
  version.
  
  HyperDbg is distributed in the hope that it will be useful, but WITHOUT ANY
  WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
  A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
  
  You should have received a copy of the GNU General Public License along with
  this program. If not, see <http://www.gnu.org/licenses/>.
  
"""

import SocketServer
import BaseHTTPServer
import socket
import threading
import httplib
import time
import os
import urllib
import ssl
import copy

from history import *
from http import *
from https import *
from logger import Logger

DEFAULT_CERT_FILE = "./cert/ncerts/proxpy.pem"

proxystate = None

#This class handles all requests from the client to the server. 
class ProxyHandler(SocketServer.StreamRequestHandler):
    CURRENT_ID = 1

    def __init__(self, request, client_address, server):
        self.peer = False
        self.keepalive = False

        # Just for debugging
        self.counter = 0
        self._host = None
        self._port = 0
        self._id = self.CURRENT_ID
        print "Making current ID", self.CURRENT_ID
        self.CURRENT_ID += 1

        SocketServer.StreamRequestHandler.__init__(self, request, client_address, server)

    #Writes to the socket
    def sendResponse(self, res):
        self.wfile.write(res)
    
    #stop listening if keepalive == true else keep listening
    def finish(self):
        if not self.keepalive:
            return SocketServer.StreamRequestHandler.finish(self)

        # Otherwise keep-alive is True, then go on and listen on the socket
        return self.handle()
    
    def handle(self):
        global proxystate

        print self._id, "Handling connection"

        if self.keepalive:
            if self.peer:
                HTTPSUtil.wait_read(self.request)
            else:
                HTTPUtil.wait_read(self.request)

            # Just debugging
            if self.counter > 0:
                proxystate.log.debug(str(self.client_address) + ' socket reused: ' + str(self.counter))
            self.counter += 1

        try:
            req = HTTPRequest.build(self.rfile)
        except Exception as e:
            proxystate.log.debug(e.__str__() + ": Error on reading request message")
            return
            
        if req is None:
            return

        # if you need a persistent connection set the flag in order to save the status
        if req.isKeepAlive():
            self.keepalive = True
        else:
            self.keepalive = False

        # Target server host and port
        host, port = ProxyState.getTargetHost(req)

        res = self.doRequest(req)
        print self._id, "DID REQ:", res
        if res:
            print self._id, "sending response: ", str(res)[str(res).index("\n")+1:]
            self.sendResponse(res)

        # if req.getMethod() == HTTPRequest.METHOD_GET:
        #     res = self.doGET(host, port, req)
        #     self.sendResponse(res)
        # elif req.getMethod() == HTTPRequest.METHOD_POST:
        #     res = self.doPOST(host, port, req)
        #     self.sendResponse(res)
        # elif req.getMethod() == HTTPRequest.METHOD_CONNECT:
        #     res = self.doCONNECT(host, port, req)

    def _request(self, conn, method, path, params, headers):
        global proxystate
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

    # returns a currently unused UDPConn if none available it makes one.
    def getOpenConnection(self):
        global proxystate

        for conn in proxystate.proxyConnections:
            if not conn.in_use:
                return conn

        host, port = proxystate.redirect
        conn = UDPConn(host, port)
        proxystate.proxyConnections.append(conn)
        return conn

    def doRequest(self, req):
        conn = self.getOpenConnection()
        conn.in_use = True
        conn.send(req.packToPack())
        if conn.s_id:
            print "ProxyHandler", self._id, "using UDPConn", conn.s_id

        msg = conn.recv()
        conn.in_use = False
        print self._id, "DID requ:", msg
        if msg != "GOOD":
            res = HTTPResponse.buildWithPack(msg)
            if not res:
                return None
            data = res.serialize()
            return data
        else:
            print "GOT GOOD", req, req.getMethod()
            if req.getMethod() == HTTPRequest.METHOD_CONNECT:
                print "Not implemented"
                # self.doCONNECT()
            return None

    def doCONNECT(self):
        print "Doing connect"
        global proxystate

        socket_req = self.request
        certfilename = DEFAULT_CERT_FILE
        socket_ssl = ssl.wrap_socket(socket_req, server_side = True, certfile = certfilename, 
                                     ssl_version = ssl.PROTOCOL_SSLv23, do_handshake_on_connect = False)
        print "SSL Wrapped"

        HTTPSRequest.sendAck(socket_req)
        
        host, port = socket_req.getpeername()
        proxystate.log.info("Send ack to the peer %s on port %d for establishing SSL tunnel" % (host, port))

        print "Starting Handshake..."
        while True:
            try:
                socket_ssl.do_handshake()
                break
            except (ssl.SSLError, IOError):
                # proxystate.log.error(e.__str__())
                return

        print "SSL is all good"

        # Switch to new socket
        self.peer    = True
        self.request = socket_ssl

        self.setup()
        self.handle()

    def _getresponse(self, conn):
        try:
            res = conn.getresponse()
        except httplib.HTTPException as e:
            proxystate.log.debug(e.__str__())
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

class ThreadedHTTPProxyServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    allow_reuse_address = True

class ProxyServer():    
    def __init__(self, init_state):
        global proxystate
        proxystate = init_state
        self.proxyServer_port = proxystate.listenport
        self.proxyServer_host = proxystate.listenaddr

    def startProxyServer(self):
        global proxystate
        
        self.proxyServer = ThreadedHTTPProxyServer((self.proxyServer_host, self.proxyServer_port), ProxyHandler)

        # Start a thread with the server (that thread will then spawn a worker
        # thread for each request)
        server_thread = threading.Thread(target = self.proxyServer.serve_forever)
    
        # Exit the server thread when the main thread terminates
        server_thread.setDaemon(True)
        proxystate.log.info("Server %s listening on port %d" % (self.proxyServer_host, self.proxyServer_port))
        server_thread.start()

        while True:
            time.sleep(0.1)

    def stopProxyServer(self):
        self.proxyServer.shutdown()

class ProxyState:
    def __init__(self, port = 8080, addr = "0.0.0.0"):
        # Configuration options, set to default values
        # self.plugin     = ProxyPlugin()
        self.listenport = port
        self.listenaddr = addr
        self.dumpfile   = None

        # Internal state
        self.log        = Logger()
        self.history    = HttpHistory()
        self.redirect   = ("127.0.0.1", 9090)
        self.proxyConnections = []

    @staticmethod
    def getTargetHost(req):
        global proxystate
        # Determine the target host (check if redirection is in place)
        if proxystate.redirect is None:
            target = req.getHost()
        else:
            target = proxystate.redirect

        return target

class UDPConn(object):
    BUFFER_SIZE = 4096

    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.connect((host, port))
        self.s_id = None
        self.in_use = False

    def send(self, data):
        if not self.s_id:  # if not connected, connect and get id
            print self.s_id,  "Sending HEY"
            self.sock.send("HEY")
            self.s_id = self.sock.recv(self.BUFFER_SIZE+20).strip()
            print self.s_id,  "GOT id:", self.s_id

        print "Sending data"
        # split data into packets
        data = "SEND " + data
        self.packets = []
        for i in range(0, len(data), self.BUFFER_SIZE):
            self.packets.append(data[i: i+self.BUFFER_SIZE])

        for i, packet_msg in enumerate(self.packets):
            self.send_pack(packet_msg, len(self.packets), i+1)

        # listen for a conformation or need for retransmission
        need_resend = True
        while need_resend:
            print  self.s_id,  " In resend loop"
            msg = self.sock.recv(self.BUFFER_SIZE+20)
            print  self.s_id,  " Got Msg"
            if not len(msg.split()) > 1:
                continue
            if msg.split()[1] == "RESEND":
                print  self.s_id,  " Needed RESEND:", msg
                # TODO: implement
                pass
            elif msg.split()[1] == "GOOD":
                need_resend = False

        print "Data sent"

    def recv(self):
        if not self.s_id: # if not connected, there is no way to receive data
            print  self.s_id, " No session"
            return

        print  self.s_id, " Receiving data"
        pack = self.sock.recv(self.BUFFER_SIZE+20)
        print "RECVED FRAME:", pack
        cur_p = pack.split()[1]
        total_p = pack.split()[2]

        pack = pack[pack.index(" ", 4)+1:]
        page = [None for i in range(int(total_p))]
        page[int(cur_p)-1] = pack

        for i in range(int(total_p)-1):
            print "Waiting for pack:", i+2, "of", total_p
            pack = self.sock.recv(self.BUFFER_SIZE+20)
            print "RECVED FRAME"
            cur_p = pack.split()[1]
            total_p = pack.split()[2]
            pack = pack[pack.index(" ", 4)+1:]
            page[int(cur_p)-1] = pack

        msg = ''.join(page)

        self.sock.send(self.s_id + " GOOD")

        print  self.s_id,  " GOT RECV:", msg

        return msg

    def send_pack(self, data, num, total):
        msg = self.s_id + " " + str(num) + " " + str(total) + " " + data
        length = len(msg)
        sent = self.sock.send(msg)

        if length != sent:
            print "Length not equal", length, "!=", sent, "packet not sent, we are not retrying"

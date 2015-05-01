#!/usr/bin/python
import socket
import select
import time
import sys

# TODO: There are quite a few problems right now
# Most of these will require client side coding as of right now there is none.
# THIS IS DONE 1. The client will only receive a max of the buffer_size(4096 bytes) of the requested website
# 2. Any packets that are lost can not be recovered and as of now neither side know about packet loss.
# 3. Can not reset destination.
# 4. Need to track state of forward. This way we can reconnect if the forward times out or send an error message if the destination was not set.
# 5. No session clean up. (We probably need a timeout for garbage collection.)


buffer_size = 4096
# Set this lower for production, like 0.0001
delay = 0.5

def chunkstring(string, length):
    return [string[0+i: length+1] for i in range(0, len(string), length)]

class Session(object):
    def __init__(self, s_id, host, port, server_socket):
        self.id = s_id
        self.buffer = ""
        self.host = host
        self.port = port
        self.dest = ('', 80)
        self.forward = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server = server_socket

    def set_dest(self, host, port):
        self.dest = (host, port)
        print "Dest set as", self.dest, "for", self.id

    def start(self):
        try:
            self.forward.connect(self.dest)
            return self.forward
        except Exception, e:
            self.forward = None
            print e
            return False

    def sendForward(self, data):
        self.buffer = ""
        self.forward.send(data)

    def on_recv(self, data):
        #append to the buffer
        self.buffer += data

    def on_close(self):
        if self.buffer:
            self.send(self.buffer)

    def send(self, data):
        self.packets = []
        for i in range(0, len(data), buffer_size):
            self.packets.append(data[i: i+buffer_size])

        for i, packet_msg in enumerate(self.packets):
            # print "Sending pack", i, "of", len(self.packets), "with", packet_msg
            self.send_pack(packet_msg, len(self.packets), i+1)

    def send_pack(self, data, total, packet_num):
        msg = str(packet_num) + " " + str(total) + " " + data
        length = len(msg)
        sent = self.server.sendto(msg, (self.host, self.port))

        if length != sent:
            print "Length not equal", length, "!=", sent, "packet not sent, we are not retrying"
 
    def resend(self, packets_rsnd):
        # TODO: make sure all packets_rsnd elements are ints
        for i in packets_rsnd:
            self.send_pack(self.packets[int(i)], len(self.packets), int(i))

class TheServer:
    input_list = []
    channel = {}
 
    def __init__(self, host, port):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((host, port))
        self.server.setblocking(0)
        self.sessions = {}
        self.newid = 0
        self.channel = {}
        # self.server.listen(200)
 
    def main_loop(self):
        # self.input_list.append(self.server)
        while 1:
            # time.sleep(delay)
            try:
                data, addr = self.server.recvfrom(buffer_size)
                host, port = addr
                print "Received from", addr, "over UDP:", data
            except socket.error:
                pass
            else:
                if data.strip() == "HEY":
                    self.sessions[self.newid] = Session(self.newid, host, port, self.server)
                    self.server.sendto(str(self.newid), (host, port))
                    self.newid += 1
                else:
                    s_id = -1
                    session = None
                    try:
                        s_id = int(data.split()[0])
                        session = self.sessions[s_id]
                    except:
                        print "No Session"
                        continue

                    if data.split()[1].strip() == "SET_DEST":
                        d_host = data.split()[2].strip()

                        #TODO: test int
                        d_port = int(data.split()[3].strip())

                        #TODO: test if session exists
                        session.set_dest(d_host, d_port)
                        forward = session.start()
                        if forward:
                            print "Adding forward to", d_host, d_port
                            self.input_list.append(forward)
                            self.channel[forward] = session
                            self.server.sendto("GOOD", (host, port))
                        else:
                            print "Can't establish connection with remote server."
                            self.server.sendto("BAD", (host, port))
                    elif data.split()[1] == "SEND":
                        msg = data[data.index(" ", 2)+1:]
                        if session.forward:
                            session.sendForward(msg)
                    elif data.split()[1] == "RESEND":
                        msg = data.split()[2:]
                        session.resend(msg)
                    elif data.split()[1] == "BYE":
                        self.input_list.remove(session.forward)
                        session.forward.close()
                        del session.forward
                        del self.sessions[s_id]


            ss = select.select
            print "Checking", self.input_list, "for", delay, "s"
            if self.input_list:
                inputready, outputready, exceptready = ss(self.input_list, [], [], delay)
                for self.s in inputready:
                    print "Input ready"

                    self.data = self.s.recv(buffer_size)
                    if len(self.data) != 0:
                        self.on_recv()
                    else:
                        print "Connection closed"
                        self.channel[self.s].on_close()
                        self.s.close()
                        self.input_list.remove(self.s)
            else:
                time.sleep(delay)

    def on_recv(self):
        data = self.data
        # here we can parse and/or modify the data before send forward
        print "Received TCP:", data
        self.channel[self.s].on_recv(data)
 
if __name__ == '__main__':
        server = TheServer('', 9090)
        try:
            server.main_loop()
        except KeyboardInterrupt:
            print "Ctrl C - Stopping server"
            sys.exit(1)

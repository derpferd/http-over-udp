import socket

from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor

class Session(object):
    def __init__(self, s_id, host, port):
        self.id = s_id
        self.host = host
        self.port = port
        self.dest = ('', 80)

    def set_dest(self, host, port):
        self.dest = (host, port)
        print "Dest set as", self.dest, "for", self.id

    def send(self, data):
        pass


class Echo(DatagramProtocol):

    def __init__(self):
        # super(Echo, self).__init__()
        self.sessions = {}
        self.newid = 0

    def datagramReceived(self, data, (host, port)):
        print "received %r from %s:%d" % (data, host, port)


        if data.strip() == "HEY":
            self.sessions[self.newid] = Session(self.newid, host, port)
            self.transport.write(str(self.newid), (host, port))
            self.newid += 1
        else:
            s_id = -1
            try:
                s_id = int(data.split()[0])
            except:
                print "No Session"
                return

            if data.split()[1].strip() == "SET_DEST":
                d_host = data.split()[2].strip()

                #TODO: test int
                d_port = int(data.split()[3].strip())

                #TODO: test if session exists
                self.sessions[s_id].set_dest(d_host, d_port)
            elif data.split()[1].strip() == "SEND":
                print "waiting"
                import time
                time.sleep(1000)


        #self.transport.write(data, (host, port))



portSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# Make the port non-blocking and start it listening.
portSocket.setblocking(False)
portSocket.bind(('127.0.0.1', 9999))

# Now pass the port file descriptor to the reactor
port = reactor.adoptDatagramPort(
    portSocket.fileno(), socket.AF_INET, Echo())

# The portSocket should be cleaned up by the process that creates it.
portSocket.close()

reactor.run()
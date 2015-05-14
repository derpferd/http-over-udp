#!/usr/bin/env python 

""" 
A simple interactive tcp client with sample messages
""" 

sample_msgs = ["""GET http://inishia.com/ HTTP/1.1
Host: inishia.com
User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10.10; rv:37.0) Gecko/20100101 Firefox/37.0
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8
Accept-Language: en-US,en;q=0.5
Accept-Encoding: gzip, deflate
Connection: keep-alive
Cache-Control: max-age=0\r\n\r\n""",
"""GET http://www.google.com/ HTTP/1.1
Host: www.google.com
User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10.10; rv:37.0) Gecko/20100101 Firefox/37.0
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8
Accept-Language: en-US,en;q=0.5
Accept-Encoding: gzip, deflate
Connection: keep-alive
Cache-Control: max-age=0\r\n\r\n""",
"""GET http://yahoo.com/ HTTP/1.1
Host: yahoo.com
User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10.10; rv:37.0) Gecko/20100101 Firefox/37.0
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8
Accept-Language: en-US,en;q=0.5
Accept-Encoding: gzip, deflate
Cookie: B=drjdui1aj3ndo&b=3&s=kh; DSS=ts=1431455649&cnt=0&sdts=1431455649&sdtp=mozilla
Connection: keep-alive\r\n\r\n""",
"""GET http://apple.com/ HTTP/1.1
Host: apple.com
User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10.10; rv:37.0) Gecko/20100101 Firefox/37.0
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8
Accept-Language: en-US,en;q=0.5
Accept-Encoding: gzip, deflate
Cookie: s_fid=3EDBA08714790847-23B8551AA1CD53A3; s_vnum_n2_us=21|1; s_vi=[CS]v1|2AA99F2505191137-4000110720000C22[CE]; xp_ci=3z4V7JDsz7F2z4mdzD5WzkRoKK699
Connection: keep-alive\r\n\r\n""",
"""GET http://d.umn.edu/ HTTP/1.1
Host: d.umn.edu
User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10.10; rv:37.0) Gecko/20100101 Firefox/37.0
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8
Accept-Language: en-US,en;q=0.5
Accept-Encoding: gzip, deflate
Cookie: __utma=178852849.2117189199.1431462518.1431462518.1431462518.1; __utmz=178852849.1431462518.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none)
Connection: keep-alive\r\n\r\n""",
"""GET http://d.umn.edu/~beau0307/book.txt HTTP/1.1
Host: d.umn.edu
User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10.10; rv:37.0) Gecko/20100101 Firefox/37.0
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8
Accept-Language: en-US,en;q=0.5
Accept-Encoding: gzip, deflate
Cookie: __utma=178852849.2117189199.1431462518.1431462518.1431462518.1; __utmz=178852849.1431462518.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none)
Connection: keep-alive\r\n\r\n"""]

import socket 

host = raw_input("Enter Host: ").strip()
if host == '':
    host = "127.0.0.1"
port = raw_input("Enter Port: ")
if port == '':
    port = 8080
else:
    port = int(port)
backlog = 5 
size = 4096
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((host, port))
while 1: 
    i = raw_input("Enter Data (to receive enter 'r'): ")
    if i == 'r':
        try:
            print "Received: ", s.recv(size)
        except KeyboardInterrupt as e:
            print ""
        except Exception as e:
            print "Error: ", e
    elif i == 'e':
        print "Quiting"
        break
    elif i[0] == 'm':
        num = int(i[1:])
        s.send(sample_msgs[num-1])
        print "Sent Msg:", num
    elif i == 's':
        for m in sample_msgs:
            st = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            st.connect((host, port))
            st.send(m)
            print "Sent Msg:", sample_msgs.index(m)
    elif i:
        s.send(i+"\r\n\r\n")
        print "Sent Msg"

s.close()
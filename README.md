# http-over-udp

Useful links
http://wxpython.org/Phoenix/docs/html/html2.WebView.html
http://stackoverflow.com/questions/4412581/seriously-simple-python-http-proxy

Useful links android
http://stackoverflow.com/questions/4543349/load-local-html-in-webview
http://stackoverflow.com/questions/24519855/how-to-send-udp-packets-between-an-android-tablet-and-raspberry-pi

This project is our attempt at creating a UDP proxy for a client that communicates with a TCP/HTTP/HTTPS connection on the other side. We have 2 sides to this projects, a server, and a client side. Each side has a way to handle the downsides of UDP which is the lack of constant connection. Both the client and the server are being implemented with a basic packet tracking so we can organize incoming packets as well as keep track of the number recieved. 

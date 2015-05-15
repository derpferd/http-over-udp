# http-over-udp

Authors:
  Jonathan Beaulieu
  Al Straumann

This project is our attempt at creating a UDP proxy for a client that communicates with a TCP/HTTP/HTTPS connection on the other side. We have 2 sides to this projects, a server, and a client side. Each side has a way to handle the downsides of UDP which is the lack of constant connection. Both the client and the server are being implemented with a basic packet tracking so we can organize incoming packets as well as keep track of the number recieved. 


To start the server:
  run the following on your server '''sudo python server.py -p 53'''
  run the following on your client '''python client.py -r 127.0.0.1:53''' with the "127.0.0.1" as the ip of your server
  
  Now set up an http proxy to 127.0.0.1:8080 for HTTP
  Navigate to your website of choice. Right now you must choose a HTTP website or it won't load the page. 
  
We used a logger, history, and a http file as a template for our design of the project from:
https://github.com/tarlabs/proxpy
The files we used are noted by the creators comments at the top of the files.

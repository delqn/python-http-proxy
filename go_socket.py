#!/usr/bin/env python

import httplib2
import re
import signal
import socket
import ssl
import sys
import threading

HOST = ''                 # Symbolic name meaning all available interfaces
PORT = 65500              # Arbitrary non-privileged port
BUFFER = 2
LINE_TERMINATOR = '\r'

def signal_handler(signal, frame):
        print("Bye!")
        sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

class Respondent(threading.Thread):
	def __init__(self, conn, addr):
		self.conn = conn
		self.addr = addr
		threading.Thread.__init__(self)

        def terminate_connection(self, headers, response):
                '''send a response to the server and terminate'''
		# must return --> HTTP/1.0 200 OK\r\n
		'''
		{'status': '200', 'content-length': '2', 'via': '1.1 varnish', 'content-location': 'http://delqn.com/dot', 'age': '0', 'x-cacheable': 'YES', 'server': 'Apache/2.2.16 (Debian)', 'last-modified': 'Mon, 31 Dec 2012 02:49:17 GMT', 'connection': 'keep-alive', 'x-varnish': '1600488335', 'etag': '"58bac-2-4d21d0f27e540"', 'date': 'Mon, 31 Dec 2012 04:11:10 GMT', 'content-type': 'text/plain'}
		'''
		hdrs = ''
		if 'via' in headers:
			hdrs = "HTTP/%s %s\r\n" % (headers['via'].split(' ')[0], headers['status'])
		if 'content-type' in headers:
			hdrs += "Content-Type: %s\r\n" % headers['content-type']
		if 'content-length' in headers:
			hdrs += "Content-Length: %s\r\n" % headers['content-length']
		hdrs += '\r\n'
                conn.sendall(hdrs)
		print 'sending these headers back:', hdrs
		print "sending this back:", response
                conn.sendall(response)
                #conn.shutdown(socket.SHUT_RDWR)
                #conn.close()

	def run(self):
                h = httplib2.Http()
                counter = 0
                found_line = False
                line = ''
                while not found_line:
                        data = conn.recv(BUFFER)
                        if not data: break
                        found_line = LINE_TERMINATOR in data
                        line += data.split(LINE_TERMINATOR)[0]
                        response = "Thank you!\n"

                # (first) line obtained would look like this:
                # GET http://delqn.com/dot HTTP/1.1
                try:
                        verb, url, protocol = line.split(' ')
			if not re.match(r'^http|https://', url):
				if ':443' in url:
					url = 'https://' + url
				else:
					url = 'http://' + url
			try:
				print "Connecting to %s" % url
	                        headers, response = h.request(url)
                        except httplib2.RelativeURIError, e:
				print "[Error] Cannot retrieve URL >>>%s<<<" % url
				headers = {'via': '1.0', 'status':'200', 'content-type':'text/html'}
				response = '501 Internal Server Error (Proxy)'
                        self.terminate_connection(headers, response)
                except ValueError, e:
			headers = "400 Bad Request"
                        response = "Your request is jacked up!\n"
                        self.terminate_connection(headers, response)
                        sys.exit(0)

                sys.exit(0)

s = ssl.SSLSocket(  
   sock=socket.socket(socket.AF_INET, socket.SOCK_STREAM),
   ssl_version=ssl.PROTOCOL_TLSv1,  
   certfile='test.pem',  
   server_side=True)

#s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

try:
        s.bind((HOST, PORT))
except socket.error, e:
        print("Error: %s" % e)
        sys.exit(1)
s.listen(1)

while 1:
	conn, addr = s.accept()
	Respondent(conn, addr).start()

print('Connected by %s:%s\n' % addr)

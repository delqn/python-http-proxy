#!/usr/bin/env python

import httplib2
from OpenSSL import SSL
import re
import signal
import socket
import sys
import threading

HOST = ''                 # Symbolic name meaning all available interfaces
PORT = 65500              # Arbitrary non-privileged port
BUFFER_SIZE = 1024
LINE_TERMINATOR = '\r\n'

def signal_handler(signal, frame):
        print("Bye!")
        sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

class Respondent(threading.Thread):
	def __init__(self, conn, addr):
		self.conn = conn
		self.addr = addr
		threading.Thread.__init__(self)

        def respond(self, headers, response):
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
                self.conn.sendall(hdrs)
		##print "response ---> %s" % response
                self.conn.sendall(response)
                #conn.shutdown(socket.SHUT_RDWR)
                #conn.close()

	def step_zero_https(self):
		'''do some primitive SSL negotiation'''
		response = "HTTP/1.1 200 OK\r\n\r\n"
		print "response ---> %s" % response
		self.conn.sendall(response)
                data = self.conn.recv(BUFFER_SIZE)
		print "got this ---> %s" % data
		response = "blah\r\n"
		self.conn.sendall(response)

	def make_request(self, url):
                h = httplib2.Http()
                try:
                        print "Connecting to %s" % url
                        headers, response = h.request(url)
                except httplib2.RelativeURIError, e:
                        print "[Error] Cannot retrieve URL >>>%s<<<" % url
                        headers = {'via': '1.0', 'status':'200', 'content-type':'text/html'}
                        response = '501 Internal Server Error (Proxy)'
		return (headers,response)


	def run(self):
                counter = 0
                found_line = False
                line = ''
		buff = ''
		done = False
		while not done:
                        while not found_line:
                                data = self.conn.recv(BUFFER_SIZE)
                                if not data: break
				buff += data
                                if LINE_TERMINATOR in buff:
					found_line = True
                                        split_buff = buff.split(LINE_TERMINATOR, 1)
                                        line = split_buff[0]
					print "found line ---> %s" % line
                                        if len(split_buff) > 1:
                                                buff = split_buff[1]
                                        response = "Thank you!\n"

                        # (first) line obtained would look like this:
                        # GET http://delqn.com/dot HTTP/1.1
                        do_step_zero_https = False
                        try:
                                verb, url, protocol = line.split(' ')
                                if not re.match(r'^http|https://', url):
                                        if ':443' in url:
                                                url = 'https://' + url
                                                do_step_zero_https = True
                                        else:
                                                url = 'http://' + url
                                elif re.match(r'^https://', url):
                                        do_step_zero_https = True

                                if do_step_zero_https:
                                        self.step_zero_https()
				h,r = self.make_request(url)
                                self.respond(h,r)
                        except ValueError, e:
                                headers = "400 Bad Request"
                                response = "Your request is jacked up!\n"
                                self.respond(headers, response)
                                sys.exit(0)

                        sys.exit(0)




ctx = SSL.Context(SSL.SSLv23_METHOD)
#server.pem's location (containing the server private key and
#the server certificate).
fpem = 'test.pem'
ctx.use_privatekey_file(fpem)
ctx.use_certificate_file(fpem)
s = SSL.Connection(ctx, socket.socket(socket.AF_INET, socket.SOCK_STREAM))


'''
s = ssl.SSLSocket(  
	sock=socket.socket(socket.AF_INET, socket.SOCK_STREAM),
	#ssl_version=ssl.PROTOCOL_TLSv1,  
	ssl_version=ssl.PROTOCOL_SSLv3,
	certfile='test.pem',  
	server_side=True)
'''

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, True)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

'''
        self.rfile = self.connection.makefile('rb', self.rbufsize)
        self.wfile = self.connection.makefile('wb', self.wbufsize)
'''

try:
        s.bind((HOST, PORT))
except socket.error, e:
        print("Error: %s" % e)
        sys.exit(1)
s.listen(1)

while 1:
	conn, addr = s.accept()
	'''
	ssl.wrap_socket(conn,
		server_side=True,
		certfile="certificate.pem", 
		keyfile="key.pem",
		ssl_version=ssl.PROTOCOL_SSLv3)
	'''
	Respondent(conn, addr).start()

print('Connected by %s:%s\n' % addr)

#!/usr/bin/env python2

import logging
import re
import signal
import socket
import sys
import threading
import urllib2

HOST = ''                 # Symbolic name meaning all available interfaces
PORT = 65500              # Arbitrary non-privileged port
BUFFER_SIZE = 1024
LINE_TERMINATOR = '\r\n'

ads = []

FORMAT = '%(asctime)-15s %(clientip)s %(user)-8s %(message)s'
logging.basicConfig(format=FORMAT, filename='./log', level=logging.INFO)
logger = logging.getLogger('python-http-proxy')

def signal_handler(signal, frame):
	print("Bye!")
	sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

class Respondent(threading.Thread):
	def __init__(self, conn, addr):
		self.conn = conn
		self.addr = addr
		threading.Thread.__init__(self)

	def respond(self, headers, response, url=''):
		'''send a response to the server and terminate'''
		'''
{'status': '200', 'x-ysws-request-id': '5caff6d4-b329-4434-ab7b-14d39e36f6ae', 'via': 'HTTP/1.1 web18.usw105.mobstor.gq1.yahoo.com YahooTrafficServer/3.0.1 (UFF), http/1.0 l8.ycs.sjb.yahoo.com (ApacheTrafficServer/3.2.0)', 'content-location': u'http://l.yimg.com/dh/ap/default/121226/vs-wk.jpg', 'accept-ranges': 'bytes', 'expires': 'Sat, 05 Sep 2026 00:00:00 GMT', 'content-length': '6492', 'server': 'ATS/3.2.0', 'last-modified': 'Wed, 26 Dec 2012 23:40:34 GMT', 'connection': 'keep-alive', 'x-ysws-visited-replicas': 'gops.usw105.mobstor.vip.gq1.yahoo.com', 'etag': '"YM:1:db935279-8ac6-4c21-ba6b-ff71ed4f73ce0004d1c9f4f0b07d"', 'cache-control': 'max-age=31536000,public', 'date': 'Wed, 26 Dec 2012 23:41:38 GMT', 'content-type': 'image/jpeg', 'age': '382039'}
		'''
		hdrs = 'HTTP/1.1 200 OK\r\n'
		if 'content-type' in headers:
			hdrs += "Content-Type: %s\r\n" % headers['content-type']
		if 'content-length' in headers:
			hdrs += "Content-Length: %s\r\n" % headers['content-length']
		try:
			self.conn.sendall(bytes(hdrs + '\r\n' + response + '\r\n'))
		except Exception:# as (errno, strerror):
			print("-----------------------------------")
			print("[Error] responding to the client")# % strerror)
			print(hdrs)
			print(len(response))
			print("The URL: %s" % url)
			print("^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n\n")
		#conn.shutdown(socket.SHUT_RDWR)
		self.conn.close()

	def make_request(self, url, request_headers):
		headers = {}
                for ad in ads:
                        if ad in url:
                                headers = {'via': '1.0', 'status':'401', 'content-type':'text/html'}
                                response = '401'
                                return (headers,response)
		request = urllib2.Request(url)
		opener = urllib2.build_opener()
		for k,v in request_headers.iteritems():
			request.add_header(k, v)
		try:
			response = opener.open(request).read()
		except Exception:
			headers = {'via': '1.0', 'status':'200', 'content-type':'text/html'}
			response = '501 Internal Server Error (Proxy)'
		return (headers,response)

	def run(self):
		counter = 0
		buff = ''
		lines = []
		done = False
		while not done:
			data = self.conn.recv(BUFFER_SIZE)
			if not data: return ##TODO
                        buff += data.decode("utf-8")
                        if LINE_TERMINATOR in buff:
				#get all the lines
				while not done:
                                        split_buff = buff.split(LINE_TERMINATOR, 1)
                                        line = split_buff[0]
                                        if len(split_buff) > 1:
                                                buff = split_buff[1]
                                        lines.append(line.strip())
					done = buff == '\r\n'

		if not lines:
			headers = "500 Bad Request"
			response = "Something's not quite right!\n"
			self.respond(headers, response)
			return
		try:
			verb, url, protocol = lines[0].split(' ')
			if not re.match(r'^(http|https)://', url):
				url = "http://" + url

			d = {'clientip': self.addr, 'user': 'not_implemented'}
			logger.info('Request: %s', url, extra=d)
			request_headers = dict([ (x.split(':',1)[0], x.split(':',1)[1]) for x in lines[1:] ])
			h,r = self.make_request(url, request_headers)
			self.respond(h, r, url)
		except ValueError:# as (errno, strerror):
			headers = "400 Bad Request"
			response = "Your request is jacked up!\n"
			self.respond(headers, response)
		return

def start_server():
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, True)
	s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

	'''
		self.rfile = self.connection.makefile('rb', self.rbufsize)
		self.wfile = self.connection.makefile('wb', self.wbufsize)
	'''
	f = open('easylist.txt')
	f.readline()
	for line in f:
		if line[0] == '!':
			continue
		ads.append(line.strip())

	try:
		s.bind((HOST, PORT))
	except socket.error:# as (errno, strerror):
		##print("Error: %s" % strerror)
		print("Could not bind to %s:%s"%(HOST,PORT))
		sys.exit(1)
	s.listen(1)

	#launch unlimited threads...
	while 1:
		conn, addr = s.accept()
		Respondent(conn, addr).start()

if __name__=='__main__':
	start_server()

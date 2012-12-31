#!/usr/bin/env python

import httplib2
import logging
import re
import signal
import socket
import sys
import threading

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
		hdrs = 'HTTP/1.1 200 OK\r\n'
		if 'content-type' in headers:
			hdrs += "Content-Type: %s\r\n" % headers['content-type']
		if 'content-length' in headers:
			hdrs += "Content-Length: %s\r\n" % headers['content-length']
		try:
			self.conn.sendall(hdrs + '\r\n' + response + '\r\n')
		except(Exception, e):
			print("-----------------------------------")
			print("[Error] responding to the client: %s" % e)
			print(hdrs)
			print(len(response))
			print("The URL: %s" % url)
			print("^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n\n")
		#conn.shutdown(socket.SHUT_RDWR)
		#conn.close()

	def make_request(self, url):
		h = httplib2.Http()
		try:
			for ad in ads:
				if ad in url:
					headers = {'via': '1.0', 'status':'401', 'content-type':'text/html'}
					response = '401'
					return (headers,response)
			headers, response = h.request(url)
		except(httplib2.RelativeURIError, e):
			headers = {'via': '1.0', 'status':'200', 'content-type':'text/html'}
			response = '501 Internal Server Error (Proxy)'
		return (headers,response)

	def run(self):
		counter = 0
		found_line = False
		buff = ''
		line = None
		while not found_line:
			data = self.conn.recv(BUFFER_SIZE)
			if not data: break
			buff += data
			if LINE_TERMINATOR in buff:
				found_line = True
				split_buff = buff.split(LINE_TERMINATOR, 1)
				line = split_buff[0]
				if len(split_buff) > 1:
					buff = split_buff[1]

		if not line:
			headers = "500 Bad Request"
			response = "Something's not quite right!\n"
			self.respond(headers, response)
			return
		try:
			verb, url, protocol = line.split(' ')
			if not re.match(r'^http|https://', url):
				url = 'http://' + url

			d = {'clientip': addr, 'user': 'not_implemented'}
			logger.info('Request: %s', url, extra=d)
			h,r = self.make_request(url)
			self.respond(h, r, url)
		except(ValueError, e):
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
	except(socket.error, e):
		print("Error: %s" % e)
		sys.exit(1)
	s.listen(5)

	#launch unlimited threads...
	while 1:
		conn, addr = s.accept()
		Respondent(conn, addr).start()

if __name__=='__main__':
	start_server()

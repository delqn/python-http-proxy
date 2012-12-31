#!/usr/bin/env python2

import logging
import re
import signal
import socket
import sys
import threading
import urllib2
import urllib

from cookielib import CookieJar

FORMAT = '%(asctime)-15s %(clientip)s %(user)-8s %(message)s'
logging.basicConfig(format=FORMAT, filename='./log', level=logging.INFO)
logger = logging.getLogger('python-http-proxy')

def signal_handler(signal, frame):
	print("Bye!")
	sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

class Responder(threading.Thread):
	def __init__(self, conn, addr):
		self.conn = conn
		self.addr = addr
		threading.Thread.__init__(self)

	def respond(self, headers, response, url=''):
		'''send a response to the server and terminate'''
		try:
			self.conn.sendall(headers + response)
		except Exception:# as (errno, strerror):
			print("-----------------------------------")
			print("[Error] responding to the client")# % strerror)
			print(hdrs)
			print(len(response))
			print("The URL: %s" % url)
			print("^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n\n")
		#conn.shutdown(socket.SHUT_RDWR)
		self.conn.close()

	def check_url(self, url):
		'''Is the url to be loaded banned'''
		# TODO
		return True
		'''
                for ad in ads:
                        if ad in url:
				return False
		'''

	def make_request(self, url, request_headers):
		headers = {}
		if not check_url(url):
			return ('HTTP/1.1 499 Banned URL\r\n\r\n','')
		data = {} ##??
		data = urllib.urlencode(data)

		query_args = { 'q':'query string', 'foo':'bar' }
		encoded_args = urllib.urlencode(query_args)
		request = urllib2.Request(url, encoded_args, request_headers)
		cj = CookieJar()
		opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
		for k,v in request_headers.iteritems():
			request.add_header(k, v)

		response = opener.open(request).read()
		headers = opener.open(request).headers
		headers = "".join([ "%s: %s\r\n" % (k,v) for k,v in headers.items() ])
		return ("HTTP/1.1 200 OK\r\n"+headers+"\r\n",response)

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
					done = (buff == '\r\n' or not buff)

		print lines
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

class Proxy:
	def __init__(self):
                self.HOST = ''                 # Symbolic name meaning all available interfaces
                self.PORT = 65500              # Arbitrary non-privileged port
                self.BUFFER_SIZE = 1024
                self.LINE_TERMINATOR = '\r\n'
		self.ads = self.load_banned()
                self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, True)
                self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

                # self.rfile = self.connection.makefile('rb', self.rbufsize)
                # self.wfile = self.connection.makefile('wb', self.wbufsize)

                try:
                        self.s.bind((self.HOST, self.PORT))
                except socket.error:
                        print("Could not bind to %s:%s" % (self.HOST, self.PORT))
                        sys.exit(1)

	def load_banned(self):
		'''Build a tree of banned things'''
		### MAJOR TODO HERE
		banned = []
                f = open('easylist.txt')
		#Skip the first line
                f.readline()
                return [ line.strip() for line in f if 
			line.startswith('/') 
			and line.statswith('||') ]

        def start(self):
                s.listen(1)

		#TODO - don't start unlimited number of threads...
                while 1:
                        conn, addr = s.accept()
                        Responder(conn, addr).start()

if __name__=='__main__':
	sys.stdout.write('Subclass the Proxy class')

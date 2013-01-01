#!/usr/bin/env python2

import httplib
import logging
import re
import socket
import sys
import threading
import urllib2
import urllib

from cookielib import CookieJar

LINE_TERMINATOR = '\r\n'
BUFFER_SIZE = 1024

class Responder(threading.Thread):
	def __init__(self, conn, addr, logger):
		self.conn = conn
		self.addr = addr
		self.logger = logger
		threading.Thread.__init__(self)

	def respond(self, headers, payload, status):
		'''send a response to the server and terminate'''
		r = {
			'http_ver': 'HTTP/1.1',
			'status': status,
			'headers': '\r\n'.join([ "%s: %s" % (k,v) for k,v in headers.items() ]),
			'payload': payload,
		}
		try:
			self.conn.sendall('%(http_ver)s %(status)s\r\n%(headers)s\r\n%(payload)s' % r)
		except Exception, e:# as (errno, strerror):
			self.logger.error('[Error] Could not send data to user! %s' % e)
		#self.conn.shutdown(socket.SHUT_RDWR)
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

	def do_request(self, url, request_headers, verb):
		if not self.check_url(url):
			return ({},'banned URL','499 Banned URL')
		query_args = { 'q':'query string', 'foo':'bar' }
		encoded_data = urllib.urlencode(query_args)

		if verb == "POST":
			fetch_request = urllib2.Request(url, encoded_data, request_headers)
		else:
			fetch_request = urllib2.Request(url)

		for k,v in request_headers.iteritems():
			fetch_request.add_header(k, v)

		self.logger.debug('Request[%s](proxy->server): %s', verb, url)
		self.logger.debug('Headers(proxy->server): \n\t%s', '\n\t'.join([ '%s: %s'%(k,v) for k,v in request_headers.iteritems() ]) )

		cj = CookieJar()
		opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))

		server_headers = {}
		server_response = ''
		status = '200 OK'
		timeout = 0.5 #seconds

		try:
			gotit = opener.open(fetch_request)
			server_response = gotit.read()
			server_headers = dict([ (k,v) for k,v in gotit.headers.items() ])
		except urllib2.HTTPError, e:
			txt = "[Error] Request(proxy<->server): HTTPError: %s\n URL:%s\nVERB: %s\nUSER_HEADERS:%s\n\n SERVER_HEADERS:%s\n CONTENT:%s"
			self.logger.error(txt % (e, url, verb, request_headers,server_headers,server_response))
		except httplib.BadStatusLine, e:
			txt = "[Error] Request(proxy<->server): Bad status line: %s\nURL:%s\nVERB: %s\nUSER_HEADERS:%s\n\nSERVER_HEADERS:%s\nCONTENT:%s"
			self.logger.error(txt % (e, url, verb, request_headers,server_headers,server_response))
		except urllib2.URLError, e:
			txt = "[Error] Request(proxy<->server): Timeout fetching url(%s): %s\nIs the timout of %s too agressive?"
			self.logger.error(txt % (url, e, timeout))
		return (server_headers, server_response, status)

	def parse_all_headers(self, lines):
		headers = {}
		# Skip the first line - that suhold be the VERB
		if len(lines) <= 1: return headers
		for line in lines[1:]:
			if ':' not in line: continue
			split_line = line.split(':', 1)
			key = split_line[0].strip()
			value = split_line[1].strip()
			headers[ key ] = value
		return headers

	def wait_for_entire_user_request(self):
		buff = ''
		done = False
		lines = []
		while not done:
			data = self.conn.recv(BUFFER_SIZE)
			if not data: break
			buff += data.decode("utf-8")
		return buff.split(LINE_TERMINATOR)

	def url_validator(self, url):
		if not re.match(r'^(http|https)://', url):
			new_url = "http://" + url
			url = new_url
		return url

	def run(self):
		r = { 'headers': {}, 'response': 'The user request is jacked up FLOBW', 'status': '499 Bad Request' }
		lines = self.wait_for_entire_user_request()
		if not lines:
			self.logger.error('Blank headers')
			self.respond(**r)
			return
		try:
			verb, url, protocol = lines[0].split(' ')
			url = url_validator(url)
			self.logger.info('Request: %s', url)
			user_headers = self.parse_all_headers(lines)
			r.headers, r.payload, r.status = self.do_request(url, user_headers, verb=verb)
		except ValueError, e:
			self.logger.error('[Error] Problem with the request: %s', e)
		self.respond(**r)

class Proxy:
	def __init__(self, logger):
		self.logger = logger
		self.HOST = ''  # Symbolic name meaning all available interfaces
		self.PORT = 8080# Arbitrary non-privileged port
		self.ads = self.load_banned()
		self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, True)
		self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

		# self.rfile = self.connection.makefile('rb', self.rbufsize)
		# self.wfile = self.connection.makefile('wb', self.wbufsize)

		try:
			self.s.bind((self.HOST, self.PORT))
		except socket.error:
			self.logger.error('Could not bind to %s:%s' % (self.HOST, self.PORT))
			sys.exit(1)

	def load_banned(self):
		'''Build a tree of banned things'''
		### MAJOR TODO HERE
		banned = []
		file_name = 'easylist.txt'
		try:
			f = open(file_name)
			#Skip the first line
			f.readline()
		except IOError, e:
			self.logger.error('Could not load %s', file_name)
			f = []
		return [ line.strip() for line in f if
			line.startswith('/')
			and line.startswith('||') ]

	def start(self):
		self.s.listen(1)
		#TODO - don't start unlimited number of threads...
		while 1:
			conn, addr = self.s.accept()
			Responder(conn, addr, self.logger).start()

if __name__=='__main__':
	sys.stdout.write('Subclass the Proxy class')

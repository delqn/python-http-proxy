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

class Responder(threading.Thread):
	def __init__(self, conn, addr, logger):
		self.BUFFER_SIZE = 1024
		self.LINE_TERMINATOR = '\r\n'
		self.conn = conn
		self.addr = addr
		self.logger = logger
		threading.Thread.__init__(self)

	def respond(self, headers, payload, status):
		'''send a response to the server and terminate'''
		if isinstance(headers, dict):
			str_headers = '\r\n'.join([ "%s: %s" % (k,v) for k,v in headers.items() ])
		else:
			str_headers = ''
		r = {
			'http_ver': 'HTTP/1.1',
			'status': status,
			'headers': str_headers + '\r\n',
			'payload': payload,
		}
		try:
			self.conn.sendall('%(http_ver)s status\r\n%(headers)s\r\n%(payload)s' % r)
		except Exception, e:# as (errno, strerror):
			self.logger.error('[Error] Could not send data to user! %s' % e)
			print "Could not send data to user: %s" % e
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
		headers = {}
		if not self.check_url(url):
			return ('HTTP/1.1 499 Banned URL\r\n\r\n','')
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
		timeout = 0.5 #seconds

		try:
			U = opener.open(fetch_request)
			server_response = U.read()
			server_headers = dict([ (k,v) for k,v in U.headers.items() ])

			#if 'content-type' in headers.keys()
			if 'content-type' in server_headers:
				if server_headers['content-type'].startswith('text'):
					resp_length = len(server_response)
					if resp_length > 10: lenlimit = 10
					else: lenlimit = resp_length-1
					self.logger.debug('Response[len=%s](server->proxy): %s...', resp_length, server_response[lenlimit])
			self.logger.debug('Headers(server->proxy): \n\t%s', '\n\t'.join([ '%s: %s'%(k,v) for k,v in server_headers.items() ]) )

		except httplib.BadStatusLine, e:
			self.logger.error("[Error] Request(proxy<->server): Bad status line: %s\nURL:%s\nVERB: %s\nUSER_HEADERS:%s\n\nSERVER_HEADERS:%s\nCONTENT:%s" % (e, url, verb, request_headers,server_headers,server_response))
		except urllib2.HTTPError, e:
			self.logger.error("[Error] Request(proxy<->server): Fetching url: %s\nURL:%s\nVERB: %s\nUSER_HEADERS:%s\n\nSERVER_HEADERS:%s\nCONTENT:%s" % (e, url, verb, request_headers,server_headers,server_response))
		except urllib2.URLError, e:
			self.logger.error("[Error] Request(proxy<->server): Timeout fetching url(%s): %s\nIs the timout of %s too agressive?" % (url, e, timeout))
		return (server_headers, server_response)

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

	def run(self):
		counter = 0
		buff = ''
		lines = []
		done = False
		while not done:
			data = self.conn.recv(self.BUFFER_SIZE)
			if not data: return ##TODO
			buff += data.decode("utf-8")
			if self.LINE_TERMINATOR in buff:
				#get all the lines
				while not done:
					split_buff = buff.split(self.LINE_TERMINATOR, 1)
					line = split_buff[0]
					if len(split_buff) > 1:
						buff = split_buff[1]
					lines.append(line.strip())
					done = (buff == self.LINE_TERMINATOR or not buff)

		if not lines:
			r = {
				'headers': {},
				'response': "Something's not quite right!",
				'status': "500 Bad Request"
			}
			self.respond(**r)
			return
		try:
			verb, url, protocol = lines[0].split(' ')

			if not re.match(r'^(http|https)://', url):
				new_url = "http://" + url
				url = new_url

			self.logger.info('Request: %s', url)
			h, r = self.do_request(url, self.parse_all_headers(lines), verb=verb)
			response_to_user = {
				'headers': h,
				'payload': r,
				'status': '200 OK'
			}
			self.respond(**response_to_user)
		except ValueError:# as (errno, strerror):
			r = {
				'headers': {},
				'payload': 'Your request is jacked up!',
				'status': '400 Bad Request'
			}
			self.respond(**r)
		return

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

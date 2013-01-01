#!/usr/bin/env python

import logging
import sys
import unittest

sys.path.insert(0, '..')
import proxy

FORMAT = '%(asctime)-15s %(message)s'
logging.basicConfig(format=FORMAT, filename='/tmp/python-http-proxy.log', level=logging.DEBUG)
logger = logging.getLogger('python-http-proxy')

class MockConnection:
	string_to_be_sent = ''
	close_was_called = False
	recv_counter = 0
	segments = ['GET /dot','HTTP/1.','1\r\nUser','-Agent: curl/7.24.0 (x86_64-',
				'apple-darwin12.0) libcurl/7.24.0 OpenSSL/0.9.8r',
				' zlib/1.2.5\r\nHost: delqn.com\r\nAccept: */*']
	def __init__(self):
		pass
	def close(self):
		self.close_was_called = True
	def sendall(self, txt):
		self.string_to_be_sent = txt
	def recv(self, buffer_size):
		if self.recv_counter >= len(self.segments):
			ret = None
		else:
			ret = self.segments[self.recv_counter]
			self.recv_counter += 1
		return ret


class TestResponder(unittest.TestCase):
    def setUp(self):
	self.conn = MockConnection()
	addr = ''
        self.r = proxy.Responder(self.conn, addr, logger)

    def test_respond_method(self):
	headers = {'key':'value'}
	payload = 'This is the HTML'
	status = '200 OK'
	self.r.respond(headers, payload, status)
	expected = 'HTTP/1.1 200 OK\r\nkey: value\r\n\r\nThis is the HTML'
	self.assertEqual(self.conn.string_to_be_sent, expected)
	self.assertTrue(self.conn.close_was_called)
	def exc(self):
		raise Exception
	self.conn.sendall = exc
	self.r.respond(headers, payload, status)

    def test_check_url(self):
	self.assertTrue(self.r.check_url('http://yahoo.com/'))

    def test_do_request(self):
	url = 'http://delqn.com/dot'
	request_headers = {}
	verb = 'GET'
	self.r.check_url = lambda x: False
	got_this = self.r.do_request(url, request_headers, verb)
	expected_this = ({},'banned URL','499 Banned URL')
	self.assertEqual(got_this, expected_this)

	self.r.check_url = lambda x: True
	got_this = self.r.do_request(url, request_headers, verb)
	expected_this = ({'content-length': '2', 'via': '1.1 varnish', 'age': '0', 'x-cacheable': 'YES', 'server': 'Apache/2.2.16 (Debian)', 'last-modified': 'Mon, 31 Dec 2012 02:49:17 GMT', 'connection': 'close', 'x-varnish': '1600489654', 'etag': '"58bac-2-4d21d0f27e540"', 'date': 'Tue, 01 Jan 2013 02:17:27 GMT', 'content-type': 'text/plain'}, '.\n', '200 OK')
	self.assertEqual(got_this[0].keys().sort(), expected_this[0].keys().sort())
	self.assertEqual(got_this[1], expected_this[1])
	self.assertEqual(got_this[2], expected_this[2])

	# TODO!!!
	# now with POST
	verb = 'GET'
	url = 'http://www.wikipedia.org'
	got_this = self.r.do_request(url, request_headers, verb)
	expected_this = ({'content-length': '2', 'via': '1.1 varnish', 'age': '0', 'x-cacheable': 'YES', 'server': 'Apache/2.2.16 (Debian)', 'last-modified': 'Mon, 31 Dec 2012 02:49:17 GMT', 'connection': 'close', 'x-varnish': '1600489654', 'etag': '"58bac-2-4d21d0f27e540"', 'date': 'Tue, 01 Jan 2013 02:17:27 GMT', 'content-type': 'text/plain'}, '.\n', '200 OK')
	self.assertEqual(got_this[0].keys().sort(), expected_this[0].keys().sort())
	##self.assertTrue(len(got_this[1]) > 100)
	self.assertEqual(got_this[2], expected_this[2])


	#TODO test cookies!


    def test_parse_all_headers(self):
	lines = ['GET /dot HTTP/1.1', 'User-Agent: curl/7.24.0 (x86_64-apple-darwin12.0) libcurl/7.24.0 OpenSSL/0.9.8r zlib/1.2.5', 'Host: delqn.com', 'Accept: */*']
	got_this = self.r.parse_all_headers(lines)
	expected_this = {'Host': 'delqn.com', 'Accept': '*/*', 'User-Agent': 'curl/7.24.0 (x86_64-apple-darwin12.0) libcurl/7.24.0 OpenSSL/0.9.8r zlib/1.2.5'}
	self.assertEqual(got_this.keys().sort(), expected_this.keys().sort())

    def test_wait_for_entire_user_request(self):
	got_this = self.r.wait_for_entire_user_request()
	expected = [u'GET /dotHTTP/1.1', u'User-Agent: curl/7.24.0 (x86_64-apple-darwin12.0) libcurl/7.24.0 OpenSSL/0.9.8r zlib/1.2.5', u'Host: delqn.com', u'Accept: */*']
	self.assertEqual(got_this, expected)

    def test_url_validator(self):
	got_this = self.r.url_validator('yahoo.com')
	expected = 'http://yahoo.com'
	self.assertEqual(got_this, expected)

class TestProxy(unittest.TestCase):
    def setUp(self):
        self.p = proxy.Proxy(logger)

    def test_load_banned_file(self):
	# TODO
	self.assertEqual(self.p.load_banned(), [])
	
if __name__ == '__main__':
    unittest.main()

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
	def __init__(self):
		pass
	def close(self):
		self.close_was_called = True
	def sendall(self, txt):
		self.string_to_be_sent = txt


class TestTechnoGraph(unittest.TestCase):

    def setUp(self):
	self.conn = MockConnection()
	addr = ''
        self.r = proxy.Responder(self.conn, addr, logger)

    def test_respond_method(self):
	headers = {'key':'value'}
	payload = 'This is the HTML'
	status = '200 OK'
	self.r.respond(headers, payload, status)
	expected = 'HTTP/1.1 200 OK\r\nkey: value\r\nThis is the HTML'
	self.assertEqual(self.conn.string_to_be_sent, expected)
	self.assertTrue(self.conn.close_was_called)
	def exc(self):
		raise Exception
	self.conn.sendall = exc
	self.r.respond(headers, payload, status)

    def test_check_url(self):
	self.assertTrue(self.r.check_url('http://yahoo.com/'))

    def test_do_request(self):
	self.asserTrue()

if __name__ == '__main__':
    unittest.main()

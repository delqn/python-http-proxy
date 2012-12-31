#!/usr/bin/env python

import sys
import unittest

sys.path.insert(0, '..')
import proxy

class TestTechnoGraph(unittest.TestCase):

    def setUp(self):
        self.p = proxy()

    def test_a_b(self):
	self.assertEqual(a,b)

if __name__ == '__main__':
    unittest.main()

#!/usr/bin/env python2

import argparse
import logging
import os
import signal
import sys
import time

from daemon import Daemon
from proxy import Proxy

FORMAT = '%(asctime)-15s %(message)s'
logging.basicConfig(format=FORMAT, filename='./log', level=logging.DEBUG)
logger = logging.getLogger('python-http-proxy')

def signal_handler1(signal, frame):
	print("Bye!")
	sys.exit(0)

SIGTERM_SENT = False

# TODO: why does this work so much better than the prev version?
def sigterm_handler(signum, frame):
	logger.error('SIGTERM handler!  Shutting Down...')
	print >>sys.stderr, "SIGTERM handler.  Shutting Down."

	global SIGTERM_SENT
	if not SIGTERM_SENT:
		SIGTERM_SENT = True
		logger.error('Sending TERM...')
		print >>sys.stderr, "Sending TERM..."
		os.killpg(0, signal.SIGTERM)

	sys.exit()

signal.signal(signal.SIGINT, sigterm_handler)

p = Proxy(logger)
p.start()

sys.exit()
class MyDaemon(Daemon):
        def run(self):
                while True:
                        time.sleep(1)
 
if __name__ == "__main__":
        parser = argparse.ArgumentParser(description='Command for the daemon')
        parser.add_argument('command', metavar='C', type=str, nargs=1, help='A string command for the daemon: start|stop|restart')
        args = parser.parse_args()

        command = args.command[0]

	#proxy.start_server()
        daemon = MyDaemon('/tmp/python-http-proxy.pid', logger)

        if command == 'start':
                daemon.start()
        elif command == 'stop':
                daemon.stop()
        elif command == 'restart':
                daemon.restart()
        else:
                print "Unknown command"
                sys.exit(2)
        sys.exit(0)

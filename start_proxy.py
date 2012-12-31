#!/usr/bin/env python2

import argparse
import logging
from proxy import Proxy
import sys
import time
from daemon import Daemon

FORMAT = '%(asctime)-15s %(clientip)s %(user)-8s %(message)s'
logging.basicConfig(format=FORMAT, filename='./log', level=logging.INFO)
logger = logging.getLogger('python-http-proxy')

p = Proxy
p.start()

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

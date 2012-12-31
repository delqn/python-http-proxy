#!/usr/bin/env python

import atexit
import sys
import time
import os
from signal import SIGTERM

class Daemon:
	'''Generic daemon class. Subclass the Daemon class and override run()'''
	def __init__(self, pidfile, stdin='/dev/null', stdout='/dev/null', stderr='/dev/null'):
		self.stdin = stdin
		self.stdout = stdout
		self.stderr = stderr
		self.pidfile = pidfile
		pass
	def daemonize(self):
		'''UNIX double-fork'''
		try:
			pid = os.fork()
			if pid > 0:
				#exit first parent
				sys.exit(0)
		except OSError, e:
			sys.stderr.write("First fork failed: %d (%s)\n" % (e.errno, e.strerror))
			sys.exit(1)

		# decouple from parent environment
		os.chdir('/')
		os.setsid()
		
		# second fork
		try:
			pid = os.fork()
			if pid > 0:
				#exit first parent
				sys.exit(0)
		except OSError, e:
			sys.stderr.write("Second fork failed: %d (%s)\n" % (e.errno, e.strerror))
			sys.exit(1)

		sys.stdout.flush()
		sys.stderr.flush()

		# register self.delpid to be executed on exit -- write pidfile
		atexit.register(self.delpid)
		pid = str(os.getpid())
		file(self.pidfile,'w+').write("%s\n" % pid)

	def delpid(self):
		os.remove(self.pidfile)

	def start(self):
		'''Start the daemon'''
		# Check for a pidfile to see if the daemon already runs
		try:
			pf = file(self.pidfile,'r')
			pid = int(pf.read().strip())
			pf.close()
		except IOError:
			pid = None

		if pid:
			message = "pidfile %s already exist. Daemon already running?\n"
			sys.stderr.write(message % self.pidfile)
			sys.exit(1)

		# Start the daemon
		self.daemonize()
		self.run()

	def stop(self):
		'''Stop the daemon'''
		# Get the pid from the pidfile
		try:
			pf = file(self.pidfile,'r')
			pid = int(pf.read().strip())
			pf.close()
		except IOError:
			pid = None

		if not pid:
			message = "pidfile %s does not exist. Daemon not running?\n"
			sys.stderr.write(message % self.pidfile)
			return # not an error in a restart

		# Try killing the daemon process
		try:
			while 1:
				os.kill(pid, SIGTERM)
				time.sleep(0.1)
		except OSError, err:
			err = str(err)
			if err.find("No such process") > 0:
				if os.path.exists(self.pidfile):
					os.remove(self.pidfile)
			else:
				print str(err)
				sys.exit(1)

	def restart(self):
		self.stop()
		self.start()

	def run(self):
		'''override this method'''

#!/usr/bin/env python2.7

# Based on previous work by
# Charles Menguy (see: http://stackoverflow.com/questions/10217067/implementing-a-full-python-unix-style-daemon-process)
# and Sander Marechal (see: http://www.jejik.com/articles/2007/02/a_simple_unix_linux_daemon_in_python/)

# Adapted by M.Hendrix [2015]

# daemon19.py measures the temperature of the diskarray.

import os, sys, time, math, commands
from libdaemon import Daemon

DEBUG = False

class MyDaemon(Daemon):
	def run(self):
		sampleptr = 0
		samples = 5
		datapoints = 4
		data = [[None]*datapoints for _ in range(samples)]

		sampleTime = 12
		cycleTime = samples * sampleTime
		# sync to whole minute
		waitTime = (cycleTime + sampleTime) - (time.time() % cycleTime)
		if DEBUG:print "Waiting {0} s".format(int(waitTime))
		time.sleep(waitTime)
		while True:
			startTime = time.time()

			result = do_work().split(',')
			if DEBUG: print result

			data[sampleptr] = map(float, result)
			# report sample average
			sampleptr = sampleptr + 1
			if (sampleptr == samples):
				somma = map(sum,zip(*data))
				averages = [format(s / samples, '.3f') for s in somma]
				if DEBUG:print averages
				do_report(averages)
				sampleptr = 0

			waitTime = sampleTime - (time.time() - startTime) - (startTime%sampleTime)
			if (waitTime > 0):
				if DEBUG:print "Waiting {0} s".format(int(waitTime))
				time.sleep(waitTime)

def do_work():
	# 4 datapoints gathered here

	# Harddisk temperatures
	outHdaTemp = commands.getoutput("smartctl -A /dev/sda -d ata |grep Temperature_Celsius |awk '{print $10}'")
	outHdbTemp = commands.getoutput("smartctl -A /dev/sdb -d ata |grep Temperature_Celsius |awk '{print $10}'")
	outHdcTemp = commands.getoutput("smartctl -A /dev/sdc -d ata |grep Temperature_Celsius |awk '{print $10}'")
	outHddTemp = commands.getoutput("smartctl -A /dev/sdd -d ata |grep Temperature_Celsius |awk '{print $10}'")

	if DEBUG: print outHdaTemp, outHdbTemp, outHdcTemp, outHddTemp
	return '{0}, {1}, {2}, {3}'.format(outHdaTemp, outHdbTemp, outHdcTemp, outHddTemp)

def do_report(result):
	# Get the time and date in human-readable form and UN*X-epoch...
	outDate = commands.getoutput("date '+%F %H:%M:%S, %s'")
	result = ', '.join(map(str, result))
	flock = '/tmp/synodiagd/11.lock'
	lock(flock)
	# beware: server expects `15-tempdisk.csv`  not `11-tempdisk.csv`!
	f = file('/tmp/synodiagd/15-tempdisk.csv', 'a')
	f.write('{0}, {1}\n'.format(outDate, result) )
	f.close()
	unlock(flock)
	return

def lock(fname):
	open(fname, 'a').close()

def unlock(fname):
	if os.path.isfile(fname):
		os.remove(fname)

if __name__ == "__main__":
	daemon = MyDaemon('/tmp/synodiagd/11.pid')
	if len(sys.argv) == 2:
		if 'start' == sys.argv[1]:
			daemon.start()
		elif 'stop' == sys.argv[1]:
			daemon.stop()
		elif 'restart' == sys.argv[1]:
			daemon.restart()
		elif 'foreground' == sys.argv[1]:
			# assist with debugging.
			print "Debug-mode started. Use <Ctrl>+C to stop."
			DEBUG = True
			daemon.run()
		else:
			print "Unknown command"
			sys.exit(2)
		sys.exit(0)
	else:
		print "usage: %s start|stop|restart|foreground" % sys.argv[0]
		sys.exit(2)

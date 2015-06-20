#!/usr/bin/env python2.7

# Based on previous work by
# Charles Menguy (see: http://stackoverflow.com/questions/10217067/implementing-a-full-python-unix-style-daemon-process)
# and Sander Marechal (see: http://www.jejik.com/articles/2007/02/a_simple_unix_linux_daemon_in_python/)

# Adapted by M.Hendrix [2015]

# daemon99.py creates an XML-file and uploads data to the server.

import os, sys, shutil, glob, platform, time, commands
from libdaemon import Daemon
from libsmart import SmartDisk

DEBUG = False
os.nice(8)

sda = SmartDisk("/dev/sda -d ata",0)
sdb = SmartDisk("/dev/sdb -d ata",0)
sdc = SmartDisk("/dev/sdc -d ata",0)
sdd = SmartDisk("/dev/sdd -d ata",0)

class MyDaemon(Daemon):
	def run(self):
		myname = os.uname()[1]
		mount_path = '/mnt/share1/'
		remote_path = mount_path + myname
		remote_lock = remote_path + '/client.lock'
		sampleptr = 0
		samples = 1

		sampleTime = 60
		cycleTime = samples * sampleTime
		# sync to whole minute
		waitTime = (cycleTime + sampleTime) - (time.time() % cycleTime)
		if DEBUG:
			print "Not Waiting {0} s".format(int(waitTime))
		else:
			time.sleep(waitTime)
		while True:
			startTime=time.time()

			if os.path.ismount(mount_path):
				do_mv_data(remote_path)
				do_xml(remote_path)

			waitTime = sampleTime - (time.time() - startTime) - (startTime%sampleTime)
			if (waitTime > 0):
				if DEBUG:print "Waiting {0} s".format(int(waitTime))
				time.sleep(waitTime)

def do_mv_data(rpath):
	hostlock = rpath + '/host.lock'
	clientlock = rpath + '/client.lock'
	count_internal_locks=1

	#
	#rpath='/tmp/test'
	#

	# wait 3 seconds for processes to finish
	time.sleep(3)

	while os.path.isfile(hostlock):
		# wait while the server has locked the directory
		if DEBUG:print "host locked (waiting)"
		time.sleep(1)

	# server already sets the client.lock. Do it anyway.
	if DEBUG:print "set clientlock"
	lock(clientlock)

	# prevent race conditions
	while os.path.isfile(hostlock):
		# wait while the server has locked the directory
		if DEBUG:print "host got locked (waiting)"
		time.sleep(1)

	if DEBUG:print "host unlocked"

	while (count_internal_locks > 0):
		time.sleep(1)
		count_internal_locks=0
		for file in glob.glob(r'/tmp/synodiagd/*.lock'):
			count_internal_locks += 1

		if DEBUG:print "{0} internal locks".format(count_internal_locks)

	if DEBUG:print "0 internal locks"

	for file in glob.glob(r'/tmp/synodiagd/*.csv'):
		if DEBUG:print file
		if os.path.isfile(clientlock):
			if not (os.path.isfile(rpath + "/" + os.path.split(file)[1])):
			  shutil.move(file, rpath)

	unlock(clientlock)
	if DEBUG:print "unset clientlock"

	return

def do_xml(wpath):
	#
	uname           = os.uname()
	Tcpu            = "---" #float(commands.getoutput("cat /sys/class/thermal/thermal_zone0/temp"))/1000
	fcpu            = float(commands.getoutput("cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq"))/1000
	synodiagdbranch = commands.getoutput("cat $HOME/.synodiagd.branch")
	uptime          = commands.getoutput("uptime")
	dfh             = commands.getoutput("df")
	freeh           = commands.getoutput("free")
	mds							= commands.getoutput("cat /proc/mdstat |awk 'NR<10'")
	psout           = commands.getoutput("top -b -n 1 | cut -c 37- | awk 'NR>4' | head -10 | sed 's/&/\&amp;/g' | sed 's/>/\&gt;/g'")
	#Tsda            = commands.getoutput("smartctl -A /dev/sda -d ata |grep Temperature_Celsius |awk '{print $10}'")
	#Tsdb            = commands.getoutput("smartctl -A /dev/sdb -d ata |grep Temperature_Celsius |awk '{print $10}'")
	#Tsdc            = commands.getoutput("smartctl -A /dev/sdc -d ata |grep Temperature_Celsius |awk '{print $10}'")
	#Tsdd            = commands.getoutput("smartctl -A /dev/sdd -d ata |grep Temperature_Celsius |awk '{print $10}'")
	#
	#
	sda.smart()
	sdb.smart()
	sdc.smart()
	sdd.smart()
	RBCsda=sda.getdata('5')
	RBCsdb=sdb.getdata('5')
	RBCsdc=sdc.getdata('5')
	RBCsdd=sdd.getdata('5')
	OUsda=sda.getdata('198')
	OUsdb=sdb.getdata('198')
	OUsdc=sdc.getdata('198')
	OUsdd=sdd.getdata('198')
	# disktemperature
	Tsda=sda.getdata('194')
	Tsdb=sdb.getdata('194')
	Tsdc=sdc.getdata('194')
	Tsdd=sdd.getdata('194')
	# disk power-on time
	Pta=sda.getdata('9')
	Ptb=sdb.getdata('9')
	Ptc=sdc.getdata('9')
	Ptd=sdd.getdata('9')
	# disk health
	Hda=sda.gethealth()
	Hdb=sdb.gethealth()
	Hdc=sdc.gethealth()
	Hdd=sdd.gethealth()
	# Self-test info
	Testa=sda.getlasttest()
	Testb=sdb.getlasttest()
	Testc=sdc.getlasttest()
	Testd=sdd.getlasttest()
	# Disk info
	Infoa=sda.getinfo()
	Infob=sdb.getinfo()
	Infoc=sdc.getinfo()
	Infod=sdd.getinfo()

	#
	f = file(wpath + '/status.xml', 'w')

	f.write('<server>\n')

	f.write('<name>\n')
	f.write(uname[1] + '\n')
	f.write('</name>\n')

	f.write('<df>\n')
	f.write(dfh + '\n')
	f.write('-\n')
	f.write(mds + '\n')
	f.write('</df>\n')

	f.write('<temperature>\n')
	f.write(str(Tcpu) + ' degC @ '+ str(fcpu) +' MHz\n')
	f.write('sda: '+ Tsda +' || sdb: '+ Tsdb +' || sdc: '+ Tsdc +' || sdd: '+ Tsdd +' degC')
	f.write('\n')
	f.write('---disk1---\n')
	f.write(' Name      : ' + Infoa + '\n')
	f.write(' PowerOn   : ' + Pta + '\n')
	f.write(' Last test : ' + Testa +'\n')
	f.write('              Retired Block Count (5) = ' + RBCsda + ' - Offline Uncorrectable (198) = ' + OUsda +'\n')
	f.write('             ' + Hda +'\n')
	f.write('---disk2---\n')
	f.write(' Name      : ' + Infob + '\n')
	f.write(' PowerOn   : ' + Ptb + '\n')
	f.write(' Last test : ' + Testb +'\n')
	f.write('              Retired Block Count (5) = ' + RBCsdb + ' - Offline Uncorrectable (198) = ' + OUsdb +'\n')
	f.write('             ' + Hdb +'\n')
	f.write('---disk3---\n')
	f.write(' Name      : ' + Infoc + '\n')
	f.write(' PowerOn   : ' + Ptc + '\n')
	f.write(' Last test : ' + Testc +'\n')
	f.write('              Retired Block Count (5) = ' + RBCsdc + ' - Offline Uncorrectable (198) = ' + OUsdc +'\n')
	f.write('             ' + Hdc +'\n')
	f.write('---disk4---\n')
	f.write(' Name      : ' + Infod + '\n')
	f.write(' PowerOn   : ' + Ptd + '\n')
	f.write(' Last test : ' + Testd +'\n')
	f.write('              Retired Block Count (5) = ' + RBCsdd + ' - Offline Uncorrectable (198) = ' + OUsdd +'\n')
	f.write('             ' + Hdd +'\n')
	f.write(' ')
	f.write('</temperature>\n')

	f.write('<memusage>\n')
	f.write(freeh + '\n')
	f.write('</memusage>\n')

	f.write('<uptime>\n')
	f.write(uptime + '\n')
	f.write(uname[0]+ ' ' +uname[1]+ ' ' +uname[2]+ ' ' +uname[3]+ ' ' +uname[4]+ ' ' +platform.platform() +'\n')
	f.write(' - synodiagd on: '+ synodiagdbranch +'\n')
	f.write('\nTop 10 processes:\n' + psout +'\n')
	f.write('</uptime>\n')

	f.write('</server>\n')

	f.close()
	return

def lock(fname):
	open(fname, 'a').close()

def unlock(fname):
	if os.path.isfile(fname):
		os.remove(fname)

if __name__ == "__main__":
	daemon = MyDaemon('/tmp/synodiagd/99.pid')
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

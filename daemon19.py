#!/usr/bin/env python2.7

# Based on previous work by
# Charles Menguy (see: http://stackoverflow.com/questions/10217067/implementing-a-full-python-unix-style-daemon-process)
# and Sander Marechal (see: http://www.jejik.com/articles/2007/02/a_simple_unix_linux_daemon_in_python/)

# Adapted by M.Hendrix [2015]

# daemon19.py measures the temperature of the diskarray.
# uses moving averages

import os, sys, time, math, commands
from libdaemon import Daemon
from libsmart import SmartDisk

# BEWARE
# The disks identified here as `sda`, `sdb` etc. may not necessarily
# be called `/dev/sda`, `/dev/sdb` etc. on the system!!
sda = SmartDisk("/dev/sda -d ata",0)
sdb = SmartDisk("/dev/sdb -d ata",0)
sdc = SmartDisk("/dev/sdc -d ata",0)
sdd = SmartDisk("/dev/sdd -d ata",0)

DEBUG = False

class MyDaemon(Daemon):
  def run(self):
    sampleptr = 0
    cycles = 6
    SamplesPerCycle = 5
    samples = SamplesPerCycle * cycles

    datapoints = 4
    data = []

    sampleTime = 60
    cycleTime = samples * sampleTime
    # sync to whole minute
    waitTime = (cycleTime + sampleTime) - (time.time() % cycleTime)
    if DEBUG:print "Waiting {0} s".format(int(waitTime))
    time.sleep(waitTime)
    while True:
      startTime = time.time()

      result = do_work().split(',')
      if DEBUG: print result

      data.append(map(float, result))
      if (len(data) > samples):data.pop(0)
      sampleptr = sampleptr + 1

      # report sample average
      if (sampleptr % SamplesPerCycle == 0):
        somma = map(sum,zip(*data))
        averages = [format(s / len(data), '.3f') for s in somma]
        if DEBUG:print averages
        do_report(averages)
        if (sampleptr == samples):
          sampleptr = 0

      waitTime = sampleTime - (time.time() - startTime) - (startTime%sampleTime)
      if (waitTime > 0):
        if DEBUG:print "Waiting {0} s".format(int(waitTime))
        time.sleep(waitTime)

def do_work():
  # 4 datapoints gathered here
  #
  sda.smart()
  sdb.smart()
  sdc.smart()
  sdd.smart()
  # disktemperature
  Tsda=sda.getdata('194')
  Tsdb=sdb.getdata('194')
  Tsdc=sdc.getdata('194')
  Tsdd=sdd.getdata('194')

  if DEBUG: print Tsda, Tsdb, Tsdc, Tsdd
  return '{0}, {1}, {2}, {3}'.format(Tsda, Tsdb, Tsdc, Tsdd)

def do_report(result):
  # Get the time and date in human-readable form and UN*X-epoch...
  outDate = commands.getoutput("date '+%F %H:%M:%S, %s'")
  result = ', '.join(map(str, result))
  flock = '/tmp/synodiagd/19.lock'
  lock(flock)
  f = file('/tmp/synodiagd/19-tempdisk.csv', 'a')
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
  daemon = MyDaemon('/tmp/synodiagd/19.pid')
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

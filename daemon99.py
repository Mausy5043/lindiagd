#!/usr/bin/env python2.7

# Based on previous work by
# Charles Menguy (see: http://stackoverflow.com/questions/10217067/implementing-a-full-python-unix-style-daemon-process)
# and Sander Marechal (see: http://www.jejik.com/articles/2007/02/a_simple_unix_linux_daemon_in_python/)

# Adapted by M.Hendrix [2015]

# daemon99.py creates an XML-file on to the server.

import syslog, traceback
import os, sys, platform, time, commands
from libdaemon import Daemon
from libsmart import SmartDisk
import subprocess

DEBUG = False
IS_SYSTEMD = os.path.isfile('/bin/journalctl')
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
      try:
        startTime=time.time()

        if os.path.ismount(mount_path):
          do_xml(remote_path)

        waitTime = sampleTime - (time.time() - startTime) - (startTime%sampleTime)
        if (waitTime > 0):
          if DEBUG:print "Waiting {0} s".format(int(waitTime))
          time.sleep(waitTime)
      except Exception as e:
        if DEBUG:
          print "Unexpected error:"
          print e.message
        syslog.syslog(syslog.LOG_ALERT,e.__doc__)
        syslog_trace(traceback.format_exc())
        raise

def syslog_trace(trace):
  #Log a python stack trace to syslog
  log_lines = trace.split('\n')
  for line in log_lines:
    if len(line):
      syslog.syslog(syslog.LOG_ALERT,line)

def do_xml(wpath):
  #
  #usr							= commands.getoutput("whoami")
  home            = os.path.expanduser("~")
  uname           = os.uname()

  Tcpu            = "---"

  fi              = "/sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq"
  f 							= file(fi,'r')
  fcpu						= float(f.read().strip('\n'))/1000
  f.close()

  fi              = home +"/.synodiagd.branch"
  f 							= file(fi,'r')
  synodiagdbranch = f.read().strip('\n')
  f.close()

  uptime          = commands.getoutput("uptime")
  dfh             = commands.getoutput("df")
  freeh           = commands.getoutput("free")
  mds							= commands.getoutput("cat /proc/mdstat |awk 'NR<9'")  #FIXME
  #psout           = commands.getoutput("top -b -n 1 | cut -c 37- | awk 'NR>4' | head -10 | sed 's/&/\&amp;/g' | sed 's/>/\&gt;/g'")
  p1              = subprocess.Popen(["ps", "-e", "-o", "pcpu,args"], stdout=subprocess.PIPE)
  p2              = subprocess.Popen(["cut", "-c", "-132"], stdin=p1.stdout, stdout=subprocess.PIPE)
  p3              = subprocess.Popen(["awk", "NR>2"], stdin=p2.stdout, stdout=subprocess.PIPE)
  p4              = subprocess.Popen(["sort", "-nr"], stdin=p3.stdout, stdout=subprocess.PIPE)
  p5              = subprocess.Popen(["head", "-10"], stdin=p4.stdout, stdout=subprocess.PIPE)
  p6              = subprocess.Popen(["sed", "s/&/\&amp;/g"], stdin=p5.stdout, stdout=subprocess.PIPE)
  p7              = subprocess.Popen(["sed", "s/>/\&gt;/g"], stdin=p6.stdout, stdout=subprocess.PIPE)
  p8              = subprocess.Popen(["sed", "s/</\&lt;/g"], stdin=p7.stdout, stdout=subprocess.PIPE)
  psout           = p8.stdout.read()

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
  if not "without" in Testa:
    f.write(' Last test : ' + Testa +'\n')
  if not "PASSED" in Hda:
    f.write('             ' + Hda +'\n')
  if not(RBCsda=="0") or not(OUsda=="0"):
    f.write('              Retired Block Count (5) = ' + RBCsda + ' - Offline Uncorrectable (198) = ' + OUsda +'\n')
  f.write('---disk2---\n')
  f.write(' Name      : ' + Infob + '\n')
  f.write(' PowerOn   : ' + Ptb + '\n')
  if not "without" in Testb:
    f.write(' Last test : ' + Testb +'\n')
  if not "PASSED" in Hdb:
    f.write('             ' + Hdb +'\n')
  if not(RBCsdb=="0") or not(OUsdb=="0"):
    f.write('              Retired Block Count (5) = ' + RBCsdb + ' - Offline Uncorrectable (198) = ' + OUsdb +'\n')
  f.write('---disk3---\n')
  f.write(' Name      : ' + Infoc + '\n')
  f.write(' PowerOn   : ' + Ptc + '\n')
  if not "without" in Testc:
    f.write(' Last test : ' + Testc +'\n')
  if not "PASSED" in Hdc:
    f.write('             ' + Hdc +'\n')
  if not(RBCsdc=="0") or not(OUsdc=="0"):
    f.write('              Retired Block Count (5) = ' + RBCsdc + ' - Offline Uncorrectable (198) = ' + OUsdc +'\n')
  f.write('---disk4---\n')
  f.write(' Name      : ' + Infod + '\n')
  f.write(' PowerOn   : ' + Ptd + '\n')
  if not "without" in Testd:
    f.write(' Last test : ' + Testd +'\n')
  if not "PASSED" in Hdd:
    f.write('             ' + Hdd +'\n')
  if not(RBCsdd=="0") or not(OUsdd=="0"):
    f.write('              Retired Block Count (5) = ' + RBCsdd + ' - Offline Uncorrectable (198) = ' + OUsdd +'\n')
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
    print "usage: {0!s} start|stop|restart|foreground".format(sys.argv[0])
    sys.exit(2)

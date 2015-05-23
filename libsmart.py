#!/usr/bin/python

import commands, time

DEBUG = False

class SmartDisk():
  """
  A class to access information on S.M.A.R.T. disks.

  Usage: (under construction)
  """
  def __init__(self,diskid):
    self.wwn = diskid
    self.vars     = "-"
    self.health   = "-"
    self.selftest = "-"
    self.info     = "-"
    self.identity = commands.getoutput("sudo smartctl -i " + self.wwn + " |awk 'NR>4'").splitlines()
    self.lasttime = -1

  def smart(self):
    t1 = time.time()
    # only read the S.M.A.R.T. data if current data is stale
    # data is considered stale if it is older than 4 minutes
    if ((t1 - self.lasttime) > (4*60)):
      self.vars     = commands.getoutput("sudo smartctl -A " + self.wwn + " |awk 'NR>4'").splitlines()
      self.info     = commands.getoutput("sudo smartctl -i " + self.wwn + " |awk 'NR>4'").splitlines()
      self.health   = commands.getoutput("sudo smartctl -H " + self.wwn + " |awk 'NR>4'").splitlines()
      self.selftest = commands.getoutput("sudo smartctl -l selftest " + self.wwn + "  |grep '\# 1'")
      self.lasttime = t1
    else:
      if DEBUG:print "Using old data: "
    if DEBUG:print self.vars
    return 0

  def getdata(self,id):
    ret = ""
    for line in self.vars:
      if (line != ''):
        ls=line.split()
        if (ls[0] == id):
          if DEBUG:print line.split()
          ret=ls[9]
    return ret

  def gethealth(self):
    ret =""
    if DEBUG:print self.health
    ret = self.health[0]
    return ret

  def getlasttest(self):
    ret =""
    if DEBUG:print self.selftest
    ret = self.selftest
    return ret

  def getinfo(self):
    ret=retm=retd=rets=""
    for line in self.identity:
      if DEBUG:print line
      if (line != ''):
        ls=line.split()
        if (line.split()[0] == "Model"):
          retm = line.split(': ')[1].strip()
        if (line.split()[0] == "Device"):
          retd = line.split(': ')[1].strip()
        if (line.split()[0] == "Serial"):
          rets = line.split(': ')[1].strip()
    ret = retm + " " + retd + " (" + rets +")"
    return ret

if __name__ == '__main__':

  DEBUG = True

  sdd = SmartDisk("/dev/sdd -d ata")
  sdd.smart()
  print sdd.getdata('194')
  print "last test:"
  print sdd.getlasttest()
  print "wwn"
  print sdd.getinfo()
  print "health"
  print sdd.gethealth()
  print "data 9"
  print sdd.getdata('9')

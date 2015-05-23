#!/usr/bin/python

import commands, time

DEBUG = False

class SmartDisk():
  """
  A class to access information on S.M.A.R.T. disks.

  Usage: (under construction)
  """
  def __init__(self,diskid):
    self.diskid = diskid
    self.vars     = "-"
    self.health   = "-"
    self.selftest = "-"
    self.info     = "-"
    self.identity = commands.getoutput("sudo smartctl -i " + self.diskid + " |awk 'NR>4'").splitlines()
    self.lasttime = -1

  def smart(self):
    t1 = time.time()
    # only read the S.M.A.R.T. data if current data is stale
    # data is considered stale if it is older than 4 minutes
    if ((t1 - self.lasttime) > (4*60)):
      self.vars     = commands.getoutput("sudo smartctl -A " + self.diskid + " |awk 'NR>4'").splitlines()
      self.info     = commands.getoutput("sudo smartctl -i " + self.diskid + " |awk 'NR>4'").splitlines()
      self.health   = commands.getoutput("sudo smartctl -H " + self.diskid + " |awk 'NR>4'").splitlines()
      self.selftest = commands.getoutput("sudo smartctl -l selftest " + self.diskid + "  |grep '\# 1'")
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
        if (ls[0] == "Model"):
          retm = line.split(': ')[1].strip()
        if (ls[0] == "Device") and (ls[1] == "Model:"):
          retd = line.split(': ')[1].strip()
        if (ls[0] == "Serial"):
          rets = line.split(': ')[1].strip()
    ret = retm + " " + retd + " (" + rets +")"
    return ret

if __name__ == '__main__':

  DEBUG = True

  # initialise a device
  sda = SmartDisk("/dev/sda -d ata")
  # request reading smart info from device
  sda.smart()
  # extract data with id=194
  print sda.getdata('194')
  print "last test:"
  print sda.getlasttest()
  print "diskid"
  print sda.getinfo()
  print "health"
  print sda.gethealth()
  print "data 9"
  print sda.getdata('9')

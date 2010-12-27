#!/usr/bin/env python

from ftplib import FTP
import os
import errno
import time
import sys

SERVERRETRY = 5
SERVERRETRYTIME = 300

conffile='/home/case/.nsmauth.conf'

def LoadConf(filename):

  global confvar
  confvar = {}
  try:
    conf=open(filename,'r')
  except:
    print "error during conf read"
    sys.exit(1)

  line = conf.readline()

  while line:
    conft = line.replace('\n','').split("=")
    confvar[conft[0]]=conft[1]
    line = conf.readline()


if __name__ == '__main__':

  LoadConf(conffile)

  MAINDIR = confvar['nsmdiffdir']
  EMAIL = MAINDIR+"/"+".tosend" 

  serverretrycount = 0
  serverok = 0
  
  while serverok == 0:
    try:
      nsm = FTP(confvar['nsmdiffftp'])
      nsm.login(confvar['nsmdiffuser'],confvar['nsmdiffpass'])
      nsm.cwd(confvar['nsmdiffremotedir'])
      lst = nsm.nlst()
      serverok = 1
    except:
      serverretrycount += 1
      time.sleep(SERVERRETRYTIME)
      if serverretrycount >= SERVERRETRY:
        print "There were errors with the connection to the server\n"
        sys.exit(1)
 
  # creating the dirs needed for the script 
  try:
    os.makedirs(EMAIL)
  except OSError as exc:
    if exc.errno == errno.EEXIST:
        pass
    else: raise

  somethingnew = 0

  difftext = "From: "+confvar['emailfrom']+" \n\
To: "+confvar['emailto']+" \n\
Subject: [NSMDIFF] update from "+(time.strftime("%Y/%m/%d %H:%M:%S",time.localtime()))+"\n" 

  for ver in lst:
    if 'LGB' in ver:
      if not os.path.isdir(MAINDIR+"/"+ver):
        vlst=nsm.nlst(ver)
        for diff in vlst:
          if '_filediff' in diff:
            rsize = nsm.size(diff)
            if ( rsize > 0 ):
              os.mkdir(MAINDIR+"/"+ver)
              try:
                nsm.retrbinary("RETR "+diff, open(MAINDIR+"/"+diff,'wb').write)
              except:
                warn("problem with the ftp server")
                os.remove(MAINDIR+"/"+diff)
                os.rmdir(MAINDIR+"/"+ver)
                sys.exit(1)              
    
              difftext += "\n\nFixes in "+ver+"\n=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=\n"
              difftext += open(MAINDIR+"/"+diff,'r').read()
              somethingnew = 1

  nsm.quit()

  if somethingnew == 1:
    difftext += "--\nYour friendly automatic servant\nAll flames/complaints will go to /dev/null\n"
    try:
      open(EMAIL+"/diff"+str(int(time.time())),'w').write(difftext)
    except:
      print difftext


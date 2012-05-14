#!/usr/bin/python

from cookielib import CookieJar
from urllib import urlencode,unquote
import urllib2 
from sgmllib import SGMLParser 
import sys
import os
import re

# usage printout
def usage():
  print "\nUsage: "+str(sys.argv[0])+" <options> Case-IDCa-seID\n\
\n\
Options:\n\
-d directory -> directory where to download attachments, inside that directory a directory with case number will be created,\n\
-f regexp -> download or list only attachments which filenames match regexp,\n\
-h -> this help,\n\
-l -> just list case attachments without downloading,\n\
-o -> force overwrite of the files,\n\
-p pass -> password used for the CM,\n\
-t -> this will download attachments to a folder temp in the destination folder (for cases that you just want to look at),\n\
-u user -> username used for the CM,\n\
\n\
You can define the user, password and the download directory in a file "+str(os.environ['HOME'])+"/.cm.conf which should look like this:\n\
cmuser=YOUR_USERNAME_FOR_CM\n\
cmpass=YOUR_PASSWORD_FOR_CM\n\
cmdir=THE_MAIN_DIRECOTORY_WHERE_TO_DOWNLOAD_ATTACHMENTS\n\
\n\
"
  sys.exit(1)

# loading of the configuration file
def LoadConf(filename):
  '''
  This loads the configuration settings from a file
  the syntax of the file looks like:
  attributename = attributevalue
  '''
  global confvar

  confvar = {} 
  try:
    conf = open(filename,'r')
  except:
    print "error during conf file read: "+str(filename)
    sys.exit(1)

  line = conf.readline()

  while line:
    conft = line.replace('\n','').split("=")
    confvar[conft[0]] = conft[1]
    line = conf.readline() 

class LoginForm(SGMLParser):
  '''
  This class analyses the Login form
  '''
  def parse(self, s):
    self.feed(s)
    self.close()

  def __init__(self, verbose = 0):
    SGMLParser.__init__(self, verbose)
    self.form = {} 
    self.inside_auth_form = 0

  def do_input(self, attributes):
    if self.inside_auth_form == 1:
      if 'hidden' in attributes[0]:
        self.form[attributes[1][1]] = attributes[2][1] 

  def start_form(self, attributes):
    for name, value in attributes:
      if name == "name" and value == "Login":
        self.inside_auth_form = 1
        break

  def end_form(self):
    self.inside_auth_form = 0 

  def get_form(self):
    return self.form


class CaseForm(SGMLParser):
  '''
  This class analyses the Case search form
  '''
  def parse(self, s):
    self.feed(s)
    self.close()

  def __init__(self, verbose = 0):
    SGMLParser.__init__(self, verbose)
    self.form = {} 
    self.inside_form = 0

  def do_input(self, attributes):
    if self.inside_form == 1:
      if 'hidden' in attributes[0]:
        self.form[attributes[1][1]] = attributes[2][1] 

  def start_form(self, attributes):
    for name, value in attributes:
      if name == "name" and value == "Login":
        self.inside_form = 1
        break

  def end_form(self):
    self.inside_form = 0 

  def get_form(self):
    return self.form

class CaseDetailsForm(SGMLParser):
  '''
  This class analyses the Case details form
  '''
  def parse(self, s):
    self.feed(s)
    self.close()

  def __init__(self, verbose = 0):
    SGMLParser.__init__(self, verbose)
    self.form = {}
    self.inside_form = 0

  def do_input(self, attributes):
    if self.inside_form == 1:
      if 'hidden' in attributes[0]:
        self.form[attributes[1][1]] = attributes[2][1]

  def start_form(self, attributes):
    for name, value in attributes:
      if name == "name" and value == "case_results":
        self.inside_form = 1
        break

  def end_form(self):
    self.inside_form = 0

  def get_form(self):
    return self.form

class CaseAttachForm(SGMLParser):
  '''
  This class analyses the Case attachments form
  '''
  def parse(self, s):
    self.feed(s)
    self.close()

  def __init__(self, verbose = 0):
    SGMLParser.__init__(self, verbose)
    self.form = {}
    self.inside_form = 0

  def do_input(self, attributes):
    if self.inside_form == 1:
      if 'hidden' in attributes[0]:
        self.form[attributes[1][1]] = attributes[2][1]

  def start_form(self, attributes):
    for name, value in attributes:
      if name == "name" and value == "case_detail":
        self.inside_form = 1
        break

  def end_form(self):
    self.inside_form = 0

  def get_form(self):
    return self.form
 
if __name__ == '__main__':

  conffile = str(os.environ['HOME'])+'/.cm.conf'
  urlcm = "https://tools.online.juniper.net/cm/"

  caseid = ""
  opt_filt = ""
  opt_list = 0
  opt_temp = 0
  opt_dir = 0 
  opt_over = 0
  opt_user = ""
  opt_pass = ""

  LoadConf(conffile)
  try:
    if confvar['cmuser']:
      opt_user = confvar['cmuser']
    if confvar['cmpass']:
      opt_pass = confvar['cmpass']
    if confvar['cmdir']:
      opt_dir = confvar['cmdir']
  except:
    pass

  # options processing
  i = 1
  imax = len(sys.argv)
  while 1:
    if i >= imax:
      break
    arg = sys.argv[i]
    if arg == "-t":
      opt_temp = 1
    elif arg == "-l":
      opt_list = 1
    elif arg == "-o":
      opt_over = 1
    elif arg == "-f":
      i += 1
      if i >= imax:
        usage()
      opt_filt = sys.argv[i]
    elif arg == "-h":
      usage()
    elif arg == "-d":
      i += 1
      if i >= imax:
        usage()
      opt_dir = sys.argv[i]
    elif arg == "-u":
      i += 1
      if i >= imax:
        usage()
      opt_user = sys.argv[i]
    elif arg == "-p":
      i += 1
      if i >= imax:
        usage()
      opt_pass = sys.argv[i]
    else:
      if re.match("^\d{4}-\d{4}-\d{4}$",arg):
        caseid = arg
      else:
        usage()
    i += 1

  # just to check we have enough information to go further
  if caseid == "" or opt_user == "" or opt_pass == "":
    usage()

  cj = CookieJar()
  opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
  urllib2.install_opener(opener)
  try:
    dat = urllib2.urlopen(urlcm)
  except:
    print "[-] problem with connecting to the CM"
    sys.exit(1)

  print "[+] logging into the cm\r",
  try:
    fparser = LoginForm()
    fparser.parse(dat.read())
    form = fparser.get_form()
    form['USER'] = opt_user
    form['PASSWORD'] = opt_pass
    dat = urllib2.urlopen(dat.geturl(),urlencode(form))
  except:
    print "[-] error while logging into cm"
    sys.exit(1)

  print "[+] searching for case "+str(caseid)+"\r",
  try:
    fparser = CaseForm()
    fparser.parse(dat.read())
    form = fparser.get_form()
    form['keyword'] = caseid
    form['fr'] = "5"
    dat = urllib2.urlopen(urlcm+"case_results.jsp",urlencode(form))
  except:
    print "[-] error while searching for the case "+str(caseid)+"."
    sys.exit(1)

  print "[+] "+str(caseid)+": getting case details\r",
  try:
    text = dat.read()
    cid = re.search("href=\"javascript:setCid\(\'(.+?)\'",text)
    fparser = CaseDetailsForm()
    fparser.parse(text)
    form = fparser.get_form()
    form['cid'] = cid.group(1)
    dat = urllib2.urlopen(urlcm+"case_detail.jsp",urlencode(form))
  except:
    print "[-] error while trying to get case "+str(caseid)+" details."
    sys.exit(1)

  print "[+] "+str(caseid)+": searching for case attachments\r",
  try:
    fparser = CaseAttachForm()
    fparser.parse(dat.read())
    form = fparser.get_form()
    dat = urllib2.urlopen(urlcm+"case_attachments.jsp",urlencode(form))
  except:
    print "[-] error while searching for case "+str(caseid)+" attachments."
    sys.exit(1)

  text = dat.read()
  attach = re.findall("href=\"(AttachDown/.+?)\"",text)

  casedir = str(opt_dir)+"/"+str(caseid)+"/"
  if opt_temp == 1:
    casedir = str(opt_dir)+"/"+"temp/"+str(caseid)+"/" 

  if opt_list == 0:
    print "[+] "+str(caseid)+": will download to "+str(casedir)

  for att in attach:
    filename = re.search("AttachDown/(.+?)\?OBJID=(.+?)\&",att)
  
    # just listing attachments
    if opt_list == 1:
      if not opt_filt == "":
        if not re.search(opt_filt,filename.group(1)):
          continue
       
      print "[+] Hash: "+str(unquote(filename.group(2)))+"  Filename: "+str(filename.group(1))
    else:
      # downloading attachments
      if not opt_filt == "":
        if not re.search(opt_filt,filename.group(1)):
          continue
      
      if not os.path.exists(casedir):
        os.makedirs(casedir)

      caseatt = str(filename.group(2))+"_"+str(filename.group(1))
      caseatt = re.sub("%3D","",caseatt)
      exists = 0
      if opt_over == 0:
        try:
          save = open(casedir+caseatt,"r")
          save.close()
          exists = 1
        except:
          pass

      if exists == 0:
        att = urllib2.urlopen(urlcm+att)
        
        csize = 0
        try:
          save = open(casedir+caseatt,"w")
          while 1:
            data = att.read(10240)
            csize = csize + len(data)
            print "[+] Downloading "+str(caseatt)+" : "+str(csize/1024)+" Kbytes\r",
            if not data:
              break
            save.write(data)
          save.close()
          print "[+] Download of "+str(caseatt)+" size:"+str(csize/1024)+" Kbytes completed"
        except:
          os.unlink(casedir+caseatt)
          print "[-] error while downloading file: "+str(caseatt)
      else:
        print "[+] File already exists: "+str(caseatt)


#!/usr/bin/python -u

# $Id$

from fcntl import fcntl, F_SETFL 
from os import O_NONBLOCK
from select import select
from struct import pack,unpack 
import socket
import sys

# main data exchnage function
def exchange(s):
  # input:
  # s - socket object
  # return:
  # nothing :)

  # setting every descriptor to be non blocking
  fcntl(s, F_SETFL, O_NONBLOCK)
  fcntl(0, F_SETFL, O_NONBLOCK)

  s_recv = s.recv
  s_send = s.send
  write  = sys.stdout.write
  read   = sys.stdin.read

  while 1:
    toread,[],[] = select([0,s],[],[],30)
    [],towrite,[] = select([],[1,s],[],30)

    if 1 in towrite and s in toread:
      data = s_recv(4096)
      if len(data) == 0:
        s.shutdown(2)
        sys.exit()
      else:
        write(data)

    elif 0 in toread and s in towrite:
      data = read(4096)
      if len(data) == 0:
        sys.exit()
      else:
        s_send(data)

# preparing a socks4 or socks4a connection
def socks4(s,host,port):
  # input:
  # s - socket object
  # host - destination host either IP or a name
  # port - destination port
  # return:
  # 1 - if ready
  # 0 - if needs authentication 

  try:
    data = pack('!2BH',4,1,port)+socket.inet_aton(host)+chr(0)
  except socket.error:
    data = pack('!2BH',4,1,port)+socket.inet_aton('0.0.0.1')+chr(0)+host+chr(0)

  s.send(data)
  data = s.recv(256)
  code = unpack('BBH',data[:4])[1]

  if code == 90:
    return 1 
  else:
    return 0 

# preaparing a socks5 connection
def socks5(s,host,port):
  # input:
  # s - socket object
  # host - destination host either IP or a name
  # port - destination port
  # return:
  # 1 - if ready
  # 0 - if needs authentication 

  data = pack('!3B',5,1,0)
  s.send(data)
  data = s.recv(1024)
  auth = unpack('2B',data)[1]
  if auth != 255:
    nport = pack('!H',port)
    try:
      if ":" in host:
        data = pack('!4B',5,1,0,4)+socket.inet_pton(socket.AF_INET6,host)+nport
      else:
        data = pack('!4B',5,1,0,1)+socket.inet_pton(socket.AF_INET,host)+nport
    except socket.error:
      data = pack('!5B',5,1,0,3,len(host))+host+nport

    s.send(data)
    data = s.recv(256)
    try:
      code = unpack('BBH',data[:4])[1]
    except:
      return 0

    if code == 0:
      return 1 
    else:
      return 0

  else:
    return 0 

#### main stuff
if __name__ == '__main__':

  if len(sys.argv) >= 5: 
    phost = sys.argv[1]
    pport = int(sys.argv[2])
    host  = sys.argv[3]
    port  = int(sys.argv[4])
    if len(sys.argv) == 6:
      ver = int(sys.argv[5])
    else:
      ver = 5

    if ":" in phost and socket.has_ipv6 == True:
      socks = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
    else:
      socks = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    #socks.setsockopt(socket.IPPROTO_TCP, socket.TCP_CORK,1)

    try:
      socks.connect((phost, pport))
    except socket.error:
      sys.stderr.write("[-] problem connecting to "+str(phost)+":"+str(pport)+"\n")
      socks.close()
      sys.exit()  

    sys.stderr.write("[+] connecting via "+str(phost)+":"+str(pport)+" to "+str(host)+":"+str(port)+"\n")

    if (ver == 5 and socks5(socks,host,port) == 1) or (ver == 4 and socks4(socks,host,port) == 1): 
      exchange(socks)
      socks.close()
    else:
      sys.stderr.write("[-] socks server couldn't establish the connection\n")

  else:
    sys.stderr.write("usage: "+sys.argv[0]+" ip_socks port_socks ip_dest port_dest [socks_ver]\n")

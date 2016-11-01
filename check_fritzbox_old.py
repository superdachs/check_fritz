#!/usr/bin/env python

from SOAPpy import SOAPProxy
import sys

host = "192.168.16.1"
port = "49000"


info = []

# addon info
interface = SOAPProxy(proxy='http://%s:%s/igdupnp/control/WANCommonIFC1' % (host, port),
    namespace ='urn:schemas-upnp-org:service:WANCommonInterfaceConfig:1',
    soapaction='urn:schemas-upnp-org:service:WANCommonInterfaceConfig:1#GetAddonInfos',
    noroot=True).GetAddonInfos()
interface = dict((key, getattr(interface, key)) for key in interface._keys())
for key in interface:
    info.append([str(key), interface[key]])

# connection info
interface = SOAPProxy(proxy='http://%s:%s/igdupnp/control/WANIPConn1' % (host, port),
    namespace ='urn:schemas-upnp-org:service:WANIPConnection:1',
    soapaction='urn:schemas-upnp-org:service:WANIPConnection:1#GetStatusInfo',
    noroot=True).GetStatusInfo()
interface = dict((key, getattr(interface, key)) for key in interface._keys())
for key in interface:
    info.append([str(key), interface[key]])

# speed info
interface = SOAPProxy(proxy='http://%s:%s/igdupnp/control/WANCommonIFC1' % (host, port),
    namespace ='urn:schemas-upnp-org:service:WANCommonInterfaceConfig:1',
    soapaction='urn:schemas-upnp-org:service:WANCommonInterfaceConfig:1#GetCommonLinkProperties',
    noroot=True).GetCommonLinkProperties()
interface = dict((key, getattr(interface, key)) for key in interface._keys())
for key in interface:
    info.append([str(key), interface[key]])

connected = False

for item in info:
    if item[0] == 'NewConnectionStatus':
        if item[1] == 'Connected':
            connected = True
    if item[0] == 'NewLayer1DownstreamMaxBitRate':
        downspeed = int(item[1])
    if item[0] == 'NewLayer1UpstreamMaxBitRate':
        upspeed = int(item[1])

if not connected:
    print "CRITICAL - No connection!"
    sys.exit(2)

print "OK - upstream: %sBit/s downstream: %sBit/s|up=%sBit/s;down=%sBit/s" % (upspeed, downspeed, upspeed, downspeed)
sys.exit(0)  

#NewVoipDNSServer1 - 0.0.0.0
#NewDNSServer2 - 217.237.149.205
#NewDNSServer1 - 217.237.149.205
#NewVoipDNSServer2 - 0.0.0.0
#NewIdleDisconnectTime - 0
#NewByteSendRate - 1965
#NewAutoDisconnectTime - 0
#NewTotalBytesSent - 316641367
#NewByteReceiveRate - 984
#NewPacketReceiveRate - 9
#NewRoutedBridgedModeBoth - 0
#NewTotalBytesReceived - 2720493853
#NewPacketSendRate - 16
#NewUpnpControlEnabled - 0
#NewConnectionStatus - Connected
#NewLastConnectionError - ERROR_NONE
#NewUptime - 78728
#NewPhysicalLinkStatus - Up
#NewLayer1DownstreamMaxBitRate - 50000000
#NewWANAccessType - DSL
#NewLayer1UpstreamMaxBitRate - 10000000

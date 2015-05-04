#!/usr/bin/env python

#####################################################
#                                                   #
# Nagios plugin for AVM FRITZ!Box monitoring        #
# (C) 2015 Stefan Kauerauf <mail@stefankauerauf.de> #
#                                                   #
#####################################################

__doc__ = "check_fritzbox.py" 
            

import argparse
import sys
import BeautifulSoup
import urllib

def getInfo(host, port):
    info = []
    desc = urllib.urlopen('http://%s:%s/igddesc.xml' % (host, port)).read()
    soup = BeautifulSoup.BeautifulSoup(desc.decode('utf-8','ignore'))
    devices = soup.root.findAll('device')
    for device in devices:
        services = device.findAll('service')
        for service in services:
            url = service.find('controlurl').string
            xml = service.find('scpdurl').string
            namespace = service.find('servicetype').string
            servicedesc = urllib.urlopen('http://%s:%s%s' % (host, port, xml)).read()
            servicedescsoup = BeautifulSoup.BeautifulSoup(servicedesc.decode('utf-8','ignore'))
            actions = servicedescsoup.findAll('action')
            for action in actions:
                name = action.find('name').string
                if 'Get' in name:
                    values = action.findAll('argument')
                    vals = []
                    for value in values:
                        if value.find('direction').string == 'out':
                            valname = value.find('name').string
                            valvar = value.find('relatedstatevariable').string
                            vals.append({'name' : valname, 'var' : valvar})
                    info.append({'action' : name, 'url' : url, 'namespace' : namespace, 'values' : vals})
    return info



def listActions(host, port):
    print 'available actions:'
    for e in getInfo(host, port):
        print '\t%s' % e['action']
    sys.exit(0)

def listValues(host, port, action):
    print 'available values for %s:' % action
    for e in getInfo(host, port):
        if e['action'] == action:
            for v in e['values']:
                print '\t%s' % v['name']
            sys.exit(0)
    print 'action %s not available' % action
    sys.exit(3)

# configure argument parser
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('-H', '--hostname', required=True, dest='hostname', help='hostname or IP address of the FRITZ!Box')
parser.add_argument('-p', '--port', required=False, dest='port', default='49000', help='port for UPnP SOAP calls')
parser.add_argument('-A', '--action', required=True, dest='action', help='action to gather information, use List for complete overview of supported actions')
parser.add_argument('-v', '--value', dest='value', help='value to check, use List for complete overview of supported values, required for all actions except list')
parser.add_argument('-w', '--warning', dest='warning', help='warning threshold, must be same type of value checked')
parser.add_argument('-c', '--critical', dest='critical', help='critical threshold, must be same type of value checked')

# get arguments

args = parser.parse_args()

# check for list options
if args.action == 'List':
    listActions(args.hostname, args.port)
elif args.value == 'List':
    listValues(args.hostname, args.port, args.action)

# check if value is given
if args.value == None:
    print "ERROR: value for action %s missing" % args.action
    sys.exit(3)


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
from SOAPpy import SOAPProxy

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
parser.add_argument('-u', '--unit', dest='unit', help='Unit for vale (e.g. B/s)', default='')


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

# actual check

info = getInfo(args.hostname, args.port)

action = (item for item in info if item["action"] == args.action).next()

if not action:
    print "ERROR: Action not found!"
    sys.exit(3)

# make the check

def info(host, port, url, ns, action):
    interface = getattr(SOAPProxy(proxy = 'http://%s:%s%s' % (host, port, url),
                            namespace = ns,
                            soapaction = '%s#%s' % (ns, action),
                            noroot=True), str(action))

    ret = ''
    try:
        ret =  interface._keys()[args.value]
    except Exception:
        print "ERROR: Value not found"
        sys.exit(3)

    return ret

def getDataType(val):
    dtype = None
    value = None
    try:
        value = str(val)
        dtype = 'string'
    except:
        pass
    try:
        value = float(val)
        dtype = 'float'
    except:
        pass
    try:
        value = int(val)
        dtype = 'int'
    except:
        pass
    
    if val == '0' or val == 0:
        value = float('0')
        dtype = 'int'
         
    
    if value == None:
        print "ERROR: type of value undefined (int, float, string)"
        sys.exit(3)

    return value, dtype

def getState(value, dtype):
    if dtype == 'string':
        wnot = False
        cnot = False
        wmatch = False
        cmatch = False
        if '!' in args.warning:
            args.warning = args.critical.replace('!', '')
            wnot = True
        if '!' in args.critical:
            args.critical = args.critical.replace('!', '')
            cnot = True
        
        if args.warning == value:
            wmatch = True
        if args.critical == value:
            cmatch = True

        if cmatch and not cnot:
            return 2
        if wmatch and not wnot:
            return 1
        if cmatch and cnot:
            return 0
        if wmatch and wnot:
            return 0

        return 0
    if dtype in ['int', 'float']:
        wneginf = False
        cneginf = False
        winside = False
        cinside = False
        
        # build up the correct range definitions
        
        # check if it is negotioated
        if '~' in args.warning:
            wneginf = True
        if '~' in args.critical:
            cneginf = True

        # check inside
        if '@' in args.warning:
            winside = True
        if '@' in args.critical:
            cinside = True

        # clean thresholds
        args.warning = args.warning.replace('~', '')
        args.warning = args.warning.replace('@', '')
        args.critical = args.critical.replace('~', '')
        args.critical = args.critical.replace('@', '')


        warnmin = None
        warnmax = None
        critmin = None
        critmax = None

        warn = None
        crit = None

        # simple thresholds example: -w 10 -c 20
        if ':' not in args.warning:
            warnmin = float(0)
            warnmax = float(args.warning)
            if not winside:
                if float(value) < warnmin or float(value) > warnmax:
                    warn = True
            else:
                if float(value) > warnmin and float(value) < warnmax:
                    warn = True

        if ':' not in args.critical:
            critmin = float(0)
            critmax = float(args.critical)
            if not cinside:
                if float(value) < critmin or float(value) > critmax:
                    crit = True
            else:
                if float(value) > critmin and float(value) < critmax:
                    crit = True

        # range with positive infinity example: -w 10: -c 20:
        if ':' in args.warning and len(args.warning.split(':')) == 1:
            warnmin = float(args.warning.split(':')[0])
            warnmax = float(value) + 1
            if not winside:
                if float(value) < warnmin or float(value) > warnmax:
                    warn = True
            else:
                if float(value) > warnmin and float(value) < warnmax:
                    warn = True
        if ':' in args.critical and len(args.critical.split(':')) == 1:
            critmin = float(args.critical.split(':')[0])
            critmax = float(value) + 1
            if not cinside:
                if float(value) < critmin or float(value) > critmax:
                    crit = True
            else:
                if float(value) > critmin and float(value) < critmax:
                    crit = True
                    
        # neginf example: -w ~:10 -c ~:5
        if ':' in args.warning and len(args.warning.split(':')) == 1 and wneginf:
            warnmax = float(args.warning.split(':')[0])
            if not winside:
                if float(value) > warnmax:
                    warn = True
            else:
                if float(value) < warnmax:
                    warn = True

        if ':' in args.critical and len(args.critical.split(':')) == 1 and cneginf:
            critmax = float(args.critical.split(':')[0])
            if not cinside:
                if float(value) > critmax:
                    crit = True
            else:
                if float(value) < critmax:
                    crit = True




        # return
        if not warn and not crit:
            return 0
        if warn and not crit:
            return 1
        if crit:
            return 2


        



value = info(args.hostname, args.port, action['url'], action['namespace'], action['action'])

value, dtype = getDataType(value)

state = 0

if args.warning or args.critical:
    state = getState(value, dtype)




out = ''

out = out + args.value + '=' + str(value) + args.unit

if state == 0:
    out = 'OK: ' + out
if state == 1:
    out = 'WARNING: ' + out
if state == 2:
    out = 'CRITICAL: ' + out
if state not in [0,1,2]:
    out = 'UNKNOWN: ' + out

if dtype in ['int', 'float'] and args.warning != None and args.critical != None:
    out = out + '|' + args.value + "=" + str(value) + args.unit + ';' + args.warning + ';' + args.critical

print out
sys.exit(state)

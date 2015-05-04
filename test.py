#!/usr/bin/env python

import urllib
import BeautifulSoup
from SOAPpy import SOAPProxy


hostname = 'fritz.box'
port = '49000'

def info(host, port, ul, ns, action):
    interface = getattr(SOAPProxy(proxy = 'http://%s:%s%s' % (host, port, url),
        namespace = ns,
        soapaction = '%s#%s' % (ns, action),
        noroot=True), str(action))

    print action

    value = ''
    for key in interface._keys():
        value = value + key
    print value        

desc = urllib.urlopen('http://%s:%s/igddesc.xml' % (hostname, port)).read()

soup = BeautifulSoup.BeautifulSoup(desc.decode('utf-8','ignore'))
devices = soup.root.findAll('device')

for device in devices:
    services = device.findAll('service')
    for service in services:
        url = service.find('controlurl').string
        xml = service.find('scpdurl').string
        namespace = service.find('servicetype').string
        servicedesc = urllib.urlopen('http://%s:%s%s' % (hostname, port, xml)).read()


        servicedescsoup = BeautifulSoup.BeautifulSoup(servicedesc.decode('utf-8','ignore'))       
 
        actions = servicedescsoup.findAll('action')
        for action in actions:
            name = action.find('name').string
            if 'Get' in name:
                info(hostname, port, url, namespace, name)
   



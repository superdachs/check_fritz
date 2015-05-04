#!/bin/bash
IP=$1

STATE=STATUS`curl -s "http://$IP:49000/igdupnp/control/WANIPConn1" -H "Content-Type: text/xml; charset="utf-8"" -H "SoapAction:urn:schemas-upnp-org:service:WANIPConnection:1#GetStatusInfo" -d "@connection_state.xml" | sed -n 's/^.*<\(NewConnectionStatus\)>\([^<]*\)<\/.*$/\2/p'`

if [ $STATE == 'STATUSConnected' ]; then
  echo "DSL Connected"
  exit 0
else
  echo "DSL Not Connected"
  exit 2
fi


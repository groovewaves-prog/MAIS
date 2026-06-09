#!/bin/sh
#------------------------------------------------------------------------------
# drive BAO-GW system patlamp in Shinjuku-OC by zabbix server
# usage: Yellow_blink_patolamp.sh <no parameters>
# response: 0(always normal)
#------------------------------------------------------------------------------

#---- define constants ----
PATOLAMP_FILE=/var/lib/baogw/yellow_patolamp_on_howcom

#---- define variables ----
PGNAME=`basename $0 .sh`
PROCID=$$

#---- define functions ----
function putlog_w() {
  logger -p local6.warn -t "${PGNAME}[${PROCID}]" "WARN: ($1) ${LOGMSG}"
}

function putlog_i() {
  logger -p local6.info -t "${PGNAME}[${PROCID}]" "INFO: ($1) ${LOGMSG}"
}

#---- start ----
putlog_i "started"

#---- execute make file ----
# do
  touch ${PATOLAMP_FILE}
#---- end ----
putlog_i "ended"
exit 0

#EOF



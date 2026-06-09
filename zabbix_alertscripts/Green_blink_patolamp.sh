#!/bin/sh
#------------------------------------------------------------------------------
# MAIS sysnormal パトランプ鳴動用shell
# usage: Green_blink_patolamp.sh <arg1>
# response: 0(normal) / 1(error)
# 2026/01/06 remake
#------------------------------------------------------------------------------

#---- define variables ----
PGNAME=`basename "$0" .sh`
PROCID=$$

#---- define functions ----
putlog_w() {
  logger -p local6.warn -t "${PGNAME}[${PROCID}]" "ERROR: ($1) ${LOGMSG}"
}

putlog_i() {
  logger -p local6.info -t "${PGNAME}[${PROCID}]" "INFO: ($1) ${LOGMSG}"
}

#---- argument check ----
if [ -z "$1" ]; then
  LOGMSG="1st argument is not specified."
  putlog_w "ARGCHK"
  exit 1
fi

#---- define constants (with 1st argument) ----
PATOLAMP_FILE="/var/lib/baogw/${1}_green_patolamp_on"

#---- start ----
LOGMSG="started '${1}' Green patolamp on"
putlog_i "START"

#---- execute make file ----
touch "${PATOLAMP_FILE}"
RET=$?
if [ $RET -ne 0 ]; then
  LOGMSG="failed to touch file: ${PATOLAMP_FILE} (rc=${RET})"
  putlog_w "TOUCH"
  exit 1
fi

#---- end ----
LOGMSG="ended '${1}' Green patolamp on"
putlog_i "END"
exit 0

#EOF


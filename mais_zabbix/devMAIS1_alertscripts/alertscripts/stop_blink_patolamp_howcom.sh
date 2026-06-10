#!/bin/sh
#------------------------------------------------------------------------------
# drive BAO-GW system patlamp in Shinjuku-OC by zabbix server and
# gw-scripts.
# usage: stop_blink_patolamp.sh
# response: 0(always normal)
#------------------------------------------------------------------------------

#---- define constants ----
HOWCOM_OLD_PATLAMP_IP=192.168.112.5
HOWCOM_OLD_PATLAMP_USER=root
HOWCOM_OLD_PATLAMP_CMD='ACOP 00000000'

KDDI_MIYAZAKI_PATLAMP_IP=10.136.173.190
KDDI_MIYAZAKI_PATLAMP_USER=root
KDDI_MIYAZAKI_PATLAMP_CMD='ACOP 00000000'

if [ -e /var/lib/baogw/howcom_old ]; then
    #---- stop howcom_old_patlamp ----
    /usr/bin/rsh ${HOWCOM_OLD_PATLAMP_IP} -l ${HOWCOM_OLD_PATLAMP_USER} ${HOWCOM_OLD_PATLAMP_CMD}
fi
if [ -e /var/lib/baogw/Kddi_Miyazaki ]; then
    #---- stop Kddi_Miyazaki_patlamp ----
    /usr/bin/rsh ${KDDI_MIYAZAKI_PATLAMP_IP} -l ${KDDI_MIYAZAKI_PATLAMP_USER} ${KDDI_MIYAZAKI_PATLAMP_CMD}
fi
exit 0
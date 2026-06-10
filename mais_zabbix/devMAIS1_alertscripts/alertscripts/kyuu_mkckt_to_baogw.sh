#!/bin/bash

#----------------------------------------------------------------
# プログラム名  :       mkckt_to_baogw.sh
#----------------------------------------------------------------
# 処理概要      :   BAO-GW用syslog出力 アラート発生時
#----------------------------------------------------------------

# --- 環境定義 ---#
#{ALERT.SENDTO}=$1
#{ALERT.SUBJECT}=$2
#{ALERT.MESSAGE}=$3
#{EVENT.DATE}@{EVENT.TIME}=$2
#{HOST.NAME}@!!!@{{TRIGGER.NAME}@!!!@{ITEM.VALUE}=$3

DLM1="@!!!@"
DLM2="@"
ALERT_TIME=$2
ALERT_TIME=${ALERT_TIME//@/ }
ALERT_TIME=`echo ${ALERT_TIME} | sed s/\\\./-/g`
ALERT_TIME_JST=`date -d "${ALERT_TIME}" +"%Y-%m-%d %H:%M:%S"`
ALERT_TIME_JST=${ALERT_TIME_JST// /@}
ALERT_TIME_JST_MIRI_SEC=`date -u +".%3N"`
HOST_NAME_TRIGGER_NAME_ITEM_VALUE=$3
TRIGGER_STATUS=error
SUMMARY=
DEVICE_NAME=ptk-zabbix-east

# --- write syslog --- #
LOG_MSG=$DLM1$ALERT_TIME_JST$ALERT_TIME_JST_MIRI_SEC$DLM1$HOST_NAME_TRIGGER_NAME_ITEM_VALUE$DLM1$TRIGGER_STATUS$DLM1$SUMMARY$DLM1$DEVICE_NAME$DLM1
echo ${LOG_MSG} >> /tmp/abc

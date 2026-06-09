#!/bin/bash

#----------------------------------------------------------------
# プログラム名  :       mkckt_to_baogw.sh
#----------------------------------------------------------------
# 処理概要      :   BAO-GW用syslog出力 アラート発生時
#----------------------------------------------------------------

# --- 冗長設定 ---#
# ha.txtを読み込めないときにリトライする回数
RETRYCOUNT=5

# 0=active, 1=slave
# 0ならばbreakして次の処理へ、1ならば実行終了、それ以外は10秒待ってリトライ
# 5回待ってもファイルの値が0,1以外または読み込めない場合は、通知スクリプトを実行
for i in `seq 1 $RETRYCOUNT`
do
  if [ `cat /usr/lib/zabbix/alertscripts/ha.txt` -eq 1 ]; then
    exit 0
  elif [ `cat /usr/lib/zabbix/alertscripts/ha.txt` -eq 0 ]; then
    break
  else
    sleep 10
  fi
done

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
TRIGGER_STATUS=error
TRIGGER_STATUS_NORMAL=normal
SUMMARY=
DEVICE_NAME=ptk-zabbix-west

# --- アラーム名・トリガー名による条件分岐 ---#
#アラーム名「apConnectionLost」or「apConnected」、トリガー名「snmptrap.fallback_AP」に
#マッチしたら変数を分解してパラメータを入れ替え

HOSTNAME_TRIGGERNAME_ITEMVALUE=$3

if [ "`echo ${HOSTNAME_TRIGGERNAME_ITEMVALUE} | grep 'snmptrap.fallback_AP' | grep 'apConnectionLost'`" ]; then
  HOST_NAME=`echo $HOSTNAME_TRIGGERNAME_ITEMVALUE | awk '{print $11}'`
  HOSTNAME_TRIGGERNAME_ITEMVALUE=${HOSTNAME_TRIGGERNAME_ITEMVALUE// /_}
  HOSTNAME_TRIGGERNAME_ITEMVALUE=( `echo $HOSTNAME_TRIGGERNAME_ITEMVALUE | tr -s '@!!!@' ' '`)
  ITEM_VALUE=${HOSTNAME_TRIGGERNAME_ITEMVALUE[2]}_${HOSTNAME_TRIGGERNAME_ITEMVALUE[0]}
  ALERT_MESSAGE=${HOST_NAME}@!!!@${HOSTNAME_TRIGGERNAME_ITEMVALUE[1]}@!!!@${ITEM_VALUE}
  LOG_MSG=$DLM1$ALERT_TIME_JST$ALERT_TIME_JST_MIRI_SEC$DLM1$ALERT_MESSAGE$DLM1$TRIGGER_STATUS$DLM1$SUMMARY$DLM1$DEVICE_NAME$DLM1
  echo ${LOG_MSG} >> /tmp/testlog
  #logger -t to_bao-gw  ${LOG_MSG}
elif [ "`echo ${HOSTNAME_TRIGGERNAME_ITEMVALUE} | grep 'snmptrap.fallback_AP' | grep 'apConnected'`" ]; then
  HOST_NAME=`echo $HOSTNAME_TRIGGERNAME_ITEMVALUE | awk '{print $11}'`
  HOSTNAME_TRIGGERNAME_ITEMVALUE=${HOSTNAME_TRIGGERNAME_ITEMVALUE// /_}
  HOSTNAME_TRIGGERNAME_ITEMVALUE=( `echo $HOSTNAME_TRIGGERNAME_ITEMVALUE | tr -s '@!!!@' ' '`)
  ITEM_VALUE=${HOSTNAME_TRIGGERNAME_ITEMVALUE[2]}_${HOSTNAME_TRIGGERNAME_ITEMVALUE[0]}
  ALERT_MESSAGE=${HOST_NAME}@!!!@${HOSTNAME_TRIGGERNAME_ITEMVALUE[1]}@!!!@${ITEM_VALUE}
  LOG_MSG=$DLM1$ALERT_TIME_JST$ALERT_TIME_JST_MIRI_SEC$DLM1$ALERT_MESSAGE$DLM1$TRIGGER_STATUS_NORMAL$DLM1$SUMMARY$DLM1$DEVICE_NAME$DLM1
  echo ${LOG_MSG} >> /tmp/testlog
  #logger -t to_bao-gw  ${LOG_MSG}
else
  LOG_MSG=$DLM1$ALERT_TIME_JST$ALERT_TIME_JST_MIRI_SEC$DLM1$HOSTNAME_TRIGGERNAME_ITEMVALUE$DLM1$TRIGGER_STATUS$DLM1$SUMMARY$DLM1$DEVICE_NAME$DLM1
  echo ${LOG_MSG} >> /tmp/testlog
  #logger -t to_bao-gw  ${LOG_MSG}
fi

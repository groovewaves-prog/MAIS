#!/bin/bash
#itosbaosoap.sh

## 必要変数セット
LOGFILE="/var/log/gwscripts/gwscripts.log"
ZabScPath="/usr/lib/zabbix/alertscripts/"
SendDir="${ZabScPath}baosoap/send/"
SendXML="${ZabScPath}baosoap/send/itosbaosoap.xml"
ResDir="${ZabScPath}baosoap/res/"
ResXML="${ZabScPath}baosoap/res/itosbaosoap_res.xml"
OrgXML="${ZabScPath}baosoap/org/itosbaosoap_org.xml"
SoapResult="${ZabScPath}baosoap/res/itosbaosoap_result"
PytoshParam="${ZabScPath}baosoap/param.txt"
OldXML="/var/log/gwscripts/baosoap-oldxml"
OldParam="/var/log/gwscripts/baosoap-oldparam"
OldRes="/var/log/gwscripts/baosoap-oldres"
Delimiter="@!!!@"
PID=`pgrep itosbaosoap.sh`

## 試験用 送信先
## BAO_1="itlbaodv1"
## BAO_2="itlbaodv2"
## 本番用 送信先
BAO_1="kisysbao1.kisys.local"
BAO_2="kisysbao2.kisys.local"

## junnbi 
logger -p local6.info -t itosbaosoap.sh[$PID] "INFO: itosbaosoap.sh start"
echo "--------------------------------" | stdbuf -oL /usr/bin/gawk '{print strftime("%Y/%m/%d %H:%M:%S"), $0; }' >> "${OldRes}"
cat "${ResXML}" >> "${OldRes}" 2>&1
cat "${SoapResult}" >> "${OldRes}" 2>&1
rm -rf "${ResXML}" 2>&1
rm -rf "${SoapResult}" 2>&1
cp ${OrgXML} ${SendXML}

## SOAPパラメータセット
value_incidentid=`cat ${PytoshParam} | /usr/bin/awk -F '@!!!@' '{print $1}'`
value_company=`cat ${PytoshParam} | /usr/bin/awk -F '@!!!@' '{print $2}'`
value_lastname=`cat ${PytoshParam} | /usr/bin/awk -F '@!!!@' '{print $3}'`
value_summary=`cat ${PytoshParam} | /usr/bin/awk -F '@!!!@' '{print $4}'`
value_ci=`cat ${PytoshParam} | /usr/bin/awk -F '@!!!@' '{print $5}'`
value_serviceci=`cat ${PytoshParam} | /usr/bin/awk -F '@!!!@' '{print $6}'`
value_occurrence=`cat ${PytoshParam} | /usr/bin/awk -F '@!!!@' '{print $7}'`
value_restore=`cat ${PytoshParam} | /usr/bin/awk -F '@!!!@' '{print $8}'`
value_status=`cat ${PytoshParam} | /usr/bin/awk -F '@!!!@' '{print $9}'`
value_resolution=`cat ${PytoshParam} | /usr/bin/awk -F '@!!!@' '{print $10}'`
value_internalalarmid=`cat ${PytoshParam} | /usr/bin/awk -F '@!!!@' '{print $11}'`
value_worklog_category=`cat ${PytoshParam} | /usr/bin/awk -F '@!!!@' '{print $12}'`
value_worklog_notes=`cat ${PytoshParam} | /usr/bin/awk -F '@!!!@' '{print $13}'`
value_worklog_date=`cat ${PytoshParam} | /usr/bin/awk -F '@!!!@' '{print $14}'`

## 送信XML作成（）SendXML
/bin/sed -i "s/#value_incidentid#/${value_incidentid}/g" ${SendXML}
/bin/sed -i "s/#value_company#/${value_company}/g" ${SendXML}
/bin/sed -i "s/#value_lastname#/${value_lastname}/g" ${SendXML}
/bin/sed -i "s/#value_summary#/${value_summary}/g" ${SendXML}
/bin/sed -i "s/#value_ci#/${value_ci}/g" ${SendXML}
/bin/sed -i "s/#value_serviceci#/${value_serviceci}/g" ${SendXML}
/bin/sed -i "s/#value_occurrence#/${value_occurrence}/g" ${SendXML}
/bin/sed -i "s/#value_restore#/${value_restore}/g" ${SendXML}
/bin/sed -i "s/#value_status#/${value_status}/g" ${SendXML}
/bin/sed -i "s/#value_resolution#/${value_resolution}/g" ${SendXML}
/bin/sed -i "s/#value_internalalarmid#/${value_internalalarmid}/g" ${SendXML}
/bin/sed -i "s/#value_worklog_category#/${value_worklog_category}/g" ${SendXML}
/bin/sed -i "s/#value_worklog_notes#/${value_worklog_notes}/g" ${SendXML}
/bin/sed -i "s/#value_worklog_date#/${value_worklog_date}/g" ${SendXML}

## XML送信
aaa=1 # 0:OFF 1:ON
if [ $aaa -eq 1 ]; then
    wget --connect-timeout=1 --timeout=300 -t 1 \
    --post-file=${SendXML} --header="Content-Type: text/xml" --header="SOAPAction: \
    \"executeProcess\"" http://${BAO_1}:28080/baocdp/orca -O ${ResXML}
    result=$?
    if [ $result = 0 ]; then
        logger -p local6.info -t itosbaosoap.sh[$PID] "INFO: BAO1号機への送信に成功しました。"
        echo `cat ${ResXML} | /usr/bin/awk -F 'result xmlns' '{print $2}' | /usr/bin/awk -F '>' '{print $2}' | /usr/bin/awk -F '<' '{print $1}'` > ${SoapResult}
    else
        logger -p local6.info -t itosbaosoap.sh[$PID] "INFO: BAO1号機への送信に失敗しました。"
        wget --connect-timeout=1 --timeout=300 -t 1 \
        --post-file=${SendXML} --header="Content-Type: text/xml" --header="SOAPAction: \
        \"executeProcess\"" http://${BAO_2}:28080/baocdp/orca -O ${ResXML}
        result2=$?
        if [ $result2 = 0 ]; then
            logger -p local6.info -t itosbaosoap.sh[$PID] "INFO: BAO2号機への送信に成功しました。"
            echo `cat ${ResXML} | /usr/bin/awk -F 'result xmlns' '{print $2}' | /usr/bin/awk -F '>' '{print $2}' | /usr/bin/awk -F '<' '{print $1}'` > ${SoapResult}
        else
            logger -p local6.err -t itosbaosoap.sh[$PID] "ERROR: BAO2号機への送信に失敗しました。"
            echo "下記のXMLファイル送信に失敗しています。" | stdbuf -oL /usr/bin/gawk '{print strftime("%Y/%m/%d %H:%M:%S"), $0; }' >> ${OldXML}
            echo "下記Paramを利用したXMLファイル送信に失敗しています。" | stdbuf -oL /usr/bin/gawk '{print strftime("%Y/%m/%d %H:%M:%S"), $0; }' >> ${OldParam}
        fi
    fi
fi
## XML送信ここまで

## 終了処理
echo "--------------------------------" | stdbuf -oL /usr/bin/gawk '{print strftime("%Y/%m/%d %H:%M:%S"), $0; }' >> "${OldXML}"
cat "${SendXML}" >> "${OldXML}" 2>&1
#rm -rf "${SendXML}" 2>&1

echo "--------------------------------" | stdbuf -oL /usr/bin/gawk '{print strftime("%Y/%m/%d %H:%M:%S"), $0; }' >> "${OldParam}"
cat "${PytoshParam}" >> "${OldParam}" 2>&1
#rm -f "${PytoshParam}" 2>&1

exit 0

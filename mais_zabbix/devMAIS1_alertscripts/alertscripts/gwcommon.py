#--------------------------------------------------------------------
# Common Configuration for GW Scripts (v1.4)
#
# Author:K.Ohshiba
#--------------------------------------------------------------------
# Modified
# 170729 K.Ohshiba 1st version
# 170810 Update by T.Hasegawa
# 170925 Update by H.OOZERA
# 171228 S-In version by K.Ohshiba
# 180215 Update by K.YAMADATE
# 180405 Update by K.YAMADATE
# 180725 Update by K.YAMADATE
# 190618 Update by M.SHIBUYA

# --- import ----
from datetime import timedelta
import logging

# --- zabbix server id ---
DETECTED_HOST01 = '162'
DETECTED_HOST02 = '165'

# --- BAOGW ip address ---
BAOGW01_IP = '10.136.162.170'
BAOGW02_IP = '10.136.165.170'

# --- internal id ---
INTERNAL_ID01 = 'ITOS_01_'
INTERNAL_ID02 = 'ITOS_02_'

# --- gateway delimiter ---
GW_DELIMITER = '@!!!@'

# --- syslog severity ---
LOG_EMERG = 'EMERG'
LOG_ALERT = 'ALERT'
LOG_CRIT = 'CRITICAL'
LOG_ERR = 'ERROR'
LOG_WARNIG = 'WARNIG'
LOG_NOTICE = 'NOTICE'
LOG_INFO = 'INFO'
LOG_DEBUG = 'DEBUG'

# --- setting LOGGER LEVEL ---
LOGGER_LEVEL_INSERT_GW_EVENTS = logging.INFO
LOGGER_LEVEL_INSERT_SYS_EVENTS = logging.INFO
LOGGER_LEVEL_SEND_TO_BAO = logging.INFO
LOGGER_LEVEL_RESCUE_GW_EVENTS = logging.INFO
LOGGER_LEVEL_EXEC_PATOLAMP = logging.INFO
LOGGER_LEVEL_DB_HOUSEKEEPING = logging.INFO
LOGGER_LEVEL_GW_FUNCTION = logging.INFO

# --- mysql client ---
MY_HOST = 'localhost'
MY_USER = 'gwuser'
MY_PASSWD = '2017B@0gw'
MY_DB = 'baogw'
MY_CHRSET = 'utf8'
MY_UNIX_SOCKET = '/db/mysql/mysql.sock'
# --- mysql client zabbix ---
MY_USER_ZABBIX = 'zabbix'
MY_PASSWD_ZABBIX = 'baogw!mysql'
MY_DB_ZABBIX = 'zabbix'
# --- zabbix api ---
ZABBIX_IP = 'localhost'
ZABBIX_USER = 'Admin'
ZABBIX_PASSWD = 'zabbix'

# --- gw event status ---
GW_EVENT_STATUS_NEW = '0'
GW_EVENT_STATUS_ACTIVE = '1'
GW_EVENT_STATUS_CLOSE = '2'
GW_EVENT_STATUS_DUP = '99'

# --- gw alarm status ---
GW_ALARM_STATUS_ERROR = "error"
GW_ALARM_STATUS_NORMAL = "normal"
GW_ALARM_STATUS_INFO = "info"
GW_ALARM_STATUS_SEC = "sec"
GW_ALARM_STATUS_SYSERROR = "syserror"
GW_ALARM_STATUS_SYSNORMAL = "sysnormal"

# --- gw incident status ---
GW_INCIDENT_STATUS_ACTIVE = '1'
GW_INCIDENT_STATUS_CLOSE = '2'

# --- kisys status ---
GW_KISYS_STATUS_NEW_OK = '0'
GW_KISYS_STATUS_NEW_NG = '1'
GW_KISYS_STATUS_NEW_NORES = '2'
GW_KISYS_STATUS_UPDATE_OK = '0'
GW_KISYS_STATUS_UPDATE_NG = '1'
GW_KISYS_STATUS_UPDATE_NORES = '2'
GW_KISYS_STATUS_KISYS_CONNECT_NORULE = '9'
GW_KISYS_STATUS_NOSEND = '10'
GW_KISYS_STATUS_NOPATOLAMP = '20'
GW_KISYS_STATUS_WAITING_5 = '30'
GW_KISYS_STATUS_WAITING_10 = '31'
GW_KISYS_STATUS_WAITING_15 = '32'
GW_KISYS_STATUS_WAITING_20 = '33'
GW_KISYS_STATUS_WAITING_25 = '34'
GW_KISYS_STATUS_WAITING_30 = '35'
# GW_KISYS_STATUS_RECOVERY = '40'
GW_KISYS_STATUS_CANCEL_OK = '40'
GW_KISYS_STATUS_CANCEL_NG = '41'
GW_KISYS_STATUS_CANCEL_NORES = '42'
GW_KISYS_STATUS_CANCEL_NOSEND = '43'
GW_KISYS_STATUS_KISYS_CONNECT_CANCEL = '49'
GW_KISYS_STATUS_NORECOVERY_OK = '50'
GW_KISYS_STATUS_NORECOVERY_NG = '51'
GW_KISYS_STATUS_NORECOVERY_NORES = '52'
GW_KISYS_STATUS_NORECOVERY_NOSEND = '53'
GW_KISYS_STATUS_KISYS_CONNECT_NORECOVERY = '59'
GW_KISYS_STATUS_NOSEND_OK = '60'
GW_KISYS_STATUS_NOSEND_NG = '61'
GW_KISYS_STATUS_NOSEND_NORES = '62'
GW_KISYS_STATUS_NOSEND_MANUAL = '69'
GW_KISYS_STATUS_NOPATOLAMP_OK = '70'
GW_KISYS_STATUS_NOPATOLAMP_NG = '71'
GW_KISYS_STATUS_NOPATOLAMP_NORES = '72'
GW_KISYS_STATUS_NOPATOLAMP_MANUAL = '79'
GW_KISYS_STATUS_MAINTENANCE = '90'
GW_KISYS_STATUS_NOSEND_BY_HOSTGROUP = '100'
GW_KISYS_STATUS_NOSEND_LIST = [
    GW_KISYS_STATUS_NOSEND,
    GW_KISYS_STATUS_NOPATOLAMP
]
GW_KISYS_STATUS_WAITING_LIST = [
    GW_KISYS_STATUS_WAITING_5,
    GW_KISYS_STATUS_WAITING_10,
    GW_KISYS_STATUS_WAITING_15,
    GW_KISYS_STATUS_WAITING_20,
    GW_KISYS_STATUS_WAITING_25,
    GW_KISYS_STATUS_WAITING_30
]
GW_KISYS_STATUS_CANCEL_LIST = [
    GW_KISYS_STATUS_CANCEL_OK,
    GW_KISYS_STATUS_CANCEL_NG,
    GW_KISYS_STATUS_CANCEL_NORES,
    GW_KISYS_STATUS_CANCEL_NOSEND
]
GW_KISYS_STATUS_NOSEND_BY_HOSTGROUP_LIST = [
    GW_KISYS_STATUS_NOSEND_BY_HOSTGROUP,
    GW_KISYS_STATUS_UPDATE_NG,
    GW_KISYS_STATUS_UPDATE_NORES
]

# --- gw rule status ---
GW_RULE_STATUS_DISABLE = '0'
GW_RULE_STATUS_ENABLE = '1'

# --- gw rule set ---
GW_RULE_SET_NEW = '1'
GW_RULE_SET_UPDATE = '2'

# --- gw rule action ---
GW_RULE_ACTION_STOP = ""
GW_RULE_ACTION_NEW_NOSOAP = '100'
GW_RULE_ACTION_UPDATE_NOSOAP = '200'
GW_RULE_ACTION_UPDATE_SOAP = '201'
GW_RULE_ACTION_UPDATE_SOAP_CC = '202'

# --- BAO interface for ITOS constant value ---
SOAP_VALUE_SUMMARY = "[TBL]"
SOAP_VALUE_SERVICECI = "ITアウトソースSOL"
SOAP_VALUE_SUPPORTGROUP = "ITOS-SYSOPE"
SOAP_VALUE_ASSIGNEE = "ITOS-OPE-AUTO"
SOAP_VALUE_WORKLOG_TEMPLATE = "--"
SOAP_VALUE_WORKLOG_SUMMARY = "■アラーム検知"
SOAP_VALUE_WORKLOG_SUMMARY_NEW = "■アラーム検知"
SOAP_VALUE_WORKLOG_SUMMARY_UPDATE = "■アラーム復旧検知"
SOAP_VALUE_WORKLOG_ASSIGNED_GROUP = "ITOS-SYSOPE"
SOAP_VALUE_WORKLOG_OPERATOR = "itos_zabbix"

# --- BAO interface for ITOS value status ---
SOAP_VALUE_STATUS_STOP = '0'
SOAP_VALUE_STATUS_NEW = '1'
SOAP_VALUE_STATUS_UPDATE = '2'
SOAP_VALUE_STATUS_CLOSE = '5'
SOAP_VALUE_STATUS_CANCEL = '6'

# --- BAO interface for ITOS value resolution ---
SOAP_VALUE_RESOLUTION = "・現象: &#xD;&#xA;・原因: &#xD;&#xA;・対処: &#xD;&#xA;・結果: &#xD;&#xA;"
SOAP_VALUE_RESOLUTION_UPDATE = ""

# --- BAO interface for ITOS value worklog category ---
SOAP_VALUE_WORKLOG_CATEGORY_NEW = "010_アラーム発生検知（初回）※CP"
SOAP_VALUE_WORKLOG_CATEGORY_UPDATE = "015_アラーム復旧検知（初回）※CP"
SOAP_VALUE_WORKLOG_CATEGORY_CANSELL = "015_アラーム復旧検知（初回）※CP"
SOAP_VALUE_WORKLOG_CATEGORY_CLOSE = ""

# --- patolamp control parameters ---
PATO_INTERVAL = 5
PATLAMP_USER = 'root'
RED_PATOLAMP_FILE = 'red_patolamp_on'
YELLOW_PATOLAMP_FILE = 'yellow_patolamp_on'
GREEN_PATOLAMP_FILE = 'green_patolamp_on'

# --- patolamp control parameters for floor-11th ---
FLOOR_11TH_HOSTGROUP = '新宿11階パトランプ';
#PATLAMP_IP = '10.128.1.10'
PATLAMP_IP = '127.0.0.1'
RED_PATOLAMP_PATTERN = '20020000'
YELLOW_PATOLAMP_PATTERN = '02020000'
GREEN_PATOLAMP_PATTERN = '00230000'

# --- patolamp control parameters for floor-12th ---
FLOOR_12TH_HOSTGROUP = '新宿12階パトランプ';
FLOOR_12TH = 'floor_12th'
#FLOOR_12TH_PATLAMP_IP = '10.128.1.36'
FLOOR_12TH_PATLAMP_IP = '127.0.0.1'
RED_PATOLAMP_PATTERN_FLOOR_12TH = '20020000'
YELLOW_PATOLAMP_PATTERN_FLOOR_12TH = '02020000'
GREEN_PATOLAMP_PATTERN_FLOOR_12TH = '00230000'

# --- patolamp control parameters for howcom ---
HOWCOM_HOSTGROUP = 'ハウコム運用顧客';
HOWCOM = 'howcom'
HOWCOM_OLD = 'howcom_old'
#HOWCOM_PATLAMP_IP = '192.168.112.5'
HOWCOM_PATLAMP_IP = '127.0.0.1'
RED_PATOLAMP_PATTERN_HOWCOM = '20020000'
YELLOW_PATOLAMP_PATTERN_HOWCOM = '02020000'
GREEN_PATOLAMP_PATTERN_HOWCOM = '00230000'

# --- patolamp control parameters for kddi_miyazaki ---
KDDI_MIYAZAKI = 'Kddi_Miyazaki'
#KDDI_MIYAZAKI_PATLAMP_IP = '10.136.173.190'
KDDI_MIYAZAKI_PATLAMP_IP = '127.0.0.1'

# --- patolamp control parameters for vip ---
VIP_HOSTGROUP = 'VIP顧客';
VIP = 'vip'
VIP_PATLAMP_IP = PATLAMP_IP
RED_PATOLAMP_PATTERN_VIP = '20020000'
YELLOW_PATOLAMP_PATTERN_VIP = '02020000'
GREEN_PATOLAMP_PATTERN_VIP = '00230000'

# --- resucue control parameters ---
RESCUE_INTERVAL = 10

# --- db delete control parameters ---
GW_RETENTION_PERIOD = 420

# --- 構築時用パラメータ ---- #
DETECTED_HOST = DETECTED_HOST01
#DETECTED_HOST = DETECTED_HOST02
#REMOTE_HOST = BAOGW01_IP
REMOTE_HOST = BAOGW02_IP
INTERNAL_ID = INTERNAL_ID01
#INTERNAL_ID = INTERNAL_ID02

# --- file path ---
ORG_XML = "/usr/lib/zabbix/alertscripts/baosoap/org/itosbaosoap_org.xml"
SEND_XML = "/usr/lib/zabbix/alertscripts/baosoap/send/itosbaosoap.xml"
PARAM_TEXT = "/usr/lib/zabbix/alertscripts/baosoap/param.txt"
RES = "/usr/lib/zabbix/alertscripts/baosoap/res/itosbaosoap_result"
RES_XML = "/usr/lib/zabbix/alertscripts/baosoap/res/itosbaosoap_res.xml"
OLD_RES = "/var/log/gwscripts/baosoap-oldres"
OLD_XML = "/var/log/gwscripts/baosoap-oldxml"
OLD_PARAM = "/var/log/gwscripts/baosoap-oldparam"

# --- BAO ip address for test ---
BAO_1 = "itlbaodv1"
BAO_2 = "itlbaodv2"
# --- BAO ip address ---
# BAO_1 = "kisysbao1.kisys.local"
# BAO_2 = "kisysbao2.kisys.local"

# --- BAO TM ip address ----
WEB_API_BASE_URL = "http://%s/api/simulator"
KISYS_TM_PRIMARY_SERVER_IP_ADDRESS = '127.0.0.1'
KISYS_TM_SECONDARY_SERVER_IP_ADDRESS = '127.0.0.1'

# ---- file path ---
BAO_REQUEST_PARAMETER_BASE_XML = '/usr/lib/zabbix/alertscripts/source/itosbaosoap_org.xml'

# --- wget command ---
WGET_CMD = "wget \
           --connect-timeout=1 \
           --timeout=300 -t 1 \
           --post-file=%s \
           --header=\"Content-Type: text/xml\" \
           --header=\"SOAPAction: \\\"executeProcess\\\"\" \
           http://%s:28080/baocdp/orca \
           -O %s"
WGET_CMD_BAO1 = WGET_CMD % (SEND_XML, BAO_1, RES_XML)
WGET_CMD_BAO2 = WGET_CMD % (SEND_XML, BAO_2, RES_XML)

# --- Kompira info ---
KOMPIRA_URL = "https://kompira/home/itos_ope/app/AlarmPortal/Channels/Alert.send"
KOMPIRA_TOKEN = "31ae725ec93e98c3f67c65e22e110f2a78b1ea0a"

KOMPIRA_STATUS_SUCCESS = '0'
KOMPIRA_STATUS_FAILURE = '1'
KOMPIRA_STATUS_NOSEND = '80'

KOMPIRA_RELATION_HOSTGROUP = 'Kompira連携顧客';

# --- K-ISYS info ---
KISYS_RELATION_HOSTGROUP = 'K-ISYS連携顧客';

# --- log delimiter ---
LOG_DELIMITER = " --------------------------------\n"

# --- Action message ---
ACTION_MESSAGE = { \
'10':'K-ISYS起票しません', \
'20':'K-ISYS起票とパトランプ鳴動しません', \
'30':'キャンセル待ちします(5分)', \
'31':'キャンセル待ちします(10分)', \
'32':'キャンセル待ちします(15分)', \
'33':'キャンセル待ちします(20分)', \
'34':'キャンセル待ちします(25分)', \
'35':'キャンセル待ちします(30分)', \
}

# --- Waiting time ---
WAITING_TIME = { \
'30':timedelta(minutes=5), \
'31':timedelta(minutes=10), \
'32':timedelta(minutes=15), \
'33':timedelta(minutes=20), \
'34':timedelta(minutes=25), \
'35':timedelta(minutes=30), \
}

# --- BAO-GW Fomart Error Message ---
#insert_gw_event処理のフォーマットエラー時のBAO-GW DB登録固定値
FORMAT_ERROR_MESSAGE = "受信項目数が不正です。"
BAO_FORMAT_ERROR_HOST = "CheckCustomerMonitoringServer"
BAO_FORMAT_ERROR_ALARM = "個別監視の画面を確認して下さい。"
BAO_FORMAT_ERROR_DEVICE = "顧客情報を確認して下さい。"

# EOF

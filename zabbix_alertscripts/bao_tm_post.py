import xml.etree.ElementTree as ET
import datetime
import time
import os
import logging
import logging.handlers
import urllib.request
import traceback
import gwcommon as COM
import gwfunction as FUNC

SCRIPT_FILE = os.path.basename(__file__)

""" log出力設定 ※rsyslogd に渡す設定 """
LOGGER = logging.getLogger(SCRIPT_FILE)
#LOGGER.setLevel(logging.INFO) # 出力レベルの設定
LOGGER.setLevel(COM.LOGGER_LEVEL_SEND_TO_BAO) # 出力レベルの設定
HANDLER = logging.handlers.SysLogHandler(address=('localhost', 514), facility='local6') # 出力先の設定
FORMATTER = logging.Formatter('%(name)s[%(process)d]: %(levelname)s: [%(lineno)d]%(message)s')
HANDLER.formatter = FORMATTER
LOGGER.addHandler(HANDLER)

class BAO_TM_CLIENT_HELPER:
    VALUE_SYSTEM = 'value_system'
    VALUE_CONTACTMAIL = 'value_contactmail'
    VALUE_CONTACTTEL = 'value_contacttel'
    VALUE_SUBMIT_MODE = 'value_submit_mode'
    VALUE_GID_ID = 'value_GID_ID'
    VALUE_INCIDENTID = 'value_incidentid'
    VALUE_COMPANY = 'value_company'
    VALUE_LASTNAME = 'value_lastname'
    VALUE_FIRSTNAME = 'value_firstname'
    VALUE_MIDDLENAME = 'value_middlename'
    VALUE_SUPPORTGROUP = 'value_supportgroup'
    VALUE_ASSIGNEE = 'value_assignee'
    VALUE_SUMMARY = 'value_summary'
    VALUE_CI = 'value_ci'
    VALUE_SERVICECI = 'value_serviceci'
    VALUE_OCCURRENCE = 'value_occurrence'
    VALUE_RESTORE = 'value_restore'
    VALUE_STATUS = 'value_status'
    VALUE_RESOLUTION = 'value_resolution'
    VALUE_INTERNALALARMID = 'value_internalalarmid'
    VALUE_WORKLOG_TEMPLATE = 'value_worklog_template'
    VALUE_WORKLOG_ASSIGNED_GROUP = 'value_worklog_assigned_group'
    VALUE_WORKLOG_OPERATOR = 'value_worklog_operator'
    VALUE_WORKLOG_GID_ID = 'value_worklog_GID_ID'
    VALUE_WORKLOG_CATEGORY = 'value_worklog_category'
    VALUE_WORKLOG_NOTES = 'value_worklog_notes'
    VALUE_WORKLOG_DATE = 'value_worklog_date'
    VALUE_WORKLOG_SUMMARY = 'value_worklog_summary'

    # --- BAO interface for ITOS constant value ---
    SOAP_VALUE_SUMMARY = "[TBL]"
    SOAP_VALUE_SERVICECI = "ITアウトソースSOL"
    SOAP_VALUE_SUPPORTGROUP = "ITOS-SYSOPE"
    SOAP_VALUE_ASSIGNEE = "ITOS-OPE-AUTO"
    SOAP_VALUE_WORKLOG_TEMPLATE = "--"
    SOAP_VALUE_WORKLOG_SUMMARY_NEW = "■アラーム検知"
    SOAP_VALUE_WORKLOG_SUMMARY_UPDATE = "■アラーム復旧検知"
    SOAP_VALUE_WORKLOG_ASSIGNED_GROUP = "ITOS-SYSOPE"
    SOAP_VALUE_WORKLOG_OPERATOR = "itos_zabbix"
    SOAP_VALUE_WORKLOG_CATEGORY_NEW = "010_アラーム発生検知（初回）※CP"
    SOAP_VALUE_WORKLOG_CATEGORY_UPDATE = "015_アラーム復旧検知（初回）※CP"

    SOAP_VALUE_STATUS_NEW = '0'
    SOAP_VALUE_STATUS_UPDATE = '2'

    SOAP_VALUE_SYSTEM = 'ITOS_BAO-GW'
    SOAP_VALUE_CONTACTMAIL = ''
    SOAP_CONTACTTEL = ''
    SOAP_VALUE_GID_ID = '173'

    # --- BAO interface for ITOS value resolution ---
    SOAP_VALUE_RESOLUTION = "・現象: &#xD;&#xA;・原因: &#xD;&#xA;・対処: &#xD;&#xA;・結果: &#xD;&#xA;"
    SOAP_VALUE_RESOLUTION_UPDATE = ""

    @staticmethod
    def make_xml(wk_hash):
        #self = BAO_TM_CLIENT_HELPER()
        orgxml = open(COM.BAO_REQUEST_PARAMETER_BASE_XML, 'r', encoding='utf-8')
        text = orgxml.read()
        orgxml.close()
        keys = (BAO_TM_CLIENT_HELPER.VALUE_SYSTEM,
                BAO_TM_CLIENT_HELPER.VALUE_CONTACTMAIL,
                BAO_TM_CLIENT_HELPER.VALUE_CONTACTTEL,
                BAO_TM_CLIENT_HELPER.VALUE_SUBMIT_MODE,
                BAO_TM_CLIENT_HELPER.VALUE_GID_ID,
                BAO_TM_CLIENT_HELPER.VALUE_INCIDENTID,
                BAO_TM_CLIENT_HELPER.VALUE_COMPANY,
                BAO_TM_CLIENT_HELPER.VALUE_LASTNAME,
                BAO_TM_CLIENT_HELPER.VALUE_FIRSTNAME,
                BAO_TM_CLIENT_HELPER.VALUE_MIDDLENAME,
                BAO_TM_CLIENT_HELPER.VALUE_SUPPORTGROUP,
                BAO_TM_CLIENT_HELPER.VALUE_ASSIGNEE,
                BAO_TM_CLIENT_HELPER.VALUE_SUMMARY,
                BAO_TM_CLIENT_HELPER.VALUE_CI,
                BAO_TM_CLIENT_HELPER.VALUE_SERVICECI,
                BAO_TM_CLIENT_HELPER.VALUE_OCCURRENCE,
                BAO_TM_CLIENT_HELPER.VALUE_RESTORE,
                BAO_TM_CLIENT_HELPER.VALUE_STATUS,
                BAO_TM_CLIENT_HELPER.VALUE_RESOLUTION,
                BAO_TM_CLIENT_HELPER.VALUE_INTERNALALARMID,
                BAO_TM_CLIENT_HELPER.VALUE_WORKLOG_TEMPLATE,
                BAO_TM_CLIENT_HELPER.VALUE_WORKLOG_ASSIGNED_GROUP,
                BAO_TM_CLIENT_HELPER.VALUE_WORKLOG_OPERATOR,
                BAO_TM_CLIENT_HELPER.VALUE_WORKLOG_GID_ID,
                BAO_TM_CLIENT_HELPER.VALUE_WORKLOG_CATEGORY,
                BAO_TM_CLIENT_HELPER.VALUE_WORKLOG_NOTES,
                BAO_TM_CLIENT_HELPER.VALUE_WORKLOG_DATE,
                BAO_TM_CLIENT_HELPER.VALUE_WORKLOG_SUMMARY)
        for key in keys:
            replace_key = '#%s#' % key
            text = text.replace(replace_key, str(wk_hash[key]))
        return text

    def create_bao_register_incident_request_params(self, new_event, kisys_incidentid, kisys_status, alias):
        gw_event_id = new_event['gw_event_id']
        customer_ci = new_event['customer_ci']
        customer_name = new_event['customer_name']
        hostname = new_event['hostname']
        alarm_time = new_event['alarm_time']
        ci_name = new_event['ci_name']
        summary = new_event['summary']

        try:
            alarm_time = alarm_time.timestamp()
            # 小数点以下の切り捨て
            alarm_unixtime = str(int(float(alarm_time)))
        except:
            exception_msg = traceback.format_exc()
            LOGGER.info(exception_msg)
            LOGGER.warning('Stopped: alarm_time ⇒ Unixtime への変換に失敗しました。')
            raise Exception("Invalid time format.")

        # summaryに詳細情報を追加する
        summary_add_details = 'お客様名：' + str(customer_name) + '&#xA;' + 'アラーム種別：error' + '&#xA;' + 'ホスト名：' + str(hostname) \
             + '&#xA;' + '日時：' + str(datetime.datetime.fromtimestamp(int(alarm_time))) + '&#xA;' + 'アラーム名：' + str(ci_name) + '&#xA;' + '詳細：' + str(summary)

        try:
            last_name = '-'
            first_name = '-'
            middle_name = ''
            if alias != '':
                names = alias.split(',')
                if len(names) >= 1:
                    first_name = names[0]
                if len(names) >= 2:
                    last_name = names[-1]
                if len(names) >= 3:
                    names.pop(0)
                    names.pop() # 末尾削除
                    middle_name = ','.join(names)
        except:
            exception_msg = traceback.format_exc()
            LOGGER.info(exception_msg)
            LOGGER.warning('Ignore: フォーマットが不正です')

        LOGGER.debug('error報のBAOSOAPパラメータ処理')
        params = {}
        params[self.VALUE_SYSTEM] = self.SOAP_VALUE_SYSTEM
        params[self.VALUE_CONTACTMAIL] = self.SOAP_VALUE_CONTACTMAIL
        params[self.VALUE_CONTACTTEL] = self.SOAP_CONTACTTEL
        params[self.VALUE_SUBMIT_MODE] = '0'
        params[self.VALUE_GID_ID] = self.SOAP_VALUE_GID_ID
        params[self.VALUE_INCIDENTID] = ''
        params[self.VALUE_COMPANY] = BAO_TM_CLIENT_HELPER.truncate_by_bytes(BAO_TM_CLIENT_HELPER.escape_bao(customer_name), 255)
        params[self.VALUE_LASTNAME] = last_name
        params[self.VALUE_FIRSTNAME] = first_name
        params[self.VALUE_MIDDLENAME] = middle_name
        params[self.VALUE_SUMMARY] = BAO_TM_CLIENT_HELPER.truncate_by_bytes(self.SOAP_VALUE_SUMMARY + BAO_TM_CLIENT_HELPER.escape_bao(ci_name), 255)
        params[self.VALUE_CI] = '%s_%s' % (hostname, customer_ci)
        params[self.VALUE_SERVICECI] = '%s(%s)' % (self.SOAP_VALUE_SERVICECI, customer_ci)
        params[self.VALUE_SUPPORTGROUP] = self.SOAP_VALUE_SUPPORTGROUP
        params[self.VALUE_ASSIGNEE] = self.SOAP_VALUE_ASSIGNEE
        params[self.VALUE_OCCURRENCE] = alarm_unixtime
        params[self.VALUE_RESTORE] = ''
        params[self.VALUE_STATUS] = self.SOAP_VALUE_STATUS_NEW
        params[self.VALUE_RESOLUTION] = self.SOAP_VALUE_RESOLUTION
        params[self.VALUE_INTERNALALARMID] = '%s%010d' % (COM.INTERNAL_ID, gw_event_id)
        params[self.VALUE_WORKLOG_TEMPLATE] = self.SOAP_VALUE_WORKLOG_TEMPLATE
        params[self.VALUE_WORKLOG_ASSIGNED_GROUP] = self.SOAP_VALUE_WORKLOG_ASSIGNED_GROUP
        params[self.VALUE_WORKLOG_OPERATOR] = self.SOAP_VALUE_WORKLOG_OPERATOR
        params[self.VALUE_WORKLOG_GID_ID] = self.SOAP_VALUE_GID_ID
        params[self.VALUE_WORKLOG_CATEGORY] = self.SOAP_VALUE_WORKLOG_CATEGORY_NEW # = "010_アラーム発生検知（初回）※CP"
        params[self.VALUE_WORKLOG_NOTES] = BAO_TM_CLIENT_HELPER.truncate_by_bytes(BAO_TM_CLIENT_HELPER.escape_bao(summary_add_details), 30000)
        params[self.VALUE_WORKLOG_DATE] = alarm_unixtime
        params[self.VALUE_WORKLOG_SUMMARY] = self.SOAP_VALUE_WORKLOG_SUMMARY_NEW

        return params

    def create_bao_recover_incident_request_params(self, new_event, kisys_incidentid, kisys_status):
        gw_event_id = new_event['gw_event_id']
        customer_ci = new_event['customer_ci']
        customer_name = new_event['customer_name']
        hostname = new_event['hostname']
        alarm_time = new_event['alarm_time']
        ci_name = new_event['ci_name']
        summary = new_event['summary']
        # updateだった場合、KISYS側のvalue_statusを変更しないよう、nullを意味する空文字で上書きする
        value_status = '' if kisys_status == self.SOAP_VALUE_STATUS_UPDATE else kisys_status

        try:
            alarm_time = alarm_time.timestamp()
            # 小数点以下の切り捨て
            alarm_unixtime = str(int(float(alarm_time)))
        except:
            exception_msg = traceback.format_exc()
            LOGGER.info(exception_msg)
            LOGGER.warning('Stopped: alarm_time ⇒ Unixtime への変換に失敗しました。')
            raise Exception("Invalid time format.")

        # summaryに詳細情報を追加する
        summary_add_details = 'お客様名：' + str(customer_name) + '&#xA;' + 'アラーム種別：normal' + '&#xA;' + 'ホスト名：' + str(hostname) \
             + '&#xA;' + '日時：' + str(datetime.datetime.fromtimestamp(int(alarm_time))) + '&#xA;' + 'アラーム名：' + str(ci_name) + '&#xA;' + '詳細：' + str(summary)

        LOGGER.debug('normal報のBAOSOAPパラメータ処理')
        params = {}
        params[self.VALUE_SYSTEM] = self.SOAP_VALUE_SYSTEM
        params[self.VALUE_CONTACTMAIL] = self.SOAP_VALUE_CONTACTMAIL
        params[self.VALUE_CONTACTTEL] = self.SOAP_CONTACTTEL
        params[self.VALUE_SUBMIT_MODE] = ''
        params[self.VALUE_GID_ID] = self.SOAP_VALUE_GID_ID
        params[self.VALUE_INCIDENTID] = kisys_incidentid
        params[self.VALUE_COMPANY] = ''
        params[self.VALUE_LASTNAME] = ''
        params[self.VALUE_FIRSTNAME] = ''
        params[self.VALUE_MIDDLENAME] = ''
        params[self.VALUE_SUMMARY] = BAO_TM_CLIENT_HELPER.truncate_by_bytes(self.SOAP_VALUE_SUMMARY + BAO_TM_CLIENT_HELPER.escape_bao(ci_name), 100)
        params[self.VALUE_CI] = '%s_%s' % (hostname, customer_ci)
        params[self.VALUE_SERVICECI] = '%s(%s)' % (self.SOAP_VALUE_SERVICECI, customer_ci)
        params[self.VALUE_SUPPORTGROUP] = ''
        params[self.VALUE_ASSIGNEE] = ''
        params[self.VALUE_OCCURRENCE] = ''
        params[self.VALUE_RESTORE] = alarm_unixtime
        params[self.VALUE_STATUS] = value_status
        params[self.VALUE_RESOLUTION] = self.SOAP_VALUE_RESOLUTION_UPDATE
        params[self.VALUE_INTERNALALARMID] = '%s%010d' % (COM.INTERNAL_ID, gw_event_id)
        params[self.VALUE_WORKLOG_TEMPLATE] = self.SOAP_VALUE_WORKLOG_TEMPLATE
        params[self.VALUE_WORKLOG_ASSIGNED_GROUP] = self.SOAP_VALUE_WORKLOG_ASSIGNED_GROUP
        params[self.VALUE_WORKLOG_OPERATOR] = self.SOAP_VALUE_WORKLOG_OPERATOR
        params[self.VALUE_WORKLOG_GID_ID] = self.SOAP_VALUE_GID_ID
        params[self.VALUE_WORKLOG_CATEGORY] = self.SOAP_VALUE_WORKLOG_CATEGORY_UPDATE # = "015_アラーム復旧検知（初回）※CP"
        params[self.VALUE_WORKLOG_NOTES] = BAO_TM_CLIENT_HELPER.truncate_by_bytes(BAO_TM_CLIENT_HELPER.escape_bao(summary_add_details), 30000)
        params[self.VALUE_WORKLOG_DATE] = alarm_unixtime
        params[self.VALUE_WORKLOG_SUMMARY] = self.SOAP_VALUE_WORKLOG_SUMMARY_UPDATE
        return params

    @staticmethod
    def truncate_by_bytes(truncate_str, truncate_bytes, encoding='utf-8'):
        while len(truncate_str.encode(encoding)) > truncate_bytes:
            truncate_str = truncate_str[:-1]
        return truncate_str

    @staticmethod
    def escape_bao(argument):
        argument = argument.replace('\r', '')
        argument = argument.replace('\n', '')
        argument = argument.replace('&', '&amp;')
        argument = argument.replace('<', '&lt;')
        argument = argument.replace('>', '&gt;')
        argument = argument.replace('"', '&quot;')
        argument = argument.replace("'", '&apos;')
        return argument

    @staticmethod
    def convert_to_hash(new_event):
        wk_hash = {}
        wk_hash['gw_event_id'] = new_event[0]
        wk_hash['event_status'] = new_event[1]
        wk_hash['update_time'] = new_event[2]
        wk_hash['gw_incident_id'] = new_event[3]
        wk_hash['detected_time'] = new_event[4]
        wk_hash['detected_host'] = new_event[5]
        wk_hash['customer_ci'] = new_event[6]
        wk_hash['customer_name'] = new_event[7]
        wk_hash['hostname'] = new_event[8]
        wk_hash['alarm_time'] = new_event[9]
        wk_hash['ci_name'] = new_event[10]
        wk_hash['device'] = new_event[11]
        wk_hash['alarm_status'] = new_event[12]
        wk_hash['summary'] = new_event[13]
        wk_hash['checked_time'] = new_event[14]
        wk_hash['checked_user'] = new_event[15]
        wk_hash['op_comment'] = new_event[16]
        wk_hash['kisys_status'] = new_event[17]
        return wk_hash

    def create_bao_request_xml(self, new_event, kisys_incidentid, kisys_status, alias):
        if len(new_event) < 18:
            LOGGER.error("new_eventが、想定のパラメータを含んでいません")
            raise Exception("Invalid new_event params.")

        new_event_hash = BAO_TM_CLIENT_HELPER.convert_to_hash(new_event)
        alarm_status = new_event_hash['alarm_status']
        api = FUNC.ZabbixApi(COM.ZABBIX_IP, COM.ZABBIX_USER, COM.ZABBIX_PASSWD)
        hostgroups = FUNC.get_hostgroups_by_host(api, new_event[18])
        GID_hostgroups = [GID for GID in hostgroups if 'GID' in GID]
        if len(GID_hostgroups) > 1:
            LOGGER.error("'GID'の文字列を含むホストグループに2つ以上所属しています")
            raise Exception("More than expected GID hostgroups.")

        elif len(GID_hostgroups) == 1:
            # リスト内のホストグループを取り出す
            for GID_hostgroup in GID_hostgroups:
                GID_param = GID_hostgroup.split(':')[-1]
                # GIDのホストグループ名の末尾部分が、シングルバイト文字であるかを確認
                if len(GID_param.encode("utf-8")) == len(GID_param):
                    self.SOAP_VALUE_GID_ID = GID_param
                elif len(GID_param.encode("utf-8")) > len(GID_param):
                    LOGGER.error("所属するGIDのホストグループの数値がマルチバイト文字です")
                    raise Exception("GID params differ bytes.")
                    
        if alarm_status == COM.GW_ALARM_STATUS_ERROR:
            params = self.create_bao_register_incident_request_params(new_event_hash, kisys_incidentid, kisys_status, alias)
        else:
            params = self.create_bao_recover_incident_request_params(new_event_hash, kisys_incidentid, kisys_status)

        xml = BAO_TM_CLIENT_HELPER.make_xml(params)
        oldxml_log = open(COM.OLD_XML, 'a', encoding='utf-8')
        oldxml_log.write(datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S") + COM.LOG_DELIMITER)
        oldxml_log.write('%s\n' % xml)
        oldxml_log.close()
        oldparam_log = open(COM.OLD_PARAM, 'a', encoding='utf-8')
        oldparam_log.write(datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S") + COM.LOG_DELIMITER)
        oldparam_log.write('%s\n' % params)
        oldparam_log.close()

        return xml

class BAO_TM_CLIENT:
    def send_request(self, host, xml_string):
        headers =  {'Content-Type': 'text/xml', 'SOAPAction': '\"execute_process:\"'}
        method =  'POST'
        bytesXMLPostBody = xml_string.encode("UTF-8")
        req = urllib.request.Request(host, method=method, headers=headers, data=bytesXMLPostBody)
        try:
            res = urllib.request.urlopen(req, timeout=180.0)
            response_body = res.read()
            return response_body
        except urllib.request.HTTPError as e:
            LOGGER.info("status:%s" % e.code)
            LOGGER.info("reason:%s" % e.reason)
            raise e

    def send(self, new_event, kisys_incidentid, kisys_status, alias):
        try:
            post_xml_data = BAO_TM_CLIENT_HELPER().create_bao_request_xml(new_event, kisys_incidentid, kisys_status, alias)
        except:
            return 'No_reply'

        try:
            LOGGER.info('通信処理を開始します。')
            url = COM.WEB_API_BASE_URL % COM.KISYS_TM_PRIMARY_SERVER_IP_ADDRESS
            res = self.send_request(url, post_xml_data)
            try:
                root = ET.fromstring(res)
            except:
                raise Exception("JSON format Error.")
            xml_prefixies = {'ns0': 'http://schemas.xmlsoap.org/soap/envelope/', 'ns1': 'http://bmc.com/ao/xsd/2008/09/soa'}
            xml_body = root.find('.//ns0:Body', xml_prefixies)
            xml_outputs_param = xml_body.find('.//ns1:executeProcessResponse/ns1:Output', xml_prefixies)

            output_params = {}
            for result in xml_outputs_param.findall('.//ns1:Parameter', xml_prefixies):
                name = result.find('ns1:Name', xml_prefixies).text
                value = result.find('ns1:Value', xml_prefixies)
                val = value.find('ns1:XmlDoc/result', xml_prefixies)
                if val is not None:
                    output_params[name] = val.text
                else:
                    output_params[name] = None
            incident_number = output_params.get('incident_number')
            create_status = output_params.get('create_status')
            if create_status is not None and create_status != '0':
                oldres_log = open(COM.OLD_RES, 'a', encoding='utf-8')
                oldres_log.write(datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S") + COM.LOG_DELIMITER)
                oldres_log.write('%s\n' % res)
                oldres_log.write('%s\n' % incident_number)
                oldres_log.close()
                oldxml = open(COM.OLD_XML, 'a', encoding='utf-8')
                oldxml.write(datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S") \
                + ' ---> XMLファイル送信に成功しました。\n')
                oldxml.write(datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S") \
                + ' ---> 応答XMLファイルにエラーが含まれています。\n')
                oldxml.close()
                oldparam = open(COM.OLD_PARAM, 'a', encoding='utf-8')
                oldparam.write(datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S") \
                + ' ---> XMLファイル送信に成功しました。\n')
                oldparam.write(datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S") \
                + ' ---> 応答XMLファイルにエラーが含まれています。\n')
                oldparam.close()
                return 'Failure'
            oldres_log = open(COM.OLD_RES, 'a', encoding='utf-8')
            oldres_log.write(datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S") + COM.LOG_DELIMITER)
            oldres_log.write('%s\n' % res)
            oldres_log.write('%s\n' % incident_number)
            oldres_log.close()
            oldxml = open(COM.OLD_XML, 'a', encoding='utf-8')
            oldxml.write(datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S") \
            + ' ---> XMLファイル送信に成功しました。\n')
            oldxml.close()
            oldparam = open(COM.OLD_PARAM, 'a', encoding='utf-8')
            oldparam.write(datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S") \
            + ' ---> XMLファイル送信に成功しました。\n')
            oldparam.close()

            LOGGER.info('通信処理を終了します。')
            return incident_number
        except Exception as e:
            LOGGER.info('送信失敗。エラーメッセージ: %s' % e)
            LOGGER.info('サーバを切り替えてリクエストを再実施します')

        # 失敗した場合の再実行処理
        try:
            url = COM.WEB_API_BASE_URL % COM.KISYS_TM_SECONDARY_SERVER_IP_ADDRESS
            res = self.send_request(url, post_xml_data)
            try:
                root = ET.fromstring(res)
            except:
                raise Exception("JSON format Error.")
            xml_prefixies = {'ns0': 'http://schemas.xmlsoap.org/soap/envelope/', 'ns1': 'http://bmc.com/ao/xsd/2008/09/soa'}
            xml_body = root.find('.//ns0:Body', xml_prefixies)
            xml_outputs_param = xml_body.find('.//ns1:executeProcessResponse/ns1:Output', xml_prefixies)

            output_params = {}
            for result in xml_outputs_param.findall('.//ns1:Parameter', xml_prefixies):
                name = result.find('ns1:Name', xml_prefixies).text
                value = result.find('ns1:Value', xml_prefixies)
                val = value.find('ns1:XmlDoc/result', xml_prefixies)
                if val is not None:
                    output_params[name] = val.text
                else:
                    output_params[name] = None
            incident_number = output_params.get('incident_number')
            create_status = output_params.get('create_status')
            if create_status is not None and create_status != '0':
                oldres_log = open(COM.OLD_RES, 'a', encoding='utf-8')
                oldres_log.write(datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S") + COM.LOG_DELIMITER)
                oldres_log.write('%s\n' % res)
                oldres_log.write('%s\n' % incident_number)
                oldres_log.close()
                oldxml = open(COM.OLD_XML, 'a', encoding='utf-8')
                oldxml.write(datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S") \
                + ' ---> XMLファイル送信に成功しました。\n')
                oldxml.write(datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S") \
                + ' ---> 応答XMLファイルにエラーが含まれています。\n')
                oldxml.close()
                oldparam = open(COM.OLD_PARAM, 'a', encoding='utf-8')
                oldparam.write(datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S") \
                + ' ---> XMLファイル送信に成功しました。\n')
                oldparam.write(datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S") \
                + ' ---> 応答XMLファイルにエラーが含まれています。\n')
                oldparam.close()
                return 'Failure'
            oldres_log = open(COM.OLD_RES, 'a', encoding='utf-8')
            oldres_log.write(datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S") + COM.LOG_DELIMITER)
            oldres_log.write('%s\n' % res)
            oldres_log.write('%s\n' % incident_number)
            oldres_log.close()
            oldxml = open(COM.OLD_XML, 'a', encoding='utf-8')
            oldxml.write(datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S") \
            + ' ---> XMLファイル送信に成功しました。\n')
            oldxml.close()
            oldparam = open(COM.OLD_PARAM, 'a', encoding='utf-8')
            oldparam.write(datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S") \
            + ' ---> XMLファイル送信に成功しました。\n')
            oldparam.close()

            LOGGER.info('通信処理を終了します。')
            return incident_number
        except Exception as e:
            LOGGER.info('送信失敗。エラーメッセージ: %s' % e)
            LOGGER.info('通信処理を終了します。')
            oldxml = open(COM.OLD_XML, 'a', encoding='utf-8')
            oldxml.write(datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S") \
            + ' ---> XMLファイル送信に失敗しました。\n')
            oldxml.close()
            oldparam = open(COM.OLD_PARAM, 'a', encoding='utf-8')
            oldparam.write(datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S") \
            + ' ---> XMLファイル送信に失敗しました。\n')
            oldparam.close()
            return 'No_reply'

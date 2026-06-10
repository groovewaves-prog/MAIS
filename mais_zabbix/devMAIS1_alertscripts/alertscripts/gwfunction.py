#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
## 概要 ##
gwfunction.py
共通関数

"""

## import ##
import traceback
import datetime
#from datetime import datetime
import os
import json
import logging
import logging.handlers
import urllib.request
import mysql.connector
import gwcommon as COM
import re
import sys

##################################

## スクリプトのパス、ファイル名を取得
SCRIPT_FILE = os.path.basename(__file__)

""" log出力設定 ※rsyslogd に渡す設定 """
LOGGER = logging.getLogger(SCRIPT_FILE)
LOGGER.setLevel(COM.LOGGER_LEVEL_GW_FUNCTION) # 出力レベルの設定
HANDLER = logging.handlers.SysLogHandler(address=('localhost', 514), facility='local6') # 出力先の設定
FORMATTER = logging.Formatter('%(name)s[%(process)d]: %(levelname)s: [%(lineno)d]%(message)s')
HANDLER.formatter = FORMATTER
LOGGER.addHandler(HANDLER)

class ZabbixApi(object):
    def __init__(self, host, user, password):
        """Zabbix API インスタンスを返す

        :param host: Zabbix サーバの IP アドレス
        :param user: Zabbix API のアクセスユーザ
        :param password: Zabbix API のアクセスユーザパスワード
        :return:
        """
        self.request_id = 1
        self.host = host
        self.auth_token = self.request('user.login', {'user': user, 'password': password})


    def request(self, method, params, auth_token=None):
        """Zabbix API にリクエストを送信する
        id は現行特に必要ないため単純にインクリメントした数値を代入している。

        :param method: Zabbix API のメソッド名
        :param params: Zabbix API のメソッドの引数
        :param auth_token: Zabbix API の認証トークン
        :return: JSON-RPC2.0 形式の応答
        """
        if hasattr(self, 'auth_token'):
            auth_token = self.auth_token.get('result')
        headers = {"Content-Type": "application/json-rpc"}
        uri = "http://{0}/zabbix/api_jsonrpc.php".format(self.host)
        data = json.dumps({'jsonrpc': '2.0',
                           'method': method,
                           'params': params,
                           'auth': auth_token,
                           'id': self.request_id}).encode('utf-8')
        request = urllib.request.Request(uri, data, headers)
        return json.loads(urllib.request.urlopen(request).read().decode('utf-8'))

def connect_db_unix_socket(dbhost=COM.MY_HOST):
    """
    unixsocketでdatabse へ接続 #カーソルを取得する場合は baogwcur = dbbaogw.cursor(buffered=True)
    """
    try:
        connect_baogw = mysql.connector.connect(
            unix_socket=COM.MY_UNIX_SOCKET,
            host=dbhost,
            db=COM.MY_DB,
            user=COM.MY_USER,
            password=COM.MY_PASSWD
        )
    except Exception as msg:
        LOGGER.critical('Stopped: Function of connect_db_unix_socket is failed.')
        LOGGER.info(msg)
        sys.exit()
    return connect_baogw

def connect_db(dbhost=COM.MY_HOST):
    """
    databse へ接続 #カーソルを取得する場合は baogwcur = dbbaogw.cursor(buffered=True)
    """
    try:
        connect_baogw = mysql.connector.connect(
            host=dbhost,
            db=COM.MY_DB,
            user=COM.MY_USER,
            password=COM.MY_PASSWD
        )
    except Exception as msg:
        LOGGER.critical('Stopped: Function of connect_db is failed.')
        LOGGER.info(msg)
        sys.exit()
    return connect_baogw

def get_new_events(dbhost, customer_name, hostname, alarm_time, ci_name):
    """
    gw_events からインサートしたイベントを抜き出す
    """
    dbbaogw = connect_db(dbhost)
    baogwcur = dbbaogw.cursor(dictionary=True)
    sql = "SELECT * FROM gw_events \
        WHERE customer_name=%s and hostname=%s and alarm_time=%s and ci_name=%s\
        ORDER BY gw_event_id DESC"
    sql_values = (customer_name, hostname, alarm_time, ci_name)
    try:
        baogwcur.execute(sql, sql_values)
        new_events = baogwcur.fetchall()
        baogwcur.close()
        dbbaogw.close()
    except Exception as msg:
        LOGGER.critical('Stopped: Function of get_new_events is failed.')
        LOGGER.info(msg)
    return new_events[0]

def update_gw_events(dbhost, event_status, gw_incident_id, gw_event_id, kisys_status):
    """
    gw_events テーブルを更新する
    """
    dbbaogw = connect_db(dbhost)
    baogwcur = dbbaogw.cursor(buffered=True)
    sql = "UPDATE gw_events SET event_status=%s, gw_incident_id=%s, update_time=now(3), \
    kisys_status=%s WHERE gw_event_id=%s"
    sql_values = (event_status, gw_incident_id, kisys_status, gw_event_id)
    try:
        baogwcur.execute(sql, sql_values)
        dbbaogw.commit()
        baogwcur.close()
        dbbaogw.close()
        LOGGER.debug('Success: update_gw_events gw_event_id=%s', gw_event_id)
    except Exception as msg:
        LOGGER.critical('Stopped: Function of update_gw_events is failed.')
        LOGGER.info(msg)

def get_dup_events(dbhost, alarm_time, customer_name, hostname, ci_name):
    """
    重複イベントを抜き出す
    alarm_time, customer_name, hostname, ci_name 全てが一致するレコードのうち、インシデント登録済みのものを重複レコードとみなす
    """
    dbbaogw = connect_db(dbhost)
    baogwcur = dbbaogw.cursor(dictionary=True)
    sql = "SELECT * FROM gw_events \
    WHERE alarm_time=%s and customer_name=%s and hostname=%s and ci_name=%s and gw_incident_id IS NOT null\
    ORDER BY gw_event_id ASC"
    sql_values = (alarm_time, customer_name, hostname, ci_name)
    try:
        baogwcur.execute(sql, sql_values)
        dup_events = baogwcur.fetchall()
        baogwcur.close()
        dbbaogw.close()
    except Exception as msg:
        LOGGER.critical('Stopped: Function of get_dup_events is failed.')
        LOGGER.info(msg)
    return dup_events

def update_gw_incidents(dbhost, incident_status, gw_event_id, gw_incident_id):
    """
    gw_incidents テーブルを更新する
    """
    dbbaogw = connect_db(dbhost)
    baogwcur = dbbaogw.cursor(buffered=True)
    sql = "UPDATE gw_incidents SET incident_status=%s, normal_event_id=%s, update_time=now() \
    WHERE gw_incident_id=%s"
    sql_values = (incident_status, gw_event_id, gw_incident_id)
    try:
        baogwcur.execute(sql, sql_values)
        dbbaogw.commit()
        baogwcur.close()
        dbbaogw.close()
    except Exception as msg:
        LOGGER.critical('Stopped: Function of update_gw_incidents is failed.')
        LOGGER.info(msg)

def insert_error_id_into_gw_incidents(dbhost, insert_values):
    """
    gw_incidents テーブルへ新規レコード挿入(error)
    """
    now_datetime = datetime.datetime.now()
    update_time = now_datetime.strftime("%Y-%m-%d %H:%M:%S")
    dbbaogw = connect_db(dbhost)
    baogwcur = dbbaogw.cursor(buffered=True)
    sql = "insert into gw_incidents (incident_status,update_time,detected_host,error_event_id,customer_name,hostname,\
    ci_name,op_comment,project_code) values (%s,%s,%s,%s,%s,%s,%s,%s,%s)"
    insert_values.insert(1, update_time)
    try:
        baogwcur.execute(sql, insert_values)
        dbbaogw.commit()
        sql = "SELECT gw_incident_id FROM gw_incidents \
        WHERE update_time=%s and error_event_id=%s and customer_name=%s and hostname=%s and ci_name=%s \
        ORDER BY gw_incident_id DESC"
        sql_values = (update_time, insert_values[3], insert_values[4], insert_values[5], insert_values[6])
        baogwcur.execute(sql, sql_values)
        gw_incident_id = baogwcur.fetchall()[0][0]
        baogwcur.close()
        dbbaogw.close()
    except Exception as msg:
        LOGGER.critical('Stopped: Function of insert_gw_incidents_error is failed.')
        LOGGER.info(msg)
    return gw_incident_id

def get_existing_events(dbhost, customer_name, hostname, ci_name, normal_alarm_time):
    """
    既存のError報を探す
    customer_name, hostname, ci_name が一致し、incident_status=1 のレコード
    """
    event_record = []
    dbbaogw = connect_db(dbhost)
    baogwcur = dbbaogw.cursor(buffered=True)
    sql = "SELECT gw_event_id,gw_incident_id,alarm_time FROM gw_events\
           WHERE gw_event_id in \
           (SELECT error_event_id FROM gw_incidents \
            WHERE incident_status=1 and customer_name=%s and hostname=%s and ci_name=%s)\
           and alarm_time<%s\
           ORDER BY gw_incident_id DESC;"

    sql_values = (customer_name, hostname, ci_name, normal_alarm_time)
    try:
        baogwcur.execute(sql, sql_values)
        existing_events = baogwcur.fetchall()
        if not existing_events:
            baogwcur.close()
            dbbaogw.close()
            return event_record
    except Exception as msg:
        LOGGER.critical('Stopped: Function of get_existing_events select events is failed.')
        LOGGER.info(msg)
    existing_event_id = existing_events[0][0]
    existing_gw_incident_id = existing_events[0][1]
    existing_alarm_time = existing_events[0][2]
    event_record = (
        existing_event_id, existing_gw_incident_id, existing_alarm_time
    )
    baogwcur.close()
    dbbaogw.close()
    return event_record

def insert_normal_id_into_gw_incidents(dbhost, insert_values):
    """
    gw_incidents テーブルへ新規レコード挿入(normal)
    """
    now_datetime = datetime.datetime.now()
    update_time = now_datetime.strftime("%Y-%m-%d %H:%M:%S")
    dbbaogw = connect_db(dbhost)
    baogwcur = dbbaogw.cursor(buffered=True)
    sql = "insert into gw_incidents (incident_status,update_time,detected_host,normal_event_id,customer_name,hostname,\
    ci_name,op_comment,project_code) values (%s,%s,%s,%s,%s,%s,%s,%s,%s)"
    insert_values.insert(1, update_time)
    try:
        baogwcur.execute(sql, insert_values)
        dbbaogw.commit()
        sql = "SELECT gw_incident_id FROM gw_incidents \
        WHERE update_time = %s and normal_event_id = %s and customer_name = %s and hostname = %s and ci_name = %s \
        ORDER BY gw_incident_id DESC"
        sql_values = (update_time, insert_values[3], insert_values[4], insert_values[5], insert_values[6])
        baogwcur.execute(sql, sql_values)
        gw_incident_id = baogwcur.fetchall()[0][0]
        baogwcur.close()
        dbbaogw.close()
    except Exception as msg:
        LOGGER.critical('Stopped: Function of insert_normal_id_into_gw_incidents is failed.')
        LOGGER.info(msg)
    return gw_incident_id

def get_action_no(customer_name, hostname, ci_name):
    """
    gw_rulesテーブルからアクションNoを抽出
    """
    nowdatetime = datetime.datetime.now()
    nowdatetimestr = nowdatetime.strftime("%Y-%m-%d %H:%M:%S")
    dbbaogw = connect_db()
    baogwcur = dbbaogw.cursor(buffered=True)

    sql = "SELECT \
            action_no \
           FROM gw_rules \
           WHERE \
             rule_status = 1 and customer_name = %s and start_time <= %s and end_time >= %s \
             AND %s LIKE REPLACE(REPLACE(REPLACE(hostname, '%', '\%'), '_', '\_'), '*', '%') \
             AND %s LIKE REPLACE(REPLACE(REPLACE(ci_name, '%', '\%'), '_', '\_'), '*', '%') \
             ORDER BY \
               (CASE \
                   WHEN action_no = 10 THEN 2 \
                   WHEN action_no = 20 THEN 3 \
                   WHEN action_no >= 30 AND action_no <= 35 THEN 4 \
                   WHEN action_no = 90 THEN 1 \
                   ELSE 99 \
                END) ASC;"
    sql_values = (
        customer_name,
        nowdatetimestr,
        nowdatetimestr,
        hostname,
        ci_name
    )

    try:
        baogwcur.execute(sql, sql_values)
        result = baogwcur.fetchone()
        baogwcur.close()
        dbbaogw.close()
    except Exception:
        LOGGER.critical('Stopped: Function of get_action_no is failed.')
        LOGGER.info(traceback.format_exc())
        sys.exit()

    if result:
        return str(result[0])

    return ''

def get_host(api, host):
    if type(host) is bytearray:
        host = host.decode()
    response = api.request('host.get', {
        'output':'extend',
        'selectGroups':'extend',
        'selectInventory': 'extend',
        'filter':{'host':host}
    })
    if 'result' in response and response['result']:
        return response['result'][0]
    return []

def get_alias_by_host(api, host):
    """
    顧客名をキーに、ホストインベントリのエイリアスを抽出
    """
    result = get_host(api, host)
    if result:
        return result['inventory']['alias']
    return ''

def get_hostgroups_by_host(api, host):
    """
    顧客名からホストグループリストを抽出
    """
    result = get_host(api, host)
    host_groups = []
    if result:
        for hostgroup in result['groups']:
            host_groups.append(hostgroup['name'])
    return host_groups

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import copy
import datetime
import glob
import mysql.connector
import os
import pathlib
import sys
import unittest
from unittest.mock import patch

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import insert_gw_incidents
import gwcommon

BAOGW_DIR = '/var/lib/baogw/'
PATOLAMP_FILE_PATH = BAOGW_DIR
UNITTEST_FILE = BAOGW_DIR + 'unittest'
STOP_FILE = BAOGW_DIR + 'stop'
TEST_FILE = BAOGW_DIR + 'test'
PRIMARY_FILE = BAOGW_DIR + 'primary'
MY_DB_LOCAL = 'baogw_test1' # localのDB
MY_DB_REMOTE = 'baogw_test2' # remoteのDB
MY_HOST_REMOTE = '127.0.0.1' #remoteのホスト
#MY_USER = 'root'
#MY_PASSWD = 'zabbix'
MY_USER = 'baogw'
MY_PASSWD = 'baogw'
NO_NOPATOLAMP_ACTION = [gwcommon.GW_KISYS_STATUS_NOPATOLAMP] + gwcommon.GW_KISYS_STATUS_WAITING_LIST

########################################################################
## Test Helper
########################################################################

def db_connect(host = gwcommon.MY_HOST):
    # DB接続
    conn = mysql.connector.connect(
        host=host,
        db=MY_DB_LOCAL,
        user=MY_USER,
        password=MY_PASSWD
    )
    conn.ping(reconnect=True)
    return conn

def insert_maintenance_rule(conn):
    cur = conn.cursor()
    sql = "INSERT INTO gw_rules (rule_id, rule_status, rule_set, start_time, end_time, customer_name, hostname, ci_name, action_no, op_comment, create_user, update_user) \
        VALUES (NULL, '1', NULL, '2020-01-01 00:00:00', '2099-12-31 00:00:00', 'KISYS', '*', '*', %s, NULL, NULL, NULL)" % '%s'
    cur.execute(sql, (gwcommon.GW_KISYS_STATUS_MAINTENANCE,))
    cur.close()
    conn.commit()

def insert_kompira_rule(conn):
    cur = conn.cursor()
    sql = "INSERT INTO gw_rules (rule_id, rule_status, rule_set, start_time, end_time, customer_name, hostname, ci_name, action_no, op_comment, create_user, update_user) \
        VALUES (NULL, '1', NULL, '2020-01-01 00:00:00', '2099-12-31 00:00:00', 'Kompira', '*', '*', %s, NULL, NULL, NULL)" % '%s'
    cur.execute(sql, (gwcommon.KOMPIRA_STATUS_NOSEND,))
    cur.close()
    conn.commit()

def insert_test_rule(conn, action_no, str):
    cur = conn.cursor()
    sql = "INSERT INTO gw_rules (rule_id, rule_status, rule_set, start_time, end_time, customer_name, hostname, ci_name, action_no, op_comment, create_user, update_user) \
        VALUES (NULL, '1', NULL, '2020-01-01 00:00:00', '2099-12-31 00:00:00', 'customer_name_%s', 'hostname_%s', 'ci_name_%s', %s, NULL, NULL, NULL)" \
        % (str, str, str, '%s')
    cur.execute(sql, (action_no,))
    cur.close()
    conn.commit()

def insert_event_data(conn, insert_hash_list):
    event_ids = []
    for insert_hash in insert_hash_list:
        cur = conn.cursor()
        insert_item = 'update_time, detected_time, detected_host, customer_ci, customer_name,\
                    hostname, alarm_time, ci_name, device, alarm_status, summary, host'
        insert_value = 'now(), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s'
        value = (insert_hash['detected_time'], insert_hash['detected_host'], insert_hash['customer_ci'],
            insert_hash['customer_name'], insert_hash['hostname'], insert_hash['alarm_time'],
            insert_hash['ci_name'], insert_hash['device'], insert_hash['alarm_status'], insert_hash['summary'], insert_hash['host'])
        sql = 'INSERT INTO gw_events (%s) VALUES (%s)' % (insert_item, insert_value)
        cur.execute(sql, value)

        last_id_sql = 'SELECT LAST_INSERT_ID()'
        cur.execute(last_id_sql)
        last_insert_id = cur.fetchone()[0]
        event_ids.append(last_insert_id)

        cur.close()
    conn.commit()
    return event_ids

def update_event_data(conn, update_hash):
    cur = conn.cursor()
    value = (update_hash['event_status'], update_hash['gw_incident_id'], update_hash['gw_event_id'])
    sql = "UPDATE gw_events SET event_status=%s, gw_incident_id=%s, update_time=now(3) WHERE gw_event_id=%s"
    cur.execute(sql, value)
    cur.close()

def insert_incident_data(conn, insert_hash_list):
    for insert_hash in insert_hash_list:
        cur = conn.cursor()
        insert_item = 'incident_status,update_time,detected_host,error_event_id,normal_event_id,\
        customer_name,hostname,ci_name,op_comment,project_code'
        insert_value = '%s, now(), %s, %s, %s, %s, %s, %s, %s, %s'
        value = (gwcommon.GW_INCIDENT_STATUS_ACTIVE, insert_hash['detected_host'], insert_hash['error_event_id'], insert_hash['normal_event_id'],
            insert_hash['customer_name'], insert_hash['hostname'], insert_hash['ci_name'], insert_hash['op_comment'], insert_hash['project_code'])
        sql = 'INSERT INTO gw_incidents (%s) VALUES (%s)' % (insert_item, insert_value)
        cur.execute(sql, value)
        
        last_id_sql = 'SELECT LAST_INSERT_ID()'
        cur.execute(last_id_sql)
        last_insert_id = cur.fetchone()[0]

        cur.close()

        error_event_id = insert_hash['error_event_id']
        normal_event_id = insert_hash['normal_event_id']
        if error_event_id != None and normal_event_id != None:
            update_hash_error = {
                'event_status': gwcommon.GW_EVENT_STATUS_CLOSE,
                'gw_incident_id': last_insert_id,
                'gw_event_id': error_event_id,
            }
            update_event_data(conn, update_hash_error)

            update_hash_normal = {
                'event_status': gwcommon.GW_EVENT_STATUS_CLOSE,
                'gw_incident_id': last_insert_id,
                'gw_event_id': normal_event_id,
            }
            update_event_data(conn, update_hash_normal)

        elif error_event_id != None:
            update_hash = {
                'event_status': gwcommon.GW_EVENT_STATUS_ACTIVE,
                'gw_incident_id': last_insert_id,
                'gw_event_id': error_event_id,
            }
            update_event_data(conn, update_hash)

        elif normal_event_id != None:
            update_hash = {
                'event_status': gwcommon.GW_EVENT_STATUS_CLOSE,
                'gw_incident_id': last_insert_id,
                'gw_event_id': normal_event_id,
            }
            update_event_data(conn, update_hash)

    conn.commit()

def insert_incident_data_errorpattern(conn, insert_hash_list):
    for insert_hash in insert_hash_list:
        cur = conn.cursor()
        insert_item = 'incident_status,update_time,detected_host,error_event_id,normal_event_id,\
        customer_name,hostname,ci_name,op_comment,project_code'
        insert_value = '%s, now(), %s, %s, %s, %s, %s, %s, %s, %s'
        value = (gwcommon.GW_INCIDENT_STATUS_ACTIVE, insert_hash['detected_host'], insert_hash['error_event_id'], insert_hash['normal_event_id'],
            insert_hash['customer_name'], insert_hash['hostname'], insert_hash['ci_name'], insert_hash['op_comment'], insert_hash['project_code'])
        sql = 'INSERT INTO gw_incidents (%s) VALUES (%s)' % (insert_item, insert_value)
        cur.execute(sql, value)
        
        last_id_sql = 'SELECT LAST_INSERT_ID()'
        cur.execute(last_id_sql)
        last_insert_id = cur.fetchone()[0]

        cur.close()

    conn.commit()

def execute_sql_one(conn, sql, value, isDict=False):
    # cur = conn.cursor()
    cur = conn.cursor(dictionary=isDict)
    cur.execute(sql, value)
    # print(cur._executed)  # SQL見たい時用
    result = cur.fetchone()
    cur.close()
    conn.commit()
    return result

def get_insert_gw_events_data(conn, insert_hash, now, table = 'gw_events'):
    sql = 'SELECT COUNT(*) FROM %s where 1 = 1' % table
    value = ()

    hash_key = [
        'detected_time',
        'customer_ci',
        'customer_name',
        'hostname',
        'alarm_time',
        'ci_name',
        'device',
        'alarm_status',
        'summary',
        'host',
    ]
    for key in hash_key:
        sql += ' AND %s = %s' % (key, '%s')
        value += (insert_hash.get(key),)

    sql += ' AND update_time >= %s'
    value += (now.strftime("%Y.%m.%d %H:%M:%S"),)   # プログラムの実行時間でずれが生じるなら削除
    sql += ' AND detected_host = %s'
    value += (gwcommon.DETECTED_HOST,)

    return execute_sql_one(conn, sql, value)

def get_updated_gw_events_data(conn, gw_event_id, table='gw_events'):
    sql = 'SELECT * FROM %s where gw_event_id = %s' % (table, '%s')
    value = (gw_event_id, )
    return execute_sql_one(conn, sql, value, True)

def get_updated_gw_incidents_data(conn, gw_incident_id, table='gw_incidents'):
    sql = 'SELECT * FROM %s where gw_incident_id = %s' % (table, '%s')
    value = (gw_incident_id, )
    return execute_sql_one(conn, sql, value, True)

def table_initializ(conn):
    cur = conn.cursor()
    for db in [MY_DB_LOCAL, MY_DB_REMOTE]:
        cur.execute('TRUNCATE TABLE %s.gw_events' % db)
        cur.execute('TRUNCATE TABLE %s.gw_incidents' % db)
        cur.execute('TRUNCATE TABLE %s.gw_rules' % db)
        cur.execute('TRUNCATE TABLE %s.gw_rescue_events' % db)
    cur.close()
    conn.commit()

def set_sys_argv(message, filename):
    # コマンドライン引数を擬似的に再現するためsys.argv()に自前で格納
    # cleanしないと正しい引数を渡せないので注意
    sys.argv.clear()
    sys.argv.append('/usr/lib/zabbix/alertscripts/' + filename)
    sys.argv.append(filename)
    sys.argv.append('')
    sys.argv.append(message)

def set_unittest_mode():
    pathlib.Path(UNITTEST_FILE).touch()

def unset_unittest_mode():
    if os.path.exists(UNITTEST_FILE):
        os.remove(UNITTEST_FILE)

def set_stop_mode():
    pathlib.Path(STOP_FILE).touch()

def set_test_mode():
    pathlib.Path(TEST_FILE).touch()
    if os.path.exists(STOP_FILE):
        os.remove(STOP_FILE)
    if os.path.exists(PRIMARY_FILE):
        os.remove(PRIMARY_FILE)

def set_master_mode():
    if os.path.exists(STOP_FILE):
        os.remove(STOP_FILE)
    if os.path.exists(TEST_FILE):
        os.remove(TEST_FILE)
    pathlib.Path(PRIMARY_FILE).touch()

def set_slave_mode():
    if os.path.exists(STOP_FILE):
        os.remove(STOP_FILE)
    if os.path.exists(TEST_FILE):
        os.remove(TEST_FILE)
    if os.path.exists(PRIMARY_FILE):
        os.remove(PRIMARY_FILE)

def convert_str(wk_str):
    ret_str = ''
    if type(wk_str) is bytearray:
        ret_str = wk_str.decode()
    else:
        ret_str = wk_str

    return ret_str


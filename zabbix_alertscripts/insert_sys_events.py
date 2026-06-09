#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
## 概要 ##
## insert_sys_event.py
## insert_gw_events.pyを元にパトランプ処理削除、時間関連編集修正 by H.OOZERA
## 2017/08/31 update_timeをDBのNOW()関数利用およびlogレベル見直し by H.OOZERA
## 2017/09/04 DB接続失敗時、log出力がループにならないようフラグ制御を追加 by H.OOZERA

# Zabbix アクションから実行
# Insert into baogw.gw_events を実行するスクリプト
#
# 第1引数:sys.argv[0]:このスクリプトファイル名
# 第2引数:sys.argv[1]:Zabbixマクロ{ALERT.SENDTO}
# 第3引数:sys.argv[2]:Zabbixマクロ{ALERT.SUBJECT}
# 第4引数:sys.argv[3]:Zabbixマクロ{ALERT.MESSAGE}
"""

## import ##
##from datetime import datetime, timedelta
from datetime import datetime
import os
import sys
import logging
import logging.handlers
import re
import mysql.connector
import gwcommon as COM
# import from pathlib import Path

## スクリプトのパス、ファイル名を取得
# __file__ = '/usr/lib/zabbix/alertscripts/inset_sys_events.py'
SCRIPT_FILE = os.path.basename(__file__)

## log出力設定 ※rsyslogd に渡す設定
LOGGER = logging.getLogger(SCRIPT_FILE)
LOGGER.setLevel(COM.LOGGER_LEVEL_INSERT_SYS_EVENTS)
HANDLER = logging.handlers.SysLogHandler(address=('localhost', 514), facility='local6')
FORMATTER = logging.Formatter('%(name)s[%(process)d]: %(levelname)s: [%(lineno)d]%(message)s')
HANDLER.formatter = FORMATTER
LOGGER.addHandler(HANDLER)

def file_check(filename):
    """
    /var/lib/baogw/配下の 指定ファイルの有無をチェック
    """
    check_file = '/var/lib/baogw/' + filename
    return os.path.exists(check_file)

def format_check(check_pattern, argument):
    """
    フォーマットチェック関数定義
    """
    return check_pattern.match(argument) is not None

def contcode_search(argument):
    """
    制御コードチェック関数
    """
    controll_code = re.compile('[\x00-\x1F\x7F]')
    return controll_code.search(argument) is None

def erase_crlf(argument):
    """
    改行コードを削除
    """
    argument = argument.replace('\r', '')
    argument = argument.replace('\n', '')
    argument = argument.replace('\\r', '')
    argument = argument.replace('\\n', '')
    return argument

def replace_crlf_bao(argument):
    """
    改行コードをBAO-IF仕様に変更
    """
    argument = argument.replace('\r', '\&#xD;')
    argument = argument.replace('\n', '\&#xA;')
    argument = argument.replace('\\r', '\&#xD;')
    argument = argument.replace('\\n', '\&#xA;')
    return argument

def get_insert_value():
    """
    データの整合性をチェックし、DB へ INSERT する変数に格納
    """
    # 現時刻取得、update_time に格納
    now_datetime = datetime.now()
    update_time = now_datetime.strftime("%Y-%m-%d %H:%M:%S")

    # BAOGW LAN側 IPv4アドレス の第4オクテット ※共通ファイルから取得
    detected_host = COM.DETECTED_HOST
    #detected_host = COM.DETECTED_HOST01 # BAOGW 1 号機
    #detected_host = COM.DETECTED_HOST02 # BAOGW 2 号機

    # 第4引数を取得、デリミタで分解 デリミタは共通設定ファイルから取得（GW_DELIMITER）
    value3 = sys.argv[3]
    value3_split = value3.split(COM.GW_DELIMITER)
    value_length = len(value3_split)
    if value_length != 14:
        LOGGER.error('受信項目数が不正です。：発生ノード= %s 発生時間= %s ', detected_host, update_time)
        LOGGER.info('データ異常：デリミタにより分解したデータ数が14ではなく %s です ', value_length)
        LOGGER.debug('%s', value3)
        sys.exit()

    # customer_name Zabbixインベントリに登録したお客様名 制御コード以外すべての文字を許可
    customer_name = value3_split[12]
    customer_name = erase_crlf(customer_name)
    if contcode_search(customer_name) is not True:
        LOGGER.error(
            'customer_nameに規定外の文字が含まれます。：発生ノード= %s 発生時間= %s ',
            detected_host, update_time)
        LOGGER.info('customer_nameに規定外の文字が含まれます。customer_name= %s', customer_name)
        LOGGER.debug('%s', value3)
        sys.exit()
    if len(customer_name) >= 128:
        LOGGER.error('customer_nameの文字数オーバーです。：発生ノード= %s 発生時間= %s ', detected_host, update_time)
        LOGGER.info('customer_nameの文字数オーバーです。customer_name= %s', customer_name)
        LOGGER.debug('%s', value3)
        sys.exit()

    # hostname：日本語も可能性有、制御コード以外すべての文字を許可
    hostname = value3_split[2]
    hostname = erase_crlf(hostname)
    if contcode_search(hostname) is not True:
        LOGGER.error(
            'hostnameに規定外の文字が含まれます。：発生ノード= %s 発生時間= %s お客様名= %s',
            detected_host, update_time, customer_name)
        LOGGER.info('hostnameに規定外の文字が含まれます。： hostname= %s', hostname)
        LOGGER.debug('%s', value3)
        sys.exit()
    if len(hostname) >= 257:
        LOGGER.error(
            'hostnameの文字数オーバーです。：発生ノード= %s 発生時間= %s お客様名= %s',
            detected_host, update_time, customer_name)
        LOGGER.info('hostnameの文字数が規定以上です hostname= %s', hostname)
        LOGGER.debug('%s', value3)
        sys.exit()

    # cmmon_alm_log に共通出力アラームを設定
    cmmon_alm_log = "発生ノード=" + detected_host + ", 発生時間=" + update_time + \
    ", お客様名=" + customer_name + ", ホスト名=" + hostname

    # ci_name 個別監視トリガー名（アラーム名）日本語も可能性有、制御コード以外すべての文字を許可
    ci_name = value3_split[3]
    ci_name = erase_crlf(ci_name)
    if contcode_search(ci_name) is not True:
        LOGGER.error('ci_nameに規定外の文字が含まれます。 %s', cmmon_alm_log)
        LOGGER.info('ci_nameに規定外の文字が含まれます %s', ci_name)
        LOGGER.debug('%s', value3)
        sys.exit()
    if len(ci_name) >= 257:
        LOGGER.error('ci_nameの文字数が規定以上です。 %s', cmmon_alm_log)
        LOGGER.info('ci_nameの文字数が規定以上です。 ci_name= %s', ci_name)
        LOGGER.debug('%s', value3)
        sys.exit()

    # detected_time Zabbixのイベント生成時刻（Zabbixマクロから取得）
    detected_time = value3_split[9]
    check_pattern = re.compile(
        r'^[0-9]{4}.[0-9]{2}.[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}$'
    )
    if format_check(check_pattern, detected_time) is not True:
        LOGGER.error('detected_timeフォーマット異常です。 %s', cmmon_alm_log)
        LOGGER.info('detected_timeフォーマット異常です。detected_time= %s', detected_time)
        LOGGER.debug('%s', value3)
        sys.exit()
    try:
        datetime.strptime(detected_time, '%Y.%m.%d %H:%M:%S')
    except ValueError:
        LOGGER.error('detected_timeフォーマット異常です。 %s', cmmon_alm_log)
        LOGGER.info('detected_timeフォーマット異常です。detected_time= %s', detected_time)
        LOGGER.debug('%s', value3)
        sys.exit()

    # customer_ci 半角英数字のみ
    customer_ci = value3_split[11]
    customer_ci = erase_crlf(customer_ci)
    check_pattern = re.compile(r'^[a-zA-Z0-9-_/]+$')
    if format_check(check_pattern, customer_ci) is not True:
        LOGGER.error('customer_ciに規定外の文字が含まれます。 %s', cmmon_alm_log)
        LOGGER.info('customer_ciに規定外の文字が含まれます。customer_ci= %s', customer_ci)
        LOGGER.debug('%s', value3)
        sys.exit()
    if len(customer_ci) >= 65:
        LOGGER.error('customer_ciの文字数オーバーです。 %s', cmmon_alm_log)
        LOGGER.info('customer_ciの文字数オーバーです。customer_ci= %s', customer_ci)
        LOGGER.debug('%s', value3)
        sys.exit()


    # zabbixの日付(JST)を(UTC)に変換してalarm_timeに格納 2017/10/26 JSTそのまま渡しに変更 by h.oozera
    alarm_time = value3_split[1]
    # 文字列パターンチェック
    check_pattern = re.compile(
        r'^[0-9]{4}.[0-9]{2}.[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}$'
    )
    if format_check(check_pattern, alarm_time) is not True:
        LOGGER.error('alarm_timeフォーマット異常です。 %s', cmmon_alm_log)
        LOGGER.info('alarm_timeフォーマット異常です。alarm_time= %s', alarm_time)
        LOGGER.debug('%s', value3)
        sys.exit()
    # UTC時間およびフォーマットの変更（-9時間） 2017/10/26 フォーマット変換のみに変更 by h.oozera
    try:
        alarm_dt_jst = datetime.strptime(alarm_time, '%Y.%m.%d %H:%M:%S')
        alarm_time = alarm_dt_jst.strftime('%Y-%m-%d %H:%M:%S') + ".00"
    except ValueError:
        LOGGER.error('alarm_timeフォーマット異常です。 %s', cmmon_alm_log)
        LOGGER.info('alarm_timeフォーマット異常です。alarm_time= %s', alarm_time)
        LOGGER.debug('%s', value3)
        sys.exit()

    # device （将来利用予定）制御コード以外すべての文字を許可
    device = value3_split[7]
    device = erase_crlf(device)
    if contcode_search(device) is not True:
        LOGGER.error('deviceに規定外の文字が含まれます。 %s', cmmon_alm_log)
        LOGGER.info('deviceに規定外の文字が含まれます device= %s', device)
        LOGGER.debug('%s', value3)
        sys.exit()
    if len(device) >= 256:
        LOGGER.error('deviceの文字数オーバーです。 %s', cmmon_alm_log)
        LOGGER.info('deviceの文字数オーバーです。device= %s', device)
        LOGGER.debug('%s', value3)
        sys.exit()

    # alarm_status 'sec','syserror','sysnormal'以外は規定外（大文字小文字も判別）
    # alarm_status の文字は共有設定ファイルから抜き出す
    alarm_status = value3_split[5]
    alarm_status_pattern = (COM.GW_ALARM_STATUS_SEC, COM.GW_ALARM_STATUS_SYSERROR, \
        COM.GW_ALARM_STATUS_SYSNORMAL)
    if alarm_status not in alarm_status_pattern:
        LOGGER.error('alarm_statusが規定外です。 %s', cmmon_alm_log)
        LOGGER.info('alarm_statusが規定外です。 alarm_status= %s', alarm_status)
        LOGGER.debug('%s', value3)
        sys.exit()

    """
    # summary 個別監視装置の「補足」情報 制御コード以外すべての文字を許可
    # 改行が含まれる場合は、BAO連携用に変換する
    """
    summary = value3_split[4]
    summary = replace_crlf_bao(summary)
    if contcode_search(summary) is not True:
        LOGGER.error('補足に規定外の文字が含まれます %s', cmmon_alm_log)
        LOGGER.info('summaryに規定外の文字が含まれます summary= %s', summary)
        LOGGER.debug('%s', value3)
        sys.exit()
    if len(summary) >= 10000:
        LOGGER.info('summaryの文字数オーバーです。規定文字数以上をカットします。 %s', summary)
        LOGGER.debug('%s', value3)
        summary = summary[:10000]

    # host 制御コード以外すべての文字を許可
    host = value3_split[13]
    host = erase_crlf(host)
    if contcode_search(host) is not True:
        LOGGER.error('hostに規定外の文字が含まれます。 %s', cmmon_alm_log)
        LOGGER.info('hostに規定外の文字が含まれます host= %s', host)
        LOGGER.debug('%s', value3)
        sys.exit()
    if len(host) >= 128:
        LOGGER.error('hostの文字数オーバーです。 %s', cmmon_alm_log)
        LOGGER.info('hostの文字数オーバーです。host= %s', host)
        LOGGER.debug('%s', value3)
        sys.exit()

    insert_value = (
        detected_time, detected_host, customer_ci,
        customer_name, hostname, alarm_time, ci_name,
        device, alarm_status, summary, host
    )
    return insert_value

def db_connect_check(dbhost, db_location):
    """
    DB への接続状態確認
    """
    # DB接続障害時、syserrorループ抑止フラグ
    db_ng_filename = db_location + '_db_ng'
    # データベース（baogw）への接続情報
    try:
        db_connect = mysql.connector.connect(
            host=dbhost,
            db=COM.MY_DB,
            user=COM.MY_USER,
            password=COM.MY_PASSWD,
            connection_timeout=3
        )
        db_connect.close()
        LOGGER.info('%s DB[%s] 接続成功', db_location, dbhost)
        if file_check(db_ng_filename) is True:
            # 抑止フラグ削除
            os.remove('/var/lib/baogw/' + db_ng_filename)
            LOGGER.info('抑止フラグ(/var/lib/baogw/%s)を削除しました。', db_ng_filename)
        return True
    except Exception as msg:
        if file_check(db_ng_filename) is True:
            LOGGER.info('抑止フラグ(/var/lib/baogw/%s)がありました。ログ出力をスキップします。', db_ng_filename)
        else:
            LOGGER.critical('%s DB[%s] 接続失敗', db_location, dbhost)
            LOGGER.info('%s', msg)
            # 抑止フラグ作成
            ng_flg = open('/var/lib/baogw/' + db_ng_filename, 'a')
            ng_flg.close()
            LOGGER.info('抑止フラグ(/var/lib/baogw/%s)を作成しました。', db_ng_filename)
        return False

def connect_db(dbhost):
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
    return connect_baogw

def insert_baogw(dbhost, table_name, insert_value, step_num):
    """
    INSERT用関数
    """
    # データベース（baogw）への接続情報
    dbbaogw = connect_db(dbhost)
    baogwcur = dbbaogw.cursor(buffered=True) # カーソル
    sql = 'INSERT INTO ' + table_name + ' (update_time, detected_time,\
    detected_host, customer_ci, customer_name, hostname,\
    alarm_time, ci_name, device, alarm_status, summary, host\
    ) VALUES (now(3), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);'
    # DB接続障害時、syserrorループ抑止フラグ
    try:
        baogwcur.execute(sql, insert_value)
        LOGGER.info('[%s] %s %s INSERT成功', step_num, dbhost, table_name)
        # コミット
        dbbaogw.commit()
    except mysql.connector.errors.IntegrityError as msg:
        LOGGER.critical('[%s] %s %s INSERT失敗 %s', step_num, dbhost, table_name, insert_value)
        LOGGER.info('%s', msg)
    # 終了処理
    baogwcur.close()
    dbbaogw.close()

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
    LOGGER.info('gw_incident_id=%s', gw_incident_id)
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
    alarm_time, customer_name, hostname, ci_name 全てが一致するレコードのうち、もっとも古いレコード以外を、重複レコードとみなす
    """
    dbbaogw = connect_db(dbhost)
    baogwcur = dbbaogw.cursor(dictionary=True)
    sql = "SELECT * FROM gw_events \
    WHERE alarm_time=%s and customer_name=%s and hostname=%s and ci_name=%s \
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

def update_gw_incidents(dbhost, incident_status, gw_incident_id):
    """
    gw_incidents テーブルを更新する
    """
    dbbaogw = connect_db(dbhost)
    baogwcur = dbbaogw.cursor(buffered=True)
    sql = "UPDATE gw_incidents SET incident_status=%s, update_time=now() \
    WHERE gw_incident_id=%s"
    sql_values = (incident_status, gw_incident_id)
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
    now_datetime = datetime.now()
    update_time = now_datetime.strftime("%Y-%m-%d %H:%M:%S")
    dbbaogw = connect_db(dbhost)
    baogwcur = dbbaogw.cursor(buffered=True)
    sql = "insert into gw_incidents (incident_status,update_time,detected_host,error_event_id,customer_name,hostname,\
    ci_name,project_code) values (%s,%s,%s,%s,%s,%s,%s,%s)"
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
        LOGGER.critical('Stopped: Function of insert_error_id_into_gw_incidents is failed.')
        LOGGER.info(msg)
    return gw_incident_id

def insert_normal_id_into_gw_incidents(dbhost, insert_values):
    """
    gw_incidents テーブルへ新規レコード挿入(sysnormal)
    """
    now_datetime = datetime.now()
    update_time = now_datetime.strftime("%Y-%m-%d %H:%M:%S")
    dbbaogw = connect_db(dbhost)
    baogwcur = dbbaogw.cursor(buffered=True)
    sql = "insert into gw_incidents (incident_status,update_time,detected_host,normal_event_id,customer_name,hostname,\
    ci_name,project_code) values (%s,%s,%s,%s,%s,%s,%s,%s)"
    insert_values.insert(1, update_time)
    try:
        baogwcur.execute(sql, insert_values)
        dbbaogw.commit()
        LOGGER.info('success: insert gw_incidentsテーブル')
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

def main():
    """
    スクリプト本体
    """
    # gw_events へ INSERT する変数を取得
    insert_value = get_insert_value()

    # 接続するDBのhostを定義
    local_host = COM.MY_HOST
    remote_host = COM.REMOTE_HOST
    current_host = local_host

    # testファイルの有無を確認
    if file_check('test') is True:
        LOGGER.info('testモードのため、テストモードで動作実行')
        # 事前にDBへ接続確認
        db_location = 'Local'
        if db_connect_check(local_host, db_location) is True:
            # local_DBに情報挿入
            insert_baogw(local_host, 'gw_events', insert_value, 'End1')

    # Primaryファイルの有無を確認
    elif file_check('primary') is True:
        LOGGER.info('マスターモードのたため、マスター動作実行')
        # 事前にDBへ接続確認
        db_location = 'Local'
        if db_connect_check(local_host, db_location) is True:
            # local_DBに情報挿入
            insert_baogw(local_host, 'gw_events', insert_value, 'End1')

    else:
        LOGGER.info('スレーブモードのため、スレーブ動作実行')
        db_location = 'Remote'
        # 事前にDBへ接続確認
        if db_connect_check(remote_host, db_location) is True:
            # Remote_DBに情報挿入
            current_host = remote_host
            insert_baogw(remote_host, 'gw_events', insert_value, 'End2')
        else:
            # local_DBにrescue情報挿入
            LOGGER.info('Remote_DBに情報挿入失敗。local_DBにrescue情報挿入します。')
             # 事前にDBへ接続確認
            db_location = 'Local'
            if db_connect_check(local_host, db_location) is True:
                # local_DBに情報挿入
                insert_baogw(local_host, 'gw_rescue_events', insert_value, 'End3')
            sys.exit()
    # 新規イベント(event_status=0)のレコードを抽出して1行ずつ処理する
    new_event = get_new_events(current_host, insert_value[3], insert_value[4], insert_value[5], insert_value[6])
    gw_event_id = new_event.get('gw_event_id')
    event_status = str(new_event.get('event_status'))
    detected_host = new_event.get('detected_host')
    customer_ci = new_event.get('customer_ci')
    customer_name = new_event.get('customer_name')
    hostname = new_event.get('hostname')
    alarm_time = new_event.get('alarm_time')
    ci_name = new_event.get('ci_name')
    alarm_status = new_event.get('alarm_status')
    gw_incident_id = None #NULLを代入しておく
    kisys_status = None  #NULLを代入しておく
    project_code = customer_ci #ZABBIXアクションからINVENTORY.TAGで受け取った値
    kisys_incidentid = ''
    #""" 重複レコードの有無確認 """
    dup_events=get_dup_events(current_host, insert_value[5], insert_value[3], insert_value[4], insert_value[6])
    if gw_event_id != dup_events[0].get('gw_event_id'):
        LOGGER.info('重複レコードです gw_event_id=%s, event_status=99 にUPDATE', gw_event_id)
        update_gw_events(
            current_host, COM.GW_EVENT_STATUS_DUP, gw_incident_id, gw_event_id, kisys_status
            )
        return
     # """gw_incidentsテーブルにインサート"""
    insert_values = [
        COM.GW_INCIDENT_STATUS_CLOSE,
        detected_host,
        gw_event_id,
        customer_name,
        hostname,
        ci_name,
        project_code
    ]
    if alarm_status == COM.GW_ALARM_STATUS_SYSNORMAL:
        try:
            gw_incident_id = insert_normal_id_into_gw_incidents(current_host, insert_values)
            LOGGER.info(
                'sysnormal報処理:インシデント登録しました。gw_incident_id=%s',
                gw_incident_id)
            update_gw_events(
                current_host, COM.GW_EVENT_STATUS_CLOSE, gw_incident_id, gw_event_id, kisys_status
                )
            LOGGER.info(
                'sysnormal報処理:イベントID：%sとインシデントID：%sを紐づけました。',
                gw_event_id, gw_incident_id
                )
        except Exception as msg:
            LOGGER.error(
                'sysnormal報処理:インシデントテーブル更新失敗。gw_event_id=%s, gw_incident_id=%s',
                gw_event_id, gw_incident_id
                )
            LOGGER.debug(msg)
    else:
        try:
            gw_incident_id = insert_error_id_into_gw_incidents(current_host, insert_values)
            LOGGER.info(
                'syserror報処理:インシデント登録しました。gw_incident_id=%s',
                gw_incident_id)
            update_gw_events(
                current_host, COM.GW_EVENT_STATUS_CLOSE, gw_incident_id, gw_event_id, kisys_status
                )
            LOGGER.info(
                'syserror報処理:イベントID：%sとインシデントID：%sを紐づけました。',
                gw_event_id, gw_incident_id
                )
        except Exception as msg:
            LOGGER.error(
                'syserror報処理:インシデントテーブル更新失敗。gw_event_id=%s, gw_incident_id=%s',
                gw_event_id, gw_incident_id
                )
            LOGGER.debug(msg)

if __name__ == '__main__':
    try:
        main()
    except Exception as msg:
        LOGGER.critical('[End0] Stopped by an unknown error.')
        LOGGER.info('%s', msg)
# EOF

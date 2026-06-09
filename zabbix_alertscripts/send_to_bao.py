#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
## 概要 ##
send_to_bao.py
gw_events から event_status = 0 を抜き出し処理

## 2017/09/15 testモード追加 by H.OOZERA
## 2018/02/15 シェルの実装部分をpythonのみで実装するように修正 by K.YAMADATE
## 2018/04/05 BAO-IF連携値修正（value_summaryを100ﾊﾞｲﾄ制限、value_ciをホスト_顧客略称） by K.YAMADATE
## 2018/07/25 Kompira連携機能 アラートフィルタ・キャンセル機能 を追加 by K.YAMADATE
## 2019/03/19 BAOからのエラーメッセージの先頭文字がINCでない場合はエラーとする。 by IMAMURA.
## 2019/04/26 /var/log/gwscripts/baosoap-oldresのタイムスタンプの出力タイミングを変更 by FUJII
## 2019/06/18 K-ISYS連携改良 ホストグループ設定による分岐を追加 by SHIBUYA
## 2020/03/31 BAOGWのUI出力を、gw_incidentsベースに切り替える対応を実施 by MOCHIZUKI
## 2020/04/03 ルール30適応 かつ 時間内復旧時のキャンセル処理でkisys_incident_idをgw_incidentsテーブルに格納していない問題を修正 by TAKETA
## 2020/04/04 重複および、gw_incidentsテーブル未登録時の救済処理を削除 By TAKETA
"""

## 共通 ########################## 別途、共通設定ファイルへ

## import ##
import traceback
from datetime import datetime as dt
from datetime import timedelta
import os
import fcntl
import time
import logging
import logging.handlers
import re
import requests
import subprocess
import json
import urllib.request
import mysql.connector
import gwcommon as COM
import gwfunction as FUNC
import bao_tm_post as CLIENT
import sys

##################################

## スクリプトのパス、ファイル名を取得
# __file__ = '/usr/lib/zabbix/alertscripts/send_to_bao.py'
SCRIPT_FILE = os.path.basename(__file__)

""" log出力設定 ※rsyslogd に渡す設定 """
LOGGER = logging.getLogger(SCRIPT_FILE)
#LOGGER.setLevel(logging.INFO) # 出力レベルの設定
LOGGER.setLevel(COM.LOGGER_LEVEL_SEND_TO_BAO) # 出力レベルの設定
HANDLER = logging.handlers.SysLogHandler(address=('localhost', 514), facility='local6') # 出力先の設定
FORMATTER = logging.Formatter('%(name)s[%(process)d]: %(levelname)s: [%(lineno)d]%(message)s')
HANDLER.formatter = FORMATTER
LOGGER.addHandler(HANDLER)

def lock_file(locktarget):
    """
    ファイルロックを試み、ロックできなければ終了
    """
    lock_file_name = '%s.lock' % (locktarget)
    fp_lock = open(lock_file_name, 'w')
    try:
        fcntl.flock(fp_lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError as msg:
        LOGGER.info(msg)
        LOGGER.info('Another process is running, so exit.')
        sys.exit()
    return fp_lock

def file_check(filename):
    """
    動作フラグファイル(/var/lib/baogw/ 配下) の有無をチェック
    """
    check_file = '/var/lib/baogw/' + filename
    return os.path.exists(check_file)

def kisys_maintenance(nowdatetimestr):
    """
    gw_rulesテーブルから、customer_name=KISYS のルールを抽出
    """
    dbbaogw = FUNC.connect_db_unix_socket(COM.MY_HOST)
    baogwcur = dbbaogw.cursor(buffered=True)
    sql = "SELECT * FROM gw_rules WHERE \
    rule_status=1 and customer_name='KISYS' and start_time<=%s and end_time>=%s \
    and hostname='*' and ci_name='*' and action_no='90' \
    ORDER BY rule_id DESC"
    sql_values = (nowdatetimestr, nowdatetimestr)
    try:
        baogwcur.execute(sql, sql_values)
        kisys_mainte = baogwcur.fetchall()
        baogwcur.close()
        dbbaogw.close()
    except Exception as msg:
        LOGGER.critical('Stopped: Function of kisys_maintenance is failed.')
        LOGGER.info(msg)
        sys.exit()
    return kisys_mainte

def get_new_events():
    """
    gw_events から新規イベント(event_status=0)を抜き出す
    """
    dbbaogw = FUNC.connect_db_unix_socket(COM.MY_HOST)
    baogwcur = dbbaogw.cursor(buffered=True)
    sql = "SELECT * FROM gw_events WHERE kisys_status in (9, 49, 59, 69, 79) ORDER BY alarm_time ASC"
    #sql = "SELECT * FROM gw_events WHERE event_status=0 ORDER BY alarm_time ASC LIMIT 1"
    try:
        baogwcur.execute(sql)
        new_events = baogwcur.fetchall()
        baogwcur.close()
        dbbaogw.close()
    except Exception as msg:
        LOGGER.critical('Stopped: Function of get_new_events is failed.')
        LOGGER.info(msg)
        sys.exit()
    return new_events

def get_existing_incident(gw_incident_id):
    """
    gw_incidents テーブルから id が一致する既存のインシデントを取得する
    """
    dbbaogw = FUNC.connect_db_unix_socket(COM.MY_HOST)
    baogwcur = dbbaogw.cursor(buffered=True)
    sql = "SELECT * FROM gw_incidents WHERE gw_incident_id=%s"
    sql_values = (str(gw_incident_id),)
    try:
        baogwcur.execute(sql, sql_values)
        gw_incidents = baogwcur.fetchall()
        baogwcur.close()
        dbbaogw.close()
    except Exception as msg:
        LOGGER.critical('Stopped: Function of get_incident_status is failed.')
        LOGGER.info(msg)
        sys.exit()
    return gw_incidents[0]

def get_paired_error_events(gw_incident_id):
    """
    既存のError報を探す
    gw_events テーブルから gw_incident_id が一致するイベントを取得する
    """
    event_record = []
    dbbaogw = FUNC.connect_db_unix_socket(COM.MY_HOST)
    baogwcur = dbbaogw.cursor(buffered=True)
    sql = "SELECT gw_event_id,alarm_time,kisys_status FROM gw_events \
    WHERE gw_incident_id=%s and alarm_status='error' \
    ORDER BY alarm_time DESC"
    sql_values = (str(gw_incident_id),)
    try:
        baogwcur.execute(sql, sql_values)
        existing_events = baogwcur.fetchall()
        if existing_events:
            sql = "SELECT kisys_incidentid FROM gw_incidents \
            WHERE gw_incident_id=%s \
            ORDER BY update_time DESC"
            sql_values = (str(gw_incident_id),)
            baogwcur.execute(sql, sql_values)
            existing_incidents = baogwcur.fetchall()
            existing_incident = existing_incidents[0][0]
            event_record = (
                existing_events[0][0], str(gw_incident_id),
                existing_events[0][1], existing_incident, existing_events[0][2])
        baogwcur.close()
        dbbaogw.close()
    except Exception as msg:
        LOGGER.critical('Stopped: Function of get_paired_error_events is failed.')
        LOGGER.info(msg)
        sys.exit()
    return event_record

def update_gw_events(gw_incident_id, gw_event_id, kisys_status):
    """
    gw_events テーブルを更新する
    """
    dbbaogw = FUNC.connect_db_unix_socket(COM.MY_HOST)
    baogwcur = dbbaogw.cursor(buffered=True)
    sql = "UPDATE gw_events SET gw_incident_id=%s, update_time=now(3), \
    kisys_status=%s WHERE gw_event_id=%s"
    sql_values = (gw_incident_id, kisys_status, gw_event_id)
    try:
        baogwcur.execute(sql, sql_values)
        dbbaogw.commit()
        baogwcur.close()
        dbbaogw.close()
        LOGGER.debug('Success: update_gw_events gw_event_id=%s', gw_event_id)
    except Exception as msg:
        LOGGER.critical('Stopped: Function of update_gw_events is failed.')
        LOGGER.info(msg)
        sys.exit()

def update_gw_incidents_add_kisys_incidentid(kisys_incidentid, gw_incident_id):
    """
    gw_incidents テーブルを更新する
    """
    dbbaogw = FUNC.connect_db_unix_socket(COM.MY_HOST)
    baogwcur = dbbaogw.cursor(buffered=True)
    sql = "UPDATE gw_incidents SET kisys_incidentid=%s, update_time=now() \
    WHERE gw_incident_id=%s"
    sql_values = (kisys_incidentid, gw_incident_id)
    try:
        baogwcur.execute(sql, sql_values)
        dbbaogw.commit()
        baogwcur.close()
        dbbaogw.close()
    except Exception as msg:
        LOGGER.critical('Stopped: Function of update_gw_incidents_add_kisys_incidentid is failed.')
        LOGGER.info(msg)
        sys.exit()

def bao_soap(new_event, kisys_incidentid, kisys_status):
    host = new_event[18]
    # ZabbixApiインスタンス作成
    api = FUNC.ZabbixApi(COM.ZABBIX_IP, COM.ZABBIX_USER, COM.ZABBIX_PASSWD)
    try:
        alias = FUNC.get_alias_by_host(api, host)
        return CLIENT.BAO_TM_CLIENT().send(new_event, kisys_incidentid, kisys_status, alias)
    except Exception as msg:
        LOGGER.info(msg)
        LOGGER.info('通信失敗として、処理を継続します')
        return 'Failure'

def get_gw_event_by_pk(gw_event_id):
    """
    gw_events から gw_event_id が一致するイベントを抜き出す
    """
    dbbaogw = FUNC.connect_db_unix_socket(COM.MY_HOST)
    baogwcur = dbbaogw.cursor(buffered=True)
    sql = "SELECT * FROM gw_events WHERE gw_event_id=%s" % gw_event_id
    try:
        baogwcur.execute(sql)
        gw_events = baogwcur.fetchall()
        if gw_events:
            gw_event = gw_events[0]
        baogwcur.close()
        dbbaogw.close()
    except Exception as msg:
        LOGGER.critical('Stopped: Function of get_gw_events_by_pk is failed.')
        LOGGER.info(msg)
        sys.exit()
    return gw_event

def update_send_status(gw_event_id, send_status):
    """
    送信状況を更新する
    """
    dbbaogw = FUNC.connect_db_unix_socket(COM.MY_HOST)
    baogwcur = dbbaogw.cursor(buffered=True)
    sql = "UPDATE gw_events SET kisys_status=%s, update_time=now(3) WHERE gw_event_id=%s"
    sql_values = (send_status, gw_event_id)
    try:
        baogwcur.execute(sql, sql_values)
        dbbaogw.commit()
        baogwcur.close()
        dbbaogw.close()
        LOGGER.debug('Success: update_send_status gw_event_id=%s', gw_event_id)
    except Exception as msg:
        LOGGER.critical('Stopped: Function of update_send_status is failed.')
        LOGGER.info(msg)
        sys.exit()

def send_to_kompira(kisys_incidentid, gw_event_id):
    """
    KompiraへREST APIを使用して連携する
    """
    kompira_status = ""
    # Kompira連携情報の取得
    gw_event = get_gw_event_by_pk(gw_event_id)
    # ZabbixApiインスタンス作成
    api = FUNC.ZabbixApi(COM.ZABBIX_IP, COM.ZABBIX_USER, COM.ZABBIX_PASSWD)
    # 顧客名からホストグループリストを抽出
    hostgroups = FUNC.get_hostgroups_by_host(api, gw_event[18])
    # 「80:Kompira連携しません」以外または顧客がKompira連携顧客の場合、Kompira連携を行う
    if FUNC.get_action_no("Kompira", "*", "*") == COM.KOMPIRA_STATUS_NOSEND \
       and COM.KOMPIRA_RELATION_HOSTGROUP not in hostgroups:
        LOGGER.info('Kompira連携しません。kisys_incidentid=%s', kisys_incidentid)
        kompira_status = COM.KOMPIRA_STATUS_NOSEND
    else:
        LOGGER.info('Kompira連携を開始します。kisys_incidentid=%s', kisys_incidentid)
        data = {}
        data["incident_id"] = kisys_incidentid
        data["customer_name"] = gw_event[7]
        data["hostname"] = gw_event[8]
        data["alarm_name"] = gw_event[10]
        data["customer_code"] = gw_event[6]
        data["alarm_date"] = (gw_event[9] - timedelta(hours=9)).strftime('%Y-%m-%dT%H:%M:%SZ')
        data["alarm_status"] = gw_event[12]
        json_data = json.dumps(data).encode("utf-8")
        headers = {}
        headers["Content-Type"] = "application/json"
        headers["Accept"] = "application/json"
        headers["Authorization"] = "Token %s" % COM.KOMPIRA_TOKEN
        try:
            # Kompira連携
            response = requests.post(COM.KOMPIRA_URL, data=json_data, headers=headers, verify=False)
            response.raise_for_status()
        except requests.exceptions.RequestException as err:
            LOGGER.error('Kompiraへの送信に失敗しました。kisys_incidentid=%s', kisys_incidentid)
            LOGGER.info(err)
            kompira_status = COM.KOMPIRA_STATUS_FAILURE
        else:
            LOGGER.info('Kompiraへの送信に成功しました。kisys_incidentid=%s', kisys_incidentid)
            kompira_status = COM.KOMPIRA_STATUS_SUCCESS

    # 送信状況を更新
    kisys_status = gw_event[17]
    update_send_status(gw_event_id, "%s,%s" % (kisys_status, kompira_status))

def cancel_error_event(new_event):
    gw_event_id = new_event[0]
    gw_incident_id = new_event[3]
    customer_name = new_event[7]
    hostname = new_event[8]
    ci_name = new_event[10]
    kisys_status = None #NULLを代入しておく
    LOGGER.info('キャンセル処理開始 gw_event_id=%s', gw_event_id)
    # """ alarm_status = error の処理 """
    kisys_incidentid = ''
    bao_soap_result = bao_soap(new_event, kisys_incidentid, COM.SOAP_VALUE_STATUS_NEW)
    if bao_soap_result == 'No_reply':
        kisys_incidentid = None
        kisys_status = COM.GW_KISYS_STATUS_CANCEL_NORES
        LOGGER.error('キャンセル処理:BAO無応答 gw_event_id=%s', gw_event_id)
    elif bao_soap_result == 'Failure':
        kisys_incidentid = None
        kisys_status = COM.GW_KISYS_STATUS_CANCEL_NG
        LOGGER.error('キャンセル処理:BAO連携失敗 gw_event_id=%s', gw_event_id)
    else:
        kisys_incidentid = bao_soap_result
        kisys_status = COM.GW_KISYS_STATUS_CANCEL_OK
        LOGGER.info('キャンセル処理:BAO連携成功 gw_event_id=%s', gw_event_id)
    try:
        update_status = kisys_status
        update_gw_events(
            gw_incident_id, gw_event_id, update_status
            )
        update_gw_incidents_add_kisys_incidentid(kisys_incidentid, gw_incident_id)
        LOGGER.info(
            'キャンセル処理:関連テーブルを更新しました。gw_event_id=%s, gw_incident_id=%s, kisys_incidentid=%s',
            gw_event_id, gw_incident_id, kisys_incidentid
            )
    except Exception as msg:
        LOGGER.error(
            'キャンセル処理:関連テーブル更新失敗。gw_event_id=%s, gw_incident_id=%s, kisys_incidentid=%s',
            gw_event_id, gw_incident_id, kisys_incidentid
            )
        LOGGER.debug(msg)

def cancel_normal_event(new_event):
    gw_event_id = new_event[0]
    gw_incident_id = new_event[3]
    kisys_status = None #NULLを代入しておく
    LOGGER.debug('キャンセル処理開始 gw_event_id=%s', gw_event_id)
    event_record = get_paired_error_events(gw_incident_id)
    related_gw_event_id = event_record[0]
    kisys_incidentid = event_record[3]
    LOGGER.debug(
        'キャンセル処理:関連erro報取得成功 gw_event_id=%s, gw_incident_id=%s, kisys_incidentid=%s',
        gw_event_id, gw_incident_id, kisys_incidentid
        )
    if kisys_incidentid:
        bao_soap_result = bao_soap(new_event, kisys_incidentid, COM.SOAP_VALUE_STATUS_CANCEL)
    else:
        bao_soap_result = 'No_send'
    if bao_soap_result == 'No_reply':
        kisys_status = COM.GW_KISYS_STATUS_CANCEL_NORES
        LOGGER.error(
            'キャンセル処理:BAO無応答 gw_event_id=%s, gw_incident_id=%s, kisys_incidentid=%s',
            gw_event_id, gw_incident_id, kisys_incidentid
            )
    elif bao_soap_result == 'Failure':
        kisys_status = COM.GW_KISYS_STATUS_CANCEL_NG
        LOGGER.error(
            'キャンセル処理:BAO更新失敗 gw_event_id=%s, gw_incident_id=%s, kisys_incidentid=%s',
            gw_event_id, gw_incident_id, kisys_incidentid
            )
    elif bao_soap_result == 'No_send':
        LOGGER.info(
            'キャンセル処理:BAO更新-未実施 gw_event_id=%s, gw_incident_id=%s, kisys_incidentid=%s',
            gw_event_id, gw_incident_id, kisys_incidentid
            )
    else:
        kisys_status = COM.GW_KISYS_STATUS_CANCEL_OK
        LOGGER.info(
            'キャンセル処理:BAO更新成功 gw_event_id=%s, gw_incident_id=%s, kisys_incidentid=%s',
            gw_event_id, gw_incident_id, kisys_incidentid
            )
    try:
        # イベントステータス以外を更新
        update_gw_events(
            gw_incident_id, gw_event_id, kisys_status
        )
        LOGGER.info(
            'キャンセル処理:関連テーブルを更新しました。gw_event_id=%s, gw_incident_id=%s, kisys_incidentid=%s',
            gw_event_id, gw_incident_id, kisys_incidentid
            )
    except Exception as msg:
        LOGGER.error(msg)
        LOGGER.error(
            'キャンセル処理:関連テーブル更新失敗 gw_event_id=%s, gw_incident_id=%s, kisys_incidentid=%s',
            gw_event_id, gw_incident_id, kisys_incidentid
            )

def normal_update_bao_result(kisys_status, gw_event_id, event_record, last_kisys_status):
    gw_incident_id = event_record[1]
    kisys_incidentid = event_record[3]
    error_kisys_status = event_record[4].split(',')[0]
    # kisys_status=BAO連携結果で設定したkisys_status
    # last_kisys_status=BAO連携結果で設定する前のkisys_status(send_to_baoにわたってきた時点のもの)
    update_status = kisys_status

    # kisys_status=59（タイムアウト）の時
    if last_kisys_status == COM.GW_KISYS_STATUS_KISYS_CONNECT_NORECOVERY:
        if kisys_status == COM.GW_KISYS_STATUS_NEW_OK:
            update_status = COM.GW_KISYS_STATUS_NORECOVERY_OK
        elif kisys_status == COM.GW_KISYS_STATUS_NEW_NG:
            update_status = COM.GW_KISYS_STATUS_NORECOVERY_NG
        elif kisys_status == COM.GW_KISYS_STATUS_NEW_NORES:
            update_status = COM.GW_KISYS_STATUS_NORECOVERY_NORES
        # todo この分岐は必要？
        elif kisys_status == COM.GW_KISYS_STATUS_NOSEND_BY_HOSTGROUP:
            update_status = COM.GW_KISYS_STATUS_NORECOVERY_NOSEND
    
    # kisys_status=69（ルール10）の時
    elif last_kisys_status == COM.GW_KISYS_STATUS_NOSEND_MANUAL:
        if kisys_status == COM.GW_KISYS_STATUS_NEW_OK:
            update_status = COM.GW_KISYS_STATUS_NOSEND_OK
        elif kisys_status == COM.GW_KISYS_STATUS_NEW_NG:
            update_status = COM.GW_KISYS_STATUS_NOSEND_NG
        elif kisys_status == COM.GW_KISYS_STATUS_NEW_NORES:
            update_status = COM.GW_KISYS_STATUS_NOSEND_NORES
    
    # kisys_status=79（ルール20）の時
    elif last_kisys_status == COM.GW_KISYS_STATUS_NOPATOLAMP_MANUAL:
        if kisys_status == COM.GW_KISYS_STATUS_NEW_OK:
            update_status = COM.GW_KISYS_STATUS_NOPATOLAMP_OK
        elif kisys_status == COM.GW_KISYS_STATUS_NEW_NG:
            update_status = COM.GW_KISYS_STATUS_NOPATOLAMP_NG
        elif kisys_status == COM.GW_KISYS_STATUS_NEW_NORES:
            update_status = COM.GW_KISYS_STATUS_NOPATOLAMP_NORES

    # kisys_status=9（ルール無）のときはそのままBAO連携結果で設定したkisys_statusで更新する
    try:
        # イベントステータス以外を更新する
        update_gw_events(gw_incident_id, gw_event_id, update_status)
        LOGGER.info(
            'normal報処理:関連テーブルを更新しました。gw_event_id=%s, gw_incident_id=%s, kisys_incidentid=%s',
            gw_event_id, gw_incident_id, kisys_incidentid
            )
    except Exception as msg:
        LOGGER.error(msg)
        LOGGER.error(
            'normal報処理:関連テーブル更新失敗 gw_event_id=%s, gw_incident_id=%s, kisys_incidentid=%s',
            gw_event_id, gw_incident_id, kisys_incidentid
            )
    # K-ISYS連携に成功した場合
    if kisys_incidentid and kisys_status == COM.GW_KISYS_STATUS_NEW_OK:
        # Kompira連携
        send_to_kompira(kisys_incidentid, gw_event_id)

def update_kisys_incident_report_to_bao(new_event, gw_event_id, event_record):
    kisys_status = None
    last_kisys_status = new_event[17]
    gw_incident_id = event_record[1]
    kisys_incidentid = event_record[3]
    if kisys_incidentid:
        bao_soap_result = bao_soap(new_event, kisys_incidentid, COM.SOAP_VALUE_STATUS_UPDATE)
    else:
        bao_soap_result = 'No_send'
    if bao_soap_result == 'No_reply':
        kisys_status = COM.GW_KISYS_STATUS_UPDATE_NORES
        LOGGER.error(
            'normal報処理:BAO無応答 gw_event_id=%s, gw_incident_id=%s, kisys_incidentid=%s',
            gw_event_id, gw_incident_id, kisys_incidentid
            )
    elif bao_soap_result == 'Failure':
        kisys_status = COM.GW_KISYS_STATUS_UPDATE_NG
        LOGGER.error(
            'normal報処理:BAO更新失敗 gw_event_id=%s, gw_incident_id=%s, kisys_incidentid=%s',
            gw_event_id, gw_incident_id, kisys_incidentid
            )
    elif bao_soap_result == 'No_send':
        LOGGER.info(
            'normal報処理:BAO更新-未実施 gw_event_id=%s, gw_incident_id=%s, kisys_incidentid=%s',
            gw_event_id, gw_incident_id, kisys_incidentid
            )
    else:
        kisys_status = COM.GW_KISYS_STATUS_UPDATE_OK
        LOGGER.info(
            'normal報処理:BAO更新成功 gw_event_id=%s, gw_incident_id=%s, kisys_incidentid=%s',
            gw_event_id, gw_incident_id, kisys_incidentid
            )
    normal_update_bao_result(kisys_status, gw_event_id, event_record, last_kisys_status)

def error_update_bao_result(kisys_incidentid, kisys_status, gw_event_id, gw_incident_id, last_kisys_status):
    try:
        # kisys_status=BAO連携結果で設定したkisys_status
        # last_kisys_status=BAO連携結果で設定する前のkisys_status(send_to_baoにわたってきた時点のもの)
        update_status = kisys_status
        # kisys_status=59（タイムアウト）の時
        if last_kisys_status == COM.GW_KISYS_STATUS_KISYS_CONNECT_NORECOVERY:
            # BAO連携結果OK
            if kisys_status == COM.GW_KISYS_STATUS_NEW_OK:
                update_status = COM.GW_KISYS_STATUS_NORECOVERY_OK
            # BAO連携結果NG
            elif kisys_status == COM.GW_KISYS_STATUS_NEW_NG:
                update_status = COM.GW_KISYS_STATUS_NORECOVERY_NG
            # BAO連携結果No_reply
            elif kisys_status == COM.GW_KISYS_STATUS_NEW_NORES:
                update_status = COM.GW_KISYS_STATUS_NORECOVERY_NORES
            # todo この分岐必要？
            elif kisys_status == COM.GW_KISYS_STATUS_NOSEND_BY_HOSTGROUP:
                update_status = COM.GW_KISYS_STATUS_NORECOVERY_NOSEND

        # kisys_status=69（ルール10）の時
        elif last_kisys_status == COM.GW_KISYS_STATUS_NOSEND_MANUAL:
            if kisys_status == COM.GW_KISYS_STATUS_NEW_OK:
                update_status = COM.GW_KISYS_STATUS_NOSEND_OK
            elif kisys_status == COM.GW_KISYS_STATUS_NEW_NG:
                update_status = COM.GW_KISYS_STATUS_NOSEND_NG
            elif kisys_status == COM.GW_KISYS_STATUS_NEW_NORES:
                update_status = COM.GW_KISYS_STATUS_NOSEND_NORES

        # kisys_status=79（ルール20）の時
        elif last_kisys_status == COM.GW_KISYS_STATUS_NOPATOLAMP_MANUAL:
            if kisys_status == COM.GW_KISYS_STATUS_NEW_OK:
                update_status = COM.GW_KISYS_STATUS_NOPATOLAMP_OK
            elif kisys_status == COM.GW_KISYS_STATUS_NEW_NG:
                update_status = COM.GW_KISYS_STATUS_NOPATOLAMP_NG
            elif kisys_status == COM.GW_KISYS_STATUS_NEW_NORES:
                update_status = COM.GW_KISYS_STATUS_NOPATOLAMP_NORES

        # kisys_status=9（ルール無）のときはそのままBAO連携結果で設定したkisys_statusで更新する

        existing_incident = get_existing_incident(gw_incident_id)
        incident_status = existing_incident[1]
        # イベント更新
        update_gw_events(gw_incident_id, gw_event_id, update_status)
        LOGGER.info(
            'error報処理:関連テーブルを更新しました。gw_event_id=%s, gw_incident_id=%s, kisys_incidentid=%s',
            gw_event_id, gw_incident_id, kisys_incidentid
            )
    except Exception as msg:
        LOGGER.error(
            'error報処理:関連テーブル更新失敗。gw_event_id=%s, gw_incident_id=%s, kisys_incidentid=%s',
            gw_event_id, gw_incident_id, kisys_incidentid
            )
        LOGGER.debug(msg)
    # K-ISYS連携に成功した場合
    if kisys_incidentid and kisys_status == COM.GW_KISYS_STATUS_NEW_OK:
        # Kompira連携
        send_to_kompira(kisys_incidentid, gw_event_id)

def register_new_incident_report_to_bao(new_event, gw_event_id, gw_incident_id):
    last_kisys_status = new_event[17]
    bao_soap_result = bao_soap(new_event, '', COM.SOAP_VALUE_STATUS_NEW)
    if bao_soap_result == 'No_reply':
        kisys_incidentid = None
        kisys_status = COM.GW_KISYS_STATUS_NEW_NORES
        LOGGER.error('error報処理:BAO無応答 gw_event_id=%s', gw_event_id)
    elif bao_soap_result == 'Failure':
        kisys_incidentid = None
        kisys_status = COM.GW_KISYS_STATUS_NEW_NG
        LOGGER.error('error報処理:BAO連携失敗 gw_event_id=%s', gw_event_id)
    else:
        kisys_incidentid = bao_soap_result
        kisys_status = COM.GW_KISYS_STATUS_NEW_OK
        LOGGER.info('error報処理:BAO連携成功 gw_event_id=%s', gw_event_id)
        try:
            update_gw_incidents_add_kisys_incidentid(kisys_incidentid, gw_incident_id)
            LOGGER.info(
                'error報処理:関連テーブルを更新しました。gw_event_id=%s, gw_incident_id=%s, kisys_incidentid=%s',
                gw_event_id, gw_incident_id, kisys_incidentid
                )
        except Exception as msg:
            LOGGER.error(
                'error報処理:関連テーブル更新失敗。gw_event_id=%s, gw_incident_id=%s, kisys_incidentid=%s',
                gw_event_id, gw_incident_id, kisys_incidentid
                )
            LOGGER.info(msg)
    error_update_bao_result(kisys_incidentid, kisys_status, gw_event_id, gw_incident_id, last_kisys_status)

def update_error_event(new_event, kisys_status):
    gw_event_id = new_event[0]
    gw_incident_id = new_event[3]
    host = new_event[18]
    LOGGER.info('error報処理開始 gw_event_id=%s', gw_event_id)
    
    # ルール30の時間内復旧だった場合、キャンセル処理をする
    if new_event[17] == COM.GW_KISYS_STATUS_KISYS_CONNECT_CANCEL:
        cancel_error_event(new_event)
        LOGGER.info('gw_event_id=%s クローズしました(event_status=2)', gw_event_id)
    else:
        # タイムアウト、それ以外
        register_new_incident_report_to_bao(new_event, gw_event_id, gw_incident_id)

def update_normal_event(new_event, kisys_status):
    gw_event_id = new_event[0]
    gw_incident_id = new_event[3]
    LOGGER.info('normal報処理開始 gw_event_id=%s', gw_event_id)
    event_record = get_paired_error_events(gw_incident_id)
    
    # ルール30の時間内復旧だった場合、キャンセル処理をする
    if new_event[17] == COM.GW_KISYS_STATUS_KISYS_CONNECT_CANCEL:
        cancel_normal_event(new_event)
        LOGGER.info('gw_event_id=%s クローズしました(event_status=2)', gw_event_id)
    else:
        # タイムアウト、それ以外
        update_kisys_incident_report_to_bao(new_event, gw_event_id, event_record)

def event_loop(new_events):
    """
    新規イベント(event_status=0)のレコードを抽出して1行ずつ処理する
    """
    val = 0
    len_new_events = len(new_events)
    for new_event in new_events:
        val += 1
        LOGGER.info('イベント処理開始(%s/%s), gw_event_id=%s', val, len_new_events, new_event[0])
        gw_event_id = new_event[0]
        event_status = str(new_event[1])
        gw_incident_id = new_event[3]
        customer_name = new_event[7]
        hostname = new_event[8]
        ci_name = new_event[10]
        alarm_status = new_event[12]
        kisys_status = None #NULLを代入しておく

        if gw_incident_id is None:
            LOGGER.info('incident番号が見つかりません, gw_event_id=%s', gw_event_id)
            LOGGER.info('イベント処理(%s/%s)終了, gw_event_id=%s', val, len_new_events, gw_event_id)
            continue

        #""" error or normal で分岐 """
        if alarm_status == COM.GW_ALARM_STATUS_ERROR:
            update_error_event(new_event, kisys_status)
        else:
            update_normal_event(new_event, kisys_status)
        LOGGER.info('イベント処理(%s/%s)終了, gw_event_id=%s', val, len_new_events, new_event[0])

def main():
    """
    メイン処理
    """
    while 1:
        #""" 無限ループ開始 """
        LOGGER.debug('無限ループ先頭')
        nowdatetime = dt.now()
        nowdatetimestr = nowdatetime.strftime("%Y-%m-%d %H:%M:%S")
        if file_check('stop') is True:
            LOGGER.info('ストップモードのため、exitで処理を終了します')
            sys.exit()
        elif file_check('test') is True:
            LOGGER.info('testモードのため、テストモードで動作実行')
        elif file_check('primary') is True:
            LOGGER.info('マスターモードのため、マスター動作実行')
        else:
            LOGGER.info('スレーブモードのため、スレーブ動作実行')
            if file_check('unittest') is True:
                break
            time.sleep(10)
            continue

        #""" K-ISYSメンテナンスルール確認関数の呼び出し """
        kisys_mainte = kisys_maintenance(nowdatetimestr)
        if kisys_mainte:
            rule_id = kisys_mainte[0][0]
            LOGGER.info('KISYSメンテナンス期間に該当(rule_id = %s)。10秒待機します。', rule_id)
            if file_check('unittest') is True:
                break
            time.sleep(10)
            continue
        else:
            LOGGER.info('KISYSメンテナンス期間に該当しないため処理を継続します。')
            #""" イベント処理関数の呼び出し """
            new_events = get_new_events()
            if new_events:
                event_loop(new_events)
            else:
                LOGGER.info('処理対象イベント無し。')

        # 無限ループ最後尾、DB切断、10秒後、無限ループ先頭に戻る。
        LOGGER.info('10秒待機します。')
        if file_check('unittest') is True:
            break
        time.sleep(10)

if __name__ == '__main__':
    # 起動済みプロセスの確認、ファイルがロックできなければ、起動済みプロセスがいると判断
    LOCK_RESULT = lock_file(__file__)
    LOGGER.debug(LOCK_RESULT)
    try:
        main()
    except Exception as msg:
        LOGGER.critical('Stopped by an unknown error.')
        #LOGGER.exception(msg)
        EXCEPTIONS_MSG = traceback.format_exc()
        LOGGER.info(EXCEPTIONS_MSG)

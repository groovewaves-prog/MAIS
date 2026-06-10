#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
## 概要 ##
# rescue_gw_events.py

# 引数無しで「rescue_gw_events.py」を実行するスクリプト
# 2017/09/09 系切り替えテスト結果よりZabbix外部監視から常駐プロセス方式に変更 by H.OOZERA
# 2018/07/25 SQLエスケープ処理修正 by K.YAMADATE
"""

## import ##
#import datetime
from datetime import datetime

import traceback
#from datetime import datetime as dt
import os
import fcntl
import time

import sys
sys.path.append("/usr/lib/baogw")
import logging
import logging.handlers
#import re
import mysql.connector
import gwcommon as COM
import gwfunction as FUNC

## スクリプトのパス、ファイル名を取得
# __file__ = '/usr/lib/zabbix/alertscripts/rescue_gw_events.py'
SCRIPT_FILE = os.path.basename(__file__)

## log出力設定 ※rsyslogd に渡す設定
LOGGER = logging.getLogger(SCRIPT_FILE)
LOGGER.setLevel(COM.LOGGER_LEVEL_RESCUE_GW_EVENTS)
HANDLER = logging.handlers.SysLogHandler(address=('localhost', 514), facility='local6')
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

def search_rescue_events(baogwcur):
    """
    検索用関数 結果をfound_recsにて返信
    """
    search_item = ('gw_event_id, update_time, detected_time, detected_host, customer_ci,'
                   'customer_name, hostname, alarm_time, ci_name, device, alarm_status, summary, host')
    table_name = 'gw_rescue_events'
    search_condition = 'event_status=%s' % COM.GW_EVENT_STATUS_NEW
    # search_baogw()をキックし、結果をfound_recsで受け取り
    sql = 'SELECT %s FROM %s WHERE %s ' % (search_item, table_name, search_condition)
    #print(sql)
    try:
        baogwcur.execute(sql)
        found_recs = baogwcur.fetchall()
        LOGGER.info('select成功:[%s] %s %s ', COM.MY_HOST, table_name, search_condition)
    except mysql.connector.errors.IntegrityError as msg:
        LOGGER.critical('select失敗:[%s] %s %s ', COM.MY_HOST, table_name, search_condition)
        LOGGER.info('%s', msg)
    return found_recs

def insert_gw_events(dbbaogw, baogwcur, found_rec):
    """
    INSERT用関数
    """
    table_name = 'gw_events'
    insert_item = 'update_time, detected_time, detected_host, customer_ci, customer_name,\
                  hostname, alarm_time, ci_name, device, alarm_status, summary, host'
    # insert_value = make_insert_value(found_rec)
    insert_value = 'now(3), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s'
    value = (found_rec['detected_time'], found_rec['detected_host'], found_rec['customer_ci'],
        found_rec['customer_name'], found_rec['hostname'], found_rec['alarm_time'],
        found_rec['ci_name'], found_rec['device'], found_rec['alarm_status'], found_rec['summary'], found_rec['host'])

    sql = 'INSERT INTO %s (%s) VALUES (%s)' % (table_name, insert_item, insert_value)
    #print(sql)
    try:
        baogwcur.execute(sql, value)
        LOGGER.info('INSERT成功:[%s] %s %s', COM.MY_HOST, table_name,  make_insert_value(found_rec))
        # コミット
        dbbaogw.commit()
        return True
    except mysql.connector.errors.IntegrityError as msg:
        LOGGER.critical('INSERT失敗:[%s] %s %s', COM.MY_HOST, table_name,  make_insert_value(found_rec))
        LOGGER.info('%s', msg)
        return False

def delete_gw_rescue_events(dbbaogw, baogwcur, delete_condition):
    """
    delete用関数 結果をdelete_resultにて返信
    """
    table_name = 'gw_rescue_events'
    sql = 'DELETE FROM %s WHERE %s' % (table_name, delete_condition)
    #print(sql)
    try:
        baogwcur.execute(sql)
        LOGGER.info('delete成功:[%s] %s %s', COM.MY_HOST, table_name, delete_condition)
        #コミット
        dbbaogw.commit()
    except mysql.connector.errors.IntegrityError as msg:
        LOGGER.critical('delete失敗:[%s] %s %s', COM.MY_HOST, table_name, delete_condition)
        LOGGER.info('%s', msg)
    return

def make_insert_value(found_rec):
    """
    insert_value作成用関数 結果をinsert_valueにて返信
    """
    insert_value = 'now(), "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s"' % \
    (found_rec['detected_time'], found_rec['detected_host'], found_rec['customer_ci'],\
    found_rec['customer_name'], found_rec['hostname'], found_rec['alarm_time'],\
    found_rec['ci_name'], found_rec['device'], found_rec['alarm_status'], found_rec['summary'], found_rec['host'])
    return insert_value

def get_new_events(found_rec):
    """
    gw_events からインサートしたイベントを抜き出す
    """
    alarm_time = found_rec.get('alarm_time').strftime('%Y-%m-%d %H:%M:%S.%f')
    dbbaogw = FUNC.connect_db_unix_socket(COM.MY_HOST)
    baogwcur = dbbaogw.cursor(dictionary=True, buffered=True)
    search_item = 'gw_event_id, event_status, customer_ci, customer_name, hostname, alarm_time, ci_name, alarm_status, detected_host'
    table_name = 'gw_events'
    search_condition = 'customer_name=%s and hostname=%s and alarm_time=%s and ci_name=%s'
    value = (found_rec.get('customer_name'), found_rec.get('hostname'), alarm_time, found_rec.get('ci_name'))
    sql = 'SELECT %s FROM %s WHERE %s ORDER BY gw_event_id DESC' % (search_item, table_name, search_condition)
    try:
        baogwcur.execute(sql, value)
        new_events = baogwcur.fetchall()
        baogwcur.close()
        dbbaogw.close()
    except Exception as msg:
        LOGGER.critical('Stopped: Function of get_new_events is failed.')
        LOGGER.info(msg)
    return new_events[0]

def search_events(baogwcur, found_rec):
    """
    gw_eventのチェック用関数　結果をcheck_resultにて返信
    """
    search_item = '*'
    table_name = 'gw_events'
    search_condition = 'alarm_time=%s and customer_name=%s and hostname=%s and ci_name=%s'
    value = (found_rec['alarm_time'], found_rec['customer_name'], found_rec['hostname'], found_rec['ci_name'])
    sql = 'SELECT %s FROM %s WHERE %s' % (search_item, table_name, search_condition)
    #print(sql)
    try:
        baogwcur.execute(sql, value)
        search_recs = baogwcur.fetchall()
        check_result = len(search_recs)
    except mysql.connector.errors.IntegrityError as msg:
        LOGGER.critical('select失敗:[%s] %s %s', COM.MY_HOST, table_name, sql)
        LOGGER.info('%s', msg)
    return check_result

def main():
    """
    スクリプト本体
    """
    # 接続するDBのhostを定義
    #local_host = COM.MY_HOST

    while 1:
        #import gwcommon as COM
        #""" 無限ループ開始 """
        LOGGER.debug('無限ループ先頭')

        # データベース（baogw）への接続情報
        dbbaogw = FUNC.connect_db_unix_socket(COM.MY_HOST)
        baogwcur = dbbaogw.cursor(dictionary=True, buffered=True)

        # testファイルの有無を確認
        if file_check('test') is True:
            LOGGER.info('testモードのため、処理をスキップします。')

        # Primaryファイルの有無を確認
        elif file_check('primary') is True:
            LOGGER.info('マスターモードのため、rescue未処理レコードをgw_eventsに挿入します。')
            # isertレコードの抽出、search_rescue_events()をキックし、結果をfound_recsで受け取り
            found_recs = search_rescue_events(baogwcur)
            # 抽出結果のチェック
            evtnum = len(found_recs)
            if evtnum == 0:
                # 処理対象無し
                LOGGER.info('rescue対象が見つからなかったため、処理を終了します。')
            else:
                # 処理対象有り、処理対象を順次取出し、gw_eventsへ挿入、gw_rescue_eventsの削除実施
                for found_rec in found_recs:
                    # isert_gw_events() キック
                    if insert_gw_events(dbbaogw, baogwcur, found_rec) is True:
                        delete_condition = 'gw_event_id=%s' % found_rec['gw_event_id']
                        # delete_baogw() キック
                        delete_gw_rescue_events(dbbaogw, baogwcur, delete_condition)
        else:
            LOGGER.info('スレーブモードのため、rescue未処理レコードの処理状況を確認します。')
            # isertレコードの抽出、search_rescue_events()をキックし、結果をfound_recsで受け取り
            found_recs = search_rescue_events(baogwcur)
            # 抽出結果のチェック
            evtnum = len(found_recs)
            if evtnum == 0:
                # 処理対象無し
                LOGGER.info('rescue対象が見つからなかったため、処理を終了します。')
            else:
                # 処理対象有り、gw_eventsに該当レコードがあるかチェックし、あればgw_rescue_eventsの削除実施
                for found_rec in found_recs:
                    # search_events() キック　結果のlengthチェックで該当レコードの有無をハンドリング
                    check_result = search_events(baogwcur, found_rec)
                    # gw_eventsにレコードが存在した場合、gw_rescue_eventsの該当レコード削除
                    if check_result == 0:
                        LOGGER.info(
                            '該当レコードがgw_eventsに見つからなかったため、次回処理に繰り越します。gw_event_id=%s update_time=%s detected_time=%s detected_host=%s customer_ci=%s customer_name=%s hostname=%s alarm_time=%s ci_name=%s device=%s alarm_status=%s summary=%s host=%s',
                            found_rec['gw_event_id'], found_rec['update_time'], found_rec['detected_time'], found_rec['detected_host'], found_rec['customer_ci'], found_rec['customer_name'], found_rec['hostname'], found_rec['alarm_time'], found_rec['ci_name'], found_rec['device'], found_rec['alarm_status'], found_rec['summary'], found_rec['host']
                            )
                    else:
                        delete_condition = 'gw_event_id=%s' % found_rec['gw_event_id']
                        # delete_baogw() キック
                        delete_gw_rescue_events(dbbaogw, baogwcur, delete_condition)

        # データベース（baogw）のクローズ情報
        baogwcur.close()
        dbbaogw.close()
        if file_check('unittest') is True:
            break
        time.sleep(COM.RESCUE_INTERVAL)

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

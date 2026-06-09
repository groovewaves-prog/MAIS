#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
## 概要 ##
インシデント登録とルール処理を行う
"""

## import ##
from datetime import datetime as dt
import os
import sys
import logging
import logging.handlers
import re
import mysql.connector
import gwcommon as COM
import gwfunction as FUNC
import time
import fcntl

## スクリプトのパス、ファイル名を取得
SCRIPT_FILE = os.path.basename(__file__)

## log出力設定 ※rsyslogd に渡す設定
LOGGER = logging.getLogger(SCRIPT_FILE)
LOGGER.setLevel(COM.LOGGER_LEVEL_INSERT_GW_EVENTS)
HANDLER = logging.handlers.SysLogHandler(address=(COM.SYSLOG_HOST, COM.SYSLOG_PORT),facility=COM.SYSLOG_FACILITY) # 出力先の設定
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

def replace_crlf_bao(argument):
    """
    改行コードをBAO-IF仕様に変更
    """
    argument = argument.replace('\r', '\&#xD;')
    argument = argument.replace('\n', '\&#xA;')
    argument = argument.replace('\\r', '\&#xD;')
    argument = argument.replace('\\n', '\&#xA;')
    return argument

def get_new_events():
    """
    gw_events から新規イベント(event_status=0)を抜き出す
    """
    dbbaogw = FUNC.connect_db_unix_socket(COM.MY_HOST)
    baogwcur = dbbaogw.cursor(buffered=True)
    sql = "SELECT * FROM gw_events WHERE event_status=0 and alarm_status not in ('sec', 'syserror', 'sysnormal') ORDER BY alarm_time ASC"
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

def waiting_alarm(new_event, gw_event_id, customer_name, alarm_time, action_no, alarm_status, gw_incident_id):
    is_not_timeout = ((alarm_time + COM.WAITING_TIME[action_no]) >= dt.now())
    host = new_event[18]
    if is_not_timeout:
        # 時間内
        if alarm_status == COM.GW_ALARM_STATUS_ERROR:
            kisys_status = action_no
            # 送信状況を更新
            update_send_status(gw_event_id, kisys_status)
            LOGGER.info('%s(gw_event_id=%s, event_status=0)', \
                        COM.ACTION_MESSAGE[action_no], gw_event_id)
            return True
        else:
            waiting_event_id = get_waiting_event_id(gw_incident_id)
            if waiting_event_id != "":
                # 時間内復旧
                waiting_event = get_gw_event_by_pk(waiting_event_id)
                if is_kisys_relation_hostgroup(host):
                    # ホストグループ設定でKISYS連携する
                    # event_status=2、kisys_status=49で更新し、send_to_baoの対象としてここでの処理は終了
                    gw_incident_id = waiting_event[3]
                    update_gw_incidents(COM.GW_INCIDENT_STATUS_CLOSE, gw_incident_id)
                    # エラー報の更新
                    LOGGER.info(
                        'キャンセルのためクローズします(gw_event_id=%s, event_status=2)',
                        waiting_event_id
                                            )
                    update_gw_events(COM.GW_EVENT_STATUS_CLOSE, gw_incident_id, waiting_event_id, COM.GW_KISYS_STATUS_KISYS_CONNECT_CANCEL)
                    # ノーマル報の更新
                    update_gw_events(COM.GW_EVENT_STATUS_CLOSE, gw_incident_id, gw_event_id, COM.GW_KISYS_STATUS_KISYS_CONNECT_CANCEL)
                    LOGGER.info('gw_event_id=%s クローズしました(event_status=2)', gw_event_id)
                else:
                    # ホストグループ設定でKISYS連携しない
                    gw_incident_id = waiting_event[3]
                    update_gw_incidents(COM.GW_INCIDENT_STATUS_CLOSE, gw_incident_id)
                    # エラー報の更新
                    LOGGER.info('error報処理:BAO連携しない gw_event_id=%s', waiting_event_id)
                    update_gw_events(COM.GW_EVENT_STATUS_CLOSE, gw_incident_id, waiting_event_id, COM.GW_KISYS_STATUS_CANCEL_NOSEND)
                    # ノーマル報の更新
                    LOGGER.info('normal報処理:BAO連携しない gw_event_id=%s', gw_event_id)
                    update_gw_events(COM.GW_EVENT_STATUS_CLOSE, gw_incident_id, gw_event_id, COM.GW_KISYS_STATUS_CANCEL_NOSEND)
                    LOGGER.info(
                        'normal報処理:関連テーブルをcloseに更新しました。gw_event_id=%s, gw_incident_id=%s',
                        gw_event_id, gw_incident_id
                        )
                return False
            return False
    else:
        # ZabbixApiインスタンス作成
        api = FUNC.ZabbixApi(COM.ZABBIX_IP, COM.ZABBIX_USER, COM.ZABBIX_PASSWD)
        # 顧客名からホストグループリストを抽出
        hostgroups = FUNC.get_hostgroups_by_host(api, host)

        # タイムアウト
        if FUNC.file_check('test') is False:
            # パトランプ鳴動ファイル作成
            patolamp_file = ''
            if alarm_status == COM.GW_ALARM_STATUS_ERROR or alarm_status == COM.GW_ALARM_STATUS_INFO:
                patolamp_file = COM.RED_PATOLAMP_FILE
            elif alarm_status == COM.GW_ALARM_STATUS_NORMAL or alarm_status == COM.GW_ALARM_STATUS_SYSNORMAL:
                patolamp_file = COM.GREEN_PATOLAMP_FILE
            else:
                patolamp_file = COM.YELLOW_PATOLAMP_FILE

            # 鳴動ファイルの命名
            FUNC.create_patolamp_files(hostgroups, patolamp_file)

        # send_to_baoに引き渡すためevent_statusとkisys_statusを更新する
        if alarm_status == COM.GW_ALARM_STATUS_ERROR:
            # ホストグループの判定
            if COM.KISYS_RELATION_HOSTGROUP in hostgroups:
                # KISYS連携顧客ならkisys_status=59で更新
                LOGGER.info('error報処理:キャンセル待ちタイムアウト、BAO連携する gw_event_id=%s', gw_event_id)
                FUNC.update_gw_events(COM.MY_HOST, COM.GW_EVENT_STATUS_ACTIVE, gw_incident_id, gw_event_id, COM.GW_KISYS_STATUS_KISYS_CONNECT_NORECOVERY)
            else:
                # KISYS連携顧客でないならkisys_status=53で更新
                LOGGER.info('error報処理:キャンセル待ちタイムアウト、BAO連携しない gw_event_id=%s', gw_event_id)
                FUNC.update_gw_events(COM.MY_HOST, COM.GW_EVENT_STATUS_ACTIVE, gw_incident_id, gw_event_id, COM.GW_KISYS_STATUS_NORECOVERY_NOSEND)
        else:
            # ノーマル報タイムアウト
            update_gw_incidents(COM.GW_INCIDENT_STATUS_CLOSE, gw_incident_id)
            # タイムアウト未処理エラー報用
            waiting_event_id = get_waiting_event_id(gw_incident_id)
            waiting_event = get_gw_event_by_pk(waiting_event_id)
            if str(waiting_event[1]) == COM.GW_EVENT_STATUS_ACTIVE:
                # エラー報のevent_status=1なら既にエラー報もタイムアウト処理済みなのでevent_status=2にだけ更新したあとノーマル報タイムアウト処理へ進む
                update_related_gw_events(COM.GW_EVENT_STATUS_CLOSE, gw_incident_id)
                LOGGER.info('normal報処理:キャンセル待ちタイムアウト、エラー報クローズしました gw_event_id=%s', waiting_event_id)
            else:
                # エラー報のevent_status=0ならまだキャンセル待ち中処理なのでevent_status=2&kisys_status=59or53に更新したあとノーマル報タイムアウト処理へ進む
                # ホストグループの判定
                if COM.KISYS_RELATION_HOSTGROUP in hostgroups:
                    # KISYS連携顧客なら、waiting_event_id（エラー報のevent_id）をkisys_status=59で更新
                    FUNC.update_gw_events(COM.MY_HOST, COM.GW_EVENT_STATUS_CLOSE, gw_incident_id, waiting_event_id, COM.GW_KISYS_STATUS_KISYS_CONNECT_NORECOVERY)
                else:
                    # KISYS連携顧客でないなら、waiting_event_id（エラー報のevent_id）をkisys_status=53で更新
                    FUNC.update_gw_events(COM.MY_HOST, COM.GW_EVENT_STATUS_CLOSE, gw_incident_id, waiting_event_id, COM.GW_KISYS_STATUS_NORECOVERY_NOSEND)
                LOGGER.info('normal報処理:キャンセル待ちタイムアウト、エラー報キャンセル待ち中なのでエラー報kisys_status更新、クローズしました gw_event_id=%s', waiting_event_id)

            # ノーマル報タイムアウト処理
            # ホストグループの判定
            if COM.KISYS_RELATION_HOSTGROUP in hostgroups:
                # KISYS連携顧客ならkisys_status=59で更新
                LOGGER.info('normal報処理:キャンセル待ちタイムアウト、BAO連携する gw_event_id=%s', gw_event_id)
                FUNC.update_gw_events(COM.MY_HOST, COM.GW_EVENT_STATUS_CLOSE, gw_incident_id, gw_event_id, COM.GW_KISYS_STATUS_KISYS_CONNECT_NORECOVERY)
            else:
                # KISYS連携顧客でないならkisys_status=53で更新
                LOGGER.info('normal報処理:キャンセル待ちタイムアウト、BAO連携しない gw_event_id=%s', gw_event_id)
                FUNC.update_gw_events(COM.MY_HOST, COM.GW_EVENT_STATUS_CLOSE, gw_incident_id, gw_event_id, COM.GW_KISYS_STATUS_NORECOVERY_NOSEND)
        return False

def update_gw_incidents(incident_status, gw_incident_id):
    """
    gw_incidents テーブルを更新する
    """
    dbbaogw = FUNC.connect_db_unix_socket(COM.MY_HOST)
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
        sys.exit()

def update_gw_events(event_status, gw_incident_id, gw_event_id, kisys_status):
    """
    gw_events テーブルを更新する
    """
    dbbaogw = FUNC.connect_db_unix_socket(COM.MY_HOST)
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
        sys.exit()

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

def get_waiting_event_id(gw_incident_id):
    """
    キャンセル待ちのError報を探す
    incident_idが一致し、alarm_status=errorのレコード
    """
    waiting_event_id = ""
    dbbaogw = FUNC.connect_db_unix_socket(COM.MY_HOST)
    baogwcur = dbbaogw.cursor(buffered=True)
    sql = "SELECT gw_event_id FROM gw_events \
    WHERE alarm_status='error' and gw_incident_id=%s ORDER BY alarm_time ASC"
    sql_values = (gw_incident_id,)
    try:
        baogwcur.execute(sql, sql_values)
        waiting_events = baogwcur.fetchall()
        if waiting_events:
            waiting_event_id = waiting_events[0][0]
        baogwcur.close()
        dbbaogw.close()
    except Exception as msg:
        LOGGER.critical('Stopped: Function of get_waiting_event_id is failed.')
        LOGGER.info(msg)
        sys.exit()
    return waiting_event_id

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

def is_kisys_relation_hostgroup(host):
    # ZabbixApiインスタンス作成
    api = FUNC.ZabbixApi(COM.ZABBIX_IP, COM.ZABBIX_USER, COM.ZABBIX_PASSWD)
    # 顧客名からホストグループリストを抽出
    hostgroups = FUNC.get_hostgroups_by_host(api, host)
    return (COM.KISYS_RELATION_HOSTGROUP in hostgroups)

def update_related_gw_events(event_status, gw_incident_id):
    """
    normal 報に関連する error 報を クローズする
    """
    dbbaogw = FUNC.connect_db_unix_socket(COM.MY_HOST)
    baogwcur = dbbaogw.cursor(buffered=True)
    sql = "UPDATE gw_events SET event_status=%s, update_time=now(3) \
    WHERE gw_incident_id=%s and event_status=1 and alarm_status='error'"
    sql_values = (event_status, gw_incident_id)
    try:
        baogwcur.execute(sql, sql_values)
        update_count = baogwcur.rowcount
        dbbaogw.commit()
        baogwcur.close()
        dbbaogw.close()
        if update_count == 1:
            LOGGER.debug('Success: update_related_gw_events gw_incident_id=%s', gw_incident_id)
        else:
            LOGGER.error('update_related_gw_eventsでupdate結果が0件でした gw_incident_id=%s', gw_incident_id)
    except Exception as msg:
        LOGGER.critical('Stopped: Function of update_related_gw_events is failed.')
        LOGGER.info(msg)
        sys.exit()

def event_loop(new_events):
    """
    新規イベント(event_status=0)のレコードを抽出して1行ずつ処理する
    """

    val = 0
    len_new_events = len(new_events)
    for new_event in new_events:
        val += 1
        LOGGER.info('イベント処理開始(%s/%s), gw_event_id=%s', val, len_new_events, new_event[0])
        #update_time = dt.now().strftime("%Y-%m-%d %H:%M:%S")
        gw_event_id = new_event[0]
        event_status = str(new_event[1])
        gw_incident_id = new_event[3]
        detected_host = new_event[5]
        customer_ci = new_event[6]
        customer_name = new_event[7]
        hostname = new_event[8]
        alarm_time = new_event[9]
        ci_name = new_event[10]
        alarm_status = new_event[12]
        host = new_event[18]
        kisys_status = None #NULLを代入しておく
        op_comment = None
        project_code = customer_ci #ZABBIXアクションからINVENTORY.TAGで受け取った値
        
        if gw_incident_id is None:
            #""" 重複レコードの有無確認 """
            # 4つのパラメータが全く一緒でインシデント登録済みのイベントを重複とみなす
            dup_events = FUNC.get_dup_events(COM.MY_HOST, alarm_time, customer_name, hostname, ci_name)
            if dup_events:
                LOGGER.info('重複レコードです gw_event_id=%s, event_status=99 にUPDATE', gw_event_id)
                # 重複イベントのときはgw_insidents_id=None
                FUNC.update_gw_events(
                    COM.MY_HOST, COM.GW_EVENT_STATUS_DUP, None, gw_event_id, kisys_status
                    )
                LOGGER.info('イベント処理(%s/%s)終了, gw_event_id=%s', val, len_new_events, new_event[0])
                continue

        # """gw_incidentsテーブルにインサート"""
        # エラー報の場合
        if alarm_status == COM.GW_ALARM_STATUS_ERROR:
            insert_values = [
                COM.GW_INCIDENT_STATUS_ACTIVE,
                detected_host,
                gw_event_id,
                customer_name,
                hostname,
                ci_name,
                op_comment,
                project_code
                ]
            try:
                # 重複してインシデント登録されないために条件追加
                if gw_incident_id is None:
                    gw_incident_id = FUNC.insert_error_id_into_gw_incidents(COM.MY_HOST, insert_values)
                    LOGGER.info(
                        'error報処理:インシデント登録しました。gw_incident_id=%s',
                        gw_incident_id)
                # インシデント登録のあと、ルール抽出後、イベントのアップデートを行う
                action_no = FUNC.get_action_no(customer_name, hostname, ci_name)
                if action_no == '10':
                    # ルール10のときkisys_statusを10＆event_statusを1に更新
                    FUNC.update_gw_events(COM.MY_HOST, COM.GW_EVENT_STATUS_ACTIVE, gw_incident_id, gw_event_id, COM.GW_KISYS_STATUS_NOSEND)
                    LOGGER.info(
                        'error報処理:イベントID：%sとインシデントID：%sを紐づけました。',
                        gw_event_id, gw_incident_id
                        )
                elif action_no == '20':
                    # ルール20のときkisys_statusを20＆event_statusを1に更新
                    FUNC.update_gw_events(COM.MY_HOST, COM.GW_EVENT_STATUS_ACTIVE, gw_incident_id, gw_event_id, COM.GW_KISYS_STATUS_NOPATOLAMP)
                    LOGGER.info(
                        'error報処理:イベントID：%sとインシデントID：%sを紐づけました。',
                        gw_event_id, gw_incident_id
                        )
                elif action_no in COM.GW_KISYS_STATUS_WAITING_LIST:
                    # ルール30台のときはキャンセル待ち処理を実行
                    # kisys_statusはaction_noで上書き
                    FUNC.update_gw_events(COM.MY_HOST, COM.GW_EVENT_STATUS_NEW, gw_incident_id, gw_event_id, action_no)
                    still_waiting = waiting_alarm(new_event, gw_event_id, customer_name, alarm_time, action_no, alarm_status, gw_incident_id)
                    if (still_waiting):
                        # 時間内
                        LOGGER.info('イベント処理(%s/%s)終了, gw_event_id=%s', val, len_new_events, new_event[0])
                        continue
                else:
                    # ルール無の場合はホストグループの判別の後kisys_statusとevent_statusを更新
                    if is_kisys_relation_hostgroup(host):
                        # KISYS連携顧客が設定されている場合kisys_status=9で更新
                        FUNC.update_gw_events(
                        COM.MY_HOST, COM.GW_EVENT_STATUS_ACTIVE, gw_incident_id, gw_event_id, COM.GW_KISYS_STATUS_KISYS_CONNECT_NORULE
                        )
                        LOGGER.info(
                        'error報処理:イベントID：%sとインシデントID：%sを紐づけました。',
                        gw_event_id, gw_incident_id
                        )
                    else:
                        # KISYS連携顧客が設定されていない場合kisys_status=100で更新
                        FUNC.update_gw_events(
                        COM.MY_HOST, COM.GW_EVENT_STATUS_ACTIVE, gw_incident_id, gw_event_id, COM.GW_KISYS_STATUS_NOSEND_BY_HOSTGROUP
                        )
                        LOGGER.info(
                        'error報処理:イベントID：%sとインシデントID：%sを紐づけました。',
                        gw_event_id, gw_incident_id
                        )

            except Exception as msg:
                LOGGER.error(
                    'error報処理:インシデントテーブル更新失敗。gw_event_id=%s, gw_incident_id=%s',
                    gw_event_id, gw_incident_id
                    )
                LOGGER.info(msg)

        # ノーマル報の場合
        elif alarm_status == COM.GW_ALARM_STATUS_NORMAL:
            event_record = FUNC.get_existing_events(COM.MY_HOST, customer_name, hostname, ci_name, alarm_time)
            if event_record == []:
                # ノーマル単体の場合
                LOGGER.info('normal報処理:error報が見つかりません。 gw_event_id=%s', gw_event_id)
                insert_values = [
                    COM.GW_INCIDENT_STATUS_CLOSE,
                    detected_host,
                    gw_event_id,
                    customer_name,
                    hostname,
                    ci_name,
                    'error報が見つかりません',
                    project_code
                    ]
                try:
                    gw_incident_id = FUNC.insert_normal_id_into_gw_incidents(COM.MY_HOST, insert_values)
                    LOGGER.info(
                        'normal報処理:インシデント登録しました。gw_incident_id=%s',
                        gw_incident_id)
                    # event_status=2,kisys_status=Noneで更新
                    FUNC.update_gw_events(
                        COM.MY_HOST, COM.GW_EVENT_STATUS_CLOSE, gw_incident_id, gw_event_id, kisys_status
                        )
                    LOGGER.info(
                        'normal報処理:イベントID：%sとインシデントID：%sを紐づけました。',
                        gw_event_id, gw_incident_id
                        )
                except Exception as msg:
                    LOGGER.error(
                        'normal報処理:インシデントテーブル更新失敗。gw_event_id=%s, gw_incident_id=%s',
                        gw_event_id, gw_incident_id
                        )
                    LOGGER.debug(msg)
            else:
                # 復旧報の場合
                error_event_id = event_record[0]
                gw_incident_id = event_record[1]
                try:
                    FUNC.update_gw_incidents(
                        COM.MY_HOST, COM.GW_INCIDENT_STATUS_CLOSE, gw_event_id, gw_incident_id
                        )
                    LOGGER.info(
                        'normal報処理:インシデントをクローズしました。gw_incident_id=%s, normal_event_id=%s, error_event_id=%s',
                        gw_incident_id, gw_event_id, error_event_id
                        )
                    action_no = FUNC.get_action_no(customer_name, hostname, ci_name)
                    if action_no == '10':
                        # ルール10のときkisys_statusを10＆event_statusを2に更新
                        update_related_gw_events(COM.GW_EVENT_STATUS_CLOSE, gw_incident_id)
                        FUNC.update_gw_events(COM.MY_HOST, COM.GW_EVENT_STATUS_CLOSE, gw_incident_id, gw_event_id, COM.GW_KISYS_STATUS_NOSEND)
                        LOGGER.info(
                            'normal報処理:イベントID：%sとインシデントID：%sを紐づけました。',
                            gw_event_id, gw_incident_id
                            )
                    elif action_no == '20':
                        # ルール20のときkisys_statusを20＆event_statusを2に更新
                        update_related_gw_events(COM.GW_EVENT_STATUS_CLOSE, gw_incident_id)
                        FUNC.update_gw_events(COM.MY_HOST, COM.GW_EVENT_STATUS_CLOSE, gw_incident_id, gw_event_id, COM.GW_KISYS_STATUS_NOPATOLAMP)
                        LOGGER.info(
                            'normal報処理:イベントID：%sとインシデントID：%sを紐づけました。',
                            gw_event_id, gw_incident_id
                            )
                    elif action_no in COM.GW_KISYS_STATUS_WAITING_LIST:
                        # ルール30台のときはキャンセル待ち処理を実行
                        # alarm_timeにエラー報の発生時刻を渡すことで、エラー報発生からの経過時間を確認できるようにする
                        alarm_time = event_record[2]
                        still_waiting = waiting_alarm(new_event, gw_event_id, customer_name, alarm_time, action_no, alarm_status, gw_incident_id)
                        if (still_waiting):
                            LOGGER.info('イベント処理(%s/%s)終了, gw_event_id=%s', val, len_new_events, new_event[0])
                            continue
                    else:
                        # ルール無の場合はホストグループの判別の後kisys_statusとevent_statusを更新
                        if is_kisys_relation_hostgroup(host):
                            # KISYS連携顧客が設定されている場合kisys_status=9で更新
                            update_related_gw_events(COM.GW_EVENT_STATUS_CLOSE, gw_incident_id)
                            FUNC.update_gw_events(COM.MY_HOST, COM.GW_EVENT_STATUS_CLOSE, gw_incident_id, gw_event_id, COM.GW_KISYS_STATUS_KISYS_CONNECT_NORULE)
                            LOGGER.info(
                            'normal報処理:イベントID：%sとインシデントID：%sを紐づけました。',
                            gw_event_id, gw_incident_id
                            )
                        else:
                            # KISYS連携顧客が設定されていない場合kisys_status=100で更新
                            update_related_gw_events(COM.GW_EVENT_STATUS_CLOSE, gw_incident_id)
                            FUNC.update_gw_events(COM.MY_HOST, COM.GW_EVENT_STATUS_CLOSE, gw_incident_id, gw_event_id, COM.GW_KISYS_STATUS_NOSEND_BY_HOSTGROUP)
                            LOGGER.info(
                            'normal報処理:イベントID：%sとインシデントID：%sを紐づけました。',
                            gw_event_id, gw_incident_id
                            )

                except Exception as msg:
                    LOGGER.error(msg)
                    LOGGER.error(
                        'normal報処理:関連テーブル更新失敗 gw_event_id=%s, gw_incident_id=%s',
                        gw_event_id, gw_incident_id
                        )

        else:
            # info,sec,sysnormal,syserrorの場合
            insert_values = [
            COM.GW_INCIDENT_STATUS_CLOSE,
            detected_host,
            gw_event_id,
            customer_name,
            hostname,
            ci_name,
            op_comment,
            project_code
            ]
            if alarm_status == COM.GW_ALARM_STATUS_SYSNORMAL:
                try:
                    gw_incident_id = FUNC.insert_normal_id_into_gw_incidents(COM.MY_HOST, insert_values)
                    LOGGER.info(
                        'sysnormal報処理:インシデント登録しました。gw_incident_id=%s',
                        gw_incident_id)
                    update_gw_events(
                        COM.GW_EVENT_STATUS_CLOSE, gw_incident_id, gw_event_id, kisys_status
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
                    gw_incident_id = FUNC.insert_error_id_into_gw_incidents(COM.MY_HOST, insert_values)
                    LOGGER.info(
                        'syserror, info, sec報処理:インシデント登録しました。gw_incident_id=%s',
                        gw_incident_id)
                    update_gw_events(
                        COM.GW_EVENT_STATUS_CLOSE, gw_incident_id, gw_event_id, kisys_status
                        )
                    LOGGER.info(
                        'syserror, info, sec報処理:イベントID：%sとインシデントID：%sを紐づけました。',
                        gw_event_id, gw_incident_id
                        )
                except Exception as msg:
                    LOGGER.error(
                        'syserror, info, sec報処理:インシデントテーブル更新失敗。gw_event_id=%s, gw_incident_id=%s',
                        gw_event_id, gw_incident_id
                        )
                    LOGGER.debug(msg)

        LOGGER.info('イベント処理(%s/%s)終了, gw_event_id=%s', val, len_new_events, new_event[0])

def main():
    """
    スクリプト本体
    """

    while 1:
        #""" 無限ループ開始 """
        LOGGER.debug('無限ループ先頭')
        nowdatetime = dt.now()
        if FUNC.file_check('stop') is True:
            LOGGER.info('ストップモードのため、exitで処理を終了します')
            sys.exit()
        elif FUNC.file_check('test') is True:
            LOGGER.info('testモードのため、テストモードで動作実行')
        elif FUNC.file_check('primary') is True:
            LOGGER.info('マスターモードのため、マスター動作実行')
        else:
            LOGGER.info('スレーブモードのため、スレーブ動作実行')
            if FUNC.file_check('unittest') is True:
                break
            time.sleep(1)
            continue

        # 新規イベント(event_status=0)のレコードを抽出して1行ずつ処理する
        target_events = get_new_events()

        # 新規イベントをループで回してひとつずつ重複チェック～インシデント登録
        if target_events:
            event_loop(target_events)
        else:
            LOGGER.info('処理対象イベント無し。')

        # 無限ループ最後尾、DB切断、1秒後、無限ループ先頭に戻る。
        LOGGER.info('1秒待機します。')
        if FUNC.file_check('unittest') is True:
            break
        time.sleep(1)
            
if __name__ == '__main__':
    # 起動済みプロセスの確認、ファイルがロックできなければ、起動済みプロセスがいると判断
    LOCK_RESULT = lock_file(__file__)
    LOGGER.debug(LOCK_RESULT)
    try:
        main()
    except Exception as msg:
        LOGGER.critical('[End0] Stopped by an unknown error.')
        LOGGER.info('%s', msg)

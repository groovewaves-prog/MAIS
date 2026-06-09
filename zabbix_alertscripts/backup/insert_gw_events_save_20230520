#!/usr/bin/env python3
# -*- coding: utf-8 -*-



"""
## 概要 ##
# insert_gw_events.py

# 2017/08/22 パトランプ鳴動処理を追加
# 2017/08/31 update_timeをDBのNOW()関数利用およびlogレベル見直し by H.OOZERA
# 2017/09/09 パトランプ鳴動処理をファイル作成方式に変更 by H.OOZERA
# 2018/02/15 顧客略称の形式チェックを変更  by K.YAMADATE
#            英数字 → 英数字＋記号（ハイフン、アンダースコア、スラッシュ）
# 2018/07/25 アラート制御を追加 by K.YAMADATE
# 2019/04/26 項目数不正エラーが発生する分岐で、K-ISYSに渡す引数を変更 by R.FUJII


# Zabbix アクションから実行
# Insert into baogw.gw_events を実行するスクリプト
#
# 第1引数:sys.argv[0]:このスクリプトファイル名
# 第2引数:sys.argv[1]:Zabbixマクロ{ALERT.SENDTO}
# 第3引数:sys.argv[2]:Zabbixマクロ{ALERT.SUBJECT}
# 第4引数:sys.argv[3]:Zabbixマクロ{ALERT.MESSAGE}
"""

## 2017/09/09 パトランプ鳴動方式変更のためコメントアウト by 大瀬良
# import subprocess

## import ##
import datetime
#from datetime import datetime
import os
import sys
import logging
import logging.handlers
import re
import mysql.connector
import gwcommon as COM
import gwfunction as FUNC

## スクリプトのパス、ファイル名を取得
# __file__ = '/usr/lib/zabbix/alertscripts/insert_gw_events.py'
SCRIPT_FILE = os.path.basename(__file__)

## log出力設定 ※rsyslogd に渡す設定
LOGGER = logging.getLogger(SCRIPT_FILE)
LOGGER.setLevel(COM.LOGGER_LEVEL_INSERT_GW_EVENTS)
HANDLER = logging.handlers.SysLogHandler(address=('localhost', 514), facility='local6')
FORMATTER = logging.Formatter('%(name)s[%(process)d]: %(levelname)s: [%(lineno)d]%(message)s')
HANDLER.formatter = FORMATTER
LOGGER.addHandler(HANDLER)

def file_check(filename):
    """
    /var/lib/baogw/primary or test ファイル有無をチェック
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
    now_datetime = datetime.datetime.now()
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
        customer_ci = value3_split[len(value3_split) - 2]
        customer_name = value3_split[len(value3_split) - 1]
        alarm_status = 'error'
        insert_value = (
            update_time, detected_host, customer_ci,
            customer_name, COM.BAO_FORMAT_ERROR_HOST, update_time, COM.BAO_FORMAT_ERROR_ALARM,
            COM.BAO_FORMAT_ERROR_DEVICE, alarm_status, COM.FORMAT_ERROR_MESSAGE, ''
        )
        return insert_value, alarm_status

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
        datetime.datetime.strptime(detected_time, '%Y.%m.%d %H:%M:%S')
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

    # alarm_time「****-**-**@**:**:**.***」のみ許可（*は半角数字のみ）
    check_pattern = re.compile(
        r'^[0-9]{4}-[0-9]{2}-[0-9]{2}@[0-9]{2}:[0-9]{2}:[0-9]{2}.[0-9]{2,3}$')
    if format_check(check_pattern, value3_split[1]) is not True:
        LOGGER.error('alarm_timeフォーマット異常です。 %s', cmmon_alm_log)
        LOGGER.info('alarm_timeフォーマット異常です。alarm_time= %s', value3_split[1])
        LOGGER.debug('%s', value3)
        sys.exit()
    alarm_time = value3_split[1].replace('@', ' ')
    try:
        datetime.datetime.strptime(alarm_time, '%Y-%m-%d %H:%M:%S.%f')
    except ValueError:
        LOGGER.error('alarm_timeフォーマット異常です。 %s', cmmon_alm_log)
        LOGGER.info('alarm_timeフォーマット異常です。 alarm_time= %s', alarm_time)
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

    # alarm_status 'error','normal','sec','info','syserror','sysnormal'以外は規定外（大文字小文字も判別）
    # alarm_status の文字は共有設定ファイルから抜き出す
    alarm_status = value3_split[5]
    alarm_status_pattern = (COM.GW_ALARM_STATUS_ERROR, COM.GW_ALARM_STATUS_NORMAL, COM.GW_ALARM_STATUS_INFO)
    if alarm_status not in alarm_status_pattern:
        LOGGER.error('alarm_statusが規定外です。 %s', cmmon_alm_log)
        LOGGER.info('alarm_statusが規定外です。 alarm_status= %s', alarm_status)
        LOGGER.debug('%s', value3)
        sys.exit()

    # summary 個別監視装置の「補足」情報 制御コード以外すべての文字を許可
    # 改行が含まれる場合は、BAO連携用に変換する
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

    return insert_value, alarm_status

def patolamp_on(alarm_status, host):
    """
    パトランプ鳴動関数
    """
    # パトランプ鳴動ファイル作成
    patolamp_file = ''
    if alarm_status == COM.GW_ALARM_STATUS_ERROR or alarm_status == COM.GW_ALARM_STATUS_INFO:
        patolamp_file = COM.RED_PATOLAMP_FILE
    elif alarm_status == COM.GW_ALARM_STATUS_NORMAL or alarm_status == COM.GW_ALARM_STATUS_SYSNORMAL:
        patolamp_file = COM.GREEN_PATOLAMP_FILE
    else:
        patolamp_file = COM.YELLOW_PATOLAMP_FILE

    # ZabbixApiインスタンス作成
    api = FUNC.ZabbixApi(COM.ZABBIX_IP, COM.ZABBIX_USER, COM.ZABBIX_PASSWD)
    # 顧客名からホストグループリストを抽出
    hostgroups = FUNC.get_hostgroups_by_host(api, host)

    # 新宿11階パトランプの場合、新宿11階パトランプ鳴動ファイル作成
    if COM.FLOOR_11TH_HOSTGROUP in hostgroups:
        make_patolamp_file(patolamp_file)
    # 新宿12階パトランプの場合、新宿12階パトランプ鳴動ファイル作成
    if COM.FLOOR_12TH_HOSTGROUP in hostgroups:
        make_patolamp_file(patolamp_file + '_' + COM.FLOOR_12TH)
    # ハウコム運用顧客の場合、ハウコム専用パトランプ鳴動ファイル作成
    if COM.HOWCOM_HOSTGROUP in hostgroups:
        make_patolamp_file(patolamp_file + '_' + COM.HOWCOM)
    # VIP顧客の場合、VIP専用パトランプ鳴動ファイル作成
    if COM.VIP_HOSTGROUP in hostgroups:
        make_patolamp_file(patolamp_file + '_' + COM.VIP)
    return


def make_patolamp_file(patolamp_on_file):
    """
    パトランプを鳴動させるファイルを作成する関数
    """
    # ファイル作成
    try:
        pato_flg = open('/var/lib/baogw/' + patolamp_on_file, 'a')
        pato_flg.close()
        LOGGER.info('パトランプフラグ(/var/lib/baogw/%s)を作成しました。', patolamp_on_file)
    except Exception as msg:
        LOGGER.error('パトランプフラグ(/var/lib/baogw/%s)の作成に失敗しました。', patolamp_on_file)
        LOGGER.info('%s', msg)
    return

def insert_baogw(dbhost, table_name, insert_value, step_num):
    """
    INSERT
    """
    # データベース（baogw）への接続情報
    dbbaogw = FUNC.connect_db(dbhost)
    baogwcur = dbbaogw.cursor(buffered=True) # カーソル
    sql = 'INSERT INTO ' + table_name + ' (update_time, detected_time,\
    detected_host, customer_ci, customer_name, hostname,\
    alarm_time, ci_name, device, alarm_status, summary, host\
    ) VALUES (now(3), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);'
    try:
        baogwcur.execute(sql, insert_value)
        LOGGER.info('[%s] %s %s INSERT成功', step_num, dbhost, table_name)
    except mysql.connector.errors.IntegrityError as msg:
        LOGGER.critical('[%s] %s %s INSERT失敗 %s', step_num, dbhost, table_name, insert_value)
        LOGGER.info('%s', msg)
    # コミット
    dbbaogw.commit()
    # 終了処理
    baogwcur.close()
    dbbaogw.close()

def remote_connect_check(dbhost):
    """
    remotehost の DB への接続確認
    """
    # データベース（baogw）への接続情報
    try:
        dbremote = mysql.connector.connect(
            host=dbhost,
            db=COM.MY_DB,
            user=COM.MY_USER,
            password=COM.MY_PASSWD,
            connection_timeout=3
        )
        dbremote.close()
        #dbremote.is_connected()
        LOGGER.info('remote DB[%s] 接続成功', dbhost)
        return True
    except Exception as msg:
        LOGGER.critical('remote DB[%s] 接続失敗、rescue 動作へ', dbhost)
        LOGGER.info('%s', msg)
        return False

def main():
    """
    スクリプト本体
    """
    # gw_events へ INSERT する変数を取得
    insert_value, alarm_status = get_insert_value()

    # 接続するDBのhostを定義
    local_host = COM.MY_HOST
    remote_host = COM.REMOTE_HOST
    current_host = local_host

    # testファイルの有無を確認
    if file_check('test') is True:
        LOGGER.info('testモードのため、テストモードで動作実行')
        try:
            insert_baogw(local_host, 'gw_events', insert_value, 'End1')
        except Exception as msg:
            LOGGER.critical('[Failed1] Stopped by an unknown error.')
            LOGGER.info('%s', msg)

    # Primaryファイルの有無を確認
    elif file_check('primary') is True:
        LOGGER.info('マスターモードのため、マスター動作実行')
        # アラート制御
        action_no = FUNC.get_action_no(insert_value[3], insert_value[4], insert_value[6])
        # アクションナンバーが20または30～35以外のときパトランプ鳴動
        if (action_no != COM.GW_KISYS_STATUS_NOPATOLAMP
            and action_no != COM.GW_KISYS_STATUS_WAITING_5
            and action_no != COM.GW_KISYS_STATUS_WAITING_10
            and action_no != COM.GW_KISYS_STATUS_WAITING_15
            and action_no != COM.GW_KISYS_STATUS_WAITING_20
            and action_no != COM.GW_KISYS_STATUS_WAITING_25
            and action_no != COM.GW_KISYS_STATUS_WAITING_30):
            # パトランプ鳴動
            patolamp_on(alarm_status, insert_value[10])
        try:
            insert_baogw(local_host, 'gw_events', insert_value, 'End2')
        except Exception as msg:
            LOGGER.critical('[Failed2] Stopped by an unknown error.')
            LOGGER.info('%s', msg)
    else:
        LOGGER.info('スレーブモードのため、スレーブ動作実行')
        # 事前にRemoteホストのDBへ接続確認
        if remote_connect_check(remote_host) is True:
            current_host = remote_host
            try:
                insert_baogw(remote_host, 'gw_events', insert_value, 'End3')
            except Exception as msg:
                LOGGER.critical('[Failed3] Stopped by an unknown error.')
                LOGGER.info('%s', msg)
        else:
            try:
                insert_baogw(local_host, 'gw_rescue_events', insert_value, 'End4')
            except Exception as msg:
                LOGGER.critical('[Failed4] Stopped by an unknown error.')
                LOGGER.info('%s', msg)
            sys.exit()

if __name__ == '__main__':
    try:
        main()
    except Exception as msg:
        LOGGER.critical('[End0] Stopped by an unknown error.')
 ##       LOGGER.exception(msg)
        LOGGER.info('%s', msg)

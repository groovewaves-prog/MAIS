#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
## 概要 ##
exec_patolamp.py
patolampファイルを監視し,存在したらrshでpatolampを鳴動させる
"""

## import ##
import traceback
import os
import sys
import fcntl
import time
import logging
import logging.handlers
import subprocess
import gwcommon as COM
import urllib.request
import json

##################################

## スクリプトのパス、ファイル名を取得
SCRIPT_FILE = os.path.basename(__file__)

""" log出力設定 rsyslogd に渡す設定 """
LOGGER = logging.getLogger(SCRIPT_FILE)
LOGGER.setLevel(COM.LOGGER_LEVEL_EXEC_PATOLAMP) # 出力レベルの設定
HANDLER = logging.handlers.SysLogHandler(address=('localhost', 514), facility='local6') # 出力先の設定
FORMATTER = logging.Formatter('%(name)s[%(process)d]: %(levelname)s: [%(lineno)d]%(message)s')
HANDLER.formatter = FORMATTER
LOGGER.addHandler(HANDLER)


def patolamp_post_request(ver, ip, pattern, timeout=2):
    """
    ver判断後、パラメータで指定するip,パターンでパトランプを鳴動させる関数
    NGは3回リトライする。
    """
    if ver == 'DN1500':
        url = f'http://{ip}/api/control'
    else:
        url = f'http://{ip}/api/control.php'
    headers = {
        'Content-Type': 'application/json'
    }
    data = {
        'acop': pattern
    }
    data = json.dumps(data).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers=headers, method='POST')

    attempts = 0
    max_attempts = 3

    while attempts < max_attempts:
        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                response_body = response.read().decode('utf-8')
                print(response_body)
                if 'success' in response_body.lower():
                    return True, 'patolamp on Successful'
                else:
                    return False, response_body
        except urllib.error.URLError as e:
            print(f"Attempt {attempts + 1}: {e.reason}")
            attempts += 1
            if attempts >= max_attempts:
                return False, e.reason
        time.sleep(1)  # Wait for 1 second before retrying

    return False, 'Failed after multiple attempts'


def lock_file(locktarget):
    """
    ファイルロックを試み、ロックできなければ終了
    """
    lock_file_name = f'{locktarget}.lock'
    try:
        with open(lock_file_name, 'w') as fp_lock:
            fcntl.flock(fp_lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        return open(lock_file_name, 'w')  # ファイルを開いたままにする
    except OSError as msg:
        LOGGER.info(f'Another process is running, so exit. {msg}')
        sys.exit()


def file_check(filename):
    """
    動作フラグファイル(/var/lib/baogw/ 配下) の有無をチェック
    """
    check_file = f'/var/lib/baogw/{filename}'
    return os.path.exists(check_file)


def file_delete(filename):
    """
    動作フラグファイル(/var/lib/baogw/ 配下) のファイルを削除
    """
    delete_file = f'/var/lib/baogw/{filename}'
    try:
        os.remove(delete_file)
        LOGGER.info(f'パトランプフラグ({delete_file})を削除しました。')
    except Exception as msg:
        LOGGER.error(f'パトランプフラグ({delete_file})の削除に失敗しました。')
        LOGGER.error(str(msg))
    return


def try_patolamp_activation(ver, patolamp_ip, patolamp_pattern, patolamp_kind, place_name):
    """
    パトランプをNG時規定回数実行し、結果をログ出力する関数
    """
    total_retries = 3  # リトライ回数を設定
    for attempt in range(total_retries):
        result, error = patolamp_post_request(ver, patolamp_ip, patolamp_pattern)
        if result:
            LOGGER.info(f'{patolamp_kind} {place_name} パトランプ鳴動成功!')
            return True
        LOGGER.info(f'{patolamp_kind} {place_name} パトランプ鳴動失敗 試行回数：{attempt + 1} cause: {error}')
        if attempt == total_retries - 1:
            LOGGER.error(f'{patolamp_kind} {place_name} パトランプ鳴動最終的に失敗')
        time.sleep(5)  # 5秒待機後リトライ
    return False # 通信失敗


def patolamp_on(ver, patolamp_kind, patolamp_pattern, patolamp_ip=None):
    """
    運用場所を設定して、パトランプを鳴動処理を実行する関数
    """
    if not patolamp_ip:
        patolamp_ip = COM.PATLAMP_IP
    
    place_name = {
        COM.FLOOR_12TH_PATLAMP_IP: 'TSD',
        COM.FLOOR_11TH_PATLAMP_IP: 'SCC',
        COM.KDDI_MIYAZAKI_PATLAMP_IP: 'KDDI宮崎'
    }.get(patolamp_ip, 'SCC運用')

    return try_patolamp_activation(ver, patolamp_ip, patolamp_pattern, patolamp_kind, place_name)


#本PGないでは利用無しだが、念のために残し
def process_patolamp_signals(patolamp_config):
    for patolamp_type, patolamp_file, patolamp_pattern in patolamp_config:
        if file_check(patolamp_file):
            if patolamp_on(patolamp_type, patolamp_pattern):
                file_delete(patolamp_file)


def main():
    # SCC(RED → YELLOW → GREEN) → TDS() → 宮崎() → VIP() の順に該当fileをチェックし、あれば、パトランプ鳴動処理を実施
    # 無限ループ開始
    while True:
        LOGGER.debug('無限ループ先頭')

        # パトランプ鳴動情報をpatolamp_detailsに設定
        patolamp_details = {
            COM.FLOOR_11TH_FILE: (
                                    COM.FLOOR_11TH_PATLAMP_IP, 
                                    COM.FLOOR_11TH_PATLAMP_VER, 
                                    (COM.RED_PATOLAMP_PATTERN_DN1700, COM.YELLOW_PATOLAMP_PATTERN_DN1700, COM.GREEN_PATOLAMP_PATTERN_DN1700)
                                    ),
            COM.FLOOR_12TH_FILE: (
                                    COM.FLOOR_12TH_PATLAMP_IP, 
                                    COM.FLOOR_12TH_PATLAMP_VER,
                                    (COM.RED_PATOLAMP_PATTERN_DN1700, COM.YELLOW_PATOLAMP_PATTERN_DN1700, COM.GREEN_PATOLAMP_PATTERN_DN1700)
                                    ),
            COM.KDDI_MIYAZAKI_FILE: (
                                    COM.KDDI_MIYAZAKI_PATLAMP_IP,
                                    COM.KDDI_MIYAZAKI_PATLAMP_VER,
                                    (COM.RED_PATOLAMP_PATTERN_DN1500, COM.YELLOW_PATOLAMP_PATTERN_DN1500, COM.GREEN_PATOLAMP_PATTERN_DN1500)
                                    ),
            COM.VIP: (
                COM.FLOOR_11TH_PATLAMP_IP,
                COM.FLOOR_11TH_PATLAMP_VER, 
                (COM.RED_PATOLAMP_PATTERN_DN1700, COM.YELLOW_PATOLAMP_PATTERN_DN1700, COM.GREEN_PATOLAMP_PATTERN_DN1700)
                )
        }
        # flieチェック → パトランプ鳴動main処理
        for identifier, (ip, ver, patterns) in patolamp_details.items():
            for color, pattern in zip(['Red', 'Yellow', 'Green'], patterns):
                patolamp_file = f'{color.lower()}_patolamp_on{identifier}'
                if file_check(patolamp_file):
                    if patolamp_on(ver, color, pattern, ip):
                        file_delete(patolamp_file)

        # インターバル
        time.sleep(COM.PATO_INTERVAL)


if __name__ == '__main__':
    # 起動済みプロセスの確認, ファイルがロックできなければ, 起動済みプロセスがいると判断
    LOCK_RESULT = lock_file(__file__)
    LOGGER.debug(LOCK_RESULT)
    try:
        main()
    except Exception as msg:
        LOGGER.critical('Stopped by an unknown error.')
        EXCEPTIONS_MSG = traceback.format_exc()
        LOGGER.info(EXCEPTIONS_MSG)


#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
## 概要 ##
exec_patolamp_20251029.py
パトランプファイルを監視し、存在したらHTTPでパトランプを鳴動させる
"""

import traceback
import os
import sys
import fcntl
import time
import logging
import logging.handlers
import gwcommon as COM
import gwfunction as FUNC
import urllib.request
import urllib.error
import json

SCRIPT_FILE = os.path.basename(__file__)

""" log出力設定 rsyslogd に渡す設定 """
LOGGER = logging.getLogger(SCRIPT_FILE)
LOGGER.setLevel(COM.LOGGER_LEVEL_EXEC_PATOLAMP)
HANDLER = logging.handlers.SysLogHandler(address=(COM.SYSLOG_HOST, COM.SYSLOG_PORT), facility=COM.SYSLOG_FACILITY)
FORMATTER = logging.Formatter('%(name)s[%(process)d]: %(levelname)s: [%(lineno)d]%(message)s')
HANDLER.formatter = FORMATTER
LOGGER.addHandler(HANDLER)

def patolamp_post_request(url, pattern, timeout=COM.PATO_REQUEST_TIMEOUT, max_attempts=COM.MAX_ATTEMPTS):
    """
    成功した場合はTrueを返し、成功以外はmax_attempts回リトライする。
    """
    headers = {'Content-Type': 'application/json'}
    data = {'acop': pattern}
    data = json.dumps(data).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers=headers, method='POST')

    attempts = 0
    last_error = ''

    while attempts < max_attempts:
        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                response_body = response.read().decode('utf-8')
                LOGGER.info(f"[Attempt {attempts+1}] Response: {response_body}")

                if 'success' in response_body.lower():
                    return True, 'patolamp on Successful'
                last_error = response_body

        except Exception as e:
            last_error = str(e)
            LOGGER.error(f"[Attempt {attempts+1}] Exception: {last_error}")

        attempts += 1
        if attempts < max_attempts:
            time.sleep(COM.PATO_REQUEST_RETRY_INTERVAL)

    return False, last_error

def lock_file(locktarget):
    """
    ファイルロックを試み、ロックできなければ終了
    """
    lock_file_name = f'{locktarget}.lock'
    try:
        fp_lock = open(lock_file_name, 'w')
        fcntl.flock(fp_lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        return fp_lock  # ファイルを開いたままにする
    except OSError as msg:
        LOGGER.info(f'Another process is running, so exit. {msg}')
        sys.exit()

def file_delete(filename):
    """
    動作フラグファイル(COM.FLAG_DIR 配下) のファイルを削除
    """
    delete_file = os.path.join(COM.FLAG_DIR, filename)
    try:
        os.remove(delete_file)
        LOGGER.info(f'パトランプフラグ({delete_file})を削除しました。')
    except Exception as msg:
        LOGGER.error(f'パトランプフラグ({delete_file})の削除に失敗しました。')
        LOGGER.error(str(msg))
    return

def get_default_patolamp_values():
    """
    PATOLAMP_DETAILSからデフォルトhostgroupの情報（URL, RED, YELLOW, GREEN パターン）を取得
    """
    for rec in FUNC.PATOLAMP_DETAILS:
        hostgroups = rec.get('hostgroups', '')
        if COM.DEFAULT_PATOLAMP_HOSTGROUP in hostgroups.split(','):
            return {
                'DEFAULT_URL': rec.get('url'),
                'DEFAULT_RED_PATTERN': rec.get('RED_PATTERN'),
                'DEFAULT_YELLOW_PATTERN': rec.get('YELLOW_PATTERN'),
                'DEFAULT_GREEN_PATTERN': rec.get('GREEN_PATTERN')
            }
    return None

def main():
    """
    メイン処理
    """

    # デフォルト値を取得
    default_values = get_default_patolamp_values()
    if (not default_values or
        not default_values['DEFAULT_URL'] or
        not default_values['DEFAULT_RED_PATTERN'] or
        not default_values['DEFAULT_YELLOW_PATTERN'] or
        not default_values['DEFAULT_GREEN_PATTERN']):
        LOGGER.error(f"デフォルトhostgroup({COM.DEFAULT_PATOLAMP_HOSTGROUP})のパトランプ情報が取得できません。PGを終了します。")
        sys.exit(1)

    while True:
        LOGGER.debug('無限ループ先頭')

        for rec in FUNC.PATOLAMP_DETAILS:
            hostgroups = rec.get('hostgroups', '')
            url = rec.get('url')
            red_pattern = rec.get('RED_PATTERN')
            yellow_pattern = rec.get('YELLOW_PATTERN')
            green_pattern = rec.get('GREEN_PATTERN')

            # どれか1つでも未指定なら全てデフォルト値で置換
            if not url or not red_pattern or not yellow_pattern or not green_pattern:
                url = default_values['DEFAULT_URL']
                red_pattern = default_values['DEFAULT_RED_PATTERN']
                yellow_pattern = default_values['DEFAULT_YELLOW_PATTERN']
                green_pattern = default_values['DEFAULT_GREEN_PATTERN']

            patterns = [red_pattern, yellow_pattern, green_pattern]
            colors = ['Red', 'Yellow', 'Green']

            for color, pattern in zip(colors, patterns):
                patolamp_file = f'{hostgroups}_{color.lower()}_patolamp_on'
                if not FUNC.file_check(patolamp_file):
                    continue

                # HTTPリクエストの成否
                result, cause = patolamp_post_request(url, pattern)
                if result is True:
                    LOGGER.info("【%s】%s を鳴動 →%s", hostgroups, color, url)
                else:
                    LOGGER.error("【%s】%s の鳴動に失敗 (cause:%s)→%s", hostgroups, color, cause, url)
                file_delete(patolamp_file)

                # 同一hostgroup内の残りフラグは鳴動せずに削除
                idx = colors.index(color)
                for skip_color in colors[idx+1:]:
                    skip_file = f'{hostgroups}_{skip_color.lower()}_patolamp_on'
                    if FUNC.file_check(skip_file):
                        LOGGER.info(f"[{hostgroups}][{url}] {skip_color} は優先度が低いため鳴動せず削除")
                        file_delete(skip_file)

                break

        # インターバル
        time.sleep(COM.PATO_INTERVAL)

if __name__ == '__main__':
    # 起動済みプロセスの確認
    lock_result = lock_file(__file__)
    LOGGER.debug(lock_result)
    try:
        main()
    except Exception as msg:
        LOGGER.error('Stopped by an unknown error.')
        exceptions_msg = traceback.format_exc()
        LOGGER.error(exceptions_msg)

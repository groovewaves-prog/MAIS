#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
## 概要 ##
insert_zabbix_user_not_use_sftp.py
新ADサーバの本格利用に伴い、AD連携方式変更。新ADサーバから連携ディレクトリにID情報のCSVファイルが存在することを前提に
以下の処理を実施するように変更　2024/09/18 by oozera
1.連携ディレクトリから、ZABBIXユーザー登録ファイルを読み込む。
2.1行ずつパラメータに分割し、パラメータチェックを行い、申請種別毎にZABBIXユーザーの登録・変更・削除を行う。
3.パラメータチェックエラーやZABBIXユーザー登録エラーなどが発生した場合も最終行まで処理を行い、最後にまとめてエラーログを出力する。
"""

## import ##
import csv
import datetime
import json
import logging
import logging.handlers
import os
import sys
import re
import traceback
import urllib.request
import user_common as COM

##################################

# スクリプトのパス、ファイル名を取得
SCRIPT_FILE = os.path.basename(__file__)

# ログ出力設定
LOGGER = logging.getLogger(SCRIPT_FILE)
LOGGER.setLevel(logging.INFO) # 出力レベルの設定
HANDLER = logging.handlers.SysLogHandler(address=('localhost', 514), facility='local6') # 出力先の設定
FORMATTER = logging.Formatter('%(name)s[%(process)d]: %(levelname)s: [%(lineno)d]%(message)s')
HANDLER.formatter = FORMATTER
LOGGER.addHandler(HANDLER)

# ZABBIXユーザー登録ファイル
CSV_FILE_PATH = COM.current_file


# ZABBIXサーバ情報
ZABBIX_IP =COM.ZABBIX_IP
ZABBIX_USER = COM.ZABBIX_USER
ZABBIX_PASSWD = COM.ZABBIX_PASSWD

# LDAPユーザーグループ
READER = 'Reader'
OPE_MANAGER = 'OpeManager'
OPE_ENGINEER = 'OpeEngineer'
SYS_ENGINEER = 'SysEngineer'
SYS_MANAGER = 'SysManager'
HOWCOM_OPE = 'HOWCOM-Operator'
HOWCOM_OPE_MANAGER = 'HOWCOM-OpeManager'
PERSOL_OPE = 'PERSOL-Operator'
PERSOL_OPE_MANAGER = 'PERSOL-OpeManager'
#MC_OPE_MANAGER = 'MC-OpeManager'
#YAZAKI_OPE_MANAGER = 'YAZAKI-OpeManager'
#ADECCO_GAP_OPE_MANAGER = 'ADECCO_GAP-OpeManager'
TOSHIBA_MEMORY_SYS_ENGINEER = 'ToshibaMemory-SysEngineer'
SL_MAINTENANCE = 'SL-Maintenance'

# ユーザーグループマッピング（LDAPユーザーグループ:ZABBIXユーザーグループ）
USER_GROUPS = [ \
READER, \
OPE_MANAGER, \
OPE_ENGINEER, \
SYS_ENGINEER, \
SYS_MANAGER, \
HOWCOM_OPE, \
HOWCOM_OPE_MANAGER, \
PERSOL_OPE, \
PERSOL_OPE_MANAGER, \
#MC_OPE_MANAGER, \
#YAZAKI_OPE_MANAGER, \
#ADECCO_GAP_OPE_MANAGER, \
TOSHIBA_MEMORY_SYS_ENGINEER, \
SL_MAINTENANCE, \
]

# ユーザーグループマッピング（LDAPユーザーグループ:ZABBIXユーザーの種類）
USER_TYPES = { \
READER:1, \
OPE_MANAGER:2, \
OPE_ENGINEER:2, \
SYS_ENGINEER:1, \
SYS_MANAGER:3, \
HOWCOM_OPE:1, \
HOWCOM_OPE_MANAGER:2, \
PERSOL_OPE:1, \
PERSOL_OPE_MANAGER:2, \
#MC_OPE_MANAGER:2, \
#YAZAKI_OPE_MANAGER:2, \
#ADECCO_GAP_OPE_MANAGER:2, \
TOSHIBA_MEMORY_SYS_ENGINEER:1, \
SL_MAINTENANCE:3, \
}

# HOWCOMユーザーグループマッピング（LDAPユーザーグループ:ZABBIXユーザーグループ）
HOWCOM_USER_GROUPS = [ \
HOWCOM_OPE, \
HOWCOM_OPE_MANAGER, \
TOSHIBA_MEMORY_SYS_ENGINEER, \
]

# 登録/変更/削除
INSERT_ACTION = '登録'
UPDATE_ACTION = '変更'
DELETE_ACTION = '削除'

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

def get_usrgrpid(api, usrgrp_name):
    """
    ユーザーグループ名からユーザーグループIDを取得する
    戻り値：ユーザーグループID、エラーメッセージ
    """
    usrgrpid = ''
    error_message = ''
    response = api.request('usergroup.get', {'output': 'usrgrpid', 'filter': {'name': usrgrp_name}})
    if 'result' in response:
        if response['result']:
            usrgrpid = response['result'][0]['usrgrpid']
        else:
            error_message = 'エラーメッセージ：ユーザーグループが登録されていません。%s' % usrgrp_name
    elif 'error' in response:
        error_message = 'エラーメッセージ：%s %s' % (response['error']['message'], response['error']['data'])
    return usrgrpid, error_message

def get_userid(api, alias):
    """
    アカウント名からユーザーIDを取得する
    戻り値：ユーザーID、エラーメッセージ
    """
    userid = ''
    error_message = ''
    # zabbixバージョンアップによりusers.aliasがusernameに変更
    response = api.request('user.get', {'output': 'userid', 'filter': {'username': alias}})
    if 'result' in response:
        if response['result']:
            userid = response['result'][0]['userid']
        else:
            error_message = 'エラーメッセージ：アカウント名が登録されていません。%s' % alias
    elif 'error' in response:
        error_message = 'エラーメッセージ：%s %s' % (response['error']['message'], response['error']['data'])
    return userid, error_message

def format_check(check_pattern, argument):
    """
    フォーマットチェック関数定義
    """
    return check_pattern.match(argument) is not None

def check_params(params):
    """
    パラメータチェック
    戻り値：エラーメッセージ
    """
    # アカウント名
    if not params['アカウント名']:
        return 'エラーメッセージ：アカウント名が未入力です。'
    # ユーザーグループ、ユーザーの種類
    if not params['説明'] in USER_TYPES and not params['説明'] in USER_GROUPS:
        return 'エラーメッセージ：ユーザーグループが対象外です。%s' % params['説明']
    return ''

def get_insert_data(api, params):
    """
    パラメータをチェックし、登録データを変数に格納
    戻り値：登録データ、エラーメッセージ
    """
    # パラメータチェック
    error_message = check_params(params)
    if error_message:
        return '', error_message

    data = {}
    # zabbixバージョンアップによりusers.aliasがusernameに変更
    data['username'] = params['アカウント名']
    data['surname'] = params['姓']
    data['name'] = params['名']
    # zabbixバージョンアップによりusers.typeがroleidに変更
    data['roleid'] = USER_TYPES[params['説明']]
    data['usrgrps'] = []
    # ユーザーグループID取得
    usrgrpid, error_message = get_usrgrpid(api, params['説明'])
    if usrgrpid:
        #data['usrgrps'].append(usrgrpid)
        wk_usrgrps = {}
        wk_usrgrps['usrgrpid'] = usrgrpid
        data['usrgrps'].append(wk_usrgrps)
    else:
        return '', error_message
    # HOWCOMユーザーグループの場合、ユーザグループ：ハウコム運用者を追加
    if params['説明'] in HOWCOM_USER_GROUPS:
        # HOWCOMユーザーグループID取得
        usrgrpid, error_message = get_usrgrpid(api, 'ハウコム運用者')
        if usrgrpid:
            #data['usrgrps'].append(usrgrpid)
            wk_usrgrps = {}
            wk_usrgrps['usrgrpid'] = usrgrpid
            data['usrgrps'].append(wk_usrgrps)
        else:
            return '', error_message
    # 初期パスワード
    #元の'P@ssw0rd'だと新しいzabbixでは短すぎてエラーになる
    data['passwd'] = 'P@ssw0rd1'
    # 自動ログアウト（0:無効）
    data['autologout'] = 0
    # 言語
    data['lang'] = 'ja_JP'
    return data, ''

def insert_zabbix_user(api, data):
    """
    ZABBIXユーザー登録
    戻り値：エラーメッセージ
    """
    # ユーザ登録
    print(data)
    response = api.request('user.create', data)
    # ユーザ登録エラー
    if 'error' in response:
        return 'エラーメッセージ：%s %s' % (response['error']['message'], response['error']['data'])
    return ''

def get_update_data(api, params):
    """
    パラメータをチェックし、変更データを変数に格納
    戻り値：変更データ、エラーメッセージ
    """
    # パラメータチェック
    error_message = check_params(params)
    if error_message:
        return '', error_message

    data = {}
    # ユーザーID取得
    userid, error_message = get_userid(api, params['アカウント名'])
    if userid:
        data['userid'] = userid
    else:
        return '', error_message
    data['surname'] = params['姓']
    data['name'] = params['名']
    # zabbixバージョンアップによりusers.typeがroleidに変更
    data['roleid'] = USER_TYPES[params['説明']]
    data['usrgrps'] = []
    # ユーザーグループID取得
    usrgrpid, error_message = get_usrgrpid(api, params['説明'])
    if usrgrpid:
        #data['usrgrps'].append(usrgrpid)
        wk_usrgrps = {}
        wk_usrgrps['usrgrpid'] = usrgrpid
        data['usrgrps'].append(wk_usrgrps)
    else:
        return '', error_message
    # HOWCOMユーザーグループの場合、ユーザグループ：ハウコム運用者を追加
    if params['説明'] in HOWCOM_USER_GROUPS:
        # HOWCOMユーザーグループID取得
        usrgrpid, error_message = get_usrgrpid(api, 'ハウコム運用者')
        if usrgrpid:
            #data['usrgrps'].append(usrgrpid)
            wk_usrgrps = {}
            wk_usrgrps['usrgrpid'] = usrgrpid
            data['usrgrps'].append(wk_usrgrps)
        else:
            return '', error_message
    return data, ''

def update_zabbix_user(api, data):
    """
    ZABBIXユーザー変更
    戻り値：エラーメッセージ
    """
    # ユーザ変更
    print(data)
    response = api.request('user.update', data)
    # ユーザ変更エラー
    if 'error' in response:
        return 'エラーメッセージ：%s %s' % (response['error']['message'], response['error']['data'])
    return ''

def get_delete_data(api, params):
    """
    パラメータをチェックし、削除データを変数に格納
    戻り値：削除データ、エラーメッセージ
    """
    # パラメータチェック
    error_message = check_params(params)
    if error_message:
        return '', error_message

    data = []
    # ユーザーID取得
    userid, error_message = get_userid(api, params['アカウント名'])
    if userid:
        data.append(userid)
    else:
        return '', error_message
    return data, ''

def delete_zabbix_user(api, data):
    """
    ZABBIXユーザー削除
    戻り値：エラーメッセージ
    """
    # ユーザ削除
    print(data)
    response = api.request('user.delete', data)
    # ユーザ削除エラー
    if 'error' in response:
        return 'エラーメッセージ：%s %s' % (response['error']['message'], response['error']['data'])
    return ''

def main():
    """
    メイン処理
    """
    # 受信ファイルの存在確認
    if not os.path.exists(CSV_FILE_PATH):
        LOGGER.error('入力ファイルがありません。処理を中断します。')
        return

    # ZabbixApiインスタンス作成
    api = ZabbixApi(ZABBIX_IP, ZABBIX_USER, ZABBIX_PASSWD)
    # エラーメッセージ
    error_messages = []
    # ファイルをオープンする
    # 文字コードをcp932→uft-8-sigに変更 2024/10/15 oozera
    csvfile = open(CSV_FILE_PATH, 'r', encoding='utf-8-sig')
    # 1行ずつユーザー登録を行う
    lines = csv.DictReader(csvfile, delimiter=",", doublequote=True, lineterminator="\r\n", quotechar='"', skipinitialspace=True)
    for params in lines:
        error_message = ''
        # ZABBIXユーザー登録
        if params['申請種別'] == INSERT_ACTION:
            insert_data, error_message = get_insert_data(api, params)
            if insert_data:
                error_message = insert_zabbix_user(api, insert_data)
            # ZABBIXユーザーが登録されている場合、変更する
            if error_message.find('already exists.') != -1:
                update_data, error_message = get_update_data(api, params)
                if update_data:
                    error_message = update_zabbix_user(api, update_data)
        # ZABBIXユーザー変更
        elif params['申請種別'] == UPDATE_ACTION:
            update_data, error_message = get_update_data(api, params)
            if update_data:
                error_message = update_zabbix_user(api, update_data)
            # ZABBIXユーザーが登録されていない場合、登録する
            if error_message.find('アカウント名が登録されていません。') != -1:
                insert_data, error_message = get_insert_data(api, params)
                if insert_data:
                    error_message = insert_zabbix_user(api, insert_data)
        # ZABBIXユーザー削除
        elif params['申請種別'] == DELETE_ACTION:
            delete_data, error_message = get_delete_data(api, params)
            if delete_data:
                error_message = delete_zabbix_user(api, delete_data)
        else:
            continue
        # エラーメッセージ格納
        if error_message:
            if error_message.find('ユーザーグループが対象外です。') != -1:
                LOGGER.info('%s アカウント名：%s', error_message, params['アカウント名'])
                continue
            LOGGER.info('ユーザー%sに失敗しました。アカウント名：%s', params['申請種別'], params['アカウント名'])
            error_messages.append('%s アカウント名：%s' % (error_message, params['アカウント名']))
        else:
            LOGGER.info('ユーザー%sに成功しました。アカウント名：%s', params['申請種別'], params['アカウント名'])

    # ファイルをクローズする
    csvfile.close()
    # ファイル削除
    os.remove(CSV_FILE_PATH)

    # エラーメッセージがあれば、まとめてエラーログを出力する
    if error_messages:
        LOGGER.info('; '.join(error_messages))


if __name__ == '__main__':
    try:
        LOGGER.info('ZABBIXユーザー登録開始')
        main()
        LOGGER.info('ZABBIXユーザー登録終了')
    except Exception as msg:
        LOGGER.error('Stopped by an unknown error.')
        EXCEPTIONS_MSG = traceback.format_exc()
        LOGGER.info(EXCEPTIONS_MSG)

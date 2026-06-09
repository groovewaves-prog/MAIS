#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
from wsgiref.util import setup_testing_defaults
from wsgiref.simple_server import make_server
import socket
import json
import os
from logging import getLogger, StreamHandler, Formatter, FileHandler, DEBUG
from logging.handlers import SysLogHandler 
import re
import config as CONFIG

#ログ出力設定
def setup_logger(log_folder, modname=__name__, level=CONFIG.log_level):
    logger = getLogger(modname)
    logger.setLevel(level)    #コンソール

    stream_h = StreamHandler()
    stream_h.setLevel(level)
    stream_formatter = Formatter('%(asctime)s %(levelname)s [%(filename)s:%(lineno)d]  %(message)s')
    stream_h.setFormatter(stream_formatter)
    logger.addHandler(stream_h)

    syslog_h = SysLogHandler(address=('localhost', 514), facility='local4') 
    syslog_h.setLevel(level)
    syslog_formatter = Formatter('%(name)s[%(process)d]: %(levelname)s: [%(filename)s:%(lineno)d] %(message)s')
    syslog_h.setFormatter(syslog_formatter)
    logger.addHandler(syslog_h)
    return logger

LOGFILE = "./%s.log"
MODULE_NAME = os.path.basename(__file__)
LOGGER = setup_logger(LOGFILE % MODULE_NAME, MODULE_NAME)
MY_HOSTNAME = socket.gethostname()

# サーバー名からホスト(IPアドレス)を返す
def gethostbyname(hostname):
    for server in CONFIG.DS_SERVER_LIST:
        if hostname == server:
            return CONFIG.DS_SERVER_LIST[server]
    return None

#トークンがヘッダに格納されているか
def is_valid_access_token_key(environ):
	if not 'HTTP_ACCESSTOKEN' in environ:
		return False
	return CONFIG.ACCESS_TOKEN == environ.get('HTTP_ACCESSTOKEN')

# 制御ファイルの有無を確認する
# 引数：　"test"　または　"primary"
# 戻り値: True 存在する, False: 存在しない
def file_check(filename):
    check_file = '/var/lib/baogw/' + filename
    return os.path.exists(check_file)

# プライマリフラグの状態を返す
# Trueの場合、サーバーは本番サービス提供中
def get_primary():
    return file_check('primary')

# テストフラグの情報を返す
# Trueの場合、サーバーはメンテナンスモード(片寄せ)
def get_maintenance():
    return file_check('test')

# サーバーグループを取得(1号機または2号機)
def get_server_group():
    #プログラムがsystemdサービスとして実行されていない場合は環境変数が取れないため仮に"1"(1号機グループ）を返している
    try:
        group = os.environ["BAO_SERVER_GROUP"]
    except:
        group = "1"
    return group

# primary制御ファイルの有無を返す
def primary(wk_id, param):
    LOGGER.debug("primary")
    hostname = socket.gethostname() 
    if gethostbyname(hostname) is None:
        return False
    else:
        return file_check('primary')

# リクエストパスを分解する
# /{method}/{id}|空{?params}|空
def parse_request(path):
    exp = re.compile(r"/([^/?]+)(?:/([^?]+)|)(?:(\?.*)|)$")
    m = exp.match(path)
    method = m.group(1)
    wk_id = m.group(2)
    params = m.group(2)
    LOGGER.debug("method:" + method if not method is None else "method:")
    LOGGER.debug("id:"+ wk_id if not wk_id is None else "id:") 
    LOGGER.debug("params:"+ params if not params is None else "params:") 
    return (method, wk_id, params)

#サーバー情報
def server_info(wk_id=None, params=None):
    LOGGER.debug("server_info")
    hostname = socket.gethostname()
    ip_addr = gethostbyname(hostname)
    if not ip_addr is None:
        return {
                'name': hostname,
                'ip-addr': ip_addr,
                'primary': get_primary(),
                'maintenance': get_maintenance(),
                'group': get_server_group()
            }
    else:
        # 対象サーバーでない
        return None

#wsgi アプリケーション
def application(env, start_response):
    try:
        method, wk_id, params = parse_request(env["PATH_INFO"])     
        if method == 'server_info':
            start_response('200 OK', [('Content-type', 'application/json')])
            return [json.dumps(server_info(wk_id, params)).encode('utf-8')]
        elif method == 'primary':
            start_response('200 OK', [('Content-type', 'application/json')])
            return [json.dumps(primary(wk_id, params)).encode('utf-8')]
        else:
            start_response('404 NOT FOUND', [])
            return [b""]
    except RuntimeError as runtime_error:
        start_response('500 Internal Server Error', [('Content-type', 'text/plain')])
        msg = 'Internal Server Error\n%s' % runtime_error
        return [msg.encode('utf-8')]

from wsgiref import simple_server
if __name__ == '__main__':
    msg = "BAO_SERVER_GROUP=%s" % get_server_group()
    LOGGER.info(msg)
    LOGGER.info("Listening on port 5353....")
    server = simple_server.make_server('', 5353, application)
    server.serve_forever()

import json
import mysql.connector
import urllib.parse
import sys
import logging
import logging.handlers
import os
import discovery as DS
ds = DS.BaoDiscovery()

#設定項目>>>
class COM:
    LOCAL_DB_HOST = "" #自動設定            #メール連携API用のDBサーバーのアドレス
    MAIL_RECEIVER_DB = 'mail_receiver'      #'メール連携API用DBのスキーマ名'mail_receiver' ※変更不可
    MY_DB = 'baogw'                         #BAO-GW用DBのスキーマ名 'baogw' ※変更不可
    MY_USER = "gwuser"
    MY_PASSWD = "2017B@0gw"
#設定項目<<<

ACCESS_TOKEN = 'jRDmfDRrAyPPRAdSJxWd2VZc7FYt66AwUMT3NdXY6KSh9uhG'

HTTP_STATUS_OK = (200, 'OK')
HTTP_STATUS_BAD_REQUEST = (400, 'Bad Request')
HTTP_STATUS_SERVICE_UNAVAILABLE= (503, 'SERVICE_UNAVAILABLE') #メンテナンスモードのためリクエストは処理されない

SCRIPT_FILE = os.path.basename(__file__)

""" log出力設定 ※rsyslogd に渡す設定 """
LOGGER = logging.getLogger(SCRIPT_FILE)
LOGGER.setLevel(logging.DEBUG)

# 5,6,7 は既存システムで利用されていたので、API関連はlocal4を指定
#local4.*	/var/log/python_api/process.log
#local5.*	/var/log/tobaogw.log
#local6.*	/var/log/gwscripts/gwscruipts.log
HANDLER = logging.handlers.SysLogHandler(address=('localhost', 514), facility='local4') # 出力先の設定
FORMATTER = logging.Formatter('%(name)s[%(process)d]: %(levelname)s: [%(lineno)d] %(message)s')
HANDLER.formatter = FORMATTER
LOGGER.addHandler(HANDLER)

#開始
def application(environ, start_response):
    query = dict(urllib.parse.parse_qsl(environ.get('QUERY_STRING')))
    server_name = query.get('server_name', '')
    LOGGER.debug('Receive request. from server name: %s', server_name)
    if not is_valid_request(environ):
        status_code = status(HTTP_STATUS_BAD_REQUEST)
        LOGGER.error('Invalid request. return status code: %s', status_code)
        start_response(status_code, [('Content-type', 'application/json')])
        return [error_response(HTTP_STATUS_BAD_REQUEST, 'Invalid parameter.')]

    # DBサーバーの確認
    # 有効なDB接続がない場合、メンテナンスモードとして、処理をスキップする
    #Primaryサーバーを検索
    server = ds.get_first_server()
    if server is None:
        # Primary設定されたサーバーが不在
        status_code = status(HTTP_STATUS_SERVICE_UNAVAILABLE)
        LOGGER.info('メンテナンスモード 一時的にDB更新の処理を中止しています。')
        start_response(status_code, [('Content-type', 'application/json')])
        return [error_response(HTTP_STATUS_SERVICE_UNAVAILABLE, 'Maintenance Mode.')]
    else:
        COM.LOCAL_DB_HOST = server["ip-addr"]
    LOGGER.info("接続サーバー: %s" % server["name"])

    params = dict(urllib.parse.parse_qsl(environ.get('QUERY_STRING')))
    LOGGER.debug('Request complete.')
    start_response(status(HTTP_STATUS_OK), [('Content-type', 'application/json')])
    return [json.dumps(wk_filter(params['server_name'])).encode('utf-8')]

#statusコード
def status(http_status):
    return '%s %s' % http_status

#フィルター条件を取得
def wk_filter(server_name):
    info = {}
    conn = mysql.connector.connect(
        host=COM.LOCAL_DB_HOST,
        db=COM.MAIL_RECEIVER_DB,
        user=COM.MY_USER,
        password=COM.MY_PASSWD
    )
    cursor = conn.cursor(dictionary=True, buffered=True) # カーソル
    try:
        #メールアドレスを取得
        sql = 'select sender_mail_address from mail_references where is_invalid=%s'
        cursor.execute(sql, (0,))
        info["from"] = []
        for record in cursor.fetchall():
            info["from"].append(record['sender_mail_address'])
        info["from"] = list(set(info["from"]))

        #sinceを取得
        sql = 'select ensured_detection_time from request_log where server_name=%s order by access_time desc'
        cursor.execute(sql, (server_name, ))
        record = cursor.fetchone()
        info['since'] = 0
        if not record is None:
            info['since'] = record['ensured_detection_time']
    except mysql.connector.errors.IntegrityError as msg:
        LOGGER.error('mysql.connector.errors.IntegrityError %s', msg)
    finally:
        cursor.close()
        conn.close()
    return info

#パラメータおよびヘッダが正しいか
def is_valid_request(environ):
    return is_valid_access_token_key(environ) and is_valid_request_param(environ)

#リクエストパラメータが正しいか(server_nameパラメータが存在するか)
def is_valid_request_param(environ):
    params = dict(urllib.parse.parse_qsl(environ.get('QUERY_STRING')))
    return 'server_name' in params

#トークンがヘッダに格納されているか
def is_valid_access_token_key(environ):
	if not 'HTTP_ACCESSTOKEN' in environ:
		return False
	return ACCESS_TOKEN == environ.get('HTTP_ACCESSTOKEN')

#エラー
def error_response(http_status, message):
    return json.dumps({'error':{'code': http_status[0], 'message': message}}).encode('utf-8')

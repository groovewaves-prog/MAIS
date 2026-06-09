#!/usr/bin/python3
# -*- coding: utf-8 -*-

#insert_gw_events_remote の実装(仮）
# TCPサーバーとしてリクエストを受け、insert_gw_events.pyを呼び出す
#
# 通信方式：
# 　ソケットをオープンし、ストリームにinsert_gw_events.pyを呼び出すためのパラメータをまとめたjsonオブジェクトを書き込む
#   書き込み後、ソケットから読み出すことによって処理結果を取得できる。
#   処理結果は以下の形式
#    {"status":"okまたはngの文字列", "msg": "エラーメッセージ(あれば)"}
# 
import socketserver
import json
import os
import logging
import logging.handlers
import subprocess
import sys
import re
import gwcommon as COM
import traceback

HOST = '0.0.0.0'

#設定項目>>>
PORT = 9999
BUFFER_SIZE=2048
# 実行コマンド
INSERT_GW_EVENTS_CMD = "python3 /usr/lib/zabbix/alertscripts/insert_gw_events.py"
INSERT_SYS_EVENTS_CMD = "python3 /usr/lib/zabbix/alertscripts/insert_sys_events.py"
GW_DELIMITER = '@!!!@'
#設定項目<<<

#ログ出力
SCRIPT_FILE = os.path.basename(__file__)
LOGGER = logging.getLogger(SCRIPT_FILE)
LOGGER.setLevel(logging.DEBUG)

# 出力先の設定 local6.* /var/log/gwscripts/gwscripts.log
#local4.*	/var/log/python_api/process.log
#local5.*	/var/log/tobaogw.log
#local6.*	/var/log/gwscripts/gwscruipts.log
HANDLER = logging.handlers.SysLogHandler(address=('localhost', 514), facility='local6') 
FORMATTER = logging.Formatter('%(name)s[%(process)d]: %(levelname)s: [%(lineno)d] %(message)s')
HANDLER.formatter = FORMATTER
LOGGER.addHandler(HANDLER)

# 文字置換テーブル
# double-quotation, single-quotation, back-quotation
trans_table = str.maketrans( { "\"":"”", "'":"’","`":"`" } )
# テキストを捜査して、使用できない文字を置換する
# 戻り値: 置換されたテキスト
def sanitize_text(text):
  return text.translate(trans_table)

# 項目に含まれる改行文字を変換する
def baocrlf(argument):
    """
    改行コードをBAO-IF仕様に変更
    """
    argument = argument.replace('\r', '&#xD;')
    argument = argument.replace('\t', '&#x9;')
    argument = argument.replace('\n', '&#xA;')

    return argument

#insert_gw_eventsをプロセス起動する
def insert_gw_events(sendto, subject, values):
    # パラメータチェック
    expect_keys = {'detected_time', 'detected_host', 'customer_ci', 'customer_name',
        'hostname', 'alarm_time', 'ci_name', 'device', 'alarm_status', 'summary','host','hostip'}
    for expect_key in expect_keys:
        if values.get(expect_key) is  None:
            if expect_key != 'hostip':
                # 想定してるキー(値)がない場合
                msg = 'Parameter error. Invalid hash. Missing key: %s' % expect_key
                LOGGER.info(msg)
                raise ValueError(msg)
            else:
                values['hostip']=''# insert_gw_events.pyでは使わないので空文字列を設定
    msg = [
        "", values["alarm_time"], values["hostname"], values["ci_name"],
        values["summary"],values["alarm_status"],"", values["device"],
        "", values["detected_time"], values["hostip"] , values["customer_ci"],
        values["customer_name"],values["host"]
    ]
    message = GW_DELIMITER.join(msg)
    # 使用禁止文字の置換
    message = sanitize_text(message)
    # 改行文字の置換
    message = baocrlf(message)
    
    # 外部プロセス呼出し
    # alarm_statusによってinsert_gw_events.pyまたはinsert_sys_events.pyのどちらかを呼ぶ
    if values["alarm_status"] in  (COM.GW_ALARM_STATUS_ERROR, COM.GW_ALARM_STATUS_NORMAL, COM.GW_ALARM_STATUS_INFO):
        script=INSERT_GW_EVENTS_CMD
    elif values["alarm_status"] in (COM.GW_ALARM_STATUS_SEC, COM.GW_ALARM_STATUS_SYSERROR, COM.GW_ALARM_STATUS_SYSNORMAL):
        script=INSERT_SYS_EVENTS_CMD
    else:
        msg="alarm_status={}".format(values["alarm_status"])
        LOGGER.info(msg)
        raise ValueError(msg)
    
    # debug 引数表示
    basename = os.path.basename(script)
    LOGGER.debug("=== {} ===".format(basename))
    for key in values:
        LOGGER.debug("values[{0}] = {1}".format(key, values[key]))
    LOGGER.debug("=== (END) ===")
    
    # コマンド実行
    cmd = '{0} "{1}" "{2}" "{3}" '.format(script, sendto, subject, message) 
    ret = subprocess.call(cmd, shell=True)
    if not ret == 0:
        # プロセス起動に失敗
        msg = "Call {} subprocess.call() failed code = {}".format(basename, ret)
        LOGGER.error(msg)
        raise RuntimeError(msg)
    
    # プロセス起動成功
    LOGGER.info("Call {} SUCCEEDED.".format(basename))
    return True, "no error"

class Handler(socketserver.StreamRequestHandler):
    def handle(self):
        try:
            # リクエスト受信
            recvData = b""
            while True:
                data = self.request.recv(BUFFER_SIZE)
                recvData = recvData + data
                recv_size = len(data) 
                if recv_size == 0: #メッセージ終了(相手側でshutdown(SHUT_WR))
                    break
            # パラメータ(json取り出し)
            try:
                params = json.loads(recvData.decode())
            except Exception as e:
                # パラメータが正常に読めない
                raise ValueError("Failed json.load() {}".format(e))
            # パラメータチェック＆コマンド呼び出し
            LOGGER.debug(params)
            status, msg = insert_gw_events("sendto", "subject", params)
            result={"status":status, "msg":msg}
            #結果をjson文字列で返す{ "status": boolean , "message": str}
            self.request.send(json.dumps(result).encode())
            self.request.close() #通信終了
            
        except ValueError as e:
            # リクエストパラメータに問題がある
            LOGGER.info(e)
            # エラーを返してセッション終了
            result={"status":False, "msg":str(e)}
            self.request.send(json.dumps(result).encode())
            self.request.close() #通信終了
            
        except Exception as e:
            # その他エラー
            # エラーが発生してもサーバーは終了させないがシステム設定等で何らかの対応が必要
            LOGGER.error('Stop by error.')
            LOGGER.error(e)
            LOGGER.error(traceback.format_exc())
    
def main():
    server = socketserver.TCPServer((HOST, PORT), Handler)
    print( "insert_gw_events_remote service start")
    print( 'listening %s' ,server.socket.getsockname())
    LOGGER.info( "*** insert_gw_events_remote ***")
    LOGGER.info('listening %s' ,server.socket.getsockname())
    server.serve_forever()

if __name__ == '__main__':
    main()

  

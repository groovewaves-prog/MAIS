import json
import socket
import os
import urllib.request
import urllib.parse
from logging import getLogger, Formatter, FileHandler, DEBUG
from logging.handlers import SysLogHandler 
from datetime import datetime as datetime, timedelta as timedelta

#動作環境
#config = 'production'       #本番環境
#config = 'development'      #検証環境
config = 'test'             #ローカルテスト

#メンテナンスモード
maintenance = True  

#log_level = 20 # INFO
log_level = 10 # DEBUG

#設定項目　ここまで

# BAO-GW zabbixサーバーのIPアドレスリスト
if config == "production":
    DS_SERVER_LIST = {
        "fuit305baogw01":"10.136.48.227", 
        "fuit305baogw02":"10.136.48.228", 
    }
elif config == "development":
    DS_SERVER_LIST = {
        "v-dev-baogw1-m20502367":"10.136.113.60", 
        "v-dev-baogw2-m20502367":"10.136.113.61"
    }
else:
    DS_SERVER_LIST = {
    # "IP_192_168_101_101":"192.168.101.101", 
        "IP_192_168_101_102":"192.168.101.102", 
        "IP_192_168_101_103":"192.168.101.103", 
        "IP_192_168_101_104":"192.168.101.104", 
        "IP_192_168_101_105":"192.168.101.105", 
    }

# リクエスト時に必要な アクセストークン
ACCESS_TOKEN = 'jRDmfDRrAyPPRAdSJxWd2VZc7FYt66AwUMT3NdXY6KSh9uhG'
WEB_API_BASE_URL = 'http://%s:5353'
API = "/server_info"
log_level = 10 #debug

#ログ出力設定
def setup_logger(log_folder, modname=__name__, level=log_level):
    logger = getLogger(modname)
    logger.setLevel(DEBUG)
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

HTTP_STATUS_OK = (200, 'OK')

class BaoDiscovery:
    def __init__(self):
        #サーバー情報のリスト
        self.server_info = []
        #有朋期限　datetime.now()形式
        self.expire = datetime.now() - timedelta(seconds=1)
    #api共通処理
    def webapi(self, host, api, method, params=None):
        headers = {'AccessToken': ACCESS_TOKEN}
        url = '%s%s' % (str(WEB_API_BASE_URL % host), api)
        req = urllib.request.Request(url, method=method, headers=headers, data=params)
        try:
            res = urllib.request.urlopen(req)
            return HTTP_STATUS_OK[0], res.read().decode('utf-8')
        except urllib.request.HTTPError as e:
            msg = "http request error %s status:%s reason:%s" % (url, e.code, e.reason)
            raise RuntimeError(msg)
        except Exception as e:
            msg = "http request error %s %s" % (url, e)
            raise RuntimeError(msg)

    #DSサーバーにリクエストしてサーバー情報を取得
    def update_serverlist(self):
        self.expire = datetime.now() + timedelta(seconds=10)
        text = ""
        self.server_info = []
        for host in DS_SERVER_LIST:
            ip_addr = DS_SERVER_LIST[host]
            try:
                status, text = self.webapi(ip_addr, API, "GET")
                if status ==  HTTP_STATUS_OK[0]:
                    #返されたjson文字列を解析
                    x = json.loads(text)
                    x["status"] = "ok"
                else:
                    LOGGER.debug("HTTP error %d" % status )
                    text = '{"name": "%s", "ip-addr": "%s", "primary": false, "maintenance": false}' % (host, ip_addr)
                    x = json.loads(text)
                    x["status"] = "http error (%d)" % status          
                self.server_info.append(x)
            except RuntimeError as e:
                LOGGER.debug(str(e))
                text = '{"name": "%s", "ip-addr": "%s", "primary": false, "maintenance": false}' %(host, ip_addr)
                x = json.loads(text)  
                x["status"] = "request error (%s)" % str(e)
                self.server_info.append(x) 
                 
    #サーバー情報を検索する
    def get_server_info(self, name ):
        #有効期限切れ
        if self.expire < datetime.now():
            self.update_serverlist() #更新
        try:
            return self.server_info[name]
        except KeyError:
            raise RuntimeError("Server not found (%s)" % name)

    #サーバー情報の一覧を取得 
    def get_server_list(self):
        if self.expire < datetime.now():
            self.update_serverlist() #更新
        return self.server_info

    #第１優先サーバーを返す
    #primary == true かつ、status == ok
    def get_first_server(self):
        wk_list = self.get_server_list()
        for db in wk_list:
            if db["status"] == "ok" and db["primary"] is True:
                return db
        return None

    #第2優先サーバーを返す(読み取り専用でも構わない)
    # status == ok
    def get_second_server(self):
        wk_list = self.get_server_list()
        for db in wk_list:
            if db["status"] == "ok":
                return db
        return None

#if __name__ == '__main__':
#    print("*** test ***")
#
#    discovery = BaoDiscovery()
#    list = discovery.get_server_list()
#    print(json.dumps(list, sort_keys=True, indent=4))
#
#    print(discovery.expire)


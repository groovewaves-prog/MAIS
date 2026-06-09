
#動作環境
config = 'production'       #本番環境
#config = 'development'      #検証環境
#config = 'test'             #ローカルテスト

#メンテナンスモード
maintenance = True  

#log_level = 20 # INFO
log_level = 10 # DEBUG

#設定項目　ここまで

# アクセストークン
ACCESS_TOKEN = 'jRDmfDRrAyPPRAdSJxWd2VZc7FYt66AwUMT3NdXY6KSh9uhG'

# BAO-GW zabbixサーバーのIPアドレスリスト
#### 正確なホスト名を使うこと ###
if config == "production":
    DS_SERVER_LIST = {
        "v-slymsvmais1-M22507751":"10.136.160.160", 
        "v-slimsvmais2-M22507751":"10.136.163.160", 
    }
elif config == "development":
     DS_SERVER_LIST = {
        "v-slymsvdevmais1-M22507751":"10.136.161.160", 
        "v-slimsvdevmais2-M22507751":"10.136.164.160"
    }
else:
    DS_SERVER_LIST = {
        "localhost.localdomain":"192.168.56.106"
    }

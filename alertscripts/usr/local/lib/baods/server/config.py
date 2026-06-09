
#動作環境
#config = 'production'       #本番環境
config = 'development'      #検証環境
#config = 'test'             #ローカルテスト

#メンテナンスモード
maintenance = True  

log_level = 20 # INFO
#log_level = 10 # DEBUG

#設定項目　ここまで

# アクセストークン
ACCESS_TOKEN = 'jRDmfDRrAyPPRAdSJxWd2VZc7FYt66AwUMT3NdXY6KSh9uhG'

if config == "production":
    DS_SERVER_LIST = {
        "fuit305baogw01":"10.136.162.160", 
        "fuit305baogw02":"10.136.165.160", 
    }
elif config == "development":
     DS_SERVER_LIST = {
        "v-dev-baogw1-m20502367":"10.136.162.170", 
        "v-dev-baogw2-m20502367":"10.136.165.170"
    }
else:
    DS_SERVER_LIST = {
        "localhost.localdomain":"192.168.56.106"
    }

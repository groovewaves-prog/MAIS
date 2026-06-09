import traceback
import json
import mysql.connector
import socket
import subprocess
import sys
import logging
import datetime
import re
import logging
import logging.handlers
import os
from pytz import timezone
import discovery as DS
ds = DS.BaoDiscovery()
import unicodedata

#設定項目>>>
class DB_CONFIG:
    LOCAL_DB_HOST = "" #自動設定
    MAIL_RECEIVER_DB = 'mail_receiver'
    MASTER_EVENT_TABLE = 'gw_events'
    SLAVE_EVENT_TABLE = 'gw_rescue_events'
    MY_DB = 'baogw'
    MY_USER = "gwuser"
    MY_PASSWD = "2017B@0gw"
    REMOTE_HOST= ""             #連携先　BAO-GWサーバーのアドレス
    PORT =  9999                #連携先 insert_gw_events_remoteのポート番号

ACCESS_TOKEN = 'jRDmfDRrAyPPRAdSJxWd2VZc7FYt66AwUMT3NdXY6KSh9uhG'

HTTP_STATUS_OK = (200, 'OK')
HTTP_STATUS_BAD_REQUEST = (400, 'Bad Request')

HTTP_STATUS_INTERNAL_SERVER_ERROR = (500, 'Internal Server Error')
HTTP_STATUS_SERVICE_UNAVAILABLE= (503, 'SERVICE_UNAVAILABLE') #メンテナンスモードのためリクエストは処理されない
HTTP_STATUS_GATEWAY_TIMEOUT = (504, 'Gateway Timeout')

SCRIPT_FILE = os.path.basename(__file__)
PATOLAMP_SCRIPT_PATH = '/var/www/api/mail_receiver/existing_machine/sub_script/notify_patolamp.py'

""" log出力設定 ※rsyslogd に渡す設定 """
LOGGER = logging.getLogger(SCRIPT_FILE)
LOGGER.setLevel(logging.DEBUG)

# 出力先の設定 local4.* /var/log/gwscripts/gwscripts.log
#local4.*	/var/log/python_api/process.log
#local5.*	/var/log/tobaogw.log
#local6.*	/var/log/gwscripts/gwscruipts.log
HANDLER = logging.handlers.SysLogHandler(address=('localhost', 514), facility='local4') 
FORMATTER = logging.Formatter('%(name)s[%(process)d]: %(levelname)s: [%(lineno)d] %(message)s')
HANDLER.formatter = FORMATTER
LOGGER.addHandler(HANDLER)

def is_exist_primary_file():
    check_file = '/var/lib/baogw/primary'
    return os.path.exists(check_file)

class DB_FIELD_SIZE:
    MAIL_TITLE = 200
    MAIL_CONTENT = 1000

def insert_gw_events_remote(params):
    '''
    insert_gw_events_remoteサービスの呼び出し
    '''
    BUFSIZE = 2048
    result = {}
    LOGGER.debug("######## insert_gw_events_remote #############")
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((DB_CONFIG.REMOTE_HOST, DB_CONFIG.PORT))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        #dictionaryをjson化してバイナリエンコード、メッセージを送信
        s.send(json.dumps(params).encode())
        s.shutdown(socket.SHUT_WR) #送信終了
    except Exception as e:
        # 通信エラー
        LOGGER.error("insert_gw_events_remote:socket error %s" % e)
        return False
    else:
        #　送信は正常終了, レスポンスを処理する
        try:
            #サーバーから処理結果を取得する(json文字列)
            recvData = b""
            while True:
                # 受信メッセージの長さが0となるまでrecvを繰り返す
                data = s.recv(BUFSIZE)
                recvData = recvData + data
                recv_size = len(data)
                if recv_size == 0: # 受信終了(相手側でshutdown(SHUT_WR))
                    break
            result = json.loads(recvData)
        except Exception as e:
            # 通信エラー, jsonフォーマットのエラー
            LOGGER.error('insert_gw_events_remote: failed: %s' % str(e) )
            return False
        else:
            # 通信OK、返されたレスポンスの確認
            if  result["status"] is True:
                LOGGER.info('insert_gw_events_remote: succeeded')
                # insert_gw_events.pyの起動に成功
                return True
            else:
                # insert_gw_events.pyの起動に失敗
                LOGGER.error('insert_gw_events_remote: failes: %s' % result['msg'])
                return False

#開始
def application(environ, start_response):
    if not is_valid_request(environ):
        status_code = status(HTTP_STATUS_BAD_REQUEST)
        LOGGER.error('Invalid request. return status code: %s', status_code)
        start_response(status_code, [('Content-type', 'application/json')])
        return [error_response(HTTP_STATUS_BAD_REQUEST, 'Invalid parameter.')]

    content_length = int(environ.get('CONTENT_LENGTH', 0))
    wsgi_input = environ['wsgi.input'] 
    # wsgi_inputで読み取りサイズを指定しないと標準のwsgiサーバーはハングアップする,gunicornなら問題は発生しない
    params = json.loads(wsgi_input.read(content_length).decode('utf-8'))

    # パラメーターチェック
    param_server_name = params.get('server_name')
    param_until = params.get('until')
    param_mails_count = params.get('count')
    param_mails = params.get('mails')
    if param_server_name is None or param_until is None or param_mails_count is None or param_mails is None:
        #パラメータエラー
        status_code = status(HTTP_STATUS_BAD_REQUEST)
        LOGGER.error('Invalid parameter. return status code: %s', status_code)
        start_response(status_code, [('Content-type', 'application/json')])
        return [error_response(HTTP_STATUS_BAD_REQUEST, 'Invalid parameter.')]

    # DBサーバーの確認
    # 有効なDB接続がない場合、メンテナンスモードとして、処理をスキップする
    #Primaryサーバーを検索
    server = ds.get_first_server()
    if server is None:
        # Primary設定されたサーバーが不在
        status_code = status(HTTP_STATUS_BAD_REQUEST)
        LOGGER.info('メンテナンスモード 一時的にDB更新の処理を中止しています。')
        start_response(status_code, [('Content-type', 'application/json')])
        return [error_response(HTTP_STATUS_SERVICE_UNAVAILABLE, 'Maintenance Mode.')]
    else:
        DB_CONFIG.LOCAL_DB_HOST = server["ip-addr"]
        DB_CONFIG.REMOTE_HOST = server["ip-addr"]
    LOGGER.info("接続サーバー: %s" % server["name"])

    request_count = len(param_mails)    # APIにリクエストされたメール件数
    detection_count = 0                 # 条件にマッチしたメール件数
    notification_count = 0              # 新規にイベント登録された件数
    duplication_count = 0               # 重複チェックで排除されたメール件数 

    # マッチするイベントを検索する
    try:
        notification_events = search_notification_events(param_mails)
    except Exception as e:
        LOGGER.error("error in search_notification_events")
        LOGGER.info(traceback.format_exc())
        start_response(status(HTTP_STATUS_INTERNAL_SERVER_ERROR), [('Content-type', 'application/json')])
        result={
            'msg': 'search_notification_events FAILED. %s' % str(e),
            'status': HTTP_STATUS_INTERNAL_SERVER_ERROR[0],
            'request_count': request_count,
            'detection_count': 0,
            'notification_count': 0,
            'duplication_count': 0
        }  
        return [json.dumps(result).encode('utf-8')]
    else:
        # BAO-GWにイベントを登録する
        try:
            # メール抽出数(連携条件にマッチしたメール数)
            detection_count = len(notification_events)
            # イベント登録されたメール数、重複処理で排除されたメール数
            notification_count, duplication_count = write_to_db(notification_events)
        except Exception as e:
            LOGGER.error("error in write_to_db")
            LOGGER.info(traceback.format_exc())
            start_response(status(HTTP_STATUS_INTERNAL_SERVER_ERROR), [('Content-type', 'application/json')])
            result={
                'msg': 'error in write_to_db. %s' % str(e),
                'status"': HTTP_STATUS_INTERNAL_SERVER_ERROR[0],
                'request_count': request_count,
                'detection_count': detection_count,
                'notification_count': notification_count,
                'duplication_count': duplication_count
            }  
            return [json.dumps(result).encode('utf-8')]
        else:
            LOGGER.info("イベント連携成功　notification_count=%d duplication_count=%d" % (notification_count, duplication_count) )
            # BAO-GWへイベントの登録が成功した、request_logに記録する
            # request_logに記録することによって、メールサーバーごとの処理済みメール（の時刻）を管理する
            # この情報はメール連携スクリプトが新規のメールを抽出する際のフィルタ条件の一部になる
            # 補足：この情報が記録されていない場合、メール連携スクリプトは受信トレイに残っているメールを何度も処理するが、
            #  メール自体の処理済みチェック(notification_mailsテーブル)を行っているため、同じメールに対して重複してイベントを
            #  登録することはない。
            request_log = {
                'server_name': param_server_name,
                'ensured_detection_time' : param_until, #確認済み時刻（この時刻の受信メールまで処理済み）
                'detection_count' : detection_count, #条件にマッチし処理したメール件数
                'notification_count' : notification_count, #上記のうち重複を排除し、GAO-GWのイベントに追加された件数
                "duplication_count": duplication_count
            }
            # リクエストログを記録
            try:
                insert_request_log(request_log)
            except Exception as e:
                LOGGER.error('error in insert_request_log')
                LOGGER.info(traceback.format_exc())
                start_response(status(HTTP_STATUS_INTERNAL_SERVER_ERROR), [('Content-type', 'application/json')])
                result={
                    'msg': 'error in insert_request_log. %s' % str(e),
                    'status': HTTP_STATUS_INTERNAL_SERVER_ERROR[0],
                    'request_count': request_count,
                    'detection_count' : detection_count,
                    'notification_count' : notification_count,
                    "duplication_count": duplication_count
                }  
                return [json.dumps(result).encode('utf-8')]
            else:
                LOGGER.debug("リクエストログ記録　notification_count=%d duplication_count=%d" % (notification_count, duplication_count) )
                start_response(status(HTTP_STATUS_OK), [('Content-type', 'application/json')])
                result={
                    'msg': 'Request SUCCEEDED. detection count: %s, notification count: %s' % (detection_count, notification_count),
                    'status': HTTP_STATUS_OK[0],
                    'request_count': request_count,
                    'detection_count': detection_count,
                    'notification_count': notification_count,
                    'duplication_count': duplication_count
                }  
                return [json.dumps(result).encode('utf-8')]

def tokyo_timezone():
    """
    日本時間を設定したタイムゾーンを返す

    Parameters
    ----------

    Returns
    ----------
    timezone: timezone
        日本時間を設定したタイムゾーン

    Raises
    ----------
        なし
    """
    return datetime.timezone(datetime.timedelta(hours=9))

def write_to_db(notification_events):
    """
    連携すべき情報をDBへ書き込んでいく
    基本的にマスターへ優先して書き込んでいくが、
    マスターに書き込み失敗した場合は、スレイブへの書き込みを試みる
    ただし、既に書き込み済みと同じメールの場合は、重複として連携しない

    Parameters
    ----------
    notification_events
        メール情報から、DBへ連携する形式へ整形した情報
        連携すべき情報がない場合は、空配列が返る
        情報の構造は次のようになる
        'gw_event': gw_eventテーブルへ書き込む情報
        'notification_mail': notification_mailsテーブルへ書き込む情報


    Returns
    ----------
    detection_count: int
        DBに書き込み完了した数

    Raises
        なし
    ----------

    """
    notification_count = 0
    duplication_count = 0
    for notification_event in notification_events:
        gw_event = notification_event['gw_event']                   # イベント生成用データ
        notification_mail = notification_event['notification_mail'] # イベント生成のもとになったメールの情報
        if is_duplicated_notification_mails(notification_mail):
            # 重複メール除去処理
            # 検討の結果、このタイミングで実施するのが漏れなく、
            # 理解しやすいため、このタイミングで実施している
            # LOGGER.debug("重複メール除去 %s " % notification_mails)
            duplication_count += 1 #抽出カウントアップ
            continue
        # insert_gw_eventコマンドでBAO-GWに連携する
        if insert_gw_events_remote(gw_event) is True:
            #成功すれば、連携済みのメールとして記録する
            insert_notification_mails(notification_mail)
            notification_count += 1 #抽出カウントアップ
        else:
            # 失敗したら処理中断
            break
    return notification_count, duplication_count #イベント連携数、重複数


def sanitize_text(text):
    """
    テキストをUnicode正規化し、utf8mb4文字（絵文字など）を"[EMOJI]"に置き換え、
    制御文字(<0x20, 0x0A, 0x0Dを除く）を削除する。
    """
    # Unicode正規化（NFC）
    text = unicodedata.normalize('NFC', text)
    # UTF8MB4文字（絵文字など）を"[EMOJI]"に置き換える
    pattern_utf8mb4 = '[\U00010000-\U0010FFFF]'
    text = re.sub(pattern_utf8mb4, '[EMOJI]', text)
    # 制御文字を削除する
    pattern_control_chars = '[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]'
    text = re.sub(pattern_control_chars, '', text)
    return text


def search_notification_events(mails):
    """
    DBヘ書き込むべきイベントを探査して、DBに変換しやすい状態にまとめて返す

    Parameters
    ----------
    mails: array
       下記に記すパラメータを持つハッシュを持つ1個以上の配列
       'title': メール件名
       'content': メール本文
       'from': メールの差出人
       'sendDate': メールの送信時刻
       'receiveDate': メールの受信時刻
       'header': メールのヘッダ

    Returns
    ----------
    notification_events
        メール情報から、DBへ連携する形式へ整形した情報
        連携すべき情報がない場合は、空配列が返る
        情報の構造は次のようになる
        'gw_event': gw_eventテーブルへ書き込む情報
        'notification_mails': notification_mailsテーブルへ書き込む情報

    Raises
    ----------
        なし
    """
    notification_events = []
    ip = socket.gethostbyname(socket.gethostname()).split('.')
    # 検出したサーバーのIDとして、スクリプトが動作しているサーバー(APIサーバー)のIPアドレス第４オクテッドを設定
    detected_host = ip[3]
    tokyo_time_zone = tokyo_timezone()
    for mail in mails:
        # メールが連携対象かどうかを確認する
        is_notify, db_values, content = extract_mail(mail)
        if is_notify:
            # 連携対象である

            # テキストにふくまれる制御コードを削除する
            mail['title'] = sanitize_text(mail['title'])
            # イベントの生成に使うメール本文はextract_mail()が選択したパートを使う
            maiL_content = sanitize_text(content)

            matched_id = db_values['id']
            customer_ci = db_values['customer_ci']
            customer_name = db_values['customer_name']
            mail_reference_type = db_values['type']
            ci_name = db_values['ci_name']

            #alert_timeはUTCで、ミリ秒の単位まで格納する
            alert_time = datetime.datetime.fromtimestamp(mail['receiveDate'], tokyo_time_zone)
            alert_time.astimezone(timezone('UTC')) 

            #イベント連携用データ(最終的にはinsert_gw_eventsに渡す)を作成する
            gw_event = {
                'detected_time': datetime.datetime.fromtimestamp(mail['receiveDate'], tokyo_time_zone).strftime("%Y.%m.%d %H:%M:%S"),
                'detected_host': detected_host,
                'customer_ci': customer_ci,
                'customer_name': customer_name,
                'hostname': mail['from'],
                'alarm_time': alert_time.strftime("%Y-%m-%d@%H:%M:%S.%f")[0:23], #マイクロ秒単位で表示した文字列から後ろの3文字を削除してミリ秒になおす
                'ci_name': ci_name,
                'device': 'mail_receiver_%s_%s' % (detected_host, matched_id),
                'alarm_status': mail_reference_type,
                'summary': mail['title'] + '\n\r' + maiL_content,
                'host': customer_ci #Zabbixのホス名(Zabbixのホストと紐づけに使う）
            }
            #イベントのもとになったメールの情報
            # (notification_mailsテーブルに保存し重複チェックに使う）
            notification_mail = {
                'sender_mail_address': mail['from'],
                'mail_title': mail['title'],
                'mail_content': maiL_content, #extract_mail()が選択したパート
                'mail_receive_time': datetime.datetime.fromtimestamp(mail['receiveDate'], tokyo_time_zone).strftime("%Y-%m-%d %H:%M:%S.%f"),
                'mail_send_time': datetime.datetime.fromtimestamp(mail['sendDate'], tokyo_time_zone).strftime("%Y-%m-%d %H:%M:%S.%f")
            }
            notification_events.append({'gw_event': gw_event,
                                        'notification_mail': notification_mail})
    return notification_events

# 1件のメールについて、登録されている連携条件と比較し、マッチする条件を検索する
# マッチすれば、イベント連携用のデータと、マッチしたメール本文を返す
def extract_mail(mail):
    """
    メールの差出人に合致する解析条件を抜き出し、BAOGWへ連携するメールを特定する

    Parameters
    ----------
    mail : hash　-- 1件のメールを表す
       下記に記すパラメータを持つハッシュの配列
       'title': メール件名
       'content': メール本文（メールに含まれるパートの配列）
       'from': メールの差出人
       'sendDate': メールの送信時刻
       'receiveDate': メールの受信時刻
       'header': メールのヘッダ

    Returns
    ----------
    (is_notify, db_values, part): tuple
        各要素の詳細は下記の
    is_notify: bool
        解析条件に合致したかどうか、True: 合致したのでイベントを生成する
    db_values: hash or None
        解析に合致しなかった場合、Noneを返す
        ハッシュに含まれるキーは次の通りである
        id: 条件に合致したID
        customer_ci: 顧客略称
        customer_name: 顧客名称
        type: 障害、復旧などを表す
    part: str or None
        解析条件によって選択された、メールのパート

    Raises
    ----------
        なし
    """
    db_mail_receiver = mysql.connector.connect(
        host=DB_CONFIG.LOCAL_DB_HOST,
        db=DB_CONFIG.MAIL_RECEIVER_DB,
        user=DB_CONFIG.MY_USER,
        password=DB_CONFIG.MY_PASSWD
    )

    # メール送信元をキーとして、DBからメール連携条件のリストを取得
    cursor = db_mail_receiver.cursor(dictionary=True, buffered=True) # カーソル
    sql = 'select id, customer_ci, customer_name, type, analysis_conditions, ci_name from mail_references where is_invalid=%s and sender_mail_address=%s \
    order by id desc'
    cursor.execute(sql, (0, mail['from']))
    analysis_records = cursor.fetchall()
    cursor.close()
    db_mail_receiver.close()

    # 対象のメールについて、マッチする連携条件を検索
    LOGGER.debug("*** 対象のメールについて、マッチする連携条件を検索 ***")
    LOGGER.debug("  対象メール(Title):%s" % mail['title'] )
    for content in mail['content']:
        LOGGER.debug("  対象メール(Content):%s... " % (content[:50]).strip() )
    LOGGER.debug("  -")

    # 20220705 最長一致検索の対応
    match_rule = None #最終的に選択されたルール
    # forループで、メール送信元に対応する連携条件をすべて比較
    for record in analysis_records:
        try:
            # TODO: \のみエスケープする(仮実装)
            condition_string = record['analysis_conditions'].replace('\\', '\\\\')
            analysis_conditions = json.loads(condition_string)
        except:
            LOGGER.error("  Invalid condition. id: %d, condition: %s" % (record['id'], condition_string))
        LOGGER.debug("  連携条件テスト analysys_conditions : d=%d %s" % (record['id'], analysis_conditions))
        
        # 連携条件がメールとマッチするかどうか確認する
        (match_title, match_content, part) = is_all_match(analysis_conditions, mail)
        LOGGER.debug("  連携条件テスト result : title:%s content:%s " % (match_title, match_content))
        if match_title and match_content:
            LOGGER.debug("  *** Condition matched. id: %d" % record['id'])
            db_value = {
                'id': record['id'],
                'customer_ci': record['customer_ci'],
                'customer_name': record['customer_name'],
                'type': record['type'],
                'ci_name': record['ci_name'],
                'content': part,
                'rule': analysis_conditions
            }
            LOGGER.info("イベント連携条件あり 連携条件ID=%d 送信元=%s タイトル=%s 受信日時=%s" % (record['id'], mail['from'], mail['title'],datetime.datetime.fromtimestamp(mail['receiveDate'])) )
            
            # マッチした場合、より長い条件なら置き換え
            # key1:今回のループでマッチした条件
            if match_rule is not None:
                key1 = "".join(match_rule["rule"]["title"]["keyword"] + match_rule["rule"]["content"]["keyword"]) 
            else:
                key1 =""
            # key2:すでに記憶されているマッチした条件
            key2 = "".join(db_value["rule"]["title"]["keyword"] + db_value["rule"]["content"]["keyword"]) 
            if len(key2) > len(key1):
                # 今回マッチした条件のほうが長ければ置き換え
                match_rule = db_value
   
    if match_rule is not None:
        # 最長のキーワードを選択
        return True, match_rule, match_rule["content"] #True:イベントを生成する
    else:
        # メール連携対象の送信元のメールを処理したが、登録されているいずれの条件にマッチしなかった（条件設定に誤りがある可能性がある）
        LOGGER.info("マッチする連携条件なし 送信元=%s タイトル=%s 受信日時=%s" % (mail['from'], mail['title'],datetime.datetime.fromtimestamp(mail['receiveDate'])) )
        return False, None, None #True:イベントを生成しない

def escapce_symbol_in_pattern(wk_str):
# perfect_match, forward_match, backword_matchが使われなくなることによりこの関数も不要になる
    """
    正規表現のパターンを作る際に、制御記号をエスケープする

    Parameters
    ----------
    wk_str: 変更を加える文字列

    Returns
    ----------
    wk_str: 制御記号をエスケープ済みの文字列

    Raises
    ----------
        なし
    """
    wk_str = wk_str.replace('*', r'\*')
    wk_str = wk_str.replace('.', r'\.')
    wk_str = wk_str.replace('[', r'\[')
    wk_str = wk_str.replace(']', r'\]')
    wk_str = wk_str.replace('{', r'\{')
    wk_str = wk_str.replace('}', r'\}')
    wk_str = wk_str.replace('?', r'\?')
    wk_str = wk_str.replace('!', r'\!')
    wk_str = wk_str.replace('^', r'\^')
    wk_str = wk_str.replace('$', r'\$')
    wk_str = wk_str.replace('~', r'\~')
    wk_str = wk_str.replace('|', r'\|')
    return wk_str

def is_hit_keyword(target, keywords, search_type):
    """
    ターゲットに、キーワードが指定した形式で含まれているか、チェックする

    Parameters
    ----------
    target: string
        探査対象の文字列
    keywords: stringの配列
        検索文字列
    search_type: string
        keywordが、targetに、どのように存在しているか指定する。
        search_typeは、下記のいずれかである
        contain: targetにkeywordが含まれている
        not_contain: targetにkeywordが含まれていない
        perfect_match: targetとkeywordが完全に一致する
        forward_match: targetの始まりが、keywordである
        backward_match: targetは、keywordで終わる

    Returns
    ----------
    is_hit: bool or None
        True: タイプに応じた形式でキーワードとターゲットを比較した結果、条件に合致したと言える場合
        False: 上記で、条件に合致しなかった場合
        None: 下記の不正条件を満たす場合
            - target, search_type, keywordのいずれかがNoneの場合
            - search_typeが期待される文字列が含まれている場合

    Raises
    ----------
        なし
    """
    if target is None or search_type is None or keywords is None:
        LOGGER.error("parameter error")
        return None # パラメータエラー的状況
    # 2020-07-20 tyamane
    # 分析用キーワードが配列で指定されるようになったことによる対応
    # keyword キーワード文字列 
    # keywords キーワード文字列の配列
    keyword = ""
    if isinstance(keywords, str):
        #2020-07-20 tyamane
        #キーワードが文字列で指定された場合には、1個の文字列を含む配列とみなして処理する
        keyword = keywords
        keywords = [ keywords ]
    elif isinstance(keywords, list):
        #2020-07-20 tyamane
        #perfect_match, forward_match, backword_match用に単一の文字列を用意しておく
        if len(keywords) > 0 :
            keyword = keywords[0]

    # containとnot_containは配列のキーワードをAND結合で評価する（すべて満たすかどうか）
    if search_type == 'contain':
        for keyword in keywords:
            if keyword not in target :
                 return False #キーワードが含まれない（条件不成立で終了）
        return True #targetはすべてのキーワードを含んでいる（条件成立で終了）
    elif search_type == 'not_contain':
        for keyword in keywords:
            if keyword in target:
                return False #キーワードが含まれていた（条件不成立で終了）
        return True #targetはすべてのキーワードが含まれない（条件成立で終了）
    else:
        return None #Noneでいいの？

# titleとcontentのすべてが合致したか判定する
def is_all_match(condition, mail):
    """
    メールに全ての条件が合致するかを判定する

    Parameters
    ----------
    condition: hash
        メールの抽出に使う条件、構造は次の通り
        { 'subject': { 'key_word': ['hoge',...], 'search_type': 'contain' }
          'content': { 'key_word': ['fuga',...], 'search_type': 'contain' }
        ※: search_typeの詳細は、本メソッドで使わないので省略する
    mail: hash
       下記に記すパラメータを持つハッシュ
       'title': メール件名
       'content': メール本文
       'from': メールの差出人
       'sendDate': メールの送信時刻
       'receiveDate': メールの受信時刻
       'header': メールのヘッダ

    ※2020-07-20 tyamane 
    ※検索キーワードは配列形式で文字列を3個まで渡せるようにする。
    ※キーワードの評価はAND結合によって評価される（すべてのキーワードの一致を以ってヒットとする）   
    ※メール件名と本文、両方の条件が成立した場合に成立とする
    Returns
    ----------
    is_hit: bool
        True: 条件全てに合致した場合
        False: 条件いずれかに該当しなかった場合

    Raises
    ----------
        なし
    """
    # 有効な条件がない場合は不一致
    if not (isinstance(condition, dict) and ("title" in condition or "content"  in condition)) :
        return (False, False, None)

    title_key = 'title'
    content_key = 'content'

    # タイトルの検索
    match_title = False
    if title_key in condition:
        condition_title = condition[title_key] # タイトルの検索条件式
        keywords = condition_title.get('keyword') #タイトルの検索キーワード(配列)
        if len(keywords) > 0 :
            search_type = condition_title.get('search_type') # タイトルの比較条件 (contain/not_contain)
            match_title = is_hit_keyword(mail['title'], keywords, search_type) is True
        else:
            # キーワードが指定されていない場合「マッチしたとみなす」
            match_title = True
    else:
        # 条件式が設定されていない場合「マッチしたとみなす」
        match_title = True

    # 本文の検索
    # 本文にキーワードが含まれるかどうかを判定するとともに、キーワードが含まれるパートを選択する
    content = None
    if content_key in condition:
        # 本文の検索条件が存在する場合
        condition_content = condition[content_key] # 本文の検索条件式
        keywords = condition_content.get('keyword') # 本文の検索キーワード(配列)
        if len(keywords) > 0: #キーワードが指定されているか
            search_type = condition_content.get('search_type') # 本文の比較条件 (contain/not_contain)
            match_content = False  
            for part in mail['content']: # 検索する本文には複数のパートがあるので、パートごとに比較
                if is_hit_keyword(part, keywords, search_type) is True:
                    match_content = True
                    content = part
                    break
                else:
                    match_content = False
                    content = None
        else:
            # キーワードが指定されていない場合「マッチしたとみなす」
            # 本文のパートは未選択なので、メールに含まれるパートすべてをマッチしたパートとみなす
            match_content = True
            content = "\n".join(mail['content'])
    else:
        # キーワードが0個の場合「マッチしたとみなす」
        match_content = True
        # 本文のパートは未選択なので、メールに含まれるパートすべてをマッチしたパートとみなす
        content = "\n".join(mail['content'])
    return (match_title, match_content, content)

# 連携対象メールが既に連携済みかどうかを判定する
# メールの重複は　送信者, タイトル, 本文、送信時刻で　notification_mailsテーブルを検索してレコードが存在すれば送信済みとする
def is_duplicated_notification_mails(notification_mail):
    db_mail_receiver = mysql.connector.connect(
        host=DB_CONFIG.LOCAL_DB_HOST,
        db=DB_CONFIG.MAIL_RECEIVER_DB,
        user = DB_CONFIG.MY_USER,
        password=DB_CONFIG.MY_PASSWD
    )
    cursor = db_mail_receiver.cursor(dictionary=True, buffered=True) # カーソル
    sql = "SELECT count(*) as cnt, max(mail_send_time) as `send_time`  from notification_mails where\
    sender_mail_address=%s and mail_title=%s and mail_content=%s and mail_send_time=%s"
    result = False
    try:
        sender_mail_address = notification_mail['sender_mail_address']
        mail_title  = notification_mail['mail_title'][:DB_FIELD_SIZE.MAIL_TITLE]
        mail_content = notification_mail['mail_content'][:DB_FIELD_SIZE.MAIL_CONTENT]
        mail_send_time = notification_mail['mail_send_time']
        cursor.execute(sql, (sender_mail_address, mail_title, mail_content, mail_send_time))
        record = cursor.fetchone()
        if not record is None:
            if record['cnt'] > 0:
                LOGGER.debug(record)
                LOGGER.debug("重複メール：send_time=%s email-address=%s, mail_title=%s,_content=%s, mail_send_time=%s" \
                    % (record['send_time'], sender_mail_address, mail_title, (mail_content[:20]).strip(), mail_send_time))
                result = True
    except mysql.connector.errors.IntegrityError as msg:
        #エラー時は重複していることとする
        LOGGER.error("重複メール(DB-ERROR)：email-address=%s, mail_title=%s, mail_content=%s, mail_send_time=%s" \
            % (sender_mail_address, mail_title, (mail_content[:20]).strip(), mail_send_time))
        result = True
        LOGGER.info('msg=%s', msg)
    cursor.close()
    db_mail_receiver.close()
    return result

# イベントとしてBAO-GWに連携したメールの情報を記録する
def insert_notification_mails(mail_information_hash):
    db_mail_receiver = mysql.connector.connect(
        host=DB_CONFIG.LOCAL_DB_HOST,
        db=DB_CONFIG.MAIL_RECEIVER_DB,
        user=DB_CONFIG.MY_USER,
        password=DB_CONFIG.MY_PASSWD
    )
    cursor = db_mail_receiver.cursor(buffered=True) # カーソル
    sql = 'INSERT INTO notification_mails (sender_mail_address, mail_title,\
    mail_content, mail_receive_time, mail_send_time, notification_time\
    ) VALUES (%s, %s, %s, %s, %s, now())'

    expect_keys = ['sender_mail_address', 'mail_title', 'mail_content', 'mail_receive_time', 'mail_send_time']
    insert_value = []
    for expect_key in expect_keys:
        if mail_information_hash.get(expect_key) is not None:
            insert_value.append(mail_information_hash[expect_key])
        else:
            LOGGER.error('Invalid hash. Missing key: %s' % expect_key)
    try:
        cursor.execute(sql, tuple(insert_value))
        # コミット
        db_mail_receiver.commit()
    except mysql.connector.errors.IntegrityError as msg:
        LOGGER.error('DB INSERT FAILED. host: %s, db: %s, table: %s' % (DB_CONFIG.LOCAL_DB_HOST, DB_CONFIG.MAIL_RECEIVER_DB, 'notification_mails'))
        LOGGER.info('msg=%s', msg)
    else:
        LOGGER.debug('DB INSERT SUCCSESS. host: %s, db: %s, table: %s'% (DB_CONFIG.LOCAL_DB_HOST, DB_CONFIG.MAIL_RECEIVER_DB, 'notification_mails'))
    # 終了処理
    cursor.close()
    db_mail_receiver.close()
#
# メールサーバー(起動パラメータで指定)ごとにどこまでメールを処理したかを検出時刻(BAO-GWに通知した時刻)ベースで記録する。
# （ensured_detection_time）
# この時刻は　get_filter_info()　API　で sinceの値として通知され、
# メール連携スクリプト(メールサーバーで動作するもの)は処理済みのメールを識別する
def insert_request_log(request_log):
    db_mail_receiver = mysql.connector.connect(
        host=DB_CONFIG.LOCAL_DB_HOST,
        db=DB_CONFIG.MAIL_RECEIVER_DB,
        user=DB_CONFIG.MY_USER,
        password=DB_CONFIG.MY_PASSWD
    )
    cursor = db_mail_receiver.cursor(buffered=True) # カーソル
    sql = 'INSERT INTO request_log (server_name, access_time,\
    ensured_detection_time, detection_count, notification_count\
    ) VALUES (%s, now(), %s, %s, %s)'
    try:
        cursor.execute(sql, \
            (request_log['server_name'], request_log['ensured_detection_time'], request_log['detection_count'], request_log['notification_count']))
        # コミット
        db_mail_receiver.commit()
    except mysql.connector.errors.IntegrityError as msg:
        LOGGER.error('insert_request_log FAILED server_name=%s' % request_log['server_name'])
        LOGGER.info('msg=%s', msg)
    except Exception as e:
        LOGGER.error("insert_request_log ERROR  %s" % str(e))
    else:
        LOGGER.debug('insert_request_log SUCCEEDED server_name=%s ensured_detection_time=%s detection_count=%s notification_count=%s' \
          % (request_log['server_name'], request_log['ensured_detection_time'], request_log['detection_count'], request_log['notification_count']))
    # 終了処理
    cursor.close()
    db_mail_receiver.close()

#statusコード
def status(http_status):
    return '%s %s' % http_status

#パラメータおよびヘッダが正しいか
def is_valid_request(environ):
    return is_valid_access_token_key(environ) and is_valid_json_param(environ)

#JSON形式パラメータが指定されているか
def is_valid_json_param(environ):
    return 'wsgi.input' in environ

#トークンがヘッダに格納されているか
def is_valid_access_token_key(environ):
	if not 'HTTP_ACCESSTOKEN' in environ:
		return False
	return ACCESS_TOKEN == environ.get('HTTP_ACCESSTOKEN')

#エラー
def error_response(http_status, message):
    return json.dumps({'error':{'code': http_status[0], 'message': message}}).encode('utf-8')

def call_patolamp_on(customer_name, hostname, customer_ci, alarm_status):
    customer_name = customer_name.encode('unicode-escape')
    hostname = hostname.encode('unicode-escape')
    customer_ci = customer_ci.encode('unicode-escape')
    alarm_status = alarm_status.encode('unicode-escape')
    subprocess.call(['python3', PATOLAMP_SCRIPT_PATH, customer_name, hostname, customer_ci, alarm_status])


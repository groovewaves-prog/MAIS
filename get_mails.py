#!/usr/bin/python3

import email
import imaplib
import json
import logging
import logging.handlers
import os
import re
import sys
import time
import traceback
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from datetime import datetime

import chardet
from email.utils import parsedate_to_datetime # 追加：新しい日付パース方式で使用
from email.utils import parseaddr  # ← 追加

import get_mails_conf as CONFIG

WEB_API_BASE_URL = 'http://%s/mail_receiver_api/'

HTTP_STATUS_OK = (200, 'OK')

SCRIPT_FILE = os.path.basename(__file__)

""" log出力設定 ※rsyslogd に渡す設定 """
LOGGER = logging.getLogger(SCRIPT_FILE)
LOGGER.setLevel(CONFIG.LOG_LEVEL)

# 5,6,7 は既存システムで利用されていたので、API関連はlocal4を指定
#local4.*  /var/log/python_api/process.log
HANDLER = logging.handlers.SysLogHandler(address=('localhost', 514), facility='local4') # 出力先の設定
FORMATTER = logging.Formatter('%(name)s[%(process)d]: %(levelname)s: [%(lineno)d]%(message)s')
HANDLER.formatter = FORMATTER
LOGGER.addHandler(HANDLER)
HANDLER = logging.StreamHandler()
HANDLER.formatter = FORMATTER
LOGGER.addHandler(HANDLER)

# メールヘッダが見つからなかったことを示す例外クラス
class HeaderNotFoundError(Exception):
    def __init__(self, header_name) -> None:
        self.header_name_ = header_name

    def header_name(self) -> str:
        return self.header_name_

# 文字コードの自動判定に失敗したことを示す例外クラス
class ChardetFailedError(Exception):
    def __init__(self, data) -> None:
        self.data_ = data
    
    def data(self) -> bytes:
        return self.data_

# 【追加】日付パース失敗時の独自例外
class UnixtimeParseError(Exception):
    """
    日付文字列をunixtimeへ変換する際のパース失敗を通知するための独自例外クラス

    Attributes
    ----------
    date_str : str
        変換に失敗した日付文字列
    header_type : str
        ヘッダ種別（'Received', 'Date' など）
    mail_info : dict
        オプション。該当メールの情報（必要に応じて）
    message : str
        エラーメッセージ
    """
    def __init__(self, date_str, header_type, mail_info=None, message=None):
        self.date_str = date_str        # 変換に失敗した日付文字列
        self.header_type = header_type  # 'Received' or 'Date'
        self.mail_info = mail_info if mail_info is not None else {}
        self.message = message if message is not None else f"Failed to parse {header_type}: {date_str}"
        super().__init__(self.message)

# 独自例外クラス
class HeaderDecodeError(Exception):
    """
    ヘッダデコード失敗時の独自例外クラス

    Attributes
    ----------
    header_name : str
        ヘッダ名（例: 'Subject', 'From'等）
    raw_value : 任意
        デコードしようとした生値
    message : str
        エラーメッセージ
    """
    def __init__(self, header_name, raw_value, message=None):
        self.header_name = header_name
        self.raw_value = raw_value
        self.message = message if message is not None else f"Failed to decode header '{header_name}': {raw_value}"
        super().__init__(self.message)


# ★追加：大文字小文字非依存でヘッダを取得する関数
def get_header_ignorecase(msg, name):
    """
    msg: email.message.Message
    name: str 取得したいヘッダ名
    戻り値: ヘッダ値（最初に見つかったもの、なければNone）
    """
    name_lower = name.lower()
    for k, v in msg.items():
        if k.lower() == name_lower:
            return v
    return None

# メイン
# api_host: APIサーバー名またはIPアドレス
# server_name: メールサーバー名
# interval: ポーリング間隔
def main( api_host, server_name, interval ):
    while True:
        try:
            LOGGER.info('受信メール検索処理 -start-' )
            result = get_mails(api_host, server_name)
            if result == True:
                LOGGER.info("受信メール検索処理 SUCCEEDED %s %s" % (api_host, server_name))
            else:
                LOGGER.info("受信メール検索処理 FAILED %s %s" % (api_host, server_name))
            LOGGER.info('受信メール検索処理 -end-' )
        except:
            LOGGER.error('受信メール検索処理 ハンドリングされていないエラーによる中断' )
            LOGGER.info(traceback.format_exc())
        LOGGER.info('受信メール検索処理 待機します: %d 秒後再開' % interval)
        time.sleep(interval)

# メール取得処理 
# 戻り値:  True: 成功、False:失敗(エラー)
def get_mails(api_host, server_name):
    statuscode, filter = get_filter_info(api_host, server_name)
    if statuscode != HTTP_STATUS_OK[0]:
        LOGGER.error( "get_mails( %s, %s ) FAILED get_filter_info() error %s %s" % (api_host, server_name, statuscode, filter))
        return False #API エラーによる中止
    mail_info = extract_mail_info(filter, server_name)
    params = json.dumps(mail_info).encode('utf-8')
    # 新着メールがある場合にのみ処理する
    if mail_info.get('count') > 0:
        statuscode, result = post_mail_info(api_host, params)
        if statuscode != HTTP_STATUS_OK[0]:
            LOGGER.error( "get_mails( %s, %s ) FAILED post_mail_info() error %s %s" % (api_host, server_name, statuscode, str(result)))
            return False #API エラーによる中止
        # 成功
        LOGGER.info(" get_mails( %s, %s ) SUCCEEDED result=%s" % (api_host, server_name, str(result)))
    else:
        LOGGER.info(" get_mails( %s, %s ) SUCCEEDED 新着メールなし" % (api_host, server_name))
    return True #成功

# API呼出し
# フィルタする条件（メールアドレス および メール取得保証時間）を取得する
# API：(GET) mail_receiver_api/get_filter_info?server_name=メールサーバー名
# 戻り値： json {"from": [メールアドレスのリスト], "since": 処理済み時刻（UNIX時刻) }
def get_filter_info(api_host, server_name):
    query = {'server_name' : server_name}
    # LOGGER.debug( 'GET get_filter_info?%s' % urllib.parse.urlencode(query))
    statuscode, body = webapi(api_host, 'get_filter_info?%s' % urllib.parse.urlencode(query), 'GET', None)
    if statuscode == HTTP_STATUS_OK[0]:
        if len(body) > 0:
            LOGGER.debug('get_mails( %s, %s ) get_filter_info SUCCEEDED status=%s results=%s' % (api_host, server_name, statuscode, str(body)))
            return statuscode, json.loads(body)
    else:
        LOGGER.error( "get_mails( %s, %s ) get_filter_info error %s %s" % (api_host, server_name, statuscode, str(body)))
    return statuscode, None

# フィルタ済みの結果をPostする
# API: (POST) mail_receiver_api/post_mail_info
# 引数: json ...
# 戻り値：json { "detection_count": 処理件数, "notification_count": イベント通知件数 }
def post_mail_info(host, params):
    param = json.loads(params)
    if len(param['mails']) == 0:
        # 連携すべきメールがない
        LOGGER.debug('post_mail_info () 処理すべきメールがない')
        return HTTP_STATUS_OK[0], "posr_mail_info()渡すメールがない"

    statuscode, body = webapi(host, 'post_mail_info', 'POST', params)
    if statuscode == HTTP_STATUS_OK[0]:
      LOGGER.info('post_mail_info SUCCEEDED status=%s results=%s' % (statuscode, body))
      if len(body) > 0:
        return statuscode, json.loads(body)
    else:
      LOGGER.error('post_mail_info FAILED status=%s results=%s' % (statuscode, body))
    return statuscode, None

#api共通処理
def webapi(host, api, method, params):
    """
    API呼出しを行い、結果json文字列を返す
    """
    headers = {'AccessToken': CONFIG.API_ACCESS_TOKEN}
    url = '%s%s' % (str(WEB_API_BASE_URL % host), api)
    LOGGER.debug("webapi: url=%s" % url)
    req = urllib.request.Request(url, method=method, headers=headers, data=params)
    try:
        res = urllib.request.urlopen(req)
        #正常時、API呼出しの結果はjsonとして処理できる文字列が返るはず
        return HTTP_STATUS_OK[0], res.read().decode('utf-8')

    # urllib.request.urlopenはURLError,HTTPError,ConnectionErrorの例外を返す可能性がある
    # 例外を返した場合、レスポンスは空
    except urllib.request.URLError as e:
        LOGGER.error("URLError reason:%s" % e.reason)
        #エラー時にはコンテンツとしてエラーメッセージ
        return 0, json.dumps({ "reason": str(e.reason) })
    except urllib.request.HTTPError as e:
        LOGGER.error("HTTPError code:%s reason:%s" % (e.code, e.reason))
        #エラー時にはコンテンツとしてエラーメッセージ
        return e.code, json.dumps({ "reason": str(e.reason) })
    except ConnectionError as e:
        LOGGER.error("%s strerror:%s" % (type(e).__name__, e.strerror))
        #エラー時にはコンテンツとしてエラーメッセージ
        return 0, json.dumps({ "reason": str(e.strerror) })

# メールメッセージをデコードする
def decode_message(message, charset):
    """
    メールメッセージをデコードする

    Parameters
    ----------
    message: bytes or string
        デコードするバイト配列
    charset: string or None
        期待する文字セット ex) 'iso-2022-jp', 'utf-8' など
    Returns
    -------
    デコードされたメールメッセージ
    Remarks
    -------
    ・デコードするバイト中に、文字セットにデコードできない部分があれば16進コード表現に置き換える
    """

    # すでにデコードされている場合は文字列をそのまま返す
    if isinstance(message, str):
        return message

    # charsetが指定されていない場合は自動判定を行う
    if isinstance(message, bytes) and charset is None:
        result = chardet.detect(message)
        if result is not None and result["confidence"] >= CONFIG.CHARSET_DETECT_THRESHOLD:
            charset = result["encoding"]
            LOGGER.debug("decode_message 文字コードの自動判定を行いました:%s, 信頼度:%g/100" % (charset, result["confidence"] * 100))
        else:
            raise ChardetFailedError(message)

    text = ""
    try:
        # メッセージをデコードする
        text = message.decode(charset)
    except:
        # デコードに失敗した場合()
        try:
            # デコードできない文字を\x.. のような16進コード表現に変換してデコードする
            text = message.decode(charset, errors='backslashreplace')
        except:
            # それでもデコードできない場合
            LOGGER.info("デコード不能 message=%s, enc=%s" % (message, charset))
            # 入力を文字列としてそのまま返す（後続のステップでは意味不明なメッセージとして表示されることになる）
            text = str(message)
        else:
            # 環境依存文字が使われたことを検知するメッセージ
            LOGGER.info("認識できないシーケンスを16進コードに変換しました message=%s, enc=%s" % (message, charset))
    return text

# メールコンテンツ(パート）のデコード
def decode_content_part(msg):
    """
    一般的なメールのエンコーディング
    charset='iso-2022-jp', Content-Transfer-Encoding='7bit'
    charset='utf-8', Content-Transfer-Encoding='Base64'または'quoted-printable'

    Content-Transfer-Encodingには7bit,8bit,binary,quoted-printable,base64 が指定できる。
    一般的には7bit,quoted-printable,base64が使われる。

    Content-Transfer-Encodingヘッダが存在しない場合は、CONFIG.FALLBACK_ENCODING の設定値を使用する。
    charsetヘッダが存在しない場合は、decode_message関数で自動判定を行う。
    """

    content_transfer_encoding = msg.get("Content-Transfer-Encoding")
    if content_transfer_encoding is None:
        content_transfer_encoding = CONFIG.FALLBACK_ENCODING
        LOGGER.debug("decode_content_part Content-Transfer-Encoding ヘッダが見つかりません。%sと仮定します。" % CONFIG.FALLBACK_ENCODING)
    else:
        LOGGER.debug("decode_content_part Content-Transfer-Encoding:%s" % content_transfer_encoding)

    content_type = msg.get_content_type()
    if content_type is None:
        LOGGER.debug("decode_content_part Content-Type ヘッダが見つかりません。")
    else:
        LOGGER.debug("decode_content_part Content-Type:%s" % content_type)

    charset = msg.get_content_charset()
    if charset is None:
        LOGGER.debug("decode_content_part charset ヘッダが見つかりません。")
    else:
        LOGGER.debug("decode_content_part charset:%s" % charset)

    if content_transfer_encoding.lower() in ["quoted-printable", "base64", "7bit", "8bit"]:
        # Content-Transfer-Encoding が "quoted-printable" または "base64" の場合、メッセージは転送エンコードされています。
        # Content-Transfer-Encoding が "7bit" または "8bit" の場合、メッセージは転送エンコードされていません。
        # decode=Trueによってペイロードを取り出すことができます。
        payload = msg.get_payload(decode=True)

        # 取り出したペイロードの中身はバイナリの場合があるので、文字コードにしたがってデコードする必要があります。
        return (decode_message(payload, charset), None)
    else:
        # 7bit,8bit,quoted-printable,base64以外(binary)のContent-Transfer-Encodingはサポートしない
        return ("メール本文を取得できません (Content-Transfer-Encoding:%s)" % content_transfer_encoding, 
                "Content-Transfer-Encoding:%s のメール本文は取得できません。" % content_transfer_encoding)

def parse_header(parts, target=''):
    """
    ヘッダのMIMEデコードおよびASCIIチェック

    Parameters
    ----------
    parts : list
        email.header.decode_headerの戻り値
    target : str
        ヘッダ名（例: 'Subject', 'From'等）

    Returns
    -------
    str
        デコード済み文字列

    Raises
    ------
    HeaderDecodeError
        デコード失敗時やASCII以外未エンコード時等
    """
    result = []
    for part, enc in parts:
        try:
            if enc:
                # エンコーディング指定あり
                if isinstance(part, bytes):
                    # 指定エンコーディングでデコード
                    result.append(part.decode(enc, errors='strict'))
                else:
                    result.append(str(part))
            else:
                # エンコーディング指定なし（ASCII想定）
                if isinstance(part, bytes):
                    result.append(part.decode('ascii', errors='strict'))
                else:
                    if not is_ascii(part):
                        # ASCII以外未エンコード時は例外
                        raise HeaderDecodeError(target, part, f"{target}ヘッダASCII以外未エンコード")
                    result.append(str(part))
        except Exception as e:
            # エンコード/デコード失敗時は独自例外で通知
            raise HeaderDecodeError(target, part, f"{target}ヘッダMIMEデコード失敗: {part}, enc={enc}, error: {str(e)}")
    return ''.join(result)

def is_ascii(s):
    """
    文字列またはバイト列がASCIIのみで構成されているか判定
    """
    try:
        if isinstance(s, bytes):
            s.decode('ascii')
        else:
            str(s).encode('ascii')
        return True
    except Exception:
        return False


# HTMLから内部のテキストを抽出する
def html_to_text(part):
    html, error = decode_content_part(part)
    class MyHTMLParser(HTMLParser):
        def __init__(self):
            HTMLParser.__init__(self)
            self.text =""
        def handle_data(self, data):
            #文字列の前後の改行文字を削除(htmlソースのタグ間にある改行文字が出てくる(不要）のでそれを削除)
            #\nだと 0x0D 0x0A のシーケンス（CRLF:Windowsの改行コード)が削除されないようなので個別に削除
            data = re.sub(r'^(\r\n|\n|\r)*|(\r\n|\n|\r)+$','', data) 
            self.text = self.text + data 

    parser = MyHTMLParser()
    parser.feed(html)
    return parser.text

#メールサーバからメール情報を抽出する
def extract_mail_info(filter, server_name):
    """
    メールサーバへアクセスしてメール情報を取得し、必要な情報へ変換する

    Parameters
    ----------
    filter: array
        メール抽出条件
        例： { from: [test_name_1@example.com, test_name_2@example.com], since: 1571929200}

    server_name: str
        処理実行したサーバ名称

    Returns
    --------
    mail_info: hash
        APIへ通知するためのフォーマット、構成は下記の通り
        server_name: str
            処理実行したサーバ名称
        until: int
            チェックしたことが、保証されるunixtime
        count: int
            後述のmailsに含まれる要素の数
        mails: array
            メールを解析し、必要な情報をまとめた結果
            各要素は、hashで下記のパラメータをもつ
            title: str
                メール件名
            content: str
                メール本文、添付ファイルなどは無視する
            from: str
                送信者のメールアドレス
                メールアドレスに紐付く、氏名などは含まれない
            sendDate: int
                送信者がメールを送信したunixtime
            receiveDate: int
                メールサーバがメールを受信したunixtime

    Raises
        なし
    ----------
    2025/05/21  メール取りこぼし防止のためメール受信時間のハンドリングを80秒遡り処理するよう修正
    """
    LOGGER.debug("extract_mail_info")

    ##### 2025/05/21　修正
    SINCE_BACK_SECONDS = 80 #遡り秒を指定

    # 【修正】filter['since'] を遡らせる（指定秒数だけ過去にずらす）
    if 'since' in filter and filter['since'] is not None:
        orig_since = filter['since']
        filter['since'] = max(0, filter['since'] - SINCE_BACK_SECONDS)
        LOGGER.info(f"filter['since'] 遡り前: {orig_since}, 遡り後: {filter['since']} (遡り秒: {SINCE_BACK_SECONDS})")

    ##### 2025/05/21　修正ここまで

    # メールサーバーログイン
    imap4 = imaplib.IMAP4_SSL(CONFIG.IMAP4_HOST, CONFIG.IMAP4_PORT)
    imap4.login(CONFIG.IMAP4_USER_NAME, CONFIG.IMAP4_PASSWORD)

    parsed_indexes = set()

    for retry_round in range(0, CONFIG.MAX_RETRY_COUNT):
        LOGGER.debug("受信メール取得 %d回目のトライ" % (retry_round + 1))

        #受信メール取得
        imap4.select()
        option = search_option(filter)
        _, mail_box = imap4.search(None, option)

        mail_info = {}
        mail_info["mails"] = []
        mail_info["until"] = 0
        mail_info["server_name"] = server_name

        for raw_index in mail_box[0].split():
            if raw_index in parsed_indexes:
                continue

            try:
                # メールボックス内でのメール番号を取得
                try:
                    mail_index = raw_index.decode("utf-8")
                except:
                    mail_index = str(raw_index)

                # メールメッセージの取得＆パース
                mail = {}
                _, raw_data = imap4.fetch(raw_index, "(RFC822)")
                raw_email = raw_data[0][1]

                msg = email.message_from_bytes(raw_email)

                # 受信日時を抽出 mail["receiveDate"]
                raw_received = msg.get("Received")
                if raw_received is None:
                    raise HeaderNotFoundError("Received")
                recvDate = email.header.decode_header(raw_received)[0][0]
                # header_type="Received"を明示的に指定し、パース失敗時は例外による分岐を可能にする
                datestr, mail["receiveDate"] = to_unixtime(recvDate, header_type="Received")

                # 前回の最終受信日時より新しいメールのみを連携対象とする
                if mail["receiveDate"] <= filter.get("since", 0):
                    LOGGER.debug("メール[%s] recvDate:%s (%d) (処理済み)" % (mail_index, datestr, mail["receiveDate"]))
                    parsed_indexes.add(raw_index)
                    continue

                # ★Subject（大文字小文字非依存で取得・例外時スキップ／ヘッダなしは""セット）
                raw_subject = get_header_ignorecase(msg, "Subject")
                if raw_subject is None:
                    mail["title"] = ""      #当初nullだったが、API側でエラーとなるので""に変更
                else:
                    try:
                        subject_parts = email.header.decode_header(raw_subject)
                        mail["title"] = parse_header(subject_parts, target="Subject")
                    except HeaderDecodeError as e:
                        # ヘッダデコード失敗時は警告ログを出力しスキップ
                        LOGGER.warning(
                            f"[HeaderDecodeError] Subjectヘッダデコードエラー: メールID:{mail_index}, raw_subject:{raw_subject}, from:{mail.get('from','')}, error:{e.message}, raw={e.raw_value}"
                        )
                        continue
                    except Exception as e:
                        # その他の例外も警告ログを出力しスキップ
                        LOGGER.warning(
                            f"Subjectヘッダデコードエラー: メールID:{mail_index}, raw_subject:{raw_subject}, from:{mail.get('from','')}, error:{str(e)}"
                        )
                        continue

                LOGGER.debug("メール[%s] Subject:%s" % (mail_index, mail["title"]))

                # 本文の抽出 mail["content"]
                contents = [] #content(本文)は複数のパートで抽出する
                if msg.is_multipart():
                    # multipartの場合
                    # msg.walk()を使うとメッセージオブジェクトツリー内のメッセージオブジェクトを列挙することができる
                    # 列挙順はdepth-firstとなる
                    for part in msg.walk():
                        # ここでは列挙したメッセージオブジェクトの内
                        # content-type="text/plain"と"text/html"を本文として取り込む(添付ファイルや画像などは読み飛ばす)
                        content_type = part.get_content_type()
                        if content_type == "text/plain":
                            content, error = decode_content_part(part)
                            if error is not None:
                                LOGGER.error("メール[%s] %s" % (mail_index, error))
                            contents.append(content)
                        elif content_type == "text/html":
                            content = html_to_text(part)
                            contents.append(content)
                        else:
                            # 添付ファイル、画像、など
                            continue #スキップ
                else:
                    # multipartでない場合
                    content, error = decode_content_part(msg)
                    if error is not None:
                        LOGGER.error("メール[%s] %s" % (mail_index, error))
                    contents.append(content)

                mail["content"] = contents

                LOGGER.debug("メール[%s] Contents:%s" % (mail_index, mail["content"]))

                # ★From（大文字小文字非依存で取得・MIMEエンコードされていない場合はスキップ）
                raw_from = get_header_ignorecase(msg, "From")
                if raw_from is None:
                    raise HeaderNotFoundError("From")
                try:
                    from_parts = email.header.decode_header(raw_from)
                    from_name = parse_header(from_parts, target="From")
                    # parseaddrでメールアドレスだけ抽出
                    _, addr = parseaddr(from_name)
                    mail["from"] = addr.strip()
                except HeaderDecodeError as e:
                    # ヘッダデコード失敗時は警告ログを出力しスキップ
                    LOGGER.warning(
                        f"[HeaderDecodeError] Fromヘッダデコードエラー: メールID:{mail_index}, raw_from:{raw_from}, subject:{mail.get('title','')}, error:{e.message}, raw={e.raw_value}"
                    )
                    continue
                except Exception as e:
                    LOGGER.warning(
                        f"Fromヘッダデコードエラー: メールID:{mail_index}, raw_from:{raw_from}, subject:{mail.get('title','')}, error:{str(e)}"
                    )
                    continue

                LOGGER.debug("メール[%s] From:%s" % (mail_index, mail["from"]))

                # ★Date（大文字小文字非依存で取得）
                raw_date = get_header_ignorecase(msg, "Date")
                if raw_date is None:
                    raise HeaderNotFoundError("Date")

                sendDate = email.header.decode_header(raw_date)[0][0]
                # header_type="Date"を明示的に指定
                datestr, mail["sendDate"] = to_unixtime(sendDate, header_type="Date")

                LOGGER.debug("メール[%s] sendDate:%s (%d)" % (mail_index, datestr, mail["sendDate"]))

                mail_info["mails"].append(mail)
                mail_info["until"] = max(mail["receiveDate"], mail_info["until"])
                parsed_indexes.add(raw_index)
                LOGGER.debug("メール[%s] recvDate:%s (%d) (新規)" % (mail_index, datestr, mail["receiveDate"]))

            except HeaderNotFoundError as e:
                LOGGER.error("メール[%s] %s ヘッダが見つかりません。メールを読み飛ばします。" % (mail_index, e.header_name()))

            except ChardetFailedError as e:
                LOGGER.error("メール[%s] 文字コードの自動判定に失敗しました。メールを読み飛ばします。" % mail_index)

            # 【修正】Received/Dateともにwarningレベルでログ出力し、API送信対象外
            except UnixtimeParseError as utpe:
                if utpe.header_type == "Received":
                    # 受信日時のパース失敗は警告ログ＋API連携から除外
                    LOGGER.warning(
                        f"Receivedヘッダ日付変換エラー: メールID:{mail_index}, from:{mail.get('from','')}, subject:{mail.get('title','')}, raw_received:{utpe.date_str}, error:{utpe.message}"
                    )
                    continue
                else:
                    # 送信日時(Date)のパース失敗も警告ログ＋API連携から除外
                    LOGGER.warning(
                        f"Dateヘッダ日付変換エラー: メールID:{mail_index}, from:{mail.get('from','')}, subject:{mail.get('title','')}, raw_date:{utpe.date_str}, error:{utpe.message}"
                    )
                    continue

            except Exception as e:
                if retry_round < CONFIG.MAX_RETRY_COUNT - 1:
                    LOGGER.debug("メール[%s] 受信メール解析中にエラーが発生しました。%d秒後にリトライします。" % (mail_index, CONFIG.RETRY_INTERVAL))
                    LOGGER.debug(traceback.format_exc())
                    time.sleep(CONFIG.RETRY_INTERVAL)
                    break
                else:
                    LOGGER.error("メール[%s] 受信メール解析中にエラーが発生しました。メールを読み飛ばします。" % mail_index)
                    LOGGER.info(traceback.format_exc())

        else:
            break

    mail_info["count"] = len(mail_info["mails"])

    # 終了処理
    imap4.close()
    imap4.logout()
    return mail_info


# 日付文字列をunixtimeに変換する（推奨版/新方式）
def to_unixtime(date_str, header_type='Date'):
    """
    日付文字列をunixtimeに変換する関数

    Parameters
    ----------
    date_str : str or bytes
        変換対象となる日付文字列。メールヘッダから取得したもの
    header_type : str, default 'Date'
        変換対象ヘッダの種別。'Received'または'Date'を指定
        ・'Received'の場合、ヘッダ末尾のセミコロン以降を日付として扱う

    Returns
    -------
    tuple(str, int)
        (正規化後の日付文字列, unixtime(int))

    Raises
    ------
    UnixtimeParseError
        日付パースに失敗した場合に発生。エラー内容・ヘッダ種別・生値等が格納される

    Remarks
    -------
    ・header_typeを必ず指定し、呼び出し元でどちらのヘッダの変換か判別可能にする
    ・失敗時は例外送出し、呼び出し元でハンドリング
    """
    if isinstance(date_str, bytes):
        try:
            date_str = date_str.decode('utf-8', errors='ignore')
        except Exception:
            pass
    date_str = re.sub(r'[\r\n\t]', ' ', date_str)
    date_str = re.sub(r'\s+', ' ', date_str)
    date_str = date_str.strip()
    # Receivedヘッダは末尾の";"以降が日付部分
    if header_type == 'Received' and ';' in date_str:
        date_str = date_str.split(';')[-1].strip()
    try:
        dt = parsedate_to_datetime(date_str)
        if dt is not None:
            return date_str, int(dt.timestamp())
        else:
            raise ValueError("parsedate_to_datetime returned None")
    except Exception as e:
        # warningログも出さず、例外でエラー詳細を渡す
        raise UnixtimeParseError(date_str, header_type, message=str(e))


#検索オプションを生成する
def search_option(filter):
    LOGGER.debug("search_option")
    search_option_from_mail_address = None
    if 'from' in filter and len(filter['from']) > 0:
        conditions = []
        for fr in filter['from']:
            conditions.append('(FROM %s)' % fr)
        condition_count = len(conditions)
        if condition_count == 1:
            search_option_from_mail_address = conditions[0]
        elif condition_count > 1:
            appended_conditions = ''
            for index, condition in enumerate(conditions):
              if index == 0:
                appended_conditions = condition
              else:
                appended_conditions = '(OR %s %s)' % (appended_conditions, condition)
            search_option_from_mail_address = appended_conditions
        else:
            search_option_from_mail_address = None

    search_option_since_time = None
    if 'since' in filter and filter['since'] is not None:
        since = datetime.fromtimestamp(filter['since']).strftime('%d-%b-%Y')
        search_option_since_time = '(SINCE "%s")' % since

    search_option = []
    if search_option_from_mail_address is not None:
      search_option.append(search_option_from_mail_address)
    if search_option_since_time is not None:
      search_option.append(search_option_since_time)

    search = None
    if len(search_option) > 0:
        search = '(%s)' % ' '.join(search_option)
    else:
        search = 'ALL'

    return search

#起動時に呼ばれる
if __name__ == "__main__":
   if len(sys.argv) == 4:
        # 接続先のホスト名（IPアドレス）、サーバ名,実行間隔(秒)
        LOGGER.debug(sys.argv)
        main(sys.argv[1], sys.argv[2], int(sys.argv[3]))
   else:
        LOGGER.error("%s invalid argument." % sys.argv[0])

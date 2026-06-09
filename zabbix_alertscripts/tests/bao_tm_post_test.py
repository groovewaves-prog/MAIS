import datetime
import os
import sys
import unittest
from unittest.mock import patch, mock_open
import xml.etree.ElementTree as ET

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import bao_tm_post

# 定数宣言
KISYS_INCIDENTID_NONE = None
KISYS_INCIDENTID_NORMAL = 'IT0000000000'
KISYS_STATUS = 9
ALIAS = 'firstname,middlename,lastname'
XMLFILE = '/var/log/gwscripts/baosoap-oldxml'
MOCK_BAO_TM_CLIENT_SEND_REQUEST_RETURN_VALUE_SUCCESS = '<?xml version="1.0" encoding="UTF-8"?>\n \
    <S:Envelope xmlns:S="http://schemas.xmlsoap.org/soap/envelope/">\n \
    <S:Body>\n<ns1:executeProcessResponse xmlns:ns1="http://bmc.com/ao/xsd/2008/09/soa">\n \
    <ns1:Output>\n<ns1:Output ns1:type="xs:anyType">\n<ns1:Parameter>\n<ns1:Name>incident_number</ns1:Name>\n \
    <ns1:Value ns1:type="xs:anyType">\n<ns1:XmlDoc>\n<result xmlns="">IT0000-00000000</result>\n \
    </ns1:XmlDoc>\n</ns1:Value>\n</ns1:Parameter>\n<ns1:Parameter>\n<ns1:Name>create_status</ns1:Name>\n \
    <ns1:Value ns1:type="xs:anyType">\n<ns1:XmlDoc>\n<result xmlns="">0</result>\n \
    </ns1:XmlDoc>\n</ns1:Value>\n</ns1:Parameter>\n<ns1:Parameter>\n<ns1:Name>create_message</ns1:Name>\n \
    <ns1:Value ns1:type="xs:anyType">\n<ns1:XmlDoc>\n<result xmlns=""></result>\n</ns1:XmlDoc>\n \
    </ns1:Value>\n</ns1:Parameter>\n<ns1:Parameter>\n<ns1:Name>internal_alarm_id</ns1:Name>\n \
    <ns1:Value ns1:type="xs:anyType">\n<ns1:XmlDoc>\n<result xmlns="">ITOS_01_0000000001</result>\n \
    </ns1:XmlDoc>\n</ns1:Value>\n</ns1:Parameter>\n</ns1:Output>\n</ns1:Output>\n</ns1:executeProcessResponse>\n \
    </S:Body>\n</S:Envelope>\n'
MOCK_BAO_TM_CLIENT_SEND_REQUEST_RETURN_VALUE_FAILURE = '<?xml version="1.0" encoding="UTF-8"?>\n \
    <S:Envelope xmlns:S="http://schemas.xmlsoap.org/soap/envelope/">\n \
    <S:Body>\n<ns1:executeProcessResponse xmlns:ns1="http://bmc.com/ao/xsd/2008/09/soa">\n \
    <ns1:Output>\n<ns1:Output ns1:type="xs:anyType">\n<ns1:Parameter>\n<ns1:Name>incident_number</ns1:Name>\n \
    <ns1:Value ns1:type="xs:anyType">\n<ns1:XmlDoc>\n<result xmlns="">IT0000-00000000</result>\n \
    </ns1:XmlDoc>\n</ns1:Value>\n</ns1:Parameter>\n<ns1:Parameter>\n<ns1:Name>create_status</ns1:Name>\n \
    <ns1:Value ns1:type="xs:anyType">\n<ns1:XmlDoc>\n<result xmlns="">1</result>\n \
    </ns1:XmlDoc>\n</ns1:Value>\n</ns1:Parameter>\n<ns1:Parameter>\n<ns1:Name>create_message</ns1:Name>\n \
    <ns1:Value ns1:type="xs:anyType">\n<ns1:XmlDoc>\n<result xmlns="">error_message</result>\n</ns1:XmlDoc>\n \
    </ns1:Value>\n</ns1:Parameter>\n<ns1:Parameter>\n<ns1:Name>internal_alarm_id</ns1:Name>\n \
    <ns1:Value ns1:type="xs:anyType">\n<ns1:XmlDoc>\n<result xmlns="">ITOS_01_0000000001</result>\n \
    </ns1:XmlDoc>\n</ns1:Value>\n</ns1:Parameter>\n</ns1:Output>\n</ns1:Output>\n</ns1:executeProcessResponse>\n \
    </S:Body>\n</S:Envelope>\n'

class BaoTmPostTest(unittest.TestCase):

    def setUp(self):
        # 最初にxmlファイルの中身をクリアする
        truncate_xmlfile()

    ### error報かつGID追加がある場合の処理 ###
    def test_error_param_check_gid(self):

        ### 引数準備 ###
        now = datetime.datetime.now()
        new_event, alarm_time = get_new_event(now, 'error', 'traptest')

        ### メソッド実行 ###
        # xmlファイルを作成するメソッドを呼び出す
        bao_tm_post.BAO_TM_CLIENT_HELPER().create_bao_request_xml(new_event, KISYS_INCIDENTID_NONE, KISYS_STATUS, ALIAS)
        # 作成されたxmlファイルをパース
        root = parse_xml()

        ### 期待値作成 ###
        # alarm_time期待値作成
        alarm_time_ts = alarm_time.timestamp()
        alarm_unixtime = str(int(float(alarm_time_ts)))

        # value_worklog_note期待値作成
        value_worklog_note = 'お客様名：customer_name&#xA;アラーム種別：error&#xA;ホスト名：hostname&#xA;' + '日時：' + str(datetime.datetime.fromtimestamp(int(alarm_time_ts))) +'&#xA;アラーム名：ci_name&#xA;詳細：summary'

        # 期待値パターン
        patterns = [
            ['ITOS_BAO-GW'],
            [None],
            [None],
            ['0'],
            ['100'],
            ['customer_name'],
            [None],
            ['lastname'],
            ['firstname'],
            ['middlename'],
            ['[TBL]ci_name'],
            ['ITアウトソースSOL(customer_ci)'],
            ['hostname_customer_ci'],
            ['ITOS-SYSOPE'],
            ['ITOS-OPE-AUTO'],
            [alarm_unixtime],
            [None],
            ['0'],
            ['・現象: \r\n・原因: \r\n・対処: \r\n・結果: \r\n'],
            ['ITOS_01_0000000001'],
            ['1'],
            ['100'],
            ['010_アラーム発生検知（初回）※CP'],
            ['--'],
            ['■アラーム検知'],
            [value_worklog_note],
            ['ITOS-SYSOPE'],
            ['itos_zabbix'],
            [alarm_unixtime]
        ]

        # パースしたxmlをタグごとにループで取り出す
        i = 0
        for param in root.iter(tag='{http://bmc.com/ao/xsd/2008/09/soa}Text'):
            with self.subTest('param=%s' % param.text):
                expected_value = patterns[i][0]
                # 期待値と取得したパラメータの正誤チェック
                self.assertEqual(param.text, expected_value)
            i += 1

    ### error報かつGID追加がない場合の処理 ###
    def test_error_param_check(self):

        ### 引数準備 ###
        now = datetime.datetime.now()
        new_event, alarm_time = get_new_event(now, 'error', 'host')

        ### メソッド実行 ###
        # xmlファイルを作成するメソッドを呼び出す
        bao_tm_post.BAO_TM_CLIENT_HELPER().create_bao_request_xml(new_event, KISYS_INCIDENTID_NONE, KISYS_STATUS, ALIAS)
        # 作成されたxmlファイルをパース
        root = parse_xml()

        ### 期待値作成 ###
        # alarm_time期待値作成
        alarm_time_ts = alarm_time.timestamp()
        alarm_unixtime = str(int(float(alarm_time_ts)))

        # value_worklog_note期待値作成
        value_worklog_note = 'お客様名：customer_name&#xA;アラーム種別：error&#xA;ホスト名：hostname&#xA;' + '日時：' + str(datetime.datetime.fromtimestamp(int(alarm_time_ts))) +'&#xA;アラーム名：ci_name&#xA;詳細：summary'

        # 期待値パターン
        patterns = [
            ['ITOS_BAO-GW'],
            [None],
            [None],
            ['0'],
            ['173'],
            ['customer_name'],
            [None],
            ['lastname'],
            ['firstname'],
            ['middlename'],
            ['[TBL]ci_name'],
            ['ITアウトソースSOL(customer_ci)'],
            ['hostname_customer_ci'],
            ['ITOS-SYSOPE'],
            ['ITOS-OPE-AUTO'],
            [alarm_unixtime],
            [None],
            ['0'],
            ['・現象: \r\n・原因: \r\n・対処: \r\n・結果: \r\n'],
            ['ITOS_01_0000000001'],
            ['1'],
            ['173'],
            ['010_アラーム発生検知（初回）※CP'],
            ['--'],
            ['■アラーム検知'],
            [value_worklog_note],
            ['ITOS-SYSOPE'],
            ['itos_zabbix'],
            [alarm_unixtime]
        ]

        # パースしたxmlをタグごとにループで取り出す
        i = 0
        for param in root.iter(tag='{http://bmc.com/ao/xsd/2008/09/soa}Text'):
            with self.subTest('param=%s' % param.text):
                expected_value = patterns[i][0]
                # 期待値と取得したパラメータの正誤チェック
                self.assertEqual(param.text, expected_value)
            i += 1

    ### normal報かつGID追加がある場合の処理 ###
    def test_normal_param_check_gid(self):

        ### 引数準備 ###
        now = datetime.datetime.now()
        new_event, alarm_time = get_new_event(now, 'normal', 'traptest')

        ### メソッド実行 ###
        # xmlファイルを作成するメソッドを呼び出す
        bao_tm_post.BAO_TM_CLIENT_HELPER().create_bao_request_xml(new_event, KISYS_INCIDENTID_NORMAL, KISYS_STATUS, ALIAS)
        # 作成されたxmlファイルをパース
        root = parse_xml()

        ### 期待値作成 ###
        # alarm_time期待値作成
        alarm_time_ts = alarm_time.timestamp()
        alarm_unixtime = str(int(float(alarm_time_ts)))

        # value_worklog_note期待値作成
        value_worklog_note = 'お客様名：customer_name&#xA;アラーム種別：normal&#xA;ホスト名：hostname&#xA;' + '日時：' + str(datetime.datetime.fromtimestamp(int(alarm_time_ts))) +'&#xA;アラーム名：ci_name&#xA;詳細：summary'

        # 期待値パターン
        patterns = [
            ['ITOS_BAO-GW'],
            [None],
            [None],
            [None],
            ['100'],
            [None],
            [KISYS_INCIDENTID_NORMAL],
            [None],
            [None],
            [None],
            ['[TBL]ci_name'],
            ['ITアウトソースSOL(customer_ci)'],
            ['hostname_customer_ci'],
            [None],
            [None],
            [None],
            [alarm_unixtime],
            [str(KISYS_STATUS)],
            [None],
            ['ITOS_01_0000000001'],
            ['1'],
            ['100'],
            ['015_アラーム復旧検知（初回）※CP'],
            ['--'],
            ['■アラーム復旧検知'],
            [value_worklog_note],
            ['ITOS-SYSOPE'],
            ['itos_zabbix'],
            [alarm_unixtime]
        ]

        # パースしたxmlをタグごとにループで取り出す
        i = 0
        for param in root.iter(tag='{http://bmc.com/ao/xsd/2008/09/soa}Text'):
            with self.subTest('param=%s' % param.text):
                expected_value = patterns[i][0]
                # 期待値と取得したパラメータの正誤チェック
                self.assertEqual(param.text, expected_value)
            i += 1

    ### normal報かつGID追加がない場合の処理 ###
    def test_normal_param_check(self):

        ### 引数準備 ###
        now = datetime.datetime.now()
        new_event, alarm_time = get_new_event(now, 'normal', 'host')

        ### メソッド実行 ###
        # xmlファイルを作成するメソッドを呼び出す
        bao_tm_post.BAO_TM_CLIENT_HELPER().create_bao_request_xml(new_event, KISYS_INCIDENTID_NORMAL, KISYS_STATUS, ALIAS)
        # 作成されたxmlファイルをパース
        root = parse_xml()

        ### 期待値作成 ###
        # alarm_time期待値作成
        alarm_time_ts = alarm_time.timestamp()
        alarm_unixtime = str(int(float(alarm_time_ts)))

        # value_worklog_note期待値作成
        value_worklog_note = 'お客様名：customer_name&#xA;アラーム種別：normal&#xA;ホスト名：hostname&#xA;' + '日時：' + str(datetime.datetime.fromtimestamp(int(alarm_time_ts))) +'&#xA;アラーム名：ci_name&#xA;詳細：summary'

        # 期待値パターン
        patterns = [
            ['ITOS_BAO-GW'],
            [None],
            [None],
            [None],
            ['173'],
            [None],
            [KISYS_INCIDENTID_NORMAL],
            [None],
            [None],
            [None],
            ['[TBL]ci_name'],
            ['ITアウトソースSOL(customer_ci)'],
            ['hostname_customer_ci'],
            [None],
            [None],
            [None],
            [alarm_unixtime],
            [str(KISYS_STATUS)],
            [None],
            ['ITOS_01_0000000001'],
            ['1'],
            ['173'],
            ['015_アラーム復旧検知（初回）※CP'],
            ['--'],
            ['■アラーム復旧検知'],
            [value_worklog_note],
            ['ITOS-SYSOPE'],
            ['itos_zabbix'],
            [alarm_unixtime]
        ]

        # パースしたxmlをタグごとにループで取り出す
        i = 0
        for param in root.iter(tag='{http://bmc.com/ao/xsd/2008/09/soa}Text'):
            with self.subTest('param=%s' % param.text):
                expected_value = patterns[i][0]
                # 期待値と取得したパラメータの正誤チェック
                self.assertEqual(param.text, expected_value)
            i += 1

    # 5-1
    @patch('bao_tm_post.BAO_TM_CLIENT.send_request')
    def test_GID_hostgroups_over_2_message_check(self, mock_bao_tm_client_send_request):

        ### 引数準備 ###
        now = datetime.datetime.now()
        return_value = get_new_event(now, 'error', 'gid_2')
        new_event = return_value[0]

        ### メソッド実行 ###
        with self.assertLogs('bao_tm_post.py') as cm:
            kisys_incidentid = bao_tm_post.BAO_TM_CLIENT().send(new_event, KISYS_INCIDENTID_NONE, KISYS_STATUS, ALIAS)
        
        self.assertEqual(kisys_incidentid, 'No_reply')

        self.assertEqual(cm.output, [
            "ERROR:bao_tm_post.py:'GID'の文字列を含むホストグループに2つ以上所属しています"
        ])

    # 5-2
    @patch('bao_tm_post.BAO_TM_CLIENT.send_request')
    def test_GID_param_multibyte_message_check(self, mock_bao_tm_client_send_request):

        ### 引数準備 ###
        now = datetime.datetime.now()
        return_value = get_new_event(now, 'error', 'gid_mult')
        new_event = return_value[0]

        ### メソッド実行 ###
        with self.assertLogs('bao_tm_post.py') as cm:
            kisys_incidentid = bao_tm_post.BAO_TM_CLIENT().send(new_event, KISYS_INCIDENTID_NONE, KISYS_STATUS, ALIAS)
        
        self.assertEqual(kisys_incidentid, 'No_reply')

        self.assertEqual(cm.output, [
            'ERROR:bao_tm_post.py:所属するGIDのホストグループの数値がマルチバイト文字です'
        ])

    # 5-3
    def test_exception_check(self):

        ### 引数準備 ###
        # new_eventの要素数を不正にして例外を発生させる
        new_event = []

        ### メソッド実行 ###
        result = bao_tm_post.BAO_TM_CLIENT().send(new_event, KISYS_INCIDENTID_NONE, KISYS_STATUS, ALIAS)
        self.assertEqual(result, 'No_reply')

    # 5-4,5-5
    @patch('bao_tm_post.BAO_TM_CLIENT.send_request')
    def test_success_add_message_check(self, mock_bao_tm_client_send_request):

        # send_requestをモック化(Success)
        mock_bao_tm_client_send_request.return_value = MOCK_BAO_TM_CLIENT_SEND_REQUEST_RETURN_VALUE_SUCCESS

        ### 引数準備 ###
        now = datetime.datetime.now()
        return_value = get_new_event(now, 'error', 'host')
        new_event = return_value[0]

        ### メソッド実行 ###
        kisys_incidentid = bao_tm_post.BAO_TM_CLIENT().send(new_event, KISYS_INCIDENTID_NONE, KISYS_STATUS, ALIAS)
        self.assertEqual(kisys_incidentid, 'IT0000-00000000')

        # 作成されたxmlファイルの最終行を取り出し正誤確認
        xmlfile_list = get_xmlfile_lines()
        result = xmlfile_list[-1]
        expected_value = datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S") + ' ---> XMLファイル送信に成功しました。\n'
        self.assertEqual(result, expected_value)

    # 5-6,5-7
    @patch('bao_tm_post.BAO_TM_CLIENT.send_request')
    def test_failuer_add_message_check(self, mock_bao_tm_client_send_request):

        # send_requestをモック化(Filure)
        mock_bao_tm_client_send_request.return_value = MOCK_BAO_TM_CLIENT_SEND_REQUEST_RETURN_VALUE_FAILURE

        ### 引数準備 ###
        now = datetime.datetime.now()
        return_value = get_new_event(now, 'error', 'host')
        new_event = return_value[0]

        ### メソッド実行 ###
        kisys_incidentid = bao_tm_post.BAO_TM_CLIENT().send(new_event, KISYS_INCIDENTID_NONE, KISYS_STATUS, ALIAS)
        self.assertEqual(kisys_incidentid, 'Failure')

        # 作成されたxmlファイルの最終行と最終行から二番目を取り出し正誤確認
        xmlfile_list = get_xmlfile_lines()
        result_lastline = xmlfile_list[-1]
        expected_value_lastline = datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S") + ' ---> 応答XMLファイルにエラーが含まれています。\n'
        result_second_to_lastline = xmlfile_list[-2]
        expected_value_second_to_lastline = datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S") + ' ---> XMLファイル送信に成功しました。\n'
        self.assertEqual(result_lastline, expected_value_lastline)
        self.assertEqual(result_second_to_lastline, expected_value_second_to_lastline)

    # 5-8,5-13,5-14
    @patch('bao_tm_post.BAO_TM_CLIENT.send_request')
    def test_no_reply_add_message_check(self, mock_bao_tm_client_send_request):

        # send_requestをモック化(例外を発生させる)
        mock_bao_tm_client_send_request.side_effect = Exception('Exception')

        ### 引数準備 ###
        now = datetime.datetime.now()
        return_value = get_new_event(now, 'error', 'host')
        new_event = return_value[0]

        ### メソッド実行 ###
        with self.assertLogs('bao_tm_post.py') as cm:
            kisys_incidentid = bao_tm_post.BAO_TM_CLIENT().send(new_event, KISYS_INCIDENTID_NONE, KISYS_STATUS, ALIAS)
        
        self.assertEqual(kisys_incidentid, 'No_reply')

        self.assertEqual(cm.output, [
            'INFO:bao_tm_post.py:通信処理を開始します。',
            'INFO:bao_tm_post.py:送信失敗。エラーメッセージ: Exception',
            'INFO:bao_tm_post.py:サーバを切り替えてリクエストを再実施します',
            'INFO:bao_tm_post.py:送信失敗。エラーメッセージ: Exception',
            'INFO:bao_tm_post.py:通信処理を終了します。'
        ])

        # 作成されたxmlファイルの最終行を取り出し正誤確認
        xmlfile_list = get_xmlfile_lines()
        result = xmlfile_list[-1]
        expected_value = datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S") + ' ---> XMLファイル送信に失敗しました。\n'
        self.assertEqual(result, expected_value)

    # 5-9,5-10
    @patch('bao_tm_post.BAO_TM_CLIENT.send_request')
    def test_first_error_second_success_check(self, mock_bao_tm_client_send_request):

        # send_requestをモック化(一回目は例外を発生させ送信失敗,二回目はsuccess)
        mock_bao_tm_client_send_request.side_effect = (Exception('Exception'), MOCK_BAO_TM_CLIENT_SEND_REQUEST_RETURN_VALUE_SUCCESS)

        ### 引数準備 ###
        now = datetime.datetime.now()
        return_value = get_new_event(now, 'error', 'host')
        new_event = return_value[0]

        ### メソッド実行 ###
        with self.assertLogs('bao_tm_post.py') as cm:
            kisys_incidentid = bao_tm_post.BAO_TM_CLIENT().send(new_event, KISYS_INCIDENTID_NONE, KISYS_STATUS, ALIAS)

        self.assertEqual(kisys_incidentid, 'IT0000-00000000')

        self.assertEqual(cm.output, [
            'INFO:bao_tm_post.py:通信処理を開始します。',
            'INFO:bao_tm_post.py:送信失敗。エラーメッセージ: Exception',
            'INFO:bao_tm_post.py:サーバを切り替えてリクエストを再実施します',
            'INFO:bao_tm_post.py:通信処理を終了します。'
        ])

        # 作成されたxmlファイルの最終行を取り出し正誤確認
        xmlfile_list = get_xmlfile_lines()
        result = xmlfile_list[-1]
        expected_value = datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S") + ' ---> XMLファイル送信に成功しました。\n'
        self.assertEqual(result, expected_value)

    # 5-11,5-12
    @patch('bao_tm_post.BAO_TM_CLIENT.send_request')
    def test_first_error_second_failure_check(self, mock_bao_tm_client_send_request):

        # send_requestをモック化(一回目は例外を発生させ送信失敗,二回目はFailure)
        mock_bao_tm_client_send_request.side_effect = (Exception('Exception'), MOCK_BAO_TM_CLIENT_SEND_REQUEST_RETURN_VALUE_FAILURE)

        ### 引数準備 ###
        now = datetime.datetime.now()
        return_value = get_new_event(now, 'error', 'host')
        new_event = return_value[0]

        ### メソッド実行 ###
        with self.assertLogs('bao_tm_post.py') as cm:
            kisys_incidentid = bao_tm_post.BAO_TM_CLIENT().send(new_event, KISYS_INCIDENTID_NONE, KISYS_STATUS, ALIAS)

        # 作成されたxmlファイルの最終行と最終行から二番目を取り出し正誤確認
        xmlfile_list = get_xmlfile_lines()
        result_lastline = xmlfile_list[-1]
        expected_value_result_lastline = datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S") + ' ---> 応答XMLファイルにエラーが含まれています。\n'
        result_second_to_lastline = xmlfile_list[-2]
        expected_value_second_to_lastline = datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S") + ' ---> XMLファイル送信に成功しました。\n'
        self.assertEqual(result_lastline, expected_value_result_lastline)
        self.assertEqual(result_second_to_lastline, expected_value_second_to_lastline)

        self.assertEqual(kisys_incidentid, 'Failure')

        self.assertEqual(cm.output, [
            'INFO:bao_tm_post.py:通信処理を開始します。',
            'INFO:bao_tm_post.py:送信失敗。エラーメッセージ: Exception',
            'INFO:bao_tm_post.py:サーバを切り替えてリクエストを再実施します'
        ])

########################################################################
## Test Helper
########################################################################

# now_eventを作成する
def get_new_event(now, alarm_status, host):
    # ミリ秒を .XXX000 にそろえるための変換 ex. 123456 -> 123000
    alarm_time_org = now.strftime('%Y-%m-%d@%H:%M:%S.%f')[:-3]
    alarm_time = datetime.datetime.strptime(alarm_time_org, '%Y-%m-%d@%H:%M:%S.%f')
    return [1, 1, now.strftime("%Y-%m-%d %H:%M:%S"), 1, now.strftime("%Y-%m-%d %H:%M:%S"), 
        129, 'customer_ci', 'customer_name', 'hostname', alarm_time, 'ci_name', 'device', alarm_status, 'summary', 
        now.strftime("%Y-%m-%d %H:%M:%S"), 'checked_user', 'op_comment', KISYS_STATUS, host], alarm_time

# xmlファイルの中身を削除する
def truncate_xmlfile():
    with open(XMLFILE, mode='a') as f:
        f.truncate(0)
        f.close()

# xmlファイルをパースする
def parse_xml():
    xmlfile_list = get_xmlfile_lines()
    # 一行目は作成日時がテキストで挿入されており、パースできないため削除
    xmlfile_list.pop(0)
    # 一行目を削除した状態で再度テキスト結合
    xmlfile_data = ''.join(xmlfile_list)
    # テキスト形式をElementTreeでパース
    root = ET.fromstring(xmlfile_data)
    return root

# xmlファイルを行ごとのリスト形式に変換する
def get_xmlfile_lines():
    with open(XMLFILE, mode='r') as f:
        xmlfile_list = f.readlines()
        f.close()
    return xmlfile_list

if __name__ == '__main__':
    unittest.main()

import copy
import datetime
import glob
import mysql.connector
import os
import pathlib
import sys
import requests
import unittest
from unittest.mock import patch

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import send_to_bao
import gwcommon
import test_helper as HELPER

@patch('gwcommon.MY_USER', HELPER.MY_USER)
@patch('gwcommon.MY_PASSWD', HELPER.MY_PASSWD)
# @patch('gwcommon.MY_DB', HELPER.MY_DB_LOCAL)
class SendToBaoTest(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        # DB接続
        conn = HELPER.db_connect()

        # 無限ループ停止のためunittestモード設定
        HELPER.set_unittest_mode()
        self.maxDiff = None

        # テーブルの初期化
        HELPER.table_initializ(conn)

        # DB close
        conn.close()

    @classmethod
    def tearDownClass(self):
        # DB接続
        conn = HELPER.db_connect()

        # 無限ループ停止のためunittestモード解除
        HELPER.unset_unittest_mode()

        # テーブルの初期化
        HELPER.table_initializ(conn)

        # DB close
        conn.close()

    def setUp(self):
        # DB接続
        self.conn = HELPER.db_connect()

        # パトランプ削除
        patolamp_files = glob.glob(HELPER.PATOLAMP_FILE_PATH + gwcommon.RED_PATOLAMP_FILE + '*')
        for patolamp_file in patolamp_files:
            os.remove(patolamp_file)

    def tearDown(self):
        # テーブルの初期化
        HELPER.table_initializ(self.conn)

        # DB close
        self.conn.close()

    # @unittest.skip('TESTSKIP')
    @patch('gwcommon.MY_DB', HELPER.MY_DB_LOCAL)
    def test_stop_mode(self):
        # モード設定
        HELPER.set_stop_mode()

        # 処理実行
        with self.assertRaises(SystemExit), self.assertLogs('send_to_bao.py') as cm:
            send_to_bao.main()

        # ログ内容の確認
        self.assertEqual(cm.output, [
            'INFO:send_to_bao.py:ストップモードのため、exitで処理を終了します',
        ])

    # @unittest.skip('TESTSKIP')
    @patch('gwcommon.MY_DB', HELPER.MY_DB_LOCAL)
    def test_test_mode(self):
        # モード設定
        HELPER.set_test_mode()

        # 処理実行
        with self.assertLogs('send_to_bao.py') as cm:
            send_to_bao.main()

        # ログ内容の確認
        self.assertEqual(cm.output, [
            'INFO:send_to_bao.py:testモードのため、テストモードで動作実行',
            'INFO:send_to_bao.py:KISYSメンテナンス期間に該当しないため処理を継続します。',
            'INFO:send_to_bao.py:処理対象イベント無し。',
            'INFO:send_to_bao.py:10秒待機します。',
        ])

    # @unittest.skip('TESTSKIP')
    @patch('gwcommon.MY_DB', HELPER.MY_DB_LOCAL)
    def test_master_mode(self):
        # モード設定
        HELPER.set_master_mode()

        # 処理実行
        with self.assertLogs('send_to_bao.py') as cm:
            send_to_bao.main()

        # ログ内容の確認
        self.assertEqual(cm.output, [
            'INFO:send_to_bao.py:マスターモードのため、マスター動作実行',
            'INFO:send_to_bao.py:KISYSメンテナンス期間に該当しないため処理を継続します。',
            'INFO:send_to_bao.py:処理対象イベント無し。',
            'INFO:send_to_bao.py:10秒待機します。',
        ])

    # @unittest.skip('TESTSKIP')
    @patch('gwcommon.MY_DB', HELPER.MY_DB_REMOTE)
    def test_slave_mode(self):
        # モード設定
        HELPER.set_slave_mode()

        # 処理実行
        with self.assertLogs('send_to_bao.py') as cm:
            send_to_bao.main()

        # ログ内容の確認
        self.assertEqual(cm.output, [
            'INFO:send_to_bao.py:スレーブモードのため、スレーブ動作実行',
        ])

    # @unittest.skip('TESTSKIP')
    @patch('gwcommon.MY_DB', HELPER.MY_DB_LOCAL)
    def test_master_mode_in_kisys_maintenance(self):
        # モード設定
        HELPER.set_master_mode()
        HELPER.insert_maintenance_rule(self.conn)

        # テストデータ投入
        now = datetime.datetime.now()
        one_minute_ago = now - datetime.timedelta(minutes=1)
        test_pattern_name = 'test_master_mode_in_kisys_maintenance'
        insert_hash1 = get_insert_hash(one_minute_ago, gwcommon.GW_ALARM_STATUS_ERROR, test_pattern_name, gwcommon.GW_KISYS_STATUS_KISYS_CONNECT_NORULE)
        insert_hash2 = get_insert_hash(now, gwcommon.GW_ALARM_STATUS_NORMAL, test_pattern_name, gwcommon.GW_KISYS_STATUS_KISYS_CONNECT_NORULE)
        event_ids = insert_event_data(self.conn, [insert_hash1, insert_hash2])
        insert_hash1['error_event_id'] = event_ids[0]
        insert_hash1['normal_event_id'] = event_ids[1]
        insert_hash1['incident_status'] = gwcommon.GW_INCIDENT_STATUS_CLOSE
        insert_incident_data(self.conn, [insert_hash1])

        # 処理実行
        with self.assertLogs('send_to_bao.py') as cm:
            send_to_bao.main()

        # ログ内容の確認
        self.assertEqual(cm.output, [
            'INFO:send_to_bao.py:マスターモードのため、マスター動作実行',
            'INFO:send_to_bao.py:KISYSメンテナンス期間に該当(rule_id = 1)。10秒待機します。',
        ])

        # DB更新結果の確認
        expect_error_event_id = event_ids[0]
        expect_normal_event_id = event_ids[1]
        error_event_result = HELPER.get_updated_gw_events_data(self.conn, expect_error_event_id)
        self.assertEqual(error_event_result['kisys_status'], gwcommon.GW_KISYS_STATUS_KISYS_CONNECT_NORULE)
        normal_event_result = HELPER.get_updated_gw_events_data(self.conn, expect_normal_event_id)
        self.assertEqual(normal_event_result['kisys_status'], gwcommon.GW_KISYS_STATUS_KISYS_CONNECT_NORULE)

    # @unittest.skip('TESTSKIP')
    @patch('gwcommon.MY_DB', HELPER.MY_DB_LOCAL)
    @patch('gwfunction.get_hostgroups_by_host')
    @patch('gwfunction.get_alias_by_host')
    @patch('bao_tm_post.BAO_TM_CLIENT.send')
    def test_master_mode_not_in_kisys_maintenance(self, mock_bao_tm_client_send, mock_get_alias_by_host, mock_get_hostgroups_by_host):
        # モード設定
        HELPER.set_master_mode()
        HELPER.insert_kompira_rule(self.conn)

        # モック準備
        mock_get_hostgroups_by_host.return_value = []
        mock_get_alias_by_host.return_value = ''
        expect_kisys_incidentid = 'IT0000-00000000'
        mock_bao_tm_client_send.return_value = expect_kisys_incidentid # 成功

        # テストデータ投入
        now = datetime.datetime.now()
        one_minute_ago = now - datetime.timedelta(minutes=1)
        test_pattern_name = 'test_master_mode_not_in_kisys_maintenance'
        insert_hash1 = get_insert_hash(one_minute_ago, gwcommon.GW_ALARM_STATUS_ERROR, test_pattern_name, gwcommon.GW_KISYS_STATUS_KISYS_CONNECT_NORULE)
        insert_hash2 = get_insert_hash(now, gwcommon.GW_ALARM_STATUS_NORMAL, test_pattern_name, gwcommon.GW_KISYS_STATUS_KISYS_CONNECT_NORULE)
        event_ids = insert_event_data(self.conn, [insert_hash1, insert_hash2])
        insert_hash1['error_event_id'] = event_ids[0]
        insert_hash1['normal_event_id'] = event_ids[1]
        insert_hash1['incident_status'] = gwcommon.GW_INCIDENT_STATUS_CLOSE
        insert_incident_data(self.conn, [insert_hash1])

        # 処理実行
        with self.assertLogs('send_to_bao.py') as cm:
            send_to_bao.main()

        # ログ内容の確認
        expect_error_event_id = event_ids[0]
        expect_normal_event_id = event_ids[1]
        expect_incident_id = '1'

        self.assertEqual(cm.output, [
            'INFO:send_to_bao.py:マスターモードのため、マスター動作実行',
            'INFO:send_to_bao.py:KISYSメンテナンス期間に該当しないため処理を継続します。',
            'INFO:send_to_bao.py:イベント処理開始(1/2), gw_event_id=%s' % expect_error_event_id,
            'INFO:send_to_bao.py:error報処理開始 gw_event_id=%s' % expect_error_event_id,
            'INFO:send_to_bao.py:error報処理:BAO連携成功 gw_event_id=%s' % expect_error_event_id,
            'INFO:send_to_bao.py:error報処理:関連テーブルを更新しました。gw_event_id=%s, gw_incident_id=%s, kisys_incidentid=%s' % (expect_error_event_id, expect_incident_id, expect_kisys_incidentid),
            'INFO:send_to_bao.py:error報処理:関連テーブルを更新しました。gw_event_id=%s, gw_incident_id=%s, kisys_incidentid=%s' % (expect_error_event_id, expect_incident_id, expect_kisys_incidentid),
            'INFO:send_to_bao.py:Kompira連携しません。kisys_incidentid=%s' % expect_kisys_incidentid,
            'INFO:send_to_bao.py:イベント処理(1/2)終了, gw_event_id=%s' % expect_error_event_id,
            'INFO:send_to_bao.py:イベント処理開始(2/2), gw_event_id=%s' % expect_normal_event_id,
            'INFO:send_to_bao.py:normal報処理開始 gw_event_id=%s' % expect_normal_event_id,
            'INFO:send_to_bao.py:normal報処理:BAO更新成功 gw_event_id=%s, gw_incident_id=%s, kisys_incidentid=%s' % (expect_normal_event_id, expect_incident_id, expect_kisys_incidentid),
            'INFO:send_to_bao.py:normal報処理:関連テーブルを更新しました。gw_event_id=%s, gw_incident_id=%s, kisys_incidentid=%s' % (expect_normal_event_id, expect_incident_id, expect_kisys_incidentid),
            'INFO:send_to_bao.py:Kompira連携しません。kisys_incidentid=%s' % expect_kisys_incidentid,
            'INFO:send_to_bao.py:イベント処理(2/2)終了, gw_event_id=%s' % expect_normal_event_id,
            'INFO:send_to_bao.py:10秒待機します。',
        ])

        # DB更新結果の確認
        expect_kisys_status = gwcommon.GW_KISYS_STATUS_NEW_OK + ',' + gwcommon.KOMPIRA_STATUS_NOSEND
        error_event_result = HELPER.get_updated_gw_events_data(self.conn, expect_error_event_id)
        self.assertEqual(error_event_result['kisys_status'], expect_kisys_status)
        normal_event_result = HELPER.get_updated_gw_events_data(self.conn, expect_normal_event_id)
        self.assertEqual(normal_event_result['kisys_status'], expect_kisys_status)

    # @unittest.skip('TESTSKIP')
    @patch('gwcommon.MY_DB', HELPER.MY_DB_LOCAL)
    @patch('gwfunction.get_hostgroups_by_host')
    @patch('gwfunction.get_alias_by_host')
    @patch('bao_tm_post.BAO_TM_CLIENT.send')
    def test_error_singly_norule_BAO_OK(self, mock_bao_tm_client_send, mock_get_alias_by_host, mock_get_hostgroups_by_host):
        # モード設定
        HELPER.set_master_mode()
        HELPER.insert_kompira_rule(self.conn)

        # モック準備
        mock_get_hostgroups_by_host.return_value = []
        mock_get_alias_by_host.return_value = ''
        expect_kisys_incidentid = 'IT0000-00000000'
        mock_bao_tm_client_send.return_value = expect_kisys_incidentid # 成功

        # テストデータ投入
        now = datetime.datetime.now()
        test_pattern_name = 'test_error_singly_norule_BAO_OK'
        insert_hash1 = get_insert_hash(now, gwcommon.GW_ALARM_STATUS_ERROR, test_pattern_name, gwcommon.GW_KISYS_STATUS_KISYS_CONNECT_NORULE)
        event_ids = insert_event_data(self.conn, [insert_hash1])
        insert_hash1['error_event_id'] = event_ids[0]
        insert_hash1['incident_status'] = gwcommon.GW_INCIDENT_STATUS_ACTIVE
        insert_incident_data(self.conn, [insert_hash1])

        # 処理実行
        with self.assertLogs('send_to_bao.py') as cm:
            send_to_bao.main()

        # ログ内容の確認
        expect_error_event_id = event_ids[0]
        expect_incident_id = '1'

        self.assertEqual(cm.output, [
            'INFO:send_to_bao.py:マスターモードのため、マスター動作実行',
            'INFO:send_to_bao.py:KISYSメンテナンス期間に該当しないため処理を継続します。',
            'INFO:send_to_bao.py:イベント処理開始(1/1), gw_event_id=%s' % expect_error_event_id,
            'INFO:send_to_bao.py:error報処理開始 gw_event_id=%s' % expect_error_event_id,
            'INFO:send_to_bao.py:error報処理:BAO連携成功 gw_event_id=%s' % expect_error_event_id,
            'INFO:send_to_bao.py:error報処理:関連テーブルを更新しました。gw_event_id=%s, gw_incident_id=%s, kisys_incidentid=%s' % (expect_error_event_id, expect_incident_id, expect_kisys_incidentid),
            'INFO:send_to_bao.py:error報処理:関連テーブルを更新しました。gw_event_id=%s, gw_incident_id=%s, kisys_incidentid=%s' % (expect_error_event_id, expect_incident_id, expect_kisys_incidentid),
            'INFO:send_to_bao.py:Kompira連携しません。kisys_incidentid=%s' % expect_kisys_incidentid,
            'INFO:send_to_bao.py:イベント処理(1/1)終了, gw_event_id=%s' % expect_error_event_id,
            'INFO:send_to_bao.py:10秒待機します。',
        ])

        # DB更新結果の確認
        expect_kisys_status = gwcommon.GW_KISYS_STATUS_NEW_OK + ',' + gwcommon.KOMPIRA_STATUS_NOSEND
        error_event_result = HELPER.get_updated_gw_events_data(self.conn, expect_error_event_id)
        self.assertEqual(error_event_result['kisys_status'], expect_kisys_status)

    # @unittest.skip('TESTSKIP')
    @patch('gwcommon.MY_DB', HELPER.MY_DB_LOCAL)
    @patch('gwfunction.get_hostgroups_by_host')
    @patch('gwfunction.get_alias_by_host')
    @patch('bao_tm_post.BAO_TM_CLIENT.send')
    def test_error_singly_norule_BAO_NORES(self, mock_bao_tm_client_send, mock_get_alias_by_host, mock_get_hostgroups_by_host):
        # モード設定
        HELPER.set_master_mode()
        HELPER.insert_kompira_rule(self.conn)

        # モック準備
        mock_get_hostgroups_by_host.return_value = []
        mock_get_alias_by_host.return_value = ''
        mock_bao_tm_client_send.return_value = 'No_reply' # 無応答

        # テストデータ投入
        now = datetime.datetime.now()
        test_pattern_name = 'test_error_singly_norule_BAO_NORES'
        insert_hash1 = get_insert_hash(now, gwcommon.GW_ALARM_STATUS_ERROR, test_pattern_name, gwcommon.GW_KISYS_STATUS_KISYS_CONNECT_NORULE)
        event_ids = insert_event_data(self.conn, [insert_hash1])
        insert_hash1['error_event_id'] = event_ids[0]
        insert_hash1['incident_status'] = gwcommon.GW_INCIDENT_STATUS_ACTIVE
        insert_incident_data(self.conn, [insert_hash1])

        # 処理実行
        with self.assertLogs('send_to_bao.py') as cm:
            send_to_bao.main()

        # ログ内容の確認
        expect_error_event_id = event_ids[0]
        expect_incident_id = '1'
        expect_kisys_incidentid = None

        self.assertEqual(cm.output, [
            'INFO:send_to_bao.py:マスターモードのため、マスター動作実行',
            'INFO:send_to_bao.py:KISYSメンテナンス期間に該当しないため処理を継続します。',
            'INFO:send_to_bao.py:イベント処理開始(1/1), gw_event_id=%s' % expect_error_event_id,
            'INFO:send_to_bao.py:error報処理開始 gw_event_id=%s' % expect_error_event_id,
            'ERROR:send_to_bao.py:error報処理:BAO無応答 gw_event_id=%s' % expect_error_event_id,
            'INFO:send_to_bao.py:error報処理:関連テーブルを更新しました。gw_event_id=%s, gw_incident_id=%s, kisys_incidentid=%s' % (expect_error_event_id, expect_incident_id, expect_kisys_incidentid),
            'INFO:send_to_bao.py:イベント処理(1/1)終了, gw_event_id=%s' % expect_error_event_id,
            'INFO:send_to_bao.py:10秒待機します。',
        ])

        # DB更新結果の確認
        expect_kisys_status = gwcommon.GW_KISYS_STATUS_NEW_NORES
        error_event_result = HELPER.get_updated_gw_events_data(self.conn, expect_error_event_id)
        self.assertEqual(error_event_result['kisys_status'], expect_kisys_status)

    # @unittest.skip('TESTSKIP')
    @patch('gwcommon.MY_DB', HELPER.MY_DB_LOCAL)
    @patch('gwfunction.get_hostgroups_by_host')
    @patch('gwfunction.get_alias_by_host')
    @patch('bao_tm_post.BAO_TM_CLIENT.send')
    def test_error_singly_norule_BAO_NG(self, mock_bao_tm_client_send, mock_get_alias_by_host, mock_get_hostgroups_by_host):
        # モード設定
        HELPER.set_master_mode()
        HELPER.insert_kompira_rule(self.conn)

        # モック準備
        mock_get_hostgroups_by_host.return_value = []
        mock_get_alias_by_host.return_value = ''
        mock_bao_tm_client_send.return_value = 'Failure' # 失敗

        # テストデータ投入
        now = datetime.datetime.now()
        test_pattern_name = 'test_error_singly_norule_BAO_NG'
        insert_hash1 = get_insert_hash(now, gwcommon.GW_ALARM_STATUS_ERROR, test_pattern_name, gwcommon.GW_KISYS_STATUS_KISYS_CONNECT_NORULE)
        event_ids = insert_event_data(self.conn, [insert_hash1])
        insert_hash1['error_event_id'] = event_ids[0]
        insert_hash1['incident_status'] = gwcommon.GW_INCIDENT_STATUS_ACTIVE
        insert_incident_data(self.conn, [insert_hash1])

        # 処理実行
        with self.assertLogs('send_to_bao.py') as cm:
            send_to_bao.main()

        # ログ内容の確認
        expect_error_event_id = event_ids[0]
        expect_incident_id = '1'
        expect_kisys_incidentid = None

        self.assertEqual(cm.output, [
            'INFO:send_to_bao.py:マスターモードのため、マスター動作実行',
            'INFO:send_to_bao.py:KISYSメンテナンス期間に該当しないため処理を継続します。',
            'INFO:send_to_bao.py:イベント処理開始(1/1), gw_event_id=%s' % expect_error_event_id,
            'INFO:send_to_bao.py:error報処理開始 gw_event_id=%s' % expect_error_event_id,
            'ERROR:send_to_bao.py:error報処理:BAO連携失敗 gw_event_id=%s' % expect_error_event_id,
            'INFO:send_to_bao.py:error報処理:関連テーブルを更新しました。gw_event_id=%s, gw_incident_id=%s, kisys_incidentid=%s' % (expect_error_event_id, expect_incident_id, expect_kisys_incidentid),
            'INFO:send_to_bao.py:イベント処理(1/1)終了, gw_event_id=%s' % expect_error_event_id,
            'INFO:send_to_bao.py:10秒待機します。',
        ])

        # DB更新結果の確認
        expect_kisys_status = gwcommon.GW_KISYS_STATUS_NEW_NG
        error_event_result = HELPER.get_updated_gw_events_data(self.conn, expect_error_event_id)
        self.assertEqual(error_event_result['kisys_status'], expect_kisys_status)

    # @unittest.skip('TESTSKIP')
    @patch('gwcommon.MY_DB', HELPER.MY_DB_LOCAL)
    @patch('gwfunction.get_hostgroups_by_host')
    @patch('gwfunction.get_alias_by_host')
    @patch('bao_tm_post.BAO_TM_CLIENT.send')
    def test_error_singly_rule10_BAO_OK(self, mock_bao_tm_client_send, mock_get_alias_by_host, mock_get_hostgroups_by_host):
        # モード設定
        HELPER.set_master_mode()
        HELPER.insert_kompira_rule(self.conn)

        # モック準備
        mock_get_hostgroups_by_host.return_value = []
        mock_get_alias_by_host.return_value = ''
        expect_kisys_incidentid = 'IT0000-00000000'
        mock_bao_tm_client_send.return_value = expect_kisys_incidentid # 成功

        # テストデータ投入
        now = datetime.datetime.now()
        test_pattern_name = 'test_error_singly_rule10_BAO_OK'
        insert_hash1 = get_insert_hash(now, gwcommon.GW_ALARM_STATUS_ERROR, test_pattern_name, gwcommon.GW_KISYS_STATUS_NOSEND_MANUAL)
        event_ids = insert_event_data(self.conn, [insert_hash1])
        insert_hash1['error_event_id'] = event_ids[0]
        insert_hash1['incident_status'] = gwcommon.GW_INCIDENT_STATUS_ACTIVE
        insert_incident_data(self.conn, [insert_hash1])
        HELPER.insert_test_rule(self.conn, gwcommon.GW_KISYS_STATUS_NOSEND, test_pattern_name)

        # 処理実行
        with self.assertLogs('send_to_bao.py') as cm:
            send_to_bao.main()

        # ログ内容の確認
        expect_error_event_id = event_ids[0]
        expect_incident_id = '1'

        self.assertEqual(cm.output, [
            'INFO:send_to_bao.py:マスターモードのため、マスター動作実行',
            'INFO:send_to_bao.py:KISYSメンテナンス期間に該当しないため処理を継続します。',
            'INFO:send_to_bao.py:イベント処理開始(1/1), gw_event_id=%s' % expect_error_event_id,
            'INFO:send_to_bao.py:error報処理開始 gw_event_id=%s' % expect_error_event_id,
            'INFO:send_to_bao.py:error報処理:BAO連携成功 gw_event_id=%s' % expect_error_event_id,
            'INFO:send_to_bao.py:error報処理:関連テーブルを更新しました。gw_event_id=%s, gw_incident_id=%s, kisys_incidentid=%s' % (expect_error_event_id, expect_incident_id, expect_kisys_incidentid),
            'INFO:send_to_bao.py:error報処理:関連テーブルを更新しました。gw_event_id=%s, gw_incident_id=%s, kisys_incidentid=%s' % (expect_error_event_id, expect_incident_id, expect_kisys_incidentid),
            'INFO:send_to_bao.py:Kompira連携しません。kisys_incidentid=%s' % expect_kisys_incidentid,
            'INFO:send_to_bao.py:イベント処理(1/1)終了, gw_event_id=%s' % expect_error_event_id,
            'INFO:send_to_bao.py:10秒待機します。',
        ])

        # DB更新結果の確認
        expect_kisys_status = gwcommon.GW_KISYS_STATUS_NOSEND_OK + ',' + gwcommon.KOMPIRA_STATUS_NOSEND
        error_event_result = HELPER.get_updated_gw_events_data(self.conn, expect_error_event_id)
        self.assertEqual(error_event_result['kisys_status'], expect_kisys_status)

    # @unittest.skip('TESTSKIP')
    @patch('gwcommon.MY_DB', HELPER.MY_DB_LOCAL)
    @patch('gwfunction.get_hostgroups_by_host')
    @patch('gwfunction.get_alias_by_host')
    @patch('bao_tm_post.BAO_TM_CLIENT.send')
    def test_error_singly_rule10_BAO_NORES(self, mock_bao_tm_client_send, mock_get_alias_by_host, mock_get_hostgroups_by_host):
        # モード設定
        HELPER.set_master_mode()
        HELPER.insert_kompira_rule(self.conn)

        # モック準備
        mock_get_hostgroups_by_host.return_value = []
        mock_get_alias_by_host.return_value = ''
        mock_bao_tm_client_send.return_value = 'No_reply' # 無応答

        # テストデータ投入
        now = datetime.datetime.now()
        test_pattern_name = 'test_error_singly_rule10_BAO_NORES'
        insert_hash1 = get_insert_hash(now, gwcommon.GW_ALARM_STATUS_ERROR, test_pattern_name, gwcommon.GW_KISYS_STATUS_NOSEND_MANUAL)
        event_ids = insert_event_data(self.conn, [insert_hash1])
        insert_hash1['error_event_id'] = event_ids[0]
        insert_hash1['incident_status'] = gwcommon.GW_INCIDENT_STATUS_ACTIVE
        insert_incident_data(self.conn, [insert_hash1])
        HELPER.insert_test_rule(self.conn, gwcommon.GW_KISYS_STATUS_NOSEND, test_pattern_name)

        # 処理実行
        with self.assertLogs('send_to_bao.py') as cm:
            send_to_bao.main()

        # ログ内容の確認
        expect_error_event_id = event_ids[0]
        expect_incident_id = '1'
        expect_kisys_incidentid = None

        self.assertEqual(cm.output, [
            'INFO:send_to_bao.py:マスターモードのため、マスター動作実行',
            'INFO:send_to_bao.py:KISYSメンテナンス期間に該当しないため処理を継続します。',
            'INFO:send_to_bao.py:イベント処理開始(1/1), gw_event_id=%s' % expect_error_event_id,
            'INFO:send_to_bao.py:error報処理開始 gw_event_id=%s' % expect_error_event_id,
            'ERROR:send_to_bao.py:error報処理:BAO無応答 gw_event_id=%s' % expect_error_event_id,
            'INFO:send_to_bao.py:error報処理:関連テーブルを更新しました。gw_event_id=%s, gw_incident_id=%s, kisys_incidentid=%s' % (expect_error_event_id, expect_incident_id, expect_kisys_incidentid),
            'INFO:send_to_bao.py:イベント処理(1/1)終了, gw_event_id=%s' % expect_error_event_id,
            'INFO:send_to_bao.py:10秒待機します。',
        ])

        # DB更新結果の確認
        expect_kisys_status = gwcommon.GW_KISYS_STATUS_NOSEND_NORES
        error_event_result = HELPER.get_updated_gw_events_data(self.conn, expect_error_event_id)
        self.assertEqual(error_event_result['kisys_status'], expect_kisys_status)

    # @unittest.skip('TESTSKIP')
    @patch('gwcommon.MY_DB', HELPER.MY_DB_LOCAL)
    @patch('gwfunction.get_hostgroups_by_host')
    @patch('gwfunction.get_alias_by_host')
    @patch('bao_tm_post.BAO_TM_CLIENT.send')
    def test_error_singly_rule10_BAO_NG(self, mock_bao_tm_client_send, mock_get_alias_by_host, mock_get_hostgroups_by_host):
        # モード設定
        HELPER.set_master_mode()
        HELPER.insert_kompira_rule(self.conn)

        # モック準備
        mock_get_hostgroups_by_host.return_value = []
        mock_get_alias_by_host.return_value = ''
        mock_bao_tm_client_send.return_value = 'Failure' # 失敗

        # テストデータ投入
        now = datetime.datetime.now()
        test_pattern_name = 'test_error_singly_rule10_BAO_NG'
        insert_hash1 = get_insert_hash(now, gwcommon.GW_ALARM_STATUS_ERROR, test_pattern_name, gwcommon.GW_KISYS_STATUS_NOSEND_MANUAL)
        event_ids = insert_event_data(self.conn, [insert_hash1])
        insert_hash1['error_event_id'] = event_ids[0]
        insert_hash1['incident_status'] = gwcommon.GW_INCIDENT_STATUS_ACTIVE
        insert_incident_data(self.conn, [insert_hash1])
        HELPER.insert_test_rule(self.conn, gwcommon.GW_KISYS_STATUS_NOSEND, test_pattern_name)

        # 処理実行
        with self.assertLogs('send_to_bao.py') as cm:
            send_to_bao.main()

        # ログ内容の確認
        expect_error_event_id = event_ids[0]
        expect_incident_id = '1'
        expect_kisys_incidentid = None

        self.assertEqual(cm.output, [
            'INFO:send_to_bao.py:マスターモードのため、マスター動作実行',
            'INFO:send_to_bao.py:KISYSメンテナンス期間に該当しないため処理を継続します。',
            'INFO:send_to_bao.py:イベント処理開始(1/1), gw_event_id=%s' % expect_error_event_id,
            'INFO:send_to_bao.py:error報処理開始 gw_event_id=%s' % expect_error_event_id,
            'ERROR:send_to_bao.py:error報処理:BAO連携失敗 gw_event_id=%s' % expect_error_event_id,
            'INFO:send_to_bao.py:error報処理:関連テーブルを更新しました。gw_event_id=%s, gw_incident_id=%s, kisys_incidentid=%s' % (expect_error_event_id, expect_incident_id, expect_kisys_incidentid),
            'INFO:send_to_bao.py:イベント処理(1/1)終了, gw_event_id=%s' % expect_error_event_id,
            'INFO:send_to_bao.py:10秒待機します。',
        ])

        # DB更新結果の確認
        expect_kisys_status = gwcommon.GW_KISYS_STATUS_NOSEND_NG
        error_event_result = HELPER.get_updated_gw_events_data(self.conn, expect_error_event_id)
        self.assertEqual(error_event_result['kisys_status'], expect_kisys_status)

    # @unittest.skip('TESTSKIP')
    @patch('gwcommon.MY_DB', HELPER.MY_DB_LOCAL)
    @patch('gwfunction.get_hostgroups_by_host')
    @patch('gwfunction.get_alias_by_host')
    @patch('bao_tm_post.BAO_TM_CLIENT.send')
    def test_error_singly_rule20_BAO_OK(self, mock_bao_tm_client_send, mock_get_alias_by_host, mock_get_hostgroups_by_host):
        # モード設定
        HELPER.set_master_mode()
        HELPER.insert_kompira_rule(self.conn)

        # モック準備
        mock_get_hostgroups_by_host.return_value = []
        mock_get_alias_by_host.return_value = ''
        expect_kisys_incidentid = 'IT0000-00000000'
        mock_bao_tm_client_send.return_value = expect_kisys_incidentid # 成功

        # テストデータ投入
        now = datetime.datetime.now()
        test_pattern_name = 'test_error_singly_rule20_BAO_OK'
        insert_hash1 = get_insert_hash(now, gwcommon.GW_ALARM_STATUS_ERROR, test_pattern_name, gwcommon.GW_KISYS_STATUS_NOPATOLAMP_MANUAL)
        event_ids = insert_event_data(self.conn, [insert_hash1])
        insert_hash1['error_event_id'] = event_ids[0]
        insert_hash1['incident_status'] = gwcommon.GW_INCIDENT_STATUS_ACTIVE
        insert_incident_data(self.conn, [insert_hash1])
        HELPER.insert_test_rule(self.conn, gwcommon.GW_KISYS_STATUS_NOPATOLAMP, test_pattern_name)

        # 処理実行
        with self.assertLogs('send_to_bao.py') as cm:
            send_to_bao.main()

        # ログ内容の確認
        expect_error_event_id = event_ids[0]
        expect_incident_id = '1'

        self.assertEqual(cm.output, [
            'INFO:send_to_bao.py:マスターモードのため、マスター動作実行',
            'INFO:send_to_bao.py:KISYSメンテナンス期間に該当しないため処理を継続します。',
            'INFO:send_to_bao.py:イベント処理開始(1/1), gw_event_id=%s' % expect_error_event_id,
            'INFO:send_to_bao.py:error報処理開始 gw_event_id=%s' % expect_error_event_id,
            'INFO:send_to_bao.py:error報処理:BAO連携成功 gw_event_id=%s' % expect_error_event_id,
            'INFO:send_to_bao.py:error報処理:関連テーブルを更新しました。gw_event_id=%s, gw_incident_id=%s, kisys_incidentid=%s' % (expect_error_event_id, expect_incident_id, expect_kisys_incidentid),
            'INFO:send_to_bao.py:error報処理:関連テーブルを更新しました。gw_event_id=%s, gw_incident_id=%s, kisys_incidentid=%s' % (expect_error_event_id, expect_incident_id, expect_kisys_incidentid),
            'INFO:send_to_bao.py:Kompira連携しません。kisys_incidentid=%s' % expect_kisys_incidentid,
            'INFO:send_to_bao.py:イベント処理(1/1)終了, gw_event_id=%s' % expect_error_event_id,
            'INFO:send_to_bao.py:10秒待機します。',
        ])

        # DB更新結果の確認
        expect_kisys_status = gwcommon.GW_KISYS_STATUS_NOPATOLAMP_OK + ',' + gwcommon.KOMPIRA_STATUS_NOSEND
        error_event_result = HELPER.get_updated_gw_events_data(self.conn, expect_error_event_id)
        self.assertEqual(error_event_result['kisys_status'], expect_kisys_status)

    # @unittest.skip('TESTSKIP')
    @patch('gwcommon.MY_DB', HELPER.MY_DB_LOCAL)
    @patch('gwfunction.get_hostgroups_by_host')
    @patch('gwfunction.get_alias_by_host')
    @patch('bao_tm_post.BAO_TM_CLIENT.send')
    def test_error_singly_rule20_BAO_NORES(self, mock_bao_tm_client_send, mock_get_alias_by_host, mock_get_hostgroups_by_host):
        # モード設定
        HELPER.set_master_mode()
        HELPER.insert_kompira_rule(self.conn)

        # モック準備
        mock_get_hostgroups_by_host.return_value = []
        mock_get_alias_by_host.return_value = ''
        mock_bao_tm_client_send.return_value = 'No_reply' # 無応答

        # テストデータ投入
        now = datetime.datetime.now()
        test_pattern_name = 'test_error_singly_rule20_BAO_NORES'
        insert_hash1 = get_insert_hash(now, gwcommon.GW_ALARM_STATUS_ERROR, test_pattern_name, gwcommon.GW_KISYS_STATUS_NOPATOLAMP_MANUAL)
        event_ids = insert_event_data(self.conn, [insert_hash1])
        insert_hash1['error_event_id'] = event_ids[0]
        insert_hash1['incident_status'] = gwcommon.GW_INCIDENT_STATUS_ACTIVE
        insert_incident_data(self.conn, [insert_hash1])
        HELPER.insert_test_rule(self.conn, gwcommon.GW_KISYS_STATUS_NOPATOLAMP, test_pattern_name)

        # 処理実行
        with self.assertLogs('send_to_bao.py') as cm:
            send_to_bao.main()

        # ログ内容の確認
        expect_error_event_id = event_ids[0]
        expect_incident_id = '1'
        expect_kisys_incidentid = None

        self.assertEqual(cm.output, [
            'INFO:send_to_bao.py:マスターモードのため、マスター動作実行',
            'INFO:send_to_bao.py:KISYSメンテナンス期間に該当しないため処理を継続します。',
            'INFO:send_to_bao.py:イベント処理開始(1/1), gw_event_id=%s' % expect_error_event_id,
            'INFO:send_to_bao.py:error報処理開始 gw_event_id=%s' % expect_error_event_id,
            'ERROR:send_to_bao.py:error報処理:BAO無応答 gw_event_id=%s' % expect_error_event_id,
            'INFO:send_to_bao.py:error報処理:関連テーブルを更新しました。gw_event_id=%s, gw_incident_id=%s, kisys_incidentid=%s' % (expect_error_event_id, expect_incident_id, expect_kisys_incidentid),
            'INFO:send_to_bao.py:イベント処理(1/1)終了, gw_event_id=%s' % expect_error_event_id,
            'INFO:send_to_bao.py:10秒待機します。',
        ])

        # DB更新結果の確認
        expect_kisys_status = gwcommon.GW_KISYS_STATUS_NOPATOLAMP_NORES
        error_event_result = HELPER.get_updated_gw_events_data(self.conn, expect_error_event_id)
        self.assertEqual(error_event_result['kisys_status'], expect_kisys_status)

    # @unittest.skip('TESTSKIP')
    @patch('gwcommon.MY_DB', HELPER.MY_DB_LOCAL)
    @patch('gwfunction.get_hostgroups_by_host')
    @patch('gwfunction.get_alias_by_host')
    @patch('bao_tm_post.BAO_TM_CLIENT.send')
    def test_error_singly_rule20_BAO_NG(self, mock_bao_tm_client_send, mock_get_alias_by_host, mock_get_hostgroups_by_host):
        # モード設定
        HELPER.set_master_mode()
        HELPER.insert_kompira_rule(self.conn)

        # モック準備
        mock_get_hostgroups_by_host.return_value = []
        mock_get_alias_by_host.return_value = ''
        mock_bao_tm_client_send.return_value = 'Failure' # 失敗

        # テストデータ投入
        now = datetime.datetime.now()
        test_pattern_name = 'test_error_singly_rule20_BAO_NG'
        insert_hash1 = get_insert_hash(now, gwcommon.GW_ALARM_STATUS_ERROR, test_pattern_name, gwcommon.GW_KISYS_STATUS_NOPATOLAMP_MANUAL)
        event_ids = insert_event_data(self.conn, [insert_hash1])
        insert_hash1['error_event_id'] = event_ids[0]
        insert_hash1['incident_status'] = gwcommon.GW_INCIDENT_STATUS_ACTIVE
        insert_incident_data(self.conn, [insert_hash1])
        HELPER.insert_test_rule(self.conn, gwcommon.GW_KISYS_STATUS_NOPATOLAMP, test_pattern_name)

        # 処理実行
        with self.assertLogs('send_to_bao.py') as cm:
            send_to_bao.main()

        # ログ内容の確認
        expect_error_event_id = event_ids[0]
        expect_incident_id = '1'
        expect_kisys_incidentid = None

        self.assertEqual(cm.output, [
            'INFO:send_to_bao.py:マスターモードのため、マスター動作実行',
            'INFO:send_to_bao.py:KISYSメンテナンス期間に該当しないため処理を継続します。',
            'INFO:send_to_bao.py:イベント処理開始(1/1), gw_event_id=%s' % expect_error_event_id,
            'INFO:send_to_bao.py:error報処理開始 gw_event_id=%s' % expect_error_event_id,
            'ERROR:send_to_bao.py:error報処理:BAO連携失敗 gw_event_id=%s' % expect_error_event_id,
            'INFO:send_to_bao.py:error報処理:関連テーブルを更新しました。gw_event_id=%s, gw_incident_id=%s, kisys_incidentid=%s' % (expect_error_event_id, expect_incident_id, expect_kisys_incidentid),
            'INFO:send_to_bao.py:イベント処理(1/1)終了, gw_event_id=%s' % expect_error_event_id,
            'INFO:send_to_bao.py:10秒待機します。',
        ])

        # DB更新結果の確認
        expect_kisys_status = gwcommon.GW_KISYS_STATUS_NOPATOLAMP_NG
        error_event_result = HELPER.get_updated_gw_events_data(self.conn, expect_error_event_id)
        self.assertEqual(error_event_result['kisys_status'], expect_kisys_status)

    # @unittest.skip('TESTSKIP')
    @patch('gwcommon.MY_DB', HELPER.MY_DB_LOCAL)
    @patch('gwfunction.get_hostgroups_by_host')
    @patch('gwfunction.get_alias_by_host')
    @patch('bao_tm_post.BAO_TM_CLIENT.send')
    def test_error_singly_rule30_BAO_OK(self, mock_bao_tm_client_send, mock_get_alias_by_host, mock_get_hostgroups_by_host):
        # モード設定
        HELPER.set_master_mode()
        HELPER.insert_kompira_rule(self.conn)

        # モック準備
        mock_get_hostgroups_by_host.return_value = []
        mock_get_alias_by_host.return_value = ''
        expect_kisys_incidentid = 'IT0000-00000000'
        mock_bao_tm_client_send.return_value = expect_kisys_incidentid # 成功

        # テストデータ投入
        now = datetime.datetime.now()
        yesterday = now - datetime.timedelta(days=1)
        test_pattern_name = 'test_error_singly_rule30_BAO_OK'
        insert_hash1 = get_insert_hash(yesterday, gwcommon.GW_ALARM_STATUS_ERROR, test_pattern_name, gwcommon.GW_KISYS_STATUS_KISYS_CONNECT_NORECOVERY)
        event_ids = insert_event_data(self.conn, [insert_hash1])
        insert_hash1['error_event_id'] = event_ids[0]
        insert_hash1['incident_status'] = gwcommon.GW_INCIDENT_STATUS_ACTIVE
        insert_incident_data(self.conn, [insert_hash1])
        HELPER.insert_test_rule(self.conn, gwcommon.GW_KISYS_STATUS_WAITING_5, test_pattern_name)

        # 処理実行
        with self.assertLogs('send_to_bao.py') as cm:
            send_to_bao.main()

        # ログ内容の確認
        expect_error_event_id = event_ids[0]
        expect_incident_id = '1'

        self.assertEqual(cm.output, [
            'INFO:send_to_bao.py:マスターモードのため、マスター動作実行',
            'INFO:send_to_bao.py:KISYSメンテナンス期間に該当しないため処理を継続します。',
            'INFO:send_to_bao.py:イベント処理開始(1/1), gw_event_id=%s' % expect_error_event_id,
            'INFO:send_to_bao.py:error報処理開始 gw_event_id=%s' % expect_error_event_id,
            'INFO:send_to_bao.py:error報処理:BAO連携成功 gw_event_id=%s' % expect_error_event_id,
            'INFO:send_to_bao.py:error報処理:関連テーブルを更新しました。gw_event_id=%s, gw_incident_id=%s, kisys_incidentid=%s' % (expect_error_event_id, expect_incident_id, expect_kisys_incidentid),
            'INFO:send_to_bao.py:error報処理:関連テーブルを更新しました。gw_event_id=%s, gw_incident_id=%s, kisys_incidentid=%s' % (expect_error_event_id, expect_incident_id, expect_kisys_incidentid),
            'INFO:send_to_bao.py:Kompira連携しません。kisys_incidentid=%s' % expect_kisys_incidentid,
            'INFO:send_to_bao.py:イベント処理(1/1)終了, gw_event_id=%s' % expect_error_event_id,
            'INFO:send_to_bao.py:10秒待機します。',
        ])

        # DB更新結果の確認
        expect_kisys_status = gwcommon.GW_KISYS_STATUS_NORECOVERY_OK + ',' + gwcommon.KOMPIRA_STATUS_NOSEND
        error_event_result = HELPER.get_updated_gw_events_data(self.conn, expect_error_event_id)
        self.assertEqual(error_event_result['kisys_status'], expect_kisys_status)

    # @unittest.skip('TESTSKIP')
    @patch('gwcommon.MY_DB', HELPER.MY_DB_LOCAL)
    @patch('gwfunction.get_hostgroups_by_host')
    @patch('gwfunction.get_alias_by_host')
    @patch('bao_tm_post.BAO_TM_CLIENT.send')
    def test_error_singly_rule30_BAO_NORES(self, mock_bao_tm_client_send, mock_get_alias_by_host, mock_get_hostgroups_by_host):
        # モード設定
        HELPER.set_master_mode()
        HELPER.insert_kompira_rule(self.conn)

        # モック準備
        mock_get_hostgroups_by_host.return_value = []
        mock_get_alias_by_host.return_value = ''
        mock_bao_tm_client_send.return_value = 'No_reply' # 無応答

        # テストデータ投入
        now = datetime.datetime.now()
        yesterday = now - datetime.timedelta(days=1)
        test_pattern_name = 'test_error_singly_rule30_BAO_NORES'
        insert_hash1 = get_insert_hash(yesterday, gwcommon.GW_ALARM_STATUS_ERROR, test_pattern_name, gwcommon.GW_KISYS_STATUS_KISYS_CONNECT_NORECOVERY)
        event_ids = insert_event_data(self.conn, [insert_hash1])
        insert_hash1['error_event_id'] = event_ids[0]
        insert_hash1['incident_status'] = gwcommon.GW_INCIDENT_STATUS_ACTIVE
        insert_incident_data(self.conn, [insert_hash1])
        HELPER.insert_test_rule(self.conn, gwcommon.GW_KISYS_STATUS_WAITING_5, test_pattern_name)

        # 処理実行
        with self.assertLogs('send_to_bao.py') as cm:
            send_to_bao.main()

        # ログ内容の確認
        expect_error_event_id = event_ids[0]
        expect_incident_id = '1'
        expect_kisys_incidentid = None

        self.assertEqual(cm.output, [
            'INFO:send_to_bao.py:マスターモードのため、マスター動作実行',
            'INFO:send_to_bao.py:KISYSメンテナンス期間に該当しないため処理を継続します。',
            'INFO:send_to_bao.py:イベント処理開始(1/1), gw_event_id=%s' % expect_error_event_id,
            'INFO:send_to_bao.py:error報処理開始 gw_event_id=%s' % expect_error_event_id,
            'ERROR:send_to_bao.py:error報処理:BAO無応答 gw_event_id=%s' % expect_error_event_id,
            'INFO:send_to_bao.py:error報処理:関連テーブルを更新しました。gw_event_id=%s, gw_incident_id=%s, kisys_incidentid=%s' % (expect_error_event_id, expect_incident_id, expect_kisys_incidentid),
            'INFO:send_to_bao.py:イベント処理(1/1)終了, gw_event_id=%s' % expect_error_event_id,
            'INFO:send_to_bao.py:10秒待機します。',
        ])

        # DB更新結果の確認
        expect_kisys_status = gwcommon.GW_KISYS_STATUS_NORECOVERY_NORES
        error_event_result = HELPER.get_updated_gw_events_data(self.conn, expect_error_event_id)
        self.assertEqual(error_event_result['kisys_status'], expect_kisys_status)

    # @unittest.skip('TESTSKIP')
    @patch('gwcommon.MY_DB', HELPER.MY_DB_LOCAL)
    @patch('gwfunction.get_hostgroups_by_host')
    @patch('gwfunction.get_alias_by_host')
    @patch('bao_tm_post.BAO_TM_CLIENT.send')
    def test_error_singly_rule30_BAO_NG(self, mock_bao_tm_client_send, mock_get_alias_by_host, mock_get_hostgroups_by_host):
        # モード設定
        HELPER.set_master_mode()
        HELPER.insert_kompira_rule(self.conn)

        # モック準備
        mock_get_hostgroups_by_host.return_value = []
        mock_get_alias_by_host.return_value = ''
        mock_bao_tm_client_send.return_value = 'Failure' # 失敗

        # テストデータ投入
        now = datetime.datetime.now()
        yesterday = now - datetime.timedelta(days=1)
        test_pattern_name = 'test_error_singly_rule30_BAO_NG'
        insert_hash1 = get_insert_hash(yesterday, gwcommon.GW_ALARM_STATUS_ERROR, test_pattern_name, gwcommon.GW_KISYS_STATUS_KISYS_CONNECT_NORECOVERY)
        event_ids = insert_event_data(self.conn, [insert_hash1])
        insert_hash1['error_event_id'] = event_ids[0]
        insert_hash1['incident_status'] = gwcommon.GW_INCIDENT_STATUS_ACTIVE
        insert_incident_data(self.conn, [insert_hash1])
        HELPER.insert_test_rule(self.conn, gwcommon.GW_KISYS_STATUS_WAITING_5, test_pattern_name)

        # 処理実行
        with self.assertLogs('send_to_bao.py') as cm:
            send_to_bao.main()

        # ログ内容の確認
        expect_error_event_id = event_ids[0]
        expect_incident_id = '1'
        expect_kisys_incidentid = None

        self.assertEqual(cm.output, [
            'INFO:send_to_bao.py:マスターモードのため、マスター動作実行',
            'INFO:send_to_bao.py:KISYSメンテナンス期間に該当しないため処理を継続します。',
            'INFO:send_to_bao.py:イベント処理開始(1/1), gw_event_id=%s' % expect_error_event_id,
            'INFO:send_to_bao.py:error報処理開始 gw_event_id=%s' % expect_error_event_id,
            'ERROR:send_to_bao.py:error報処理:BAO連携失敗 gw_event_id=%s' % expect_error_event_id,
            'INFO:send_to_bao.py:error報処理:関連テーブルを更新しました。gw_event_id=%s, gw_incident_id=%s, kisys_incidentid=%s' % (expect_error_event_id, expect_incident_id, expect_kisys_incidentid),
            'INFO:send_to_bao.py:イベント処理(1/1)終了, gw_event_id=%s' % expect_error_event_id,
            'INFO:send_to_bao.py:10秒待機します。',
        ])

        # DB更新結果の確認
        expect_kisys_status = gwcommon.GW_KISYS_STATUS_NORECOVERY_NG
        error_event_result = HELPER.get_updated_gw_events_data(self.conn, expect_error_event_id)
        self.assertEqual(error_event_result['kisys_status'], expect_kisys_status)

    # @unittest.skip('TESTSKIP')
    @patch('gwcommon.MY_DB', HELPER.MY_DB_LOCAL)
    def test_normal_singly_norule_BAO_NOSEND(self):
        # モード設定
        HELPER.set_master_mode()
        HELPER.insert_kompira_rule(self.conn)

        # テストデータ投入
        now = datetime.datetime.now()
        test_pattern_name = 'test_normal_singly_norule_BAO_NOSEND'
        insert_hash1 = get_insert_hash(now, gwcommon.GW_ALARM_STATUS_NORMAL, test_pattern_name, None)
        event_ids = insert_event_data(self.conn, [insert_hash1])
        insert_hash1['normal_event_id'] = event_ids[0]
        insert_hash1['incident_status'] = gwcommon.GW_INCIDENT_STATUS_CLOSE
        insert_incident_data(self.conn, [insert_hash1])

        # 処理実行
        with self.assertLogs('send_to_bao.py') as cm:
            send_to_bao.main()

        # ログ内容の確認
        self.assertEqual(cm.output, [
            'INFO:send_to_bao.py:マスターモードのため、マスター動作実行',
            'INFO:send_to_bao.py:KISYSメンテナンス期間に該当しないため処理を継続します。',
            'INFO:send_to_bao.py:処理対象イベント無し。',
            'INFO:send_to_bao.py:10秒待機します。',
        ])

        # DB更新結果の確認
        expect_normal_event_id = event_ids[0]
        expect_kisys_status = None
        normal_event_result = HELPER.get_updated_gw_events_data(self.conn, expect_normal_event_id)
        self.assertEqual(normal_event_result['kisys_status'], expect_kisys_status)

    # @unittest.skip('TESTSKIP')
    @patch('gwcommon.MY_DB', HELPER.MY_DB_LOCAL)
    @patch('gwfunction.get_hostgroups_by_host')
    @patch('gwfunction.get_alias_by_host')
    @patch('bao_tm_post.BAO_TM_CLIENT.send')
    def test_error_normal_paired_norule_BAO_OK(self, mock_bao_tm_client_send, mock_get_alias_by_host, mock_get_hostgroups_by_host):
        # モード設定
        HELPER.set_master_mode()
        HELPER.insert_kompira_rule(self.conn)

        # モック準備
        mock_get_hostgroups_by_host.return_value = []
        mock_get_alias_by_host.return_value = ''
        expect_kisys_incidentid = 'IT0000-00000000'
        mock_bao_tm_client_send.return_value = expect_kisys_incidentid # 成功

        # テストデータ投入
        now = datetime.datetime.now()
        one_minute_ago = now - datetime.timedelta(minutes=1)
        test_pattern_name = 'test_error_normal_paired_norule_BAO_OK'
        insert_hash1 = get_insert_hash(one_minute_ago, gwcommon.GW_ALARM_STATUS_ERROR, test_pattern_name, gwcommon.GW_KISYS_STATUS_NEW_OK)
        insert_hash2 = get_insert_hash(now, gwcommon.GW_ALARM_STATUS_NORMAL, test_pattern_name, gwcommon.GW_KISYS_STATUS_KISYS_CONNECT_NORULE)
        event_ids = insert_event_data(self.conn, [insert_hash1, insert_hash2])
        insert_hash1['error_event_id'] = event_ids[0]
        insert_hash1['normal_event_id'] = event_ids[1]
        insert_hash1['incident_status'] = gwcommon.GW_INCIDENT_STATUS_CLOSE
        insert_incident_data(self.conn, [insert_hash1])
        expect_incident_id = '1'
        expect_kisys_incidentid = 'IT0000-00000000'
        update_gw_incident_data(self.conn, expect_incident_id, expect_kisys_incidentid)

        # 処理実行
        with self.assertLogs('send_to_bao.py') as cm:
            send_to_bao.main()

        # ログ内容の確認
        expect_error_event_id = event_ids[0]
        expect_normal_event_id = event_ids[1]

        self.assertEqual(cm.output, [
            'INFO:send_to_bao.py:マスターモードのため、マスター動作実行',
            'INFO:send_to_bao.py:KISYSメンテナンス期間に該当しないため処理を継続します。',
            'INFO:send_to_bao.py:イベント処理開始(1/1), gw_event_id=%s' % expect_normal_event_id,
            'INFO:send_to_bao.py:normal報処理開始 gw_event_id=%s' % expect_normal_event_id,
            'INFO:send_to_bao.py:normal報処理:BAO更新成功 gw_event_id=%s, gw_incident_id=%s, kisys_incidentid=%s' % (expect_normal_event_id, expect_incident_id, expect_kisys_incidentid),
            'INFO:send_to_bao.py:normal報処理:関連テーブルを更新しました。gw_event_id=%s, gw_incident_id=%s, kisys_incidentid=%s' % (expect_normal_event_id, expect_incident_id, expect_kisys_incidentid),
            'INFO:send_to_bao.py:Kompira連携しません。kisys_incidentid=%s' % expect_kisys_incidentid,
            'INFO:send_to_bao.py:イベント処理(1/1)終了, gw_event_id=%s' % expect_normal_event_id,
            'INFO:send_to_bao.py:10秒待機します。',
        ])

        # DB更新結果の確認
        expect_kisys_status = gwcommon.GW_KISYS_STATUS_NEW_OK + ',' + gwcommon.KOMPIRA_STATUS_NOSEND
        error_event_result = HELPER.get_updated_gw_events_data(self.conn, expect_error_event_id)
        self.assertEqual(error_event_result['kisys_status'], gwcommon.GW_KISYS_STATUS_NEW_OK)
        normal_event_result = HELPER.get_updated_gw_events_data(self.conn, expect_normal_event_id)
        self.assertEqual(normal_event_result['kisys_status'], expect_kisys_status)

    # @unittest.skip('TESTSKIP')
    @patch('gwcommon.MY_DB', HELPER.MY_DB_LOCAL)
    @patch('gwfunction.get_hostgroups_by_host')
    @patch('gwfunction.get_alias_by_host')
    @patch('bao_tm_post.BAO_TM_CLIENT.send')
    def test_error_normal_paired_norule_BAO_NORES(self, mock_bao_tm_client_send, mock_get_alias_by_host, mock_get_hostgroups_by_host):
        # モード設定
        HELPER.set_master_mode()
        HELPER.insert_kompira_rule(self.conn)

        # モック準備
        mock_get_hostgroups_by_host.return_value = []
        mock_get_alias_by_host.return_value = ''
        mock_bao_tm_client_send.return_value = 'No_reply' # 無応答

        # テストデータ投入
        now = datetime.datetime.now()
        one_minute_ago = now - datetime.timedelta(minutes=1)
        test_pattern_name = 'test_error_normal_paired_norule_BAO_NORES'
        insert_hash1 = get_insert_hash(one_minute_ago, gwcommon.GW_ALARM_STATUS_ERROR, test_pattern_name, gwcommon.GW_KISYS_STATUS_NEW_OK)
        insert_hash2 = get_insert_hash(now, gwcommon.GW_ALARM_STATUS_NORMAL, test_pattern_name, gwcommon.GW_KISYS_STATUS_KISYS_CONNECT_NORULE)
        event_ids = insert_event_data(self.conn, [insert_hash1, insert_hash2])
        insert_hash1['error_event_id'] = event_ids[0]
        insert_hash1['normal_event_id'] = event_ids[1]
        insert_hash1['incident_status'] = gwcommon.GW_INCIDENT_STATUS_CLOSE
        insert_incident_data(self.conn, [insert_hash1])
        expect_incident_id = '1'
        expect_kisys_incidentid = 'IT0000-00000000'
        update_gw_incident_data(self.conn, expect_incident_id, expect_kisys_incidentid)

        # 処理実行
        with self.assertLogs('send_to_bao.py') as cm:
            send_to_bao.main()

        # ログ内容の確認
        expect_error_event_id = event_ids[0]
        expect_normal_event_id = event_ids[1]

        self.assertEqual(cm.output, [
            'INFO:send_to_bao.py:マスターモードのため、マスター動作実行',
            'INFO:send_to_bao.py:KISYSメンテナンス期間に該当しないため処理を継続します。',
            'INFO:send_to_bao.py:イベント処理開始(1/1), gw_event_id=%s' % expect_normal_event_id,
            'INFO:send_to_bao.py:normal報処理開始 gw_event_id=%s' % expect_normal_event_id,
            'ERROR:send_to_bao.py:normal報処理:BAO無応答 gw_event_id=%s, gw_incident_id=%s, kisys_incidentid=%s' % (expect_normal_event_id, expect_incident_id, expect_kisys_incidentid),
            'INFO:send_to_bao.py:normal報処理:関連テーブルを更新しました。gw_event_id=%s, gw_incident_id=%s, kisys_incidentid=%s' % (expect_normal_event_id, expect_incident_id, expect_kisys_incidentid),
            'INFO:send_to_bao.py:イベント処理(1/1)終了, gw_event_id=%s' % expect_normal_event_id,
            'INFO:send_to_bao.py:10秒待機します。',
        ])

        # DB更新結果の確認
        expect_error_kisys_status = gwcommon.GW_KISYS_STATUS_NEW_OK
        error_event_result = HELPER.get_updated_gw_events_data(self.conn, expect_error_event_id)
        self.assertEqual(error_event_result['kisys_status'], expect_error_kisys_status)
        expect_normal_kisys_status = gwcommon.GW_KISYS_STATUS_NEW_NORES
        normal_event_result = HELPER.get_updated_gw_events_data(self.conn, expect_normal_event_id)
        self.assertEqual(normal_event_result['kisys_status'], expect_normal_kisys_status)

    # @unittest.skip('TESTSKIP')
    @patch('gwcommon.MY_DB', HELPER.MY_DB_LOCAL)
    @patch('gwfunction.get_hostgroups_by_host')
    @patch('gwfunction.get_alias_by_host')
    @patch('bao_tm_post.BAO_TM_CLIENT.send')
    def test_error_normal_paired_norule_BAO_NG(self, mock_bao_tm_client_send, mock_get_alias_by_host, mock_get_hostgroups_by_host):
        # モード設定
        HELPER.set_master_mode()
        HELPER.insert_kompira_rule(self.conn)

        # モック準備
        mock_get_hostgroups_by_host.return_value = []
        mock_get_alias_by_host.return_value = ''
        mock_bao_tm_client_send.return_value = 'Failure' # 失敗

        # テストデータ投入
        now = datetime.datetime.now()
        one_minute_ago = now - datetime.timedelta(minutes=1)
        test_pattern_name = 'test_error_normal_paired_norule_BAO_NG'
        insert_hash1 = get_insert_hash(one_minute_ago, gwcommon.GW_ALARM_STATUS_ERROR, test_pattern_name, gwcommon.GW_KISYS_STATUS_NEW_OK)
        insert_hash2 = get_insert_hash(now, gwcommon.GW_ALARM_STATUS_NORMAL, test_pattern_name, gwcommon.GW_KISYS_STATUS_KISYS_CONNECT_NORULE)
        event_ids = insert_event_data(self.conn, [insert_hash1, insert_hash2])
        insert_hash1['error_event_id'] = event_ids[0]
        insert_hash1['normal_event_id'] = event_ids[1]
        insert_hash1['incident_status'] = gwcommon.GW_INCIDENT_STATUS_CLOSE
        insert_incident_data(self.conn, [insert_hash1])
        expect_incident_id = '1'
        expect_kisys_incidentid = 'IT0000-00000000'
        update_gw_incident_data(self.conn, expect_incident_id, expect_kisys_incidentid)

        # 処理実行
        with self.assertLogs('send_to_bao.py') as cm:
            send_to_bao.main()

        # ログ内容の確認
        expect_error_event_id = event_ids[0]
        expect_normal_event_id = event_ids[1]

        self.assertEqual(cm.output, [
            'INFO:send_to_bao.py:マスターモードのため、マスター動作実行',
            'INFO:send_to_bao.py:KISYSメンテナンス期間に該当しないため処理を継続します。',
            'INFO:send_to_bao.py:イベント処理開始(1/1), gw_event_id=%s' % expect_normal_event_id,
            'INFO:send_to_bao.py:normal報処理開始 gw_event_id=%s' % expect_normal_event_id,
            'ERROR:send_to_bao.py:normal報処理:BAO更新失敗 gw_event_id=%s, gw_incident_id=%s, kisys_incidentid=%s' % (expect_normal_event_id, expect_incident_id, expect_kisys_incidentid),
            'INFO:send_to_bao.py:normal報処理:関連テーブルを更新しました。gw_event_id=%s, gw_incident_id=%s, kisys_incidentid=%s' % (expect_normal_event_id, expect_incident_id, expect_kisys_incidentid),
            'INFO:send_to_bao.py:イベント処理(1/1)終了, gw_event_id=%s' % expect_normal_event_id,
            'INFO:send_to_bao.py:10秒待機します。',

        ])

        # DB更新結果の確認
        expect_error_kisys_status = gwcommon.GW_KISYS_STATUS_NEW_OK
        error_event_result = HELPER.get_updated_gw_events_data(self.conn, expect_error_event_id)
        self.assertEqual(error_event_result['kisys_status'], expect_error_kisys_status)
        expect_normal_kisys_status = gwcommon.GW_KISYS_STATUS_NEW_NG
        normal_event_result = HELPER.get_updated_gw_events_data(self.conn, expect_normal_event_id)
        self.assertEqual(normal_event_result['kisys_status'], expect_normal_kisys_status)

    # @unittest.skip('TESTSKIP')
    @patch('gwcommon.MY_DB', HELPER.MY_DB_LOCAL)
    @patch('gwfunction.get_hostgroups_by_host')
    @patch('gwfunction.get_alias_by_host')
    @patch('bao_tm_post.BAO_TM_CLIENT.send')
    def test_error_normal_paired_norule_BAO_NOSEND(self, mock_bao_tm_client_send, mock_get_alias_by_host, mock_get_hostgroups_by_host):
        # モード設定
        HELPER.set_master_mode()
        HELPER.insert_kompira_rule(self.conn)

        # モック準備
        mock_get_hostgroups_by_host.return_value = []
        mock_get_alias_by_host.return_value = ''
        mock_bao_tm_client_send.return_value = 'Failure' # 失敗

        # テストデータ投入
        now = datetime.datetime.now()
        one_minute_ago = now - datetime.timedelta(minutes=1)
        test_pattern_name = 'test_error_normal_paired_norule_BAO_NG'
        insert_hash1 = get_insert_hash(one_minute_ago, gwcommon.GW_ALARM_STATUS_ERROR, test_pattern_name, gwcommon.GW_KISYS_STATUS_KISYS_CONNECT_NORULE)
        insert_hash2 = get_insert_hash(now, gwcommon.GW_ALARM_STATUS_NORMAL, test_pattern_name, gwcommon.GW_KISYS_STATUS_KISYS_CONNECT_NORULE)
        event_ids = insert_event_data(self.conn, [insert_hash1, insert_hash2])
        insert_hash1['error_event_id'] = event_ids[0]
        insert_hash1['normal_event_id'] = event_ids[1]
        insert_hash1['incident_status'] = gwcommon.GW_INCIDENT_STATUS_CLOSE
        insert_incident_data(self.conn, [insert_hash1])

        # 処理実行
        with self.assertLogs('send_to_bao.py') as cm:
            send_to_bao.main()

        # ログ内容の確認
        expect_error_event_id = event_ids[0]
        expect_normal_event_id = event_ids[1]
        expect_incident_id = '1'
        expect_kisys_incidentid = None

        self.assertEqual(cm.output, [
            'INFO:send_to_bao.py:マスターモードのため、マスター動作実行',
            'INFO:send_to_bao.py:KISYSメンテナンス期間に該当しないため処理を継続します。',
            'INFO:send_to_bao.py:イベント処理開始(1/2), gw_event_id=%s' % expect_error_event_id,
            'INFO:send_to_bao.py:error報処理開始 gw_event_id=%s' % expect_error_event_id,
            'ERROR:send_to_bao.py:error報処理:BAO連携失敗 gw_event_id=%s' % expect_error_event_id,
            'INFO:send_to_bao.py:error報処理:関連テーブルを更新しました。gw_event_id=%s, gw_incident_id=%s, kisys_incidentid=%s' % (expect_error_event_id, expect_incident_id, expect_kisys_incidentid),
            'INFO:send_to_bao.py:イベント処理(1/2)終了, gw_event_id=%s' % expect_error_event_id,
            'INFO:send_to_bao.py:イベント処理開始(2/2), gw_event_id=%s' % expect_normal_event_id,
            'INFO:send_to_bao.py:normal報処理開始 gw_event_id=%s' % expect_normal_event_id,
            'INFO:send_to_bao.py:normal報処理:BAO更新-未実施 gw_event_id=%s, gw_incident_id=%s, kisys_incidentid=%s' % (expect_normal_event_id, expect_incident_id, expect_kisys_incidentid),
            'INFO:send_to_bao.py:normal報処理:関連テーブルを更新しました。gw_event_id=%s, gw_incident_id=%s, kisys_incidentid=%s' % (expect_normal_event_id, expect_incident_id, expect_kisys_incidentid),
            'INFO:send_to_bao.py:イベント処理(2/2)終了, gw_event_id=%s' % expect_normal_event_id,
            'INFO:send_to_bao.py:10秒待機します。',
        ])

        # DB更新結果の確認
        expect_error_kisys_status = gwcommon.GW_KISYS_STATUS_NEW_NG
        error_event_result = HELPER.get_updated_gw_events_data(self.conn, expect_error_event_id)
        self.assertEqual(error_event_result['kisys_status'], expect_error_kisys_status)
        expect_normal_kisys_status = None
        normal_event_result = HELPER.get_updated_gw_events_data(self.conn, expect_normal_event_id)
        self.assertEqual(normal_event_result['kisys_status'], expect_normal_kisys_status)


    # @unittest.skip('TESTSKIP')
    @patch('gwcommon.MY_DB', HELPER.MY_DB_LOCAL)
    @patch('gwfunction.get_hostgroups_by_host')
    @patch('gwfunction.get_alias_by_host')
    @patch('bao_tm_post.BAO_TM_CLIENT.send')
    def test_error_normal_paired_rule10_BAO_OK(self, mock_bao_tm_client_send, mock_get_alias_by_host, mock_get_hostgroups_by_host):
        # モード設定
        HELPER.set_master_mode()
        HELPER.insert_kompira_rule(self.conn)

        # モック準備
        mock_get_hostgroups_by_host.return_value = []
        mock_get_alias_by_host.return_value = ''
        expect_kisys_incidentid = 'IT0000-00000000'
        mock_bao_tm_client_send.return_value = expect_kisys_incidentid # 成功

        # テストデータ投入
        now = datetime.datetime.now()
        one_minute_ago = now - datetime.timedelta(minutes=1)
        test_pattern_name = 'test_error_normal_paired_rule10_BAO_OK'
        insert_hash1 = get_insert_hash(one_minute_ago, gwcommon.GW_ALARM_STATUS_ERROR, test_pattern_name, gwcommon.GW_KISYS_STATUS_NOSEND_OK)
        insert_hash2 = get_insert_hash(now, gwcommon.GW_ALARM_STATUS_NORMAL, test_pattern_name, gwcommon.GW_KISYS_STATUS_NOSEND_MANUAL)
        event_ids = insert_event_data(self.conn, [insert_hash1, insert_hash2])
        insert_hash1['error_event_id'] = event_ids[0]
        insert_hash1['normal_event_id'] = event_ids[1]
        insert_hash1['incident_status'] = gwcommon.GW_INCIDENT_STATUS_CLOSE
        insert_incident_data(self.conn, [insert_hash1])
        expect_incident_id = '1'
        expect_kisys_incidentid = 'IT0000-00000000'
        update_gw_incident_data(self.conn, expect_incident_id, expect_kisys_incidentid)
        HELPER.insert_test_rule(self.conn, gwcommon.GW_KISYS_STATUS_NOSEND, test_pattern_name)

        # 処理実行
        with self.assertLogs('send_to_bao.py') as cm:
            send_to_bao.main()

        # ログ内容の確認
        expect_error_event_id = event_ids[0]
        expect_normal_event_id = event_ids[1]

        self.assertEqual(cm.output, [
            'INFO:send_to_bao.py:マスターモードのため、マスター動作実行',
            'INFO:send_to_bao.py:KISYSメンテナンス期間に該当しないため処理を継続します。',
            'INFO:send_to_bao.py:イベント処理開始(1/1), gw_event_id=%s' % expect_normal_event_id,
            'INFO:send_to_bao.py:normal報処理開始 gw_event_id=%s' % expect_normal_event_id,
            'INFO:send_to_bao.py:normal報処理:BAO更新成功 gw_event_id=%s, gw_incident_id=%s, kisys_incidentid=%s' % (expect_normal_event_id, expect_incident_id, expect_kisys_incidentid),
            'INFO:send_to_bao.py:normal報処理:関連テーブルを更新しました。gw_event_id=%s, gw_incident_id=%s, kisys_incidentid=%s' % (expect_normal_event_id, expect_incident_id, expect_kisys_incidentid),
            'INFO:send_to_bao.py:Kompira連携しません。kisys_incidentid=%s' % expect_kisys_incidentid,
            'INFO:send_to_bao.py:イベント処理(1/1)終了, gw_event_id=%s' % expect_normal_event_id,
            'INFO:send_to_bao.py:10秒待機します。',
        ])

        # DB更新結果の確認
        expect_kisys_status = gwcommon.GW_KISYS_STATUS_NOSEND_OK + ',' + gwcommon.KOMPIRA_STATUS_NOSEND
        error_event_result = HELPER.get_updated_gw_events_data(self.conn, expect_error_event_id)
        self.assertEqual(error_event_result['kisys_status'], gwcommon.GW_KISYS_STATUS_NOSEND_OK)
        normal_event_result = HELPER.get_updated_gw_events_data(self.conn, expect_normal_event_id)
        self.assertEqual(normal_event_result['kisys_status'], expect_kisys_status)

    # @unittest.skip('TESTSKIP')
    @patch('gwcommon.MY_DB', HELPER.MY_DB_LOCAL)
    @patch('gwfunction.get_hostgroups_by_host')
    @patch('gwfunction.get_alias_by_host')
    @patch('bao_tm_post.BAO_TM_CLIENT.send')
    def test_error_normal_paired_rule10_BAO_NORES(self, mock_bao_tm_client_send, mock_get_alias_by_host, mock_get_hostgroups_by_host):
        # モード設定
        HELPER.set_master_mode()
        HELPER.insert_kompira_rule(self.conn)

        # モック準備
        mock_get_hostgroups_by_host.return_value = []
        mock_get_alias_by_host.return_value = ''
        mock_bao_tm_client_send.return_value = 'No_reply' # 無応答

        # テストデータ投入
        now = datetime.datetime.now()
        one_minute_ago = now - datetime.timedelta(minutes=1)
        test_pattern_name = 'test_error_normal_paired_rule10_BAO_NORES'
        insert_hash1 = get_insert_hash(one_minute_ago, gwcommon.GW_ALARM_STATUS_ERROR, test_pattern_name, gwcommon.GW_KISYS_STATUS_NOSEND_OK)
        insert_hash2 = get_insert_hash(now, gwcommon.GW_ALARM_STATUS_NORMAL, test_pattern_name, gwcommon.GW_KISYS_STATUS_NOSEND_MANUAL)
        event_ids = insert_event_data(self.conn, [insert_hash1, insert_hash2])
        insert_hash1['error_event_id'] = event_ids[0]
        insert_hash1['normal_event_id'] = event_ids[1]
        insert_hash1['incident_status'] = gwcommon.GW_INCIDENT_STATUS_CLOSE
        insert_incident_data(self.conn, [insert_hash1])
        expect_incident_id = '1'
        expect_kisys_incidentid = 'IT0000-00000000'
        update_gw_incident_data(self.conn, expect_incident_id, expect_kisys_incidentid)
        HELPER.insert_test_rule(self.conn, gwcommon.GW_KISYS_STATUS_NOSEND, test_pattern_name)

        # 処理実行
        with self.assertLogs('send_to_bao.py') as cm:
            send_to_bao.main()

        # ログ内容の確認
        expect_error_event_id = event_ids[0]
        expect_normal_event_id = event_ids[1]

        self.assertEqual(cm.output, [
            'INFO:send_to_bao.py:マスターモードのため、マスター動作実行',
            'INFO:send_to_bao.py:KISYSメンテナンス期間に該当しないため処理を継続します。',
            'INFO:send_to_bao.py:イベント処理開始(1/1), gw_event_id=%s' % expect_normal_event_id,
            'INFO:send_to_bao.py:normal報処理開始 gw_event_id=%s' % expect_normal_event_id,
            'ERROR:send_to_bao.py:normal報処理:BAO無応答 gw_event_id=%s, gw_incident_id=%s, kisys_incidentid=%s' % (expect_normal_event_id, expect_incident_id, expect_kisys_incidentid),
            'INFO:send_to_bao.py:normal報処理:関連テーブルを更新しました。gw_event_id=%s, gw_incident_id=%s, kisys_incidentid=%s' % (expect_normal_event_id, expect_incident_id, expect_kisys_incidentid),
            'INFO:send_to_bao.py:イベント処理(1/1)終了, gw_event_id=%s' % expect_normal_event_id,
            'INFO:send_to_bao.py:10秒待機します。',
        ])

        # DB更新結果の確認
        expect_error_kisys_status = gwcommon.GW_KISYS_STATUS_NOSEND_OK
        error_event_result = HELPER.get_updated_gw_events_data(self.conn, expect_error_event_id)
        self.assertEqual(error_event_result['kisys_status'], expect_error_kisys_status)
        expect_normal_kisys_status = gwcommon.GW_KISYS_STATUS_NOSEND_NORES
        normal_event_result = HELPER.get_updated_gw_events_data(self.conn, expect_normal_event_id)
        self.assertEqual(normal_event_result['kisys_status'], expect_normal_kisys_status)

    # @unittest.skip('TESTSKIP')
    @patch('gwcommon.MY_DB', HELPER.MY_DB_LOCAL)
    @patch('gwfunction.get_hostgroups_by_host')
    @patch('gwfunction.get_alias_by_host')
    @patch('bao_tm_post.BAO_TM_CLIENT.send')
    def test_error_normal_paired_rule10_BAO_NG(self, mock_bao_tm_client_send, mock_get_alias_by_host, mock_get_hostgroups_by_host):
        # モード設定
        HELPER.set_master_mode()
        HELPER.insert_kompira_rule(self.conn)

        # モック準備
        mock_get_hostgroups_by_host.return_value = []
        mock_get_alias_by_host.return_value = ''
        mock_bao_tm_client_send.return_value = 'Failure' # 失敗

        # テストデータ投入
        now = datetime.datetime.now()
        one_minute_ago = now - datetime.timedelta(minutes=1)
        test_pattern_name = 'test_error_normal_paired_rule10_BAO_NG'
        insert_hash1 = get_insert_hash(one_minute_ago, gwcommon.GW_ALARM_STATUS_ERROR, test_pattern_name, gwcommon.GW_KISYS_STATUS_NOSEND_OK)
        insert_hash2 = get_insert_hash(now, gwcommon.GW_ALARM_STATUS_NORMAL, test_pattern_name, gwcommon.GW_KISYS_STATUS_NOSEND_MANUAL)
        event_ids = insert_event_data(self.conn, [insert_hash1, insert_hash2])
        insert_hash1['error_event_id'] = event_ids[0]
        insert_hash1['normal_event_id'] = event_ids[1]
        insert_hash1['incident_status'] = gwcommon.GW_INCIDENT_STATUS_CLOSE
        insert_incident_data(self.conn, [insert_hash1])
        expect_incident_id = '1'
        expect_kisys_incidentid = 'IT0000-00000000'
        update_gw_incident_data(self.conn, expect_incident_id, expect_kisys_incidentid)
        HELPER.insert_test_rule(self.conn, gwcommon.GW_KISYS_STATUS_NOSEND, test_pattern_name)

        # 処理実行
        with self.assertLogs('send_to_bao.py') as cm:
            send_to_bao.main()

        # ログ内容の確認
        expect_error_event_id = event_ids[0]
        expect_normal_event_id = event_ids[1]

        self.assertEqual(cm.output, [
            'INFO:send_to_bao.py:マスターモードのため、マスター動作実行',
            'INFO:send_to_bao.py:KISYSメンテナンス期間に該当しないため処理を継続します。',
            'INFO:send_to_bao.py:イベント処理開始(1/1), gw_event_id=%s' % expect_normal_event_id,
            'INFO:send_to_bao.py:normal報処理開始 gw_event_id=%s' % expect_normal_event_id,
            'ERROR:send_to_bao.py:normal報処理:BAO更新失敗 gw_event_id=%s, gw_incident_id=%s, kisys_incidentid=%s' % (expect_normal_event_id, expect_incident_id, expect_kisys_incidentid),
            'INFO:send_to_bao.py:normal報処理:関連テーブルを更新しました。gw_event_id=%s, gw_incident_id=%s, kisys_incidentid=%s' % (expect_normal_event_id, expect_incident_id, expect_kisys_incidentid),
            'INFO:send_to_bao.py:イベント処理(1/1)終了, gw_event_id=%s' % expect_normal_event_id,
            'INFO:send_to_bao.py:10秒待機します。',

        ])

        # DB更新結果の確認
        expect_error_kisys_status = gwcommon.GW_KISYS_STATUS_NOSEND_OK
        error_event_result = HELPER.get_updated_gw_events_data(self.conn, expect_error_event_id)
        self.assertEqual(error_event_result['kisys_status'], expect_error_kisys_status)
        expect_normal_kisys_status = gwcommon.GW_KISYS_STATUS_NOSEND_NG
        normal_event_result = HELPER.get_updated_gw_events_data(self.conn, expect_normal_event_id)
        self.assertEqual(normal_event_result['kisys_status'], expect_normal_kisys_status)

    # @unittest.skip('TESTSKIP')
    @patch('gwcommon.MY_DB', HELPER.MY_DB_LOCAL)
    @patch('gwfunction.get_hostgroups_by_host')
    @patch('gwfunction.get_alias_by_host')
    @patch('bao_tm_post.BAO_TM_CLIENT.send')
    def test_error_normal_paired_rule30_norecovery_BAO_OK(self, mock_bao_tm_client_send, mock_get_alias_by_host, mock_get_hostgroups_by_host):
        # モード設定
        HELPER.set_master_mode()
        HELPER.insert_kompira_rule(self.conn)

        # モック準備
        mock_get_hostgroups_by_host.return_value = []
        mock_get_alias_by_host.return_value = ''
        expect_kisys_incidentid = 'IT0000-00000000'
        mock_bao_tm_client_send.return_value = expect_kisys_incidentid # 成功

        # テストデータ投入
        now = datetime.datetime.now()
        yesterday = now - datetime.timedelta(days=1)
        test_pattern_name = 'test_error_normal_paired_rule30_norecovery_BAO_OK'
        insert_hash1 = get_insert_hash(yesterday, gwcommon.GW_ALARM_STATUS_ERROR, test_pattern_name, gwcommon.GW_KISYS_STATUS_NORECOVERY_OK)
        insert_hash2 = get_insert_hash(now, gwcommon.GW_ALARM_STATUS_NORMAL, test_pattern_name, gwcommon.GW_KISYS_STATUS_KISYS_CONNECT_NORECOVERY)
        event_ids = insert_event_data(self.conn, [insert_hash1, insert_hash2])
        insert_hash1['error_event_id'] = event_ids[0]
        insert_hash1['normal_event_id'] = event_ids[1]
        insert_hash1['incident_status'] = gwcommon.GW_INCIDENT_STATUS_CLOSE
        insert_incident_data(self.conn, [insert_hash1])
        expect_incident_id = '1'
        expect_kisys_incidentid = 'IT0000-00000000'
        update_gw_incident_data(self.conn, expect_incident_id, expect_kisys_incidentid)
        HELPER.insert_test_rule(self.conn, gwcommon.GW_KISYS_STATUS_WAITING_5, test_pattern_name)

        # 処理実行
        with self.assertLogs('send_to_bao.py') as cm:
            send_to_bao.main()

        # ログ内容の確認
        expect_error_event_id = event_ids[0]
        expect_normal_event_id = event_ids[1]

        self.assertEqual(cm.output, [
            'INFO:send_to_bao.py:マスターモードのため、マスター動作実行',
            'INFO:send_to_bao.py:KISYSメンテナンス期間に該当しないため処理を継続します。',
            'INFO:send_to_bao.py:イベント処理開始(1/1), gw_event_id=%s' % expect_normal_event_id,
            'INFO:send_to_bao.py:normal報処理開始 gw_event_id=%s' % expect_normal_event_id,
            'INFO:send_to_bao.py:normal報処理:BAO更新成功 gw_event_id=%s, gw_incident_id=%s, kisys_incidentid=%s' % (expect_normal_event_id, expect_incident_id, expect_kisys_incidentid),
            'INFO:send_to_bao.py:normal報処理:関連テーブルを更新しました。gw_event_id=%s, gw_incident_id=%s, kisys_incidentid=%s' % (expect_normal_event_id, expect_incident_id, expect_kisys_incidentid),
            'INFO:send_to_bao.py:Kompira連携しません。kisys_incidentid=%s' % expect_kisys_incidentid,
            'INFO:send_to_bao.py:イベント処理(1/1)終了, gw_event_id=%s' % expect_normal_event_id,
            'INFO:send_to_bao.py:10秒待機します。',
        ])

        # DB更新結果の確認
        expect_kisys_status = gwcommon.GW_KISYS_STATUS_NORECOVERY_OK + ',' + gwcommon.KOMPIRA_STATUS_NOSEND
        error_event_result = HELPER.get_updated_gw_events_data(self.conn, expect_error_event_id)
        self.assertEqual(error_event_result['kisys_status'], gwcommon.GW_KISYS_STATUS_NORECOVERY_OK)
        normal_event_result = HELPER.get_updated_gw_events_data(self.conn, expect_normal_event_id)
        self.assertEqual(normal_event_result['kisys_status'], expect_kisys_status)

    # @unittest.skip('TESTSKIP')
    @patch('gwcommon.MY_DB', HELPER.MY_DB_LOCAL)
    @patch('gwfunction.get_hostgroups_by_host')
    @patch('gwfunction.get_alias_by_host')
    @patch('bao_tm_post.BAO_TM_CLIENT.send')
    def test_error_normal_paired_rule30_norecovery_BAO_NORES(self, mock_bao_tm_client_send, mock_get_alias_by_host, mock_get_hostgroups_by_host):
        # モード設定
        HELPER.set_master_mode()
        HELPER.insert_kompira_rule(self.conn)

        # モック準備
        mock_get_hostgroups_by_host.return_value = []
        mock_get_alias_by_host.return_value = ''
        mock_bao_tm_client_send.return_value = 'No_reply' # 無応答

        # テストデータ投入
        now = datetime.datetime.now()
        yesterday = now - datetime.timedelta(days=1)
        test_pattern_name = 'test_error_normal_paired_rule30_norecovery_BAO_NORES'
        insert_hash1 = get_insert_hash(yesterday, gwcommon.GW_ALARM_STATUS_ERROR, test_pattern_name, gwcommon.GW_KISYS_STATUS_NORECOVERY_OK)
        insert_hash2 = get_insert_hash(now, gwcommon.GW_ALARM_STATUS_NORMAL, test_pattern_name, gwcommon.GW_KISYS_STATUS_KISYS_CONNECT_NORECOVERY)
        event_ids = insert_event_data(self.conn, [insert_hash1, insert_hash2])
        insert_hash1['error_event_id'] = event_ids[0]
        insert_hash1['normal_event_id'] = event_ids[1]
        insert_hash1['incident_status'] = gwcommon.GW_INCIDENT_STATUS_CLOSE
        insert_incident_data(self.conn, [insert_hash1])
        expect_incident_id = '1'
        expect_kisys_incidentid = 'IT0000-00000000'
        update_gw_incident_data(self.conn, expect_incident_id, expect_kisys_incidentid)
        HELPER.insert_test_rule(self.conn, gwcommon.GW_KISYS_STATUS_WAITING_5, test_pattern_name)

        # 処理実行
        with self.assertLogs('send_to_bao.py') as cm:
            send_to_bao.main()

        # ログ内容の確認
        expect_error_event_id = event_ids[0]
        expect_normal_event_id = event_ids[1]

        self.assertEqual(cm.output, [
            'INFO:send_to_bao.py:マスターモードのため、マスター動作実行',
            'INFO:send_to_bao.py:KISYSメンテナンス期間に該当しないため処理を継続します。',
            'INFO:send_to_bao.py:イベント処理開始(1/1), gw_event_id=%s' % expect_normal_event_id,
            'INFO:send_to_bao.py:normal報処理開始 gw_event_id=%s' % expect_normal_event_id,
            'ERROR:send_to_bao.py:normal報処理:BAO無応答 gw_event_id=%s, gw_incident_id=%s, kisys_incidentid=%s' % (expect_normal_event_id, expect_incident_id, expect_kisys_incidentid),
            'INFO:send_to_bao.py:normal報処理:関連テーブルを更新しました。gw_event_id=%s, gw_incident_id=%s, kisys_incidentid=%s' % (expect_normal_event_id, expect_incident_id, expect_kisys_incidentid),
            'INFO:send_to_bao.py:イベント処理(1/1)終了, gw_event_id=%s' % expect_normal_event_id,
            'INFO:send_to_bao.py:10秒待機します。',
        ])

        # DB更新結果の確認
        expect_error_kisys_status = gwcommon.GW_KISYS_STATUS_NORECOVERY_OK
        error_event_result = HELPER.get_updated_gw_events_data(self.conn, expect_error_event_id)
        self.assertEqual(error_event_result['kisys_status'], expect_error_kisys_status)
        expect_normal_kisys_status = gwcommon.GW_KISYS_STATUS_NORECOVERY_NORES
        normal_event_result = HELPER.get_updated_gw_events_data(self.conn, expect_normal_event_id)
        self.assertEqual(normal_event_result['kisys_status'], expect_normal_kisys_status)

    # @unittest.skip('TESTSKIP')
    @patch('gwcommon.MY_DB', HELPER.MY_DB_LOCAL)
    @patch('gwfunction.get_hostgroups_by_host')
    @patch('gwfunction.get_alias_by_host')
    @patch('bao_tm_post.BAO_TM_CLIENT.send')
    def test_error_normal_paired_rule30_norecovery_BAO_NG(self, mock_bao_tm_client_send, mock_get_alias_by_host, mock_get_hostgroups_by_host):
        # モード設定
        HELPER.set_master_mode()
        HELPER.insert_kompira_rule(self.conn)

        # モック準備
        mock_get_hostgroups_by_host.return_value = []
        mock_get_alias_by_host.return_value = ''
        mock_bao_tm_client_send.return_value = 'Failure' # 失敗

        # テストデータ投入
        now = datetime.datetime.now()
        yesterday = now - datetime.timedelta(days=1)
        test_pattern_name = 'test_error_normal_paired_rule30_norecovery_BAO_NG'
        insert_hash1 = get_insert_hash(yesterday, gwcommon.GW_ALARM_STATUS_ERROR, test_pattern_name, gwcommon.GW_KISYS_STATUS_NORECOVERY_OK)
        insert_hash2 = get_insert_hash(now, gwcommon.GW_ALARM_STATUS_NORMAL, test_pattern_name, gwcommon.GW_KISYS_STATUS_KISYS_CONNECT_NORECOVERY)
        event_ids = insert_event_data(self.conn, [insert_hash1, insert_hash2])
        insert_hash1['error_event_id'] = event_ids[0]
        insert_hash1['normal_event_id'] = event_ids[1]
        insert_hash1['incident_status'] = gwcommon.GW_INCIDENT_STATUS_CLOSE
        insert_incident_data(self.conn, [insert_hash1])
        expect_incident_id = '1'
        expect_kisys_incidentid = 'IT0000-00000000'
        update_gw_incident_data(self.conn, expect_incident_id, expect_kisys_incidentid)
        HELPER.insert_test_rule(self.conn, gwcommon.GW_KISYS_STATUS_WAITING_5, test_pattern_name)

        # 処理実行
        with self.assertLogs('send_to_bao.py') as cm:
            send_to_bao.main()

        # ログ内容の確認
        expect_error_event_id = event_ids[0]
        expect_normal_event_id = event_ids[1]

        self.assertEqual(cm.output, [
            'INFO:send_to_bao.py:マスターモードのため、マスター動作実行',
            'INFO:send_to_bao.py:KISYSメンテナンス期間に該当しないため処理を継続します。',
            'INFO:send_to_bao.py:イベント処理開始(1/1), gw_event_id=%s' % expect_normal_event_id,
            'INFO:send_to_bao.py:normal報処理開始 gw_event_id=%s' % expect_normal_event_id,
            'ERROR:send_to_bao.py:normal報処理:BAO更新失敗 gw_event_id=%s, gw_incident_id=%s, kisys_incidentid=%s' % (expect_normal_event_id, expect_incident_id, expect_kisys_incidentid),
            'INFO:send_to_bao.py:normal報処理:関連テーブルを更新しました。gw_event_id=%s, gw_incident_id=%s, kisys_incidentid=%s' % (expect_normal_event_id, expect_incident_id, expect_kisys_incidentid),
            'INFO:send_to_bao.py:イベント処理(1/1)終了, gw_event_id=%s' % expect_normal_event_id,
            'INFO:send_to_bao.py:10秒待機します。',
        ])

        # DB更新結果の確認
        expect_error_kisys_status = gwcommon.GW_KISYS_STATUS_NORECOVERY_OK
        error_event_result = HELPER.get_updated_gw_events_data(self.conn, expect_error_event_id)
        self.assertEqual(error_event_result['kisys_status'], expect_error_kisys_status)
        expect_normal_kisys_status = gwcommon.GW_KISYS_STATUS_NORECOVERY_NG
        normal_event_result = HELPER.get_updated_gw_events_data(self.conn, expect_normal_event_id)
        self.assertEqual(normal_event_result['kisys_status'], expect_normal_kisys_status)

    # @unittest.skip('TESTSKIP')
    @patch('gwcommon.MY_DB', HELPER.MY_DB_LOCAL)
    @patch('gwfunction.get_hostgroups_by_host')
    @patch('gwfunction.get_alias_by_host')
    @patch('bao_tm_post.BAO_TM_CLIENT.send')
    def test_error_normal_paired_rule30_cancel_BAO_OK(self, mock_bao_tm_client_send, mock_get_alias_by_host, mock_get_hostgroups_by_host):
        # モード設定
        HELPER.set_master_mode()
        HELPER.insert_kompira_rule(self.conn)

        # モック準備
        mock_get_hostgroups_by_host.return_value = []
        mock_get_alias_by_host.return_value = ''
        expect_kisys_incidentid = 'IT0000-00000000'
        mock_bao_tm_client_send.return_value = expect_kisys_incidentid # 成功

        # テストデータ投入
        now = datetime.datetime.now()
        one_minute_ago = now - datetime.timedelta(minutes=1)
        test_pattern_name = 'test_error_normal_paired_rule30_cancel_BAO_OK'
        insert_hash1 = get_insert_hash(one_minute_ago, gwcommon.GW_ALARM_STATUS_ERROR, test_pattern_name, gwcommon.GW_KISYS_STATUS_KISYS_CONNECT_CANCEL)
        insert_hash2 = get_insert_hash(now, gwcommon.GW_ALARM_STATUS_NORMAL, test_pattern_name, gwcommon.GW_KISYS_STATUS_KISYS_CONNECT_CANCEL)
        event_ids = insert_event_data(self.conn, [insert_hash1, insert_hash2])
        insert_hash1['error_event_id'] = event_ids[0]
        insert_hash1['normal_event_id'] = event_ids[1]
        insert_hash1['incident_status'] = gwcommon.GW_INCIDENT_STATUS_CLOSE
        insert_incident_data(self.conn, [insert_hash1])
        HELPER.insert_test_rule(self.conn, gwcommon.GW_KISYS_STATUS_WAITING_5, test_pattern_name)

        # 処理実行
        with self.assertLogs('send_to_bao.py') as cm:
            send_to_bao.main()

        # ログ内容の確認
        expect_error_event_id = event_ids[0]
        expect_normal_event_id = event_ids[1]
        expect_incident_id = '1'
        expect_kisys_incidentid = 'IT0000-00000000'

        self.assertEqual(cm.output, [
            'INFO:send_to_bao.py:マスターモードのため、マスター動作実行',
            'INFO:send_to_bao.py:KISYSメンテナンス期間に該当しないため処理を継続します。',
            'INFO:send_to_bao.py:イベント処理開始(1/2), gw_event_id=%s' % expect_error_event_id,
            'INFO:send_to_bao.py:error報処理開始 gw_event_id=%s' % expect_error_event_id,
            'INFO:send_to_bao.py:キャンセル処理開始 gw_event_id=%s' % expect_error_event_id,
            'INFO:send_to_bao.py:キャンセル処理:BAO連携成功 gw_event_id=%s' % expect_error_event_id,
            'INFO:send_to_bao.py:キャンセル処理:関連テーブルを更新しました。gw_event_id=%s, gw_incident_id=%s, kisys_incidentid=%s' % (expect_error_event_id, expect_incident_id, expect_kisys_incidentid),
            'INFO:send_to_bao.py:gw_event_id=%s クローズしました(event_status=2)' % expect_error_event_id,
            'INFO:send_to_bao.py:イベント処理(1/2)終了, gw_event_id=%s' % expect_error_event_id,
            'INFO:send_to_bao.py:イベント処理開始(2/2), gw_event_id=%s' % expect_normal_event_id,
            'INFO:send_to_bao.py:normal報処理開始 gw_event_id=%s' % expect_normal_event_id,
            'INFO:send_to_bao.py:キャンセル処理:BAO更新成功 gw_event_id=%s, gw_incident_id=%s, kisys_incidentid=%s' % (expect_normal_event_id, expect_incident_id, expect_kisys_incidentid),
            'INFO:send_to_bao.py:キャンセル処理:関連テーブルを更新しました。gw_event_id=%s, gw_incident_id=%s, kisys_incidentid=%s' % (expect_normal_event_id, expect_incident_id, expect_kisys_incidentid),
            'INFO:send_to_bao.py:gw_event_id=%s クローズしました(event_status=2)' % expect_normal_event_id,
            'INFO:send_to_bao.py:イベント処理(2/2)終了, gw_event_id=%s' % expect_normal_event_id,
            'INFO:send_to_bao.py:10秒待機します。',
        ])

        # DB更新結果の確認
        expect_kisys_status = gwcommon.GW_KISYS_STATUS_CANCEL_OK
        error_event_result = HELPER.get_updated_gw_events_data(self.conn, expect_error_event_id)
        self.assertEqual(error_event_result['kisys_status'], expect_kisys_status)
        normal_event_result = HELPER.get_updated_gw_events_data(self.conn, expect_normal_event_id)
        self.assertEqual(normal_event_result['kisys_status'], expect_kisys_status)

    # @unittest.skip('TESTSKIP')
    @patch('gwcommon.MY_DB', HELPER.MY_DB_LOCAL)
    @patch('gwfunction.get_hostgroups_by_host')
    @patch('gwfunction.get_alias_by_host')
    @patch('bao_tm_post.BAO_TM_CLIENT.send')
    def test_error_normal_paired_rule30_cancel_BAO_NORES(self, mock_bao_tm_client_send, mock_get_alias_by_host, mock_get_hostgroups_by_host):
        # モード設定
        HELPER.set_master_mode()
        HELPER.insert_kompira_rule(self.conn)

        # モック準備
        mock_get_hostgroups_by_host.return_value = []
        mock_get_alias_by_host.return_value = ''
        mock_bao_tm_client_send.return_value = 'No_reply' # 無応答

        # テストデータ投入
        now = datetime.datetime.now()
        one_minute_ago = now - datetime.timedelta(minutes=1)
        test_pattern_name = 'test_error_normal_paired_rule30_cancel_BAO_NORES'
        insert_hash1 = get_insert_hash(one_minute_ago, gwcommon.GW_ALARM_STATUS_ERROR, test_pattern_name, gwcommon.GW_KISYS_STATUS_CANCEL_OK)
        insert_hash2 = get_insert_hash(now, gwcommon.GW_ALARM_STATUS_NORMAL, test_pattern_name, gwcommon.GW_KISYS_STATUS_KISYS_CONNECT_CANCEL)
        event_ids = insert_event_data(self.conn, [insert_hash1, insert_hash2])
        insert_hash1['error_event_id'] = event_ids[0]
        insert_hash1['normal_event_id'] = event_ids[1]
        insert_hash1['incident_status'] = gwcommon.GW_INCIDENT_STATUS_CLOSE
        insert_incident_data(self.conn, [insert_hash1])
        expect_incident_id = '1'
        expect_kisys_incidentid = 'IT0000-00000000'
        update_gw_incident_data(self.conn, expect_incident_id, expect_kisys_incidentid)
        HELPER.insert_test_rule(self.conn, gwcommon.GW_KISYS_STATUS_WAITING_5, test_pattern_name)

        # 処理実行
        with self.assertLogs('send_to_bao.py') as cm:
            send_to_bao.main()

        # ログ内容の確認
        expect_error_event_id = event_ids[0]
        expect_normal_event_id = event_ids[1]

        self.assertEqual(cm.output, [
            'INFO:send_to_bao.py:マスターモードのため、マスター動作実行',
            'INFO:send_to_bao.py:KISYSメンテナンス期間に該当しないため処理を継続します。',
            'INFO:send_to_bao.py:イベント処理開始(1/1), gw_event_id=%s' % expect_normal_event_id,
            'INFO:send_to_bao.py:normal報処理開始 gw_event_id=%s' % expect_normal_event_id,
            'ERROR:send_to_bao.py:キャンセル処理:BAO無応答 gw_event_id=%s, gw_incident_id=%s, kisys_incidentid=%s' % (expect_normal_event_id, expect_incident_id, expect_kisys_incidentid),
            'INFO:send_to_bao.py:キャンセル処理:関連テーブルを更新しました。gw_event_id=%s, gw_incident_id=%s, kisys_incidentid=%s' % (expect_normal_event_id, expect_incident_id, expect_kisys_incidentid),
            'INFO:send_to_bao.py:gw_event_id=%s クローズしました(event_status=2)' % expect_normal_event_id,
            'INFO:send_to_bao.py:イベント処理(1/1)終了, gw_event_id=%s' % expect_normal_event_id,
            'INFO:send_to_bao.py:10秒待機します。',
        ])

        # DB更新結果の確認
        expect_error_kisys_status = gwcommon.GW_KISYS_STATUS_CANCEL_OK
        error_event_result = HELPER.get_updated_gw_events_data(self.conn, expect_error_event_id)
        self.assertEqual(error_event_result['kisys_status'], expect_error_kisys_status)
        expect_normal_kisys_status = gwcommon.GW_KISYS_STATUS_CANCEL_NORES
        normal_event_result = HELPER.get_updated_gw_events_data(self.conn, expect_normal_event_id)
        self.assertEqual(normal_event_result['kisys_status'], expect_normal_kisys_status)

    # @unittest.skip('TESTSKIP')
    @patch('gwcommon.MY_DB', HELPER.MY_DB_LOCAL)
    @patch('gwfunction.get_hostgroups_by_host')
    @patch('gwfunction.get_alias_by_host')
    @patch('bao_tm_post.BAO_TM_CLIENT.send')
    def test_error_normal_paired_rule30_cancel_BAO_NG(self, mock_bao_tm_client_send, mock_get_alias_by_host, mock_get_hostgroups_by_host):
        # モード設定
        HELPER.set_master_mode()
        HELPER.insert_kompira_rule(self.conn)

        # モック準備
        mock_get_hostgroups_by_host.return_value = []
        mock_get_alias_by_host.return_value = ''
        mock_bao_tm_client_send.return_value = 'Failure' # 失敗

        # テストデータ投入
        now = datetime.datetime.now()
        one_minute_ago = now - datetime.timedelta(minutes=1)
        test_pattern_name = 'test_error_normal_paired_rule30_cancel_BAO_NG'
        insert_hash1 = get_insert_hash(one_minute_ago, gwcommon.GW_ALARM_STATUS_ERROR, test_pattern_name, gwcommon.GW_KISYS_STATUS_CANCEL_OK)
        insert_hash2 = get_insert_hash(now, gwcommon.GW_ALARM_STATUS_NORMAL, test_pattern_name, gwcommon.GW_KISYS_STATUS_KISYS_CONNECT_CANCEL)
        event_ids = insert_event_data(self.conn, [insert_hash1, insert_hash2])
        insert_hash1['error_event_id'] = event_ids[0]
        insert_hash1['normal_event_id'] = event_ids[1]
        insert_hash1['incident_status'] = gwcommon.GW_INCIDENT_STATUS_CLOSE
        insert_incident_data(self.conn, [insert_hash1])
        expect_incident_id = '1'
        expect_kisys_incidentid = 'IT0000-00000000'
        update_gw_incident_data(self.conn, expect_incident_id, expect_kisys_incidentid)
        HELPER.insert_test_rule(self.conn, gwcommon.GW_KISYS_STATUS_WAITING_5, test_pattern_name)

        # 処理実行
        with self.assertLogs('send_to_bao.py') as cm:
            send_to_bao.main()

        # ログ内容の確認
        expect_error_event_id = event_ids[0]
        expect_normal_event_id = event_ids[1]

        self.assertEqual(cm.output, [
            'INFO:send_to_bao.py:マスターモードのため、マスター動作実行',
            'INFO:send_to_bao.py:KISYSメンテナンス期間に該当しないため処理を継続します。',
            'INFO:send_to_bao.py:イベント処理開始(1/1), gw_event_id=%s' % expect_normal_event_id,
            'INFO:send_to_bao.py:normal報処理開始 gw_event_id=%s' % expect_normal_event_id,
            'ERROR:send_to_bao.py:キャンセル処理:BAO更新失敗 gw_event_id=%s, gw_incident_id=%s, kisys_incidentid=%s' % (expect_normal_event_id, expect_incident_id, expect_kisys_incidentid),
            'INFO:send_to_bao.py:キャンセル処理:関連テーブルを更新しました。gw_event_id=%s, gw_incident_id=%s, kisys_incidentid=%s' % (expect_normal_event_id, expect_incident_id, expect_kisys_incidentid),
            'INFO:send_to_bao.py:gw_event_id=%s クローズしました(event_status=2)' % expect_normal_event_id,
            'INFO:send_to_bao.py:イベント処理(1/1)終了, gw_event_id=%s' % expect_normal_event_id,
            'INFO:send_to_bao.py:10秒待機します。',
        ])

        # DB更新結果の確認
        expect_error_kisys_status = gwcommon.GW_KISYS_STATUS_CANCEL_OK
        error_event_result = HELPER.get_updated_gw_events_data(self.conn, expect_error_event_id)
        self.assertEqual(error_event_result['kisys_status'], expect_error_kisys_status)
        expect_normal_kisys_status = gwcommon.GW_KISYS_STATUS_CANCEL_NG
        normal_event_result = HELPER.get_updated_gw_events_data(self.conn, expect_normal_event_id)
        self.assertEqual(normal_event_result['kisys_status'], expect_normal_kisys_status)

    # @unittest.skip('TESTSKIP')
    @patch('gwcommon.MY_DB', HELPER.MY_DB_LOCAL)
    @patch('gwfunction.get_hostgroups_by_host')
    @patch('gwfunction.get_alias_by_host')
    @patch('bao_tm_post.BAO_TM_CLIENT.send')
    @patch('requests.post')
    def test_kompira_OK(self, mock_requests_post, mock_bao_tm_client_send, mock_get_alias_by_host, mock_get_hostgroups_by_host):
        # モード設定
        HELPER.set_master_mode()
        HELPER.insert_kompira_rule(self.conn)

        # モック準備
        mock_get_hostgroups_by_host.return_value = [gwcommon.KOMPIRA_RELATION_HOSTGROUP]
        mock_get_alias_by_host.return_value = ''
        expect_kisys_incidentid = 'IT0000-00000000'
        mock_bao_tm_client_send.return_value = expect_kisys_incidentid # 成功
        dummy_response = requests.Response()
        dummy_response.status_code = 200 # 成功
        mock_requests_post.return_value = dummy_response

        # テストデータ投入
        now = datetime.datetime.now()
        one_minute_ago = now - datetime.timedelta(minutes=1)
        test_pattern_name = 'test_kompira_OK'
        insert_hash1 = get_insert_hash(one_minute_ago, gwcommon.GW_ALARM_STATUS_ERROR, test_pattern_name, gwcommon.GW_KISYS_STATUS_KISYS_CONNECT_NORULE)
        insert_hash2 = get_insert_hash(now, gwcommon.GW_ALARM_STATUS_NORMAL, test_pattern_name, gwcommon.GW_KISYS_STATUS_KISYS_CONNECT_NORULE)
        event_ids = insert_event_data(self.conn, [insert_hash1, insert_hash2])
        insert_hash1['error_event_id'] = event_ids[0]
        insert_hash1['normal_event_id'] = event_ids[1]
        insert_hash1['incident_status'] = gwcommon.GW_INCIDENT_STATUS_CLOSE
        insert_incident_data(self.conn, [insert_hash1])

        # 処理実行
        with self.assertLogs('send_to_bao.py') as cm:
            send_to_bao.main()

        # ログ内容の確認
        expect_error_event_id = event_ids[0]
        expect_normal_event_id = event_ids[1]
        expect_incident_id = '1'

        self.assertEqual(cm.output, [
            'INFO:send_to_bao.py:マスターモードのため、マスター動作実行',
            'INFO:send_to_bao.py:KISYSメンテナンス期間に該当しないため処理を継続します。',
            'INFO:send_to_bao.py:イベント処理開始(1/2), gw_event_id=%s' % expect_error_event_id,
            'INFO:send_to_bao.py:error報処理開始 gw_event_id=%s' % expect_error_event_id,
            'INFO:send_to_bao.py:error報処理:BAO連携成功 gw_event_id=%s' % expect_error_event_id,
            'INFO:send_to_bao.py:error報処理:関連テーブルを更新しました。gw_event_id=%s, gw_incident_id=%s, kisys_incidentid=%s' % (expect_error_event_id, expect_incident_id, expect_kisys_incidentid),
            'INFO:send_to_bao.py:error報処理:関連テーブルを更新しました。gw_event_id=%s, gw_incident_id=%s, kisys_incidentid=%s' % (expect_error_event_id, expect_incident_id, expect_kisys_incidentid),
            'INFO:send_to_bao.py:Kompira連携を開始します。kisys_incidentid=%s' % expect_kisys_incidentid,
            'INFO:send_to_bao.py:Kompiraへの送信に成功しました。kisys_incidentid=%s' % expect_kisys_incidentid,
            'INFO:send_to_bao.py:イベント処理(1/2)終了, gw_event_id=%s' % expect_error_event_id,
            'INFO:send_to_bao.py:イベント処理開始(2/2), gw_event_id=%s' % expect_normal_event_id,
            'INFO:send_to_bao.py:normal報処理開始 gw_event_id=%s' % expect_normal_event_id,
            'INFO:send_to_bao.py:normal報処理:BAO更新成功 gw_event_id=%s, gw_incident_id=%s, kisys_incidentid=%s' % (expect_normal_event_id, expect_incident_id, expect_kisys_incidentid),
            'INFO:send_to_bao.py:normal報処理:関連テーブルを更新しました。gw_event_id=%s, gw_incident_id=%s, kisys_incidentid=%s' % (expect_normal_event_id, expect_incident_id, expect_kisys_incidentid),
            'INFO:send_to_bao.py:Kompira連携を開始します。kisys_incidentid=%s' % expect_kisys_incidentid,
            'INFO:send_to_bao.py:Kompiraへの送信に成功しました。kisys_incidentid=%s' % expect_kisys_incidentid,
            'INFO:send_to_bao.py:イベント処理(2/2)終了, gw_event_id=%s' % expect_normal_event_id,
            'INFO:send_to_bao.py:10秒待機します。',
        ])

        # DB更新結果の確認
        expect_kisys_status = gwcommon.GW_KISYS_STATUS_NEW_OK + ',' + gwcommon.KOMPIRA_STATUS_SUCCESS
        error_event_result = HELPER.get_updated_gw_events_data(self.conn, expect_error_event_id)
        self.assertEqual(error_event_result['kisys_status'], expect_kisys_status)
        normal_event_result = HELPER.get_updated_gw_events_data(self.conn, expect_normal_event_id)
        self.assertEqual(normal_event_result['kisys_status'], expect_kisys_status)

    # @unittest.skip('TESTSKIP')
    @patch('gwcommon.MY_DB', HELPER.MY_DB_LOCAL)
    @patch('gwfunction.get_hostgroups_by_host')
    @patch('gwfunction.get_alias_by_host')
    @patch('bao_tm_post.BAO_TM_CLIENT.send')
    @patch('requests.post')
    def test_kompira_NG(self, mock_requests_post, mock_bao_tm_client_send, mock_get_alias_by_host, mock_get_hostgroups_by_host):
        # モード設定
        HELPER.set_master_mode()
        HELPER.insert_kompira_rule(self.conn)

        # モック準備
        mock_get_hostgroups_by_host.return_value = [gwcommon.KOMPIRA_RELATION_HOSTGROUP]
        mock_get_alias_by_host.return_value = ''
        expect_kisys_incidentid = 'IT0000-00000000'
        mock_bao_tm_client_send.return_value = expect_kisys_incidentid # 成功
        dummy_response = requests.Response()
        dummy_response.status_code = 400 # 失敗
        mock_requests_post.return_value = dummy_response

        # テストデータ投入
        now = datetime.datetime.now()
        one_minute_ago = now - datetime.timedelta(minutes=1)
        test_pattern_name = 'test_kompira_NG'
        insert_hash1 = get_insert_hash(one_minute_ago, gwcommon.GW_ALARM_STATUS_ERROR, test_pattern_name, gwcommon.GW_KISYS_STATUS_KISYS_CONNECT_NORULE)
        insert_hash2 = get_insert_hash(now, gwcommon.GW_ALARM_STATUS_NORMAL, test_pattern_name, gwcommon.GW_KISYS_STATUS_KISYS_CONNECT_NORULE)
        event_ids = insert_event_data(self.conn, [insert_hash1, insert_hash2])
        insert_hash1['error_event_id'] = event_ids[0]
        insert_hash1['normal_event_id'] = event_ids[1]
        insert_hash1['incident_status'] = gwcommon.GW_INCIDENT_STATUS_CLOSE
        insert_incident_data(self.conn, [insert_hash1])

        # 処理実行
        with self.assertLogs('send_to_bao.py') as cm:
            send_to_bao.main()

        # ログ内容の確認
        expect_error_event_id = event_ids[0]
        expect_normal_event_id = event_ids[1]
        expect_incident_id = '1'

        self.assertEqual(cm.output, [
            'INFO:send_to_bao.py:マスターモードのため、マスター動作実行',
            'INFO:send_to_bao.py:KISYSメンテナンス期間に該当しないため処理を継続します。',
            'INFO:send_to_bao.py:イベント処理開始(1/2), gw_event_id=%s' % expect_error_event_id,
            'INFO:send_to_bao.py:error報処理開始 gw_event_id=%s' % expect_error_event_id,
            'INFO:send_to_bao.py:error報処理:BAO連携成功 gw_event_id=%s' % expect_error_event_id,
            'INFO:send_to_bao.py:error報処理:関連テーブルを更新しました。gw_event_id=%s, gw_incident_id=%s, kisys_incidentid=%s' % (expect_error_event_id, expect_incident_id, expect_kisys_incidentid),
            'INFO:send_to_bao.py:error報処理:関連テーブルを更新しました。gw_event_id=%s, gw_incident_id=%s, kisys_incidentid=%s' % (expect_error_event_id, expect_incident_id, expect_kisys_incidentid),
            'INFO:send_to_bao.py:Kompira連携を開始します。kisys_incidentid=%s' % expect_kisys_incidentid,
            'ERROR:send_to_bao.py:Kompiraへの送信に失敗しました。kisys_incidentid=%s' % expect_kisys_incidentid,
            'INFO:send_to_bao.py:400 Client Error: None for url: None', # テスト用のダミーResponseによるエラーメッセージのため本番とは異なる可能性あり
            'INFO:send_to_bao.py:イベント処理(1/2)終了, gw_event_id=%s' % expect_error_event_id,
            'INFO:send_to_bao.py:イベント処理開始(2/2), gw_event_id=%s' % expect_normal_event_id,
            'INFO:send_to_bao.py:normal報処理開始 gw_event_id=%s' % expect_normal_event_id,
            'INFO:send_to_bao.py:normal報処理:BAO更新成功 gw_event_id=%s, gw_incident_id=%s, kisys_incidentid=%s' % (expect_normal_event_id, expect_incident_id, expect_kisys_incidentid),
            'INFO:send_to_bao.py:normal報処理:関連テーブルを更新しました。gw_event_id=%s, gw_incident_id=%s, kisys_incidentid=%s' % (expect_normal_event_id, expect_incident_id, expect_kisys_incidentid),
            'INFO:send_to_bao.py:Kompira連携を開始します。kisys_incidentid=%s' % expect_kisys_incidentid,
            'ERROR:send_to_bao.py:Kompiraへの送信に失敗しました。kisys_incidentid=%s' % expect_kisys_incidentid,
            'INFO:send_to_bao.py:400 Client Error: None for url: None', # テスト用のダミーResponseによるエラーメッセージのため本番とは異なる可能性あり
            'INFO:send_to_bao.py:イベント処理(2/2)終了, gw_event_id=%s' % expect_normal_event_id,
            'INFO:send_to_bao.py:10秒待機します。',
        ])

        # DB更新結果の確認
        expect_kisys_status = gwcommon.GW_KISYS_STATUS_NEW_OK + ',' + gwcommon.KOMPIRA_STATUS_FAILURE
        error_event_result = HELPER.get_updated_gw_events_data(self.conn, expect_error_event_id)
        self.assertEqual(error_event_result['kisys_status'], expect_kisys_status)
        normal_event_result = HELPER.get_updated_gw_events_data(self.conn, expect_normal_event_id)
        self.assertEqual(normal_event_result['kisys_status'], expect_kisys_status)

    # @unittest.skip('TESTSKIP')
    @patch('gwcommon.MY_DB', HELPER.MY_DB_LOCAL)
    @patch('gwfunction.get_hostgroups_by_host')
    @patch('gwfunction.get_alias_by_host')
    @patch('bao_tm_post.BAO_TM_CLIENT.send')
    def test_kompira_NOSEND(self, mock_bao_tm_client_send, mock_get_alias_by_host, mock_get_hostgroups_by_host):
        # モード設定
        HELPER.set_master_mode()
        HELPER.insert_kompira_rule(self.conn)

        # モック準備
        mock_get_hostgroups_by_host.return_value = []
        mock_get_alias_by_host.return_value = ''
        expect_kisys_incidentid = 'IT0000-00000000'
        mock_bao_tm_client_send.return_value = expect_kisys_incidentid # 成功

        # テストデータ投入
        now = datetime.datetime.now()
        one_minute_ago = now - datetime.timedelta(minutes=1)
        test_pattern_name = 'test_kompira_NOSEND'
        insert_hash1 = get_insert_hash(one_minute_ago, gwcommon.GW_ALARM_STATUS_ERROR, test_pattern_name, gwcommon.GW_KISYS_STATUS_KISYS_CONNECT_NORULE)
        insert_hash2 = get_insert_hash(now, gwcommon.GW_ALARM_STATUS_NORMAL, test_pattern_name, gwcommon.GW_KISYS_STATUS_KISYS_CONNECT_NORULE)
        event_ids = insert_event_data(self.conn, [insert_hash1, insert_hash2])
        insert_hash1['error_event_id'] = event_ids[0]
        insert_hash1['normal_event_id'] = event_ids[1]
        insert_hash1['incident_status'] = gwcommon.GW_INCIDENT_STATUS_CLOSE
        insert_incident_data(self.conn, [insert_hash1])

        # 処理実行
        with self.assertLogs('send_to_bao.py') as cm:
            send_to_bao.main()

        # ログ内容の確認
        expect_error_event_id = event_ids[0]
        expect_normal_event_id = event_ids[1]
        expect_incident_id = '1'

        self.assertEqual(cm.output, [
            'INFO:send_to_bao.py:マスターモードのため、マスター動作実行',
            'INFO:send_to_bao.py:KISYSメンテナンス期間に該当しないため処理を継続します。',
            'INFO:send_to_bao.py:イベント処理開始(1/2), gw_event_id=%s' % expect_error_event_id,
            'INFO:send_to_bao.py:error報処理開始 gw_event_id=%s' % expect_error_event_id,
            'INFO:send_to_bao.py:error報処理:BAO連携成功 gw_event_id=%s' % expect_error_event_id,
            'INFO:send_to_bao.py:error報処理:関連テーブルを更新しました。gw_event_id=%s, gw_incident_id=%s, kisys_incidentid=%s' % (expect_error_event_id, expect_incident_id, expect_kisys_incidentid),
            'INFO:send_to_bao.py:error報処理:関連テーブルを更新しました。gw_event_id=%s, gw_incident_id=%s, kisys_incidentid=%s' % (expect_error_event_id, expect_incident_id, expect_kisys_incidentid),
            'INFO:send_to_bao.py:Kompira連携しません。kisys_incidentid=%s' % expect_kisys_incidentid,
            'INFO:send_to_bao.py:イベント処理(1/2)終了, gw_event_id=%s' % expect_error_event_id,
            'INFO:send_to_bao.py:イベント処理開始(2/2), gw_event_id=%s' % expect_normal_event_id,
            'INFO:send_to_bao.py:normal報処理開始 gw_event_id=%s' % expect_normal_event_id,
            'INFO:send_to_bao.py:normal報処理:BAO更新成功 gw_event_id=%s, gw_incident_id=%s, kisys_incidentid=%s' % (expect_normal_event_id, expect_incident_id, expect_kisys_incidentid),
            'INFO:send_to_bao.py:normal報処理:関連テーブルを更新しました。gw_event_id=%s, gw_incident_id=%s, kisys_incidentid=%s' % (expect_normal_event_id, expect_incident_id, expect_kisys_incidentid),
            'INFO:send_to_bao.py:Kompira連携しません。kisys_incidentid=%s' % expect_kisys_incidentid,
            'INFO:send_to_bao.py:イベント処理(2/2)終了, gw_event_id=%s' % expect_normal_event_id,
            'INFO:send_to_bao.py:10秒待機します。',
        ])

        # DB更新結果の確認
        expect_kisys_status = gwcommon.GW_KISYS_STATUS_NEW_OK + ',' + gwcommon.KOMPIRA_STATUS_NOSEND
        error_event_result = HELPER.get_updated_gw_events_data(self.conn, expect_error_event_id)
        self.assertEqual(error_event_result['kisys_status'], expect_kisys_status)
        normal_event_result = HELPER.get_updated_gw_events_data(self.conn, expect_normal_event_id)
        self.assertEqual(normal_event_result['kisys_status'], expect_kisys_status)

########################################################################
## Test Helper
########################################################################

def get_insert_hash(now, alarm_status, str, kisys_status=None):
    # ミリ秒を .XXX000 にそろえるための変換 ex. 123456 -> 123000
    alarm_time_org = now.strftime('%Y-%m-%d@%H:%M:%S.%f')[:-3]
    alarm_time = datetime.datetime.strptime(alarm_time_org, '%Y-%m-%d@%H:%M:%S.%f')
    host = 'host_%s' % str
    return {
        'summary': 'summary_%s' % str,
        'device': 'device_%s' % str,
        'detected_time': now.strftime("%Y-%m-%d %H:%M:%S"),
        'detected_host': 129,
        'customer_ci': 'customer_ci_%s' % str,
        'hostname': 'hostname_%s' % str,
        'ci_name': 'ci_name_%s' % str,
        'alarm_status': alarm_status,
        'customer_name': 'customer_name_%s' % str,
        'host': bytearray(host.encode()),
        'alarm_time': alarm_time,
        'error_event_id': None,
        'normal_event_id': None,
        'op_comment': 'op_comment_%s' % str,
        'project_code': 'project_code%s' % str,
        'kisys_status': kisys_status,
    }

def insert_event_data(conn, insert_hash_list):
    event_ids = []
    for insert_hash in insert_hash_list:
        cur = conn.cursor()
        insert_item = 'update_time, detected_time, detected_host, customer_ci, customer_name,\
                    hostname, alarm_time, ci_name, device, alarm_status, summary, host, kisys_status'
        insert_value = 'now(), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s'
        value = (insert_hash['detected_time'], insert_hash['detected_host'], insert_hash['customer_ci'],
            insert_hash['customer_name'], insert_hash['hostname'], insert_hash['alarm_time'],
            insert_hash['ci_name'], insert_hash['device'], insert_hash['alarm_status'], insert_hash['summary'], insert_hash['host'], insert_hash['kisys_status'])
        sql = 'INSERT INTO gw_events (%s) VALUES (%s)' % (insert_item, insert_value)
        cur.execute(sql, value)

        last_id_sql = 'SELECT LAST_INSERT_ID()'
        cur.execute(last_id_sql)
        last_insert_id = cur.fetchone()[0]
        event_ids.append(last_insert_id)

        cur.close()
    conn.commit()
    return event_ids

def insert_incident_data(conn, insert_hash_list):
    for insert_hash in insert_hash_list:
        cur = conn.cursor()
        insert_item = 'incident_status,update_time,detected_host,error_event_id,normal_event_id,\
        customer_name,hostname,ci_name,op_comment,project_code'
        insert_value = '%s, now(), %s, %s, %s, %s, %s, %s, %s, %s'
        value = (insert_hash['incident_status'], insert_hash['detected_host'], insert_hash['error_event_id'], insert_hash['normal_event_id'],
            insert_hash['customer_name'], insert_hash['hostname'], insert_hash['ci_name'], insert_hash['op_comment'], insert_hash['project_code'])
        sql = 'INSERT INTO gw_incidents (%s) VALUES (%s)' % (insert_item, insert_value)
        cur.execute(sql, value)
        
        last_id_sql = 'SELECT LAST_INSERT_ID()'
        cur.execute(last_id_sql)
        last_insert_id = cur.fetchone()[0]

        cur.close()

        error_event_id = insert_hash['error_event_id']
        normal_event_id = insert_hash['normal_event_id']
        if error_event_id != None and normal_event_id != None:
            update_hash_error = {
                'event_status': gwcommon.GW_EVENT_STATUS_CLOSE,
                'gw_incident_id': last_insert_id,
                'gw_event_id': error_event_id,
            }
            HELPER.update_event_data(conn, update_hash_error)

            update_hash_normal = {
                'event_status': gwcommon.GW_EVENT_STATUS_CLOSE,
                'gw_incident_id': last_insert_id,
                'gw_event_id': normal_event_id,
            }
            HELPER.update_event_data(conn, update_hash_normal)

        elif error_event_id != None:
            update_hash = {
                'event_status': gwcommon.GW_EVENT_STATUS_ACTIVE,
                'gw_incident_id': last_insert_id,
                'gw_event_id': error_event_id,
            }
            HELPER.update_event_data(conn, update_hash)

        elif normal_event_id != None:
            update_hash = {
                'event_status': gwcommon.GW_EVENT_STATUS_CLOSE,
                'gw_incident_id': last_insert_id,
                'gw_event_id': normal_event_id,
            }
            HELPER.update_event_data(conn, update_hash)

    conn.commit()

def update_gw_incident_data(conn, gw_incident_id, kisys_incidentid):
    cur = conn.cursor()
    value = (kisys_incidentid, gw_incident_id)
    sql = "UPDATE gw_incidents SET kisys_incidentid=%s, update_time=now(3) WHERE gw_incident_id=%s"
    cur.execute(sql, value)
    cur.close()
    conn.commit()

if __name__ == '__main__':
    unittest.main()

import copy
import datetime
import glob
import mysql.connector
import os
import pathlib
import sys
import unittest
from unittest.mock import patch

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import insert_gw_incidents
import gwcommon
import test_helper as HELPER

@patch('gwcommon.MY_USER', HELPER.MY_USER)
@patch('gwcommon.MY_PASSWD', HELPER.MY_PASSWD)
# @patch('gwcommon.MY_DB', HELPER.MY_DB_LOCAL)
class InsertGwIncidentsTest(unittest.TestCase):

    maxDiff = None
    @classmethod
    def setUpClass(self):
        # DB接続
        conn = HELPER.db_connect()

        # 無限ループ停止のためunittestモード設定
        HELPER.set_unittest_mode()

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
        with self.assertRaises(SystemExit), self.assertLogs('insert_gw_incidents.py') as cm:
            insert_gw_incidents.main()

        # ログ内容の確認
        self.assertEqual(cm.output, [
            'INFO:insert_gw_incidents.py:ストップモードのため、exitで処理を終了します',
        ])

    # @unittest.skip('TESTSKIP')
    @patch('gwcommon.MY_DB', HELPER.MY_DB_LOCAL)
    def test_test_mode(self):
        # モード設定
        HELPER.set_test_mode()

        # 処理実行
        with self.assertLogs('insert_gw_incidents.py') as cm:
            insert_gw_incidents.main()

        # ログ内容の確認
        self.assertEqual(cm.output, [
            'INFO:insert_gw_incidents.py:testモードのため、テストモードで動作実行',
            'INFO:insert_gw_incidents.py:処理対象イベント無し。',
            'INFO:insert_gw_incidents.py:1秒待機します。',
        ])

    # @unittest.skip('TESTSKIP')
    @patch('gwcommon.MY_DB', HELPER.MY_DB_LOCAL)
    def test_master_mode(self):
        # モード設定
        HELPER.set_master_mode()

        # 処理実行
        with self.assertLogs('insert_gw_incidents.py') as cm:
            insert_gw_incidents.main()

        # ログ内容の確認
        self.assertEqual(cm.output, [
            'INFO:insert_gw_incidents.py:マスターモードのため、マスター動作実行',
            'INFO:insert_gw_incidents.py:処理対象イベント無し。',
            'INFO:insert_gw_incidents.py:1秒待機します。',
        ])

    # @unittest.skip('TESTSKIP')
    @patch('gwcommon.MY_DB', HELPER.MY_DB_REMOTE)
    def test_slave_mode(self):
        # モード設定
        HELPER.set_slave_mode()

        # 処理実行
        with self.assertLogs('insert_gw_incidents.py') as cm:
            insert_gw_incidents.main()

        # ログ内容の確認
        self.assertEqual(cm.output, [
            'INFO:insert_gw_incidents.py:スレーブモードのため、スレーブ動作実行',
        ])

    # @unittest.skip('TESTSKIP')
    @patch('gwcommon.MY_DB', HELPER.MY_DB_LOCAL)
    def test_dup_check(self):
        # モード設定
        HELPER.set_master_mode()

        # テストデータ投入
        now = datetime.datetime.now()
        insert_hash1 = get_insert_hash(now, gwcommon.GW_ALARM_STATUS_ERROR, 'test_dup_check')
        event_ids = HELPER.insert_event_data(self.conn, [insert_hash1, insert_hash1])
        insert_hash1['error_event_id'] = event_ids[0]
        HELPER.insert_incident_data(self.conn, [insert_hash1])

        # 処理実行
        with self.assertLogs('insert_gw_incidents.py') as cm:
            insert_gw_incidents.main()

        # ログ内容の確認
        expect_event_id = event_ids[1]

        self.assertEqual(cm.output, [
            'INFO:insert_gw_incidents.py:マスターモードのため、マスター動作実行',
            'INFO:insert_gw_incidents.py:イベント処理開始(1/1), gw_event_id=%s' % expect_event_id,
            'INFO:insert_gw_incidents.py:重複レコードです gw_event_id=%s, event_status=99 にUPDATE' % expect_event_id,
            'INFO:insert_gw_incidents.py:イベント処理(1/1)終了, gw_event_id=%s' % expect_event_id,
            'INFO:insert_gw_incidents.py:1秒待機します。',
        ])

        # DB更新結果の確認
        result = HELPER.get_updated_gw_events_data(self.conn, expect_event_id)
        self.assertEqual(result['event_status'], int(gwcommon.GW_EVENT_STATUS_DUP))

    # @unittest.skip('TESTSKIP')
    @patch('gwcommon.MY_DB', HELPER.MY_DB_LOCAL)
    def test_insert_error_norule(self):
        # モード設定
        HELPER.set_master_mode()

        # テストデータ投入
        now = datetime.datetime.now()
        insert_hash1 = get_insert_hash(now, gwcommon.GW_ALARM_STATUS_ERROR, 'test_insert_error_norule')
        event_ids = HELPER.insert_event_data(self.conn, [insert_hash1])

        # 処理実行
        with self.assertLogs('insert_gw_incidents.py') as cm:
            insert_gw_incidents.main()

        # ログ内容の確認
        expect_event_id = event_ids[0]
        expect_incident_id = '1'

        self.assertEqual(cm.output, [
            'INFO:insert_gw_incidents.py:マスターモードのため、マスター動作実行',
            'INFO:insert_gw_incidents.py:イベント処理開始(1/1), gw_event_id=%s' % expect_event_id,
            'INFO:insert_gw_incidents.py:error報処理:インシデント登録しました。gw_incident_id=%s' % expect_incident_id,
            'INFO:insert_gw_incidents.py:error報処理:イベントID：%sとインシデントID：%sを紐づけました。' % (expect_event_id, expect_incident_id),
            'INFO:insert_gw_incidents.py:イベント処理(1/1)終了, gw_event_id=%s' % expect_event_id,
            'INFO:insert_gw_incidents.py:1秒待機します。',
        ])

        # DB更新結果の確認
        event_result = HELPER.get_updated_gw_events_data(self.conn, expect_event_id)
        self.assertEqual(event_result['event_status'], int(gwcommon.GW_EVENT_STATUS_ACTIVE))
        incident_result = HELPER.get_updated_gw_incidents_data(self.conn, expect_incident_id)
        self.assertEqual(incident_result['error_event_id'], expect_event_id)

    # @unittest.skip('TESTSKIP')
    @patch('gwcommon.MY_DB', HELPER.MY_DB_LOCAL)
    def test_insert_error_rules(self):
        test_patterns = [
            { # 4-2
                'action_no':gwcommon.GW_KISYS_STATUS_NOSEND,
                'event_status':gwcommon.GW_EVENT_STATUS_ACTIVE,
                'kisys_status':gwcommon.GW_KISYS_STATUS_NOSEND,
                'incident_status':gwcommon.GW_INCIDENT_STATUS_ACTIVE,
                'result_log':'INFO:insert_gw_incidents.py:error報処理:イベントID：%sとインシデントID：%sを紐づけました。',
            },
            { # 4-3
                'action_no':gwcommon.GW_KISYS_STATUS_NOPATOLAMP,
                'event_status':gwcommon.GW_EVENT_STATUS_ACTIVE,
                'kisys_status':gwcommon.GW_KISYS_STATUS_NOPATOLAMP,
                'incident_status':gwcommon.GW_INCIDENT_STATUS_ACTIVE,
                'result_log':'INFO:insert_gw_incidents.py:error報処理:イベントID：%sとインシデントID：%sを紐づけました。',
            },
            { # 4-4
                'action_no':gwcommon.GW_KISYS_STATUS_WAITING_5,
                'event_status':gwcommon.GW_EVENT_STATUS_NEW,
                'kisys_status':gwcommon.GW_KISYS_STATUS_WAITING_5,
                'incident_status':gwcommon.GW_INCIDENT_STATUS_ACTIVE,
                'result_log':'INFO:insert_gw_incidents.py:キャンセル待ちします(5分)(gw_event_id=%s, event_status=%s)',
            },
            { # 4-5
                'action_no':gwcommon.GW_KISYS_STATUS_WAITING_10,
                'event_status':gwcommon.GW_EVENT_STATUS_NEW,
                'kisys_status':gwcommon.GW_KISYS_STATUS_WAITING_10,
                'incident_status':gwcommon.GW_INCIDENT_STATUS_ACTIVE,
                'result_log':'INFO:insert_gw_incidents.py:キャンセル待ちします(10分)(gw_event_id=%s, event_status=%s)',
            },
            { # 4-6
                'action_no':gwcommon.GW_KISYS_STATUS_WAITING_15,
                'event_status':gwcommon.GW_EVENT_STATUS_NEW,
                'kisys_status':gwcommon.GW_KISYS_STATUS_WAITING_15,
                'incident_status':gwcommon.GW_INCIDENT_STATUS_ACTIVE,
                'result_log':'INFO:insert_gw_incidents.py:キャンセル待ちします(15分)(gw_event_id=%s, event_status=%s)',
            },
            { # 4-7
                'action_no':gwcommon.GW_KISYS_STATUS_WAITING_20,
                'event_status':gwcommon.GW_EVENT_STATUS_NEW,
                'kisys_status':gwcommon.GW_KISYS_STATUS_WAITING_20,
                'incident_status':gwcommon.GW_INCIDENT_STATUS_ACTIVE,
                'result_log':'INFO:insert_gw_incidents.py:キャンセル待ちします(20分)(gw_event_id=%s, event_status=%s)',
            },
            { # 4-8
                'action_no':gwcommon.GW_KISYS_STATUS_WAITING_25,
                'event_status':gwcommon.GW_EVENT_STATUS_NEW,
                'kisys_status':gwcommon.GW_KISYS_STATUS_WAITING_25,
                'incident_status':gwcommon.GW_INCIDENT_STATUS_ACTIVE,
                'result_log':'INFO:insert_gw_incidents.py:キャンセル待ちします(25分)(gw_event_id=%s, event_status=%s)',
            },
            { # 4-9
                'action_no':gwcommon.GW_KISYS_STATUS_WAITING_30,
                'event_status':gwcommon.GW_EVENT_STATUS_NEW,
                'kisys_status':gwcommon.GW_KISYS_STATUS_WAITING_30,
                'incident_status':gwcommon.GW_INCIDENT_STATUS_ACTIVE,
                'result_log':'INFO:insert_gw_incidents.py:キャンセル待ちします(30分)(gw_event_id=%s, event_status=%s)',
            },
        ]
        # モード設定
        HELPER.set_master_mode()

        # テストデータ投入
        HELPER.insert_test_rule(self.conn, gwcommon.GW_KISYS_STATUS_NOSEND,     'test_insert_error_rule10')
        HELPER.insert_test_rule(self.conn, gwcommon.GW_KISYS_STATUS_NOPATOLAMP, 'test_insert_error_rule20')
        HELPER.insert_test_rule(self.conn, gwcommon.GW_KISYS_STATUS_WAITING_5,  'test_insert_error_rule30')
        HELPER.insert_test_rule(self.conn, gwcommon.GW_KISYS_STATUS_WAITING_10, 'test_insert_error_rule31')
        HELPER.insert_test_rule(self.conn, gwcommon.GW_KISYS_STATUS_WAITING_15, 'test_insert_error_rule32')
        HELPER.insert_test_rule(self.conn, gwcommon.GW_KISYS_STATUS_WAITING_20, 'test_insert_error_rule33')
        HELPER.insert_test_rule(self.conn, gwcommon.GW_KISYS_STATUS_WAITING_25, 'test_insert_error_rule34')
        HELPER.insert_test_rule(self.conn, gwcommon.GW_KISYS_STATUS_WAITING_30, 'test_insert_error_rule35')

        expect_logs = [
            'INFO:insert_gw_incidents.py:マスターモードのため、マスター動作実行',
        ]

        for i, test_pattern in enumerate(test_patterns):

            now = datetime.datetime.now()
            test_pattern_name = 'test_insert_error_rule' + test_pattern['action_no']
            insert_hash = get_insert_hash(now, gwcommon.GW_ALARM_STATUS_ERROR, test_pattern_name)
            event_ids = HELPER.insert_event_data(self.conn, [insert_hash])

            # ログ内容の確認
            expect_event_id = i+1
            # expect_event_id = event_ids[0]
            expect_incident_id = i+1

            expect_log = test_pattern['result_log'] % (expect_event_id, expect_incident_id)
            if test_pattern['action_no'] in gwcommon.GW_KISYS_STATUS_WAITING_LIST:
                expect_log = test_pattern['result_log'] % (expect_event_id, test_pattern['event_status'])
            
            expect_logs.extend([
                'INFO:insert_gw_incidents.py:イベント処理開始(%s/%s), gw_event_id=%s' % (i+1, len(test_patterns), expect_event_id),
                'INFO:insert_gw_incidents.py:error報処理:インシデント登録しました。gw_incident_id=%s' % expect_incident_id,
                expect_log,
                'INFO:insert_gw_incidents.py:イベント処理(%s/%s)終了, gw_event_id=%s' % (i+1, len(test_patterns), expect_event_id)
            ])

        # 処理実行
        with self.assertLogs('insert_gw_incidents.py') as cm:
            insert_gw_incidents.main()

        # ログ内容の確認
        expect_logs.extend([
            'INFO:insert_gw_incidents.py:1秒待機します。'
        ])
        self.assertEqual(cm.output, expect_logs)

        for i, test_pattern in enumerate(test_patterns):
            with self.subTest('case%s test_pattern=%s' % (i, test_pattern)):
                expect_event_id = i+1
                expect_incident_id = i+1

                # DB更新結果の確認
                event_result = HELPER.get_updated_gw_events_data(self.conn, expect_event_id)
                self.assertEqual(event_result['event_status'], int(test_pattern['event_status']))
                self.assertEqual(event_result['kisys_status'], test_pattern['kisys_status'])
                incident_result = HELPER.get_updated_gw_incidents_data(self.conn, expect_incident_id)
                self.assertEqual(incident_result['error_event_id'], expect_event_id)
                self.assertEqual(incident_result['incident_status'], int(test_pattern['incident_status']))

    # @unittest.skip('TESTSKIP')
    @patch('gwcommon.MY_DB', HELPER.MY_DB_LOCAL)
    @patch('gwfunction.get_hostgroups_by_host')
    def test_insert_error_norule_hostgroup(self, mock_get_hostgroups_by_host):
        # モード設定
        HELPER.set_master_mode()
        mock_get_hostgroups_by_host.return_value = [gwcommon.KISYS_RELATION_HOSTGROUP]

        # テストデータ投入
        now = datetime.datetime.now()
        insert_hash = get_insert_hash(now, gwcommon.GW_ALARM_STATUS_ERROR, 'test_insert_error_norule_hostgroup')
        event_ids = HELPER.insert_event_data(self.conn, [insert_hash])

        # 処理実行
        with self.assertLogs('insert_gw_incidents.py') as cm:
            insert_gw_incidents.main()

        # ログ内容の確認
        expect_event_id = event_ids[0]
        expect_incident_id = '1'

        self.assertEqual(cm.output, [
            'INFO:insert_gw_incidents.py:マスターモードのため、マスター動作実行',
            'INFO:insert_gw_incidents.py:イベント処理開始(1/1), gw_event_id=%s' % expect_event_id,
            'INFO:insert_gw_incidents.py:error報処理:インシデント登録しました。gw_incident_id=%s' % expect_incident_id,
            'INFO:insert_gw_incidents.py:error報処理:イベントID：%sとインシデントID：%sを紐づけました。' % (expect_event_id, expect_incident_id),
            'INFO:insert_gw_incidents.py:イベント処理(1/1)終了, gw_event_id=%s' % expect_event_id,
            'INFO:insert_gw_incidents.py:1秒待機します。',
        ])

        # DB更新結果の確認
        event_result = HELPER.get_updated_gw_events_data(self.conn, expect_event_id)
        self.assertEqual(event_result['event_status'], int(gwcommon.GW_EVENT_STATUS_ACTIVE))
        self.assertEqual(event_result['kisys_status'], gwcommon.GW_KISYS_STATUS_KISYS_CONNECT_NORULE)
        incident_result = HELPER.get_updated_gw_incidents_data(self.conn, expect_incident_id)
        self.assertEqual(incident_result['error_event_id'], expect_event_id)

    # @unittest.skip('TESTSKIP')
    @patch('gwcommon.MY_DB', HELPER.MY_DB_LOCAL)
    @patch('gwfunction.get_hostgroups_by_host')
    def test_insert_error_norule_nohostgroup(self, mock_get_hostgroups_by_host):
        # モード設定
        HELPER.set_master_mode()
        mock_get_hostgroups_by_host.return_value = []

        # テストデータ投入
        now = datetime.datetime.now()
        insert_hash = get_insert_hash(now, gwcommon.GW_ALARM_STATUS_ERROR, 'test_insert_error_norule_nohostgroup')
        event_ids = HELPER.insert_event_data(self.conn, [insert_hash])

        # 処理実行
        with self.assertLogs('insert_gw_incidents.py') as cm:
            insert_gw_incidents.main()

        # ログ内容の確認
        expect_event_id = event_ids[0]
        expect_incident_id = '1'

        self.assertEqual(cm.output, [
            'INFO:insert_gw_incidents.py:マスターモードのため、マスター動作実行',
            'INFO:insert_gw_incidents.py:イベント処理開始(1/1), gw_event_id=%s' % expect_event_id,
            'INFO:insert_gw_incidents.py:error報処理:インシデント登録しました。gw_incident_id=%s' % expect_incident_id,
            'INFO:insert_gw_incidents.py:error報処理:イベントID：%sとインシデントID：%sを紐づけました。' % (expect_event_id, expect_incident_id),
            'INFO:insert_gw_incidents.py:イベント処理(1/1)終了, gw_event_id=%s' % expect_event_id,
            'INFO:insert_gw_incidents.py:1秒待機します。',
        ])

        # DB更新結果の確認
        event_result = HELPER.get_updated_gw_events_data(self.conn, expect_event_id)
        self.assertEqual(event_result['event_status'], int(gwcommon.GW_EVENT_STATUS_ACTIVE))
        self.assertEqual(event_result['kisys_status'], gwcommon.GW_KISYS_STATUS_NOSEND_BY_HOSTGROUP)
        incident_result = HELPER.get_updated_gw_incidents_data(self.conn, expect_incident_id)
        self.assertEqual(incident_result['error_event_id'], expect_event_id)

    # @unittest.skip('TESTSKIP')
    @patch('gwcommon.MY_DB', HELPER.MY_DB_LOCAL)
    @patch('gwfunction.get_hostgroups_by_host')
    def test_insert_error_rule30_timeout_hostgroup(self, mock_get_hostgroups_by_host):
        # モード設定
        HELPER.set_master_mode()
        mock_get_hostgroups_by_host.return_value = [gwcommon.KISYS_RELATION_HOSTGROUP]

        # テストデータ投入
        HELPER.insert_test_rule(self.conn, gwcommon.GW_KISYS_STATUS_WAITING_5, 'test_insert_error_rule30_timeout_hostgroup')
        now = datetime.datetime.now()
        yesterday = now - datetime.timedelta(days=1)
        insert_hash = get_insert_hash(yesterday, gwcommon.GW_ALARM_STATUS_ERROR, 'test_insert_error_rule30_timeout_hostgroup')
        event_ids = HELPER.insert_event_data(self.conn, [insert_hash])

        # 処理実行
        with self.assertLogs('insert_gw_incidents.py') as cm:
            insert_gw_incidents.main()

        # ログ内容の確認
        expect_event_id = event_ids[0]
        expect_incident_id = '1'

        self.assertEqual(cm.output, [
            'INFO:insert_gw_incidents.py:マスターモードのため、マスター動作実行',
            'INFO:insert_gw_incidents.py:イベント処理開始(1/1), gw_event_id=%s' % expect_event_id,
            'INFO:insert_gw_incidents.py:error報処理:インシデント登録しました。gw_incident_id=%s' % expect_incident_id,
            'INFO:insert_gw_incidents.py:error報処理:キャンセル待ちタイムアウト、BAO連携する gw_event_id=%s' % expect_event_id,
            'INFO:insert_gw_incidents.py:イベント処理(1/1)終了, gw_event_id=%s' % expect_event_id,
            'INFO:insert_gw_incidents.py:1秒待機します。',
        ])

        # DB更新結果の確認
        event_result = HELPER.get_updated_gw_events_data(self.conn, expect_event_id)
        self.assertEqual(event_result['event_status'], int(gwcommon.GW_EVENT_STATUS_ACTIVE))
        self.assertEqual(event_result['kisys_status'], gwcommon.GW_KISYS_STATUS_KISYS_CONNECT_NORECOVERY)
        incident_result = HELPER.get_updated_gw_incidents_data(self.conn, expect_incident_id)
        self.assertEqual(incident_result['error_event_id'], expect_event_id)

    # @unittest.skip('TESTSKIP')
    @patch('gwcommon.MY_DB', HELPER.MY_DB_LOCAL)
    @patch('gwfunction.get_hostgroups_by_host')
    def test_insert_error_rule30_timeout_nohostgroup(self, mock_get_hostgroups_by_host):
        # モード設定
        HELPER.set_master_mode()
        mock_get_hostgroups_by_host.return_value = []

        # テストデータ投入
        HELPER.insert_test_rule(self.conn, gwcommon.GW_KISYS_STATUS_WAITING_5, 'test_insert_error_rule30_timeout_nohostgroup')
        now = datetime.datetime.now()
        yesterday = now - datetime.timedelta(days=1)
        insert_hash = get_insert_hash(yesterday, gwcommon.GW_ALARM_STATUS_ERROR, 'test_insert_error_rule30_timeout_nohostgroup')
        event_ids = HELPER.insert_event_data(self.conn, [insert_hash])

        # 処理実行
        with self.assertLogs('insert_gw_incidents.py') as cm:
            insert_gw_incidents.main()

        # ログ内容の確認
        expect_event_id = event_ids[0]
        expect_incident_id = '1'

        self.assertEqual(cm.output, [
            'INFO:insert_gw_incidents.py:マスターモードのため、マスター動作実行',
            'INFO:insert_gw_incidents.py:イベント処理開始(1/1), gw_event_id=%s' % expect_event_id,
            'INFO:insert_gw_incidents.py:error報処理:インシデント登録しました。gw_incident_id=%s' % expect_incident_id,
            'INFO:insert_gw_incidents.py:error報処理:キャンセル待ちタイムアウト、BAO連携しない gw_event_id=%s' % expect_event_id,
            'INFO:insert_gw_incidents.py:イベント処理(1/1)終了, gw_event_id=%s' % expect_event_id,
            'INFO:insert_gw_incidents.py:1秒待機します。',
        ])

        # DB更新結果の確認
        event_result = HELPER.get_updated_gw_events_data(self.conn, expect_event_id)
        self.assertEqual(event_result['event_status'], int(gwcommon.GW_EVENT_STATUS_ACTIVE))
        self.assertEqual(event_result['kisys_status'], gwcommon.GW_KISYS_STATUS_NORECOVERY_NOSEND)
        incident_result = HELPER.get_updated_gw_incidents_data(self.conn, expect_incident_id)
        self.assertEqual(incident_result['error_event_id'], expect_event_id)

    # @unittest.skip('TESTSKIP')
    @patch('gwcommon.MY_DB', HELPER.MY_DB_LOCAL)
    def test_insert_normal_norule(self):
        # モード設定
        HELPER.set_master_mode()

        # テストデータ投入
        now = datetime.datetime.now()
        insert_hash1 = get_insert_hash(now, gwcommon.GW_ALARM_STATUS_NORMAL, 'test_insert_normal_norule')
        event_ids = HELPER.insert_event_data(self.conn, [insert_hash1])

        # 処理実行
        with self.assertLogs('insert_gw_incidents.py') as cm:
            insert_gw_incidents.main()

        # ログ内容の確認
        expect_event_id = event_ids[0]
        expect_incident_id = '1'

        self.assertEqual(cm.output, [
            'INFO:insert_gw_incidents.py:マスターモードのため、マスター動作実行',
            'INFO:insert_gw_incidents.py:イベント処理開始(1/1), gw_event_id=%s' % expect_event_id,
            'INFO:insert_gw_incidents.py:normal報処理:error報が見つかりません。 gw_event_id=%s' % expect_event_id,
            'INFO:insert_gw_incidents.py:normal報処理:インシデント登録しました。gw_incident_id=%s' % expect_incident_id,
            'INFO:insert_gw_incidents.py:normal報処理:イベントID：%sとインシデントID：%sを紐づけました。' % (expect_event_id, expect_incident_id),
            'INFO:insert_gw_incidents.py:イベント処理(1/1)終了, gw_event_id=%s' % expect_event_id,
            'INFO:insert_gw_incidents.py:1秒待機します。',
        ])

        # DB更新結果の確認
        event_result = HELPER.get_updated_gw_events_data(self.conn, expect_event_id)
        self.assertEqual(event_result['event_status'], int(gwcommon.GW_EVENT_STATUS_CLOSE))
        incident_result = HELPER.get_updated_gw_incidents_data(self.conn, expect_incident_id)
        self.assertEqual(incident_result['normal_event_id'], expect_event_id)

    # @unittest.skip('TESTSKIP')
    @patch('gwcommon.MY_DB', HELPER.MY_DB_LOCAL)
    @patch('gwfunction.get_hostgroups_by_host')
    def test_insert_normal_rules(self, mock_get_hostgroups_by_host):
        test_patterns = [
            { # 5-2
                'action_no':gwcommon.GW_KISYS_STATUS_NOSEND,
                'event_status':gwcommon.GW_EVENT_STATUS_CLOSE,
                'kisys_status':gwcommon.GW_KISYS_STATUS_NOSEND,
                'incident_status':gwcommon.GW_INCIDENT_STATUS_CLOSE,
                'result_logs':[
                    'INFO:insert_gw_incidents.py:normal報処理:イベントID：%sとインシデントID：%sを紐づけました。',
                    ],
            },
            { # 5-3
                'action_no':gwcommon.GW_KISYS_STATUS_NOPATOLAMP,
                'event_status':gwcommon.GW_EVENT_STATUS_CLOSE,
                'kisys_status':gwcommon.GW_KISYS_STATUS_NOPATOLAMP,
                'incident_status':gwcommon.GW_INCIDENT_STATUS_CLOSE,
                'result_logs':[
                    'INFO:insert_gw_incidents.py:normal報処理:イベントID：%sとインシデントID：%sを紐づけました。',
                    ],
            },
            { # 5-4
                'action_no':gwcommon.GW_KISYS_STATUS_WAITING_5,
                'event_status':gwcommon.GW_EVENT_STATUS_CLOSE,
                'kisys_status':gwcommon.GW_KISYS_STATUS_KISYS_CONNECT_CANCEL,
                'incident_status':gwcommon.GW_INCIDENT_STATUS_CLOSE,
                'result_logs':[
                    'INFO:insert_gw_incidents.py:キャンセルのためクローズします(gw_event_id=%s, event_status=%s)',
                    'INFO:insert_gw_incidents.py:gw_event_id=%s クローズしました(event_status=%s)',
                    ],
            },
            { # 5-5
                'action_no':gwcommon.GW_KISYS_STATUS_WAITING_10,
                'event_status':gwcommon.GW_EVENT_STATUS_CLOSE,
                'kisys_status':gwcommon.GW_KISYS_STATUS_KISYS_CONNECT_CANCEL,
                'incident_status':gwcommon.GW_INCIDENT_STATUS_CLOSE,
                'result_logs':[
                    'INFO:insert_gw_incidents.py:キャンセルのためクローズします(gw_event_id=%s, event_status=%s)',
                    'INFO:insert_gw_incidents.py:gw_event_id=%s クローズしました(event_status=%s)',
                    ],
            },
            { # 5-6
                'action_no':gwcommon.GW_KISYS_STATUS_WAITING_15,
                'event_status':gwcommon.GW_EVENT_STATUS_CLOSE,
                'kisys_status':gwcommon.GW_KISYS_STATUS_KISYS_CONNECT_CANCEL,
                'incident_status':gwcommon.GW_INCIDENT_STATUS_CLOSE,
                'result_logs':[
                    'INFO:insert_gw_incidents.py:キャンセルのためクローズします(gw_event_id=%s, event_status=%s)',
                    'INFO:insert_gw_incidents.py:gw_event_id=%s クローズしました(event_status=%s)',
                    ],
            },
            { # 5-7
                'action_no':gwcommon.GW_KISYS_STATUS_WAITING_20,
                'event_status':gwcommon.GW_EVENT_STATUS_CLOSE,
                'kisys_status':gwcommon.GW_KISYS_STATUS_KISYS_CONNECT_CANCEL,
                'incident_status':gwcommon.GW_INCIDENT_STATUS_CLOSE,
                'result_logs':[
                    'INFO:insert_gw_incidents.py:キャンセルのためクローズします(gw_event_id=%s, event_status=%s)',
                    'INFO:insert_gw_incidents.py:gw_event_id=%s クローズしました(event_status=%s)',
                    ],
            },
            { # 5-8
                'action_no':gwcommon.GW_KISYS_STATUS_WAITING_25,
                'event_status':gwcommon.GW_EVENT_STATUS_CLOSE,
                'kisys_status':gwcommon.GW_KISYS_STATUS_KISYS_CONNECT_CANCEL,
                'incident_status':gwcommon.GW_INCIDENT_STATUS_CLOSE,
                'result_logs':[
                    'INFO:insert_gw_incidents.py:キャンセルのためクローズします(gw_event_id=%s, event_status=%s)',
                    'INFO:insert_gw_incidents.py:gw_event_id=%s クローズしました(event_status=%s)',
                    ],
            },
            { # 5-9
                'action_no':gwcommon.GW_KISYS_STATUS_WAITING_30,
                'event_status':gwcommon.GW_EVENT_STATUS_CLOSE,
                'kisys_status':gwcommon.GW_KISYS_STATUS_KISYS_CONNECT_CANCEL,
                'incident_status':gwcommon.GW_INCIDENT_STATUS_CLOSE,
                'result_logs':[
                    'INFO:insert_gw_incidents.py:キャンセルのためクローズします(gw_event_id=%s, event_status=%s)',
                    'INFO:insert_gw_incidents.py:gw_event_id=%s クローズしました(event_status=%s)',
                    ],
            },
        ]
        # モード設定
        HELPER.set_master_mode()
        mock_get_hostgroups_by_host.return_value = [gwcommon.KISYS_RELATION_HOSTGROUP]

        # テストデータ投入
        HELPER.insert_test_rule(self.conn, gwcommon.GW_KISYS_STATUS_NOSEND,     'test_insert_normal_rule10')
        HELPER.insert_test_rule(self.conn, gwcommon.GW_KISYS_STATUS_NOPATOLAMP, 'test_insert_normal_rule20')
        HELPER.insert_test_rule(self.conn, gwcommon.GW_KISYS_STATUS_WAITING_5,  'test_insert_normal_rule30')
        HELPER.insert_test_rule(self.conn, gwcommon.GW_KISYS_STATUS_WAITING_10, 'test_insert_normal_rule31')
        HELPER.insert_test_rule(self.conn, gwcommon.GW_KISYS_STATUS_WAITING_15, 'test_insert_normal_rule32')
        HELPER.insert_test_rule(self.conn, gwcommon.GW_KISYS_STATUS_WAITING_20, 'test_insert_normal_rule33')
        HELPER.insert_test_rule(self.conn, gwcommon.GW_KISYS_STATUS_WAITING_25, 'test_insert_normal_rule34')
        HELPER.insert_test_rule(self.conn, gwcommon.GW_KISYS_STATUS_WAITING_30, 'test_insert_normal_rule35')

        expect_logs = [
            'INFO:insert_gw_incidents.py:マスターモードのため、マスター動作実行',
        ]
        expect_ids = []

        for i, test_pattern in enumerate(test_patterns):

            now = datetime.datetime.now()
            one_minute_ago = now - datetime.timedelta(minutes=1)
            test_pattern_name = 'test_insert_normal_rule' + test_pattern['action_no']
            insert_hash1 = get_insert_hash(one_minute_ago, gwcommon.GW_ALARM_STATUS_ERROR, test_pattern_name)
            insert_hash2 = get_insert_hash(now, gwcommon.GW_ALARM_STATUS_NORMAL, test_pattern_name)
            event_ids = HELPER.insert_event_data(self.conn, [insert_hash1, insert_hash2])
            insert_hash1['error_event_id'] = event_ids[0]
            HELPER.insert_incident_data(self.conn, [insert_hash1])

            # ログ内容の確認
            expect_error_event_id = event_ids[0]
            expect_normal_event_id = event_ids[1]
            expect_incident_id = i+1
            expect_ids.append({
                'error_event_id':expect_error_event_id,
                'normal_event_id':expect_normal_event_id,
                'incident_id':expect_incident_id,
            })

            expect_logs2 = [test_pattern['result_logs'][0] % (expect_normal_event_id, expect_incident_id)]
            if test_pattern['action_no'] in gwcommon.GW_KISYS_STATUS_WAITING_LIST:
                expect_logs2 = [
                    test_pattern['result_logs'][0] % (expect_error_event_id, test_pattern['event_status']),
                    test_pattern['result_logs'][1] % (expect_normal_event_id, test_pattern['event_status']),
                ]

            expect_logs.extend([
                'INFO:insert_gw_incidents.py:イベント処理開始(%s/%s), gw_event_id=%s' % (i+1, len(test_patterns), expect_normal_event_id),
                'INFO:insert_gw_incidents.py:normal報処理:インシデントをクローズしました。gw_incident_id=%s, normal_event_id=%s, error_event_id=%s' % (expect_incident_id, expect_normal_event_id, expect_error_event_id),
            ])
            expect_logs.extend(expect_logs2)
            expect_logs.extend([
                'INFO:insert_gw_incidents.py:イベント処理(%s/%s)終了, gw_event_id=%s' % (i+1, len(test_patterns), expect_normal_event_id)
            ])

        # 処理実行
        with self.assertLogs('insert_gw_incidents.py') as cm:
            insert_gw_incidents.main()

        # ログ内容の確認
        expect_logs.extend([
            'INFO:insert_gw_incidents.py:1秒待機します。'
        ])
        self.assertEqual(cm.output, expect_logs)

        for i, test_pattern in enumerate(test_patterns):
            with self.subTest('case%s test_pattern=%s' % (i, test_pattern)):
                # DB更新結果の確認
                event_result = HELPER.get_updated_gw_events_data(self.conn, expect_ids[i]['normal_event_id'])
                self.assertEqual(event_result['event_status'], int(test_pattern['event_status']))
                self.assertEqual(event_result['kisys_status'], test_pattern['kisys_status'])
                incident_result = HELPER.get_updated_gw_incidents_data(self.conn, expect_ids[i]['incident_id'])
                self.assertEqual(incident_result['normal_event_id'], expect_ids[i]['normal_event_id'])
                self.assertEqual(incident_result['incident_status'], int(test_pattern['incident_status']))

    # @unittest.skip('TESTSKIP')
    @patch('gwcommon.MY_DB', HELPER.MY_DB_LOCAL)
    @patch('gwfunction.get_hostgroups_by_host')
    def test_insert_normal_rule30_cancel_hostgroup(self, mock_get_hostgroups_by_host):
        # モード設定
        HELPER.set_master_mode()
        mock_get_hostgroups_by_host.return_value = [gwcommon.KISYS_RELATION_HOSTGROUP]

        # テストデータ投入
        HELPER.insert_test_rule(self.conn, gwcommon.GW_KISYS_STATUS_WAITING_5, 'test_insert_normal_rule30_cancel_hostgroup')
        now = datetime.datetime.now()
        one_minute_ago = now - datetime.timedelta(minutes=1)
        insert_hash1 = get_insert_hash(one_minute_ago, gwcommon.GW_ALARM_STATUS_ERROR, 'test_insert_normal_rule30_cancel_hostgroup')
        insert_hash2 = get_insert_hash(now, gwcommon.GW_ALARM_STATUS_NORMAL, 'test_insert_normal_rule30_cancel_hostgroup')
        event_ids = HELPER.insert_event_data(self.conn, [insert_hash1, insert_hash2])

        # 処理実行
        with self.assertLogs('insert_gw_incidents.py') as cm:
            insert_gw_incidents.main()

        # ログ内容の確認
        expect_error_event_id = event_ids[0]
        expect_normal_event_id = event_ids[1]
        expect_incident_id = '1'

        self.assertEqual(cm.output, [
            'INFO:insert_gw_incidents.py:マスターモードのため、マスター動作実行',
            'INFO:insert_gw_incidents.py:イベント処理開始(1/2), gw_event_id=%s' % expect_error_event_id,
            'INFO:insert_gw_incidents.py:error報処理:インシデント登録しました。gw_incident_id=%s' % expect_incident_id,
            'INFO:insert_gw_incidents.py:キャンセル待ちします(5分)(gw_event_id=%s, event_status=%s)' % (expect_error_event_id, gwcommon.GW_EVENT_STATUS_NEW),
            'INFO:insert_gw_incidents.py:イベント処理(1/2)終了, gw_event_id=%s' % expect_error_event_id,
            'INFO:insert_gw_incidents.py:イベント処理開始(2/2), gw_event_id=%s' % expect_normal_event_id,
            'INFO:insert_gw_incidents.py:normal報処理:インシデントをクローズしました。gw_incident_id=%s, normal_event_id=%s, error_event_id=%s' % (expect_incident_id, expect_normal_event_id, expect_error_event_id),
            'INFO:insert_gw_incidents.py:キャンセルのためクローズします(gw_event_id=%s, event_status=%s)' % (expect_error_event_id, gwcommon.GW_EVENT_STATUS_CLOSE),
            'INFO:insert_gw_incidents.py:gw_event_id=%s クローズしました(event_status=%s)' % (expect_normal_event_id, gwcommon.GW_EVENT_STATUS_CLOSE),
            'INFO:insert_gw_incidents.py:イベント処理(2/2)終了, gw_event_id=%s' % expect_normal_event_id,
            'INFO:insert_gw_incidents.py:1秒待機します。',
        ])

        # DB更新結果の確認
        error_event_result = HELPER.get_updated_gw_events_data(self.conn, expect_error_event_id)
        self.assertEqual(error_event_result['event_status'], int(gwcommon.GW_EVENT_STATUS_CLOSE))
        self.assertEqual(error_event_result['kisys_status'], gwcommon.GW_KISYS_STATUS_KISYS_CONNECT_CANCEL)
        normal_event_result = HELPER.get_updated_gw_events_data(self.conn, expect_normal_event_id)
        self.assertEqual(normal_event_result['event_status'], int(gwcommon.GW_EVENT_STATUS_CLOSE))
        self.assertEqual(normal_event_result['kisys_status'], gwcommon.GW_KISYS_STATUS_KISYS_CONNECT_CANCEL)
        incident_result = HELPER.get_updated_gw_incidents_data(self.conn, expect_incident_id)
        self.assertEqual(incident_result['normal_event_id'], expect_normal_event_id)
        self.assertEqual(incident_result['incident_status'], int(gwcommon.GW_INCIDENT_STATUS_CLOSE))

    # @unittest.skip('TESTSKIP')
    @patch('gwcommon.MY_DB', HELPER.MY_DB_LOCAL)
    @patch('gwfunction.get_hostgroups_by_host')
    def test_insert_normal_rule30_cancel_nohostgroup(self, mock_get_hostgroups_by_host):
        # モード設定
        HELPER.set_master_mode()
        mock_get_hostgroups_by_host.return_value = []

        # テストデータ投入
        HELPER.insert_test_rule(self.conn, gwcommon.GW_KISYS_STATUS_WAITING_5, 'test_insert_normal_rule30_cancel_nohostgroup')
        now = datetime.datetime.now()
        one_minute_ago = now - datetime.timedelta(minutes=1)
        insert_hash1 = get_insert_hash(one_minute_ago, gwcommon.GW_ALARM_STATUS_ERROR, 'test_insert_normal_rule30_cancel_nohostgroup')
        insert_hash2 = get_insert_hash(now, gwcommon.GW_ALARM_STATUS_NORMAL, 'test_insert_normal_rule30_cancel_nohostgroup')
        event_ids = HELPER.insert_event_data(self.conn, [insert_hash1, insert_hash2])

        # 処理実行
        with self.assertLogs('insert_gw_incidents.py') as cm:
            insert_gw_incidents.main()

        # ログ内容の確認
        expect_error_event_id = event_ids[0]
        expect_normal_event_id = event_ids[1]
        expect_incident_id = '1'

        self.assertEqual(cm.output, [
            'INFO:insert_gw_incidents.py:マスターモードのため、マスター動作実行',
            'INFO:insert_gw_incidents.py:イベント処理開始(1/2), gw_event_id=%s' % expect_error_event_id,
            'INFO:insert_gw_incidents.py:error報処理:インシデント登録しました。gw_incident_id=%s' % expect_incident_id,
            'INFO:insert_gw_incidents.py:キャンセル待ちします(5分)(gw_event_id=%s, event_status=%s)' % (expect_error_event_id, gwcommon.GW_EVENT_STATUS_NEW),
            'INFO:insert_gw_incidents.py:イベント処理(1/2)終了, gw_event_id=%s' % expect_error_event_id,
            'INFO:insert_gw_incidents.py:イベント処理開始(2/2), gw_event_id=%s' % expect_normal_event_id,
            'INFO:insert_gw_incidents.py:normal報処理:インシデントをクローズしました。gw_incident_id=%s, normal_event_id=%s, error_event_id=%s' % (expect_incident_id, expect_normal_event_id, expect_error_event_id),
            'INFO:insert_gw_incidents.py:error報処理:BAO連携しない gw_event_id=%s' % expect_error_event_id,
            'INFO:insert_gw_incidents.py:normal報処理:BAO連携しない gw_event_id=%s' % expect_normal_event_id,
            'INFO:insert_gw_incidents.py:normal報処理:関連テーブルをcloseに更新しました。gw_event_id=%s, gw_incident_id=%s' % (expect_normal_event_id, expect_incident_id),
            'INFO:insert_gw_incidents.py:イベント処理(2/2)終了, gw_event_id=%s' % expect_normal_event_id,
            'INFO:insert_gw_incidents.py:1秒待機します。',
        ])

        # DB更新結果の確認
        error_event_result = HELPER.get_updated_gw_events_data(self.conn, expect_error_event_id)
        self.assertEqual(error_event_result['event_status'], int(gwcommon.GW_EVENT_STATUS_CLOSE))
        self.assertEqual(error_event_result['kisys_status'], gwcommon.GW_KISYS_STATUS_CANCEL_NOSEND)
        normal_event_result = HELPER.get_updated_gw_events_data(self.conn, expect_normal_event_id)
        self.assertEqual(normal_event_result['event_status'], int(gwcommon.GW_EVENT_STATUS_CLOSE))
        self.assertEqual(normal_event_result['kisys_status'], gwcommon.GW_KISYS_STATUS_CANCEL_NOSEND)
        incident_result = HELPER.get_updated_gw_incidents_data(self.conn, expect_incident_id)
        self.assertEqual(incident_result['normal_event_id'], expect_normal_event_id)
        self.assertEqual(incident_result['incident_status'], int(gwcommon.GW_INCIDENT_STATUS_CLOSE))

    # @unittest.skip('TESTSKIP')
    @patch('gwcommon.MY_DB', HELPER.MY_DB_LOCAL)
    @patch('gwfunction.get_hostgroups_by_host')
    def test_insert_normal_rule30_timeout_hostgroup(self, mock_get_hostgroups_by_host):
        # モード設定
        HELPER.set_master_mode()
        mock_get_hostgroups_by_host.return_value = [gwcommon.KISYS_RELATION_HOSTGROUP]

        # テストデータ投入
        HELPER.insert_test_rule(self.conn, gwcommon.GW_KISYS_STATUS_WAITING_5, 'test_insert_normal_rule30_timeout_hostgroup')
        now = datetime.datetime.now()
        yesterday = now - datetime.timedelta(days=1)
        insert_hash1 = get_insert_hash(yesterday, gwcommon.GW_ALARM_STATUS_ERROR, 'test_insert_normal_rule30_timeout_hostgroup')
        insert_hash2 = get_insert_hash(now, gwcommon.GW_ALARM_STATUS_NORMAL, 'test_insert_normal_rule30_timeout_hostgroup')
        event_ids = HELPER.insert_event_data(self.conn, [insert_hash1, insert_hash2])

        # 処理実行
        with self.assertLogs('insert_gw_incidents.py') as cm:
            insert_gw_incidents.main()

        # ログ内容の確認
        expect_error_event_id = event_ids[0]
        expect_normal_event_id = event_ids[1]
        expect_incident_id = '1'

        self.assertEqual(cm.output, [
            'INFO:insert_gw_incidents.py:マスターモードのため、マスター動作実行',
            'INFO:insert_gw_incidents.py:イベント処理開始(1/2), gw_event_id=%s' % expect_error_event_id,
            'INFO:insert_gw_incidents.py:error報処理:インシデント登録しました。gw_incident_id=%s' % expect_incident_id,
            'INFO:insert_gw_incidents.py:error報処理:キャンセル待ちタイムアウト、BAO連携する gw_event_id=%s' % expect_error_event_id,
            'INFO:insert_gw_incidents.py:イベント処理(1/2)終了, gw_event_id=%s' % expect_error_event_id,
            'INFO:insert_gw_incidents.py:イベント処理開始(2/2), gw_event_id=%s' % expect_normal_event_id,
            'INFO:insert_gw_incidents.py:normal報処理:インシデントをクローズしました。gw_incident_id=%s, normal_event_id=%s, error_event_id=%s' % (expect_incident_id, expect_normal_event_id, expect_error_event_id),
            'INFO:insert_gw_incidents.py:normal報処理:キャンセル待ちタイムアウト、エラー報クローズしました gw_event_id=%s' % expect_error_event_id,
            'INFO:insert_gw_incidents.py:normal報処理:キャンセル待ちタイムアウト、BAO連携する gw_event_id=%s' % expect_normal_event_id,
            'INFO:insert_gw_incidents.py:イベント処理(2/2)終了, gw_event_id=%s' % expect_normal_event_id,
            'INFO:insert_gw_incidents.py:1秒待機します。',
        ])

        # DB更新結果の確認
        error_event_result = HELPER.get_updated_gw_events_data(self.conn, expect_error_event_id)
        self.assertEqual(error_event_result['event_status'], int(gwcommon.GW_EVENT_STATUS_CLOSE))
        self.assertEqual(error_event_result['kisys_status'], gwcommon.GW_KISYS_STATUS_KISYS_CONNECT_NORECOVERY)
        normal_event_result = HELPER.get_updated_gw_events_data(self.conn, expect_normal_event_id)
        self.assertEqual(normal_event_result['event_status'], int(gwcommon.GW_EVENT_STATUS_CLOSE))
        self.assertEqual(normal_event_result['kisys_status'], gwcommon.GW_KISYS_STATUS_KISYS_CONNECT_NORECOVERY)
        incident_result = HELPER.get_updated_gw_incidents_data(self.conn, expect_incident_id)
        self.assertEqual(incident_result['normal_event_id'], expect_normal_event_id)
        self.assertEqual(incident_result['incident_status'], int(gwcommon.GW_INCIDENT_STATUS_CLOSE))

    # @unittest.skip('TESTSKIP')
    @patch('gwcommon.MY_DB', HELPER.MY_DB_LOCAL)
    @patch('gwfunction.get_hostgroups_by_host')
    def test_insert_normal_rule30_timeout_nohostgroup(self, mock_get_hostgroups_by_host):
        # モード設定
        HELPER.set_master_mode()
        mock_get_hostgroups_by_host.return_value = []

        # テストデータ投入
        HELPER.insert_test_rule(self.conn, gwcommon.GW_KISYS_STATUS_WAITING_5, 'test_insert_normal_rule30_timeout_nohostgroup')
        now = datetime.datetime.now()
        yesterday = now - datetime.timedelta(days=1)
        insert_hash1 = get_insert_hash(yesterday, gwcommon.GW_ALARM_STATUS_ERROR, 'test_insert_normal_rule30_timeout_nohostgroup')
        insert_hash2 = get_insert_hash(now, gwcommon.GW_ALARM_STATUS_NORMAL, 'test_insert_normal_rule30_timeout_nohostgroup')
        event_ids = HELPER.insert_event_data(self.conn, [insert_hash1, insert_hash2])

        # 処理実行
        with self.assertLogs('insert_gw_incidents.py') as cm:
            insert_gw_incidents.main()

        # ログ内容の確認
        expect_error_event_id = event_ids[0]
        expect_normal_event_id = event_ids[1]
        expect_incident_id = '1'

        self.assertEqual(cm.output, [
            'INFO:insert_gw_incidents.py:マスターモードのため、マスター動作実行',
            'INFO:insert_gw_incidents.py:イベント処理開始(1/2), gw_event_id=%s' % expect_error_event_id,
            'INFO:insert_gw_incidents.py:error報処理:インシデント登録しました。gw_incident_id=%s' % expect_incident_id,
            'INFO:insert_gw_incidents.py:error報処理:キャンセル待ちタイムアウト、BAO連携しない gw_event_id=%s' % expect_error_event_id,
            'INFO:insert_gw_incidents.py:イベント処理(1/2)終了, gw_event_id=%s' % expect_error_event_id,
            'INFO:insert_gw_incidents.py:イベント処理開始(2/2), gw_event_id=%s' % expect_normal_event_id,
            'INFO:insert_gw_incidents.py:normal報処理:インシデントをクローズしました。gw_incident_id=%s, normal_event_id=%s, error_event_id=%s' % (expect_incident_id, expect_normal_event_id, expect_error_event_id),
            'INFO:insert_gw_incidents.py:normal報処理:キャンセル待ちタイムアウト、エラー報クローズしました gw_event_id=%s' % expect_error_event_id,
            'INFO:insert_gw_incidents.py:normal報処理:キャンセル待ちタイムアウト、BAO連携しない gw_event_id=%s' % expect_normal_event_id,
            'INFO:insert_gw_incidents.py:イベント処理(2/2)終了, gw_event_id=%s' % expect_normal_event_id,
            'INFO:insert_gw_incidents.py:1秒待機します。',
        ])

        # DB更新結果の確認
        error_event_result = HELPER.get_updated_gw_events_data(self.conn, expect_error_event_id)
        self.assertEqual(error_event_result['event_status'], int(gwcommon.GW_EVENT_STATUS_CLOSE))
        self.assertEqual(error_event_result['kisys_status'], gwcommon.GW_KISYS_STATUS_NORECOVERY_NOSEND)
        normal_event_result = HELPER.get_updated_gw_events_data(self.conn, expect_normal_event_id)
        self.assertEqual(normal_event_result['event_status'], int(gwcommon.GW_EVENT_STATUS_CLOSE))
        self.assertEqual(normal_event_result['kisys_status'], gwcommon.GW_KISYS_STATUS_NORECOVERY_NOSEND)
        incident_result = HELPER.get_updated_gw_incidents_data(self.conn, expect_incident_id)
        self.assertEqual(incident_result['normal_event_id'], expect_normal_event_id)
        self.assertEqual(incident_result['incident_status'], int(gwcommon.GW_INCIDENT_STATUS_CLOSE))

    # 5-14(エラー報時間内、ノーマル報タイムアウトの場合)
    # @unittest.skip('TESTSKIP')
    @patch('gwcommon.MY_DB', HELPER.MY_DB_LOCAL)
    @patch('gwfunction.get_hostgroups_by_host')
    def test_insert_normal_rule30_errorwaiting_normaltimeout_hostgroup(self, mock_get_hostgroups_by_host):
        # モード設定
        HELPER.set_master_mode()
        mock_get_hostgroups_by_host.return_value = [gwcommon.KISYS_RELATION_HOSTGROUP]

        # テストデータ投入
        HELPER.insert_test_rule(self.conn, gwcommon.GW_KISYS_STATUS_WAITING_5, 'test_insert_normal_rule30_errwait_nmltmout_hstgrp')
        now = datetime.datetime.now()
        one_minute_ago = now - datetime.timedelta(minutes=4.9997)
        insert_hash1 = get_insert_hash(one_minute_ago, gwcommon.GW_ALARM_STATUS_ERROR, 'test_insert_normal_rule30_errwait_nmltmout_hstgrp')
        insert_hash2 = get_insert_hash(now, gwcommon.GW_ALARM_STATUS_NORMAL, 'test_insert_normal_rule30_errwait_nmltmout_hstgrp')
        event_ids = HELPER.insert_event_data(self.conn, [insert_hash1, insert_hash2])

        # 処理実行
        with self.assertLogs('insert_gw_incidents.py') as cm:
            insert_gw_incidents.main()

        # ログ内容の確認
        expect_error_event_id = event_ids[0]
        expect_normal_event_id = event_ids[1]
        expect_incident_id = '1'

        self.assertEqual(cm.output, [
            'INFO:insert_gw_incidents.py:マスターモードのため、マスター動作実行',
            'INFO:insert_gw_incidents.py:イベント処理開始(1/2), gw_event_id=%s' % expect_error_event_id,
            'INFO:insert_gw_incidents.py:error報処理:インシデント登録しました。gw_incident_id=%s' % expect_incident_id,
            'INFO:insert_gw_incidents.py:キャンセル待ちします(5分)(gw_event_id=%s, event_status=0)' % expect_error_event_id,
            'INFO:insert_gw_incidents.py:イベント処理(1/2)終了, gw_event_id=%s' % expect_error_event_id,
            'INFO:insert_gw_incidents.py:イベント処理開始(2/2), gw_event_id=%s' % expect_normal_event_id,
            'INFO:insert_gw_incidents.py:normal報処理:インシデントをクローズしました。gw_incident_id=%s, normal_event_id=%s, error_event_id=%s' % (expect_incident_id, expect_normal_event_id, expect_error_event_id),
            'INFO:insert_gw_incidents.py:normal報処理:キャンセル待ちタイムアウト、エラー報キャンセル待ち中なのでエラー報kisys_status更新、クローズしました gw_event_id=%s' % expect_error_event_id,
            'INFO:insert_gw_incidents.py:normal報処理:キャンセル待ちタイムアウト、BAO連携する gw_event_id=%s' % expect_normal_event_id,
            'INFO:insert_gw_incidents.py:イベント処理(2/2)終了, gw_event_id=%s' % expect_normal_event_id,
            'INFO:insert_gw_incidents.py:1秒待機します。',
        ])

        # DB更新結果の確認
        error_event_result = HELPER.get_updated_gw_events_data(self.conn, expect_error_event_id)
        self.assertEqual(error_event_result['event_status'], int(gwcommon.GW_EVENT_STATUS_CLOSE))
        self.assertEqual(error_event_result['kisys_status'], gwcommon.GW_KISYS_STATUS_KISYS_CONNECT_NORECOVERY)
        normal_event_result = HELPER.get_updated_gw_events_data(self.conn, expect_normal_event_id)
        self.assertEqual(normal_event_result['event_status'], int(gwcommon.GW_EVENT_STATUS_CLOSE))
        self.assertEqual(normal_event_result['kisys_status'], gwcommon.GW_KISYS_STATUS_KISYS_CONNECT_NORECOVERY)
        incident_result = HELPER.get_updated_gw_incidents_data(self.conn, expect_incident_id)
        self.assertEqual(incident_result['normal_event_id'], expect_normal_event_id)
        self.assertEqual(incident_result['incident_status'], int(gwcommon.GW_INCIDENT_STATUS_CLOSE))


    # 5-15(エラー報時間内、ノーマル報タイムアウトの場合)
    # @unittest.skip('TESTSKIP')
    @patch('gwcommon.MY_DB', HELPER.MY_DB_LOCAL)
    @patch('gwfunction.get_hostgroups_by_host')
    def test_insert_normal_rule30_errorwaiting_normaltimeout_nohostgroup(self, mock_get_hostgroups_by_host):
        # モード設定
        HELPER.set_master_mode()
        mock_get_hostgroups_by_host.return_value = []

        # テストデータ投入
        HELPER.insert_test_rule(self.conn, gwcommon.GW_KISYS_STATUS_WAITING_5, 'test_insert_normal_rule30_errwait_nmltmout_nohstgrp')
        now = datetime.datetime.now()
        one_minute_ago = now - datetime.timedelta(minutes=4.9997)
        insert_hash1 = get_insert_hash(one_minute_ago, gwcommon.GW_ALARM_STATUS_ERROR, 'test_insert_normal_rule30_errwait_nmltmout_nohstgrp')
        insert_hash2 = get_insert_hash(now, gwcommon.GW_ALARM_STATUS_NORMAL, 'test_insert_normal_rule30_errwait_nmltmout_nohstgrp')
        event_ids = HELPER.insert_event_data(self.conn, [insert_hash1, insert_hash2])

        # 処理実行
        with self.assertLogs('insert_gw_incidents.py') as cm:
            insert_gw_incidents.main()

        # ログ内容の確認
        expect_error_event_id = event_ids[0]
        expect_normal_event_id = event_ids[1]
        expect_incident_id = '1'

        self.assertEqual(cm.output, [
            'INFO:insert_gw_incidents.py:マスターモードのため、マスター動作実行',
            'INFO:insert_gw_incidents.py:イベント処理開始(1/2), gw_event_id=%s' % expect_error_event_id,
            'INFO:insert_gw_incidents.py:error報処理:インシデント登録しました。gw_incident_id=%s' % expect_incident_id,
            'INFO:insert_gw_incidents.py:キャンセル待ちします(5分)(gw_event_id=%s, event_status=0)' % expect_error_event_id,
            'INFO:insert_gw_incidents.py:イベント処理(1/2)終了, gw_event_id=%s' % expect_error_event_id,
            'INFO:insert_gw_incidents.py:イベント処理開始(2/2), gw_event_id=%s' % expect_normal_event_id,
            'INFO:insert_gw_incidents.py:normal報処理:インシデントをクローズしました。gw_incident_id=%s, normal_event_id=%s, error_event_id=%s' % (expect_incident_id, expect_normal_event_id, expect_error_event_id),
            'INFO:insert_gw_incidents.py:normal報処理:キャンセル待ちタイムアウト、エラー報キャンセル待ち中なのでエラー報kisys_status更新、クローズしました gw_event_id=%s' % expect_error_event_id,
            'INFO:insert_gw_incidents.py:normal報処理:キャンセル待ちタイムアウト、BAO連携しない gw_event_id=%s' % expect_normal_event_id,
            'INFO:insert_gw_incidents.py:イベント処理(2/2)終了, gw_event_id=%s' % expect_normal_event_id,
            'INFO:insert_gw_incidents.py:1秒待機します。',
        ])

        # DB更新結果の確認
        error_event_result = HELPER.get_updated_gw_events_data(self.conn, expect_error_event_id)
        self.assertEqual(error_event_result['event_status'], int(gwcommon.GW_EVENT_STATUS_CLOSE))
        self.assertEqual(error_event_result['kisys_status'], gwcommon.GW_KISYS_STATUS_NORECOVERY_NOSEND)
        normal_event_result = HELPER.get_updated_gw_events_data(self.conn, expect_normal_event_id)
        self.assertEqual(normal_event_result['event_status'], int(gwcommon.GW_EVENT_STATUS_CLOSE))
        self.assertEqual(normal_event_result['kisys_status'], gwcommon.GW_KISYS_STATUS_NORECOVERY_NOSEND)
        incident_result = HELPER.get_updated_gw_incidents_data(self.conn, expect_incident_id)
        self.assertEqual(incident_result['normal_event_id'], expect_normal_event_id)
        self.assertEqual(incident_result['incident_status'], int(gwcommon.GW_INCIDENT_STATUS_CLOSE))

    # @unittest.skip('TESTSKIP')
    @patch('gwcommon.MY_DB', HELPER.MY_DB_LOCAL)
    @patch('gwfunction.get_hostgroups_by_host')
    def test_insert_normal_norule_hostgroup(self, mock_get_hostgroups_by_host):
        # モード設定
        HELPER.set_master_mode()
        mock_get_hostgroups_by_host.return_value = [gwcommon.KISYS_RELATION_HOSTGROUP]

        # テストデータ投入
        now = datetime.datetime.now()
        one_minute_ago = now - datetime.timedelta(minutes=1)
        insert_hash1 = get_insert_hash(one_minute_ago, gwcommon.GW_ALARM_STATUS_ERROR, 'test_insert_normal_norule_hostgroup')
        insert_hash2 = get_insert_hash(now, gwcommon.GW_ALARM_STATUS_NORMAL, 'test_insert_normal_norule_hostgroup')
        event_ids = HELPER.insert_event_data(self.conn, [insert_hash1, insert_hash2])

        # 処理実行
        with self.assertLogs('insert_gw_incidents.py') as cm:
            insert_gw_incidents.main()

        # ログ内容の確認
        expect_error_event_id = event_ids[0]
        expect_normal_event_id = event_ids[1]
        expect_incident_id = '1'

        self.assertEqual(cm.output, [
            'INFO:insert_gw_incidents.py:マスターモードのため、マスター動作実行',
            'INFO:insert_gw_incidents.py:イベント処理開始(1/2), gw_event_id=%s' % expect_error_event_id,
            'INFO:insert_gw_incidents.py:error報処理:インシデント登録しました。gw_incident_id=%s' % expect_incident_id,
            'INFO:insert_gw_incidents.py:error報処理:イベントID：%sとインシデントID：%sを紐づけました。' % (expect_error_event_id, expect_incident_id),
            'INFO:insert_gw_incidents.py:イベント処理(1/2)終了, gw_event_id=%s' % expect_error_event_id,
            'INFO:insert_gw_incidents.py:イベント処理開始(2/2), gw_event_id=%s' % expect_normal_event_id,
            'INFO:insert_gw_incidents.py:normal報処理:インシデントをクローズしました。gw_incident_id=%s, normal_event_id=%s, error_event_id=%s' % (expect_incident_id, expect_normal_event_id, expect_error_event_id),
            'INFO:insert_gw_incidents.py:normal報処理:イベントID：%sとインシデントID：%sを紐づけました。' % (expect_normal_event_id, expect_incident_id),
            'INFO:insert_gw_incidents.py:イベント処理(2/2)終了, gw_event_id=%s' % expect_normal_event_id,
            'INFO:insert_gw_incidents.py:1秒待機します。',
        ])

        # DB更新結果の確認
        error_event_result = HELPER.get_updated_gw_events_data(self.conn, expect_error_event_id)
        self.assertEqual(error_event_result['event_status'], int(gwcommon.GW_EVENT_STATUS_CLOSE))
        self.assertEqual(error_event_result['kisys_status'], gwcommon.GW_KISYS_STATUS_KISYS_CONNECT_NORULE)
        normal_event_result = HELPER.get_updated_gw_events_data(self.conn, expect_normal_event_id)
        self.assertEqual(normal_event_result['event_status'], int(gwcommon.GW_EVENT_STATUS_CLOSE))
        self.assertEqual(normal_event_result['kisys_status'], gwcommon.GW_KISYS_STATUS_KISYS_CONNECT_NORULE)
        incident_result = HELPER.get_updated_gw_incidents_data(self.conn, expect_incident_id)
        self.assertEqual(incident_result['normal_event_id'], expect_normal_event_id)
        self.assertEqual(incident_result['incident_status'], int(gwcommon.GW_INCIDENT_STATUS_CLOSE))

    # @unittest.skip('TESTSKIP')
    @patch('gwcommon.MY_DB', HELPER.MY_DB_LOCAL)
    @patch('gwfunction.get_hostgroups_by_host')
    def test_insert_normal_norule_nohostgroup(self, mock_get_hostgroups_by_host):
        # モード設定
        HELPER.set_master_mode()
        mock_get_hostgroups_by_host.return_value = []

        # テストデータ投入
        now = datetime.datetime.now()
        one_minute_ago = now - datetime.timedelta(minutes=1)
        insert_hash1 = get_insert_hash(one_minute_ago, gwcommon.GW_ALARM_STATUS_ERROR, 'test_insert_normal_norule_nohostgroup')
        insert_hash2 = get_insert_hash(now, gwcommon.GW_ALARM_STATUS_NORMAL, 'test_insert_normal_norule_nohostgroup')
        event_ids = HELPER.insert_event_data(self.conn, [insert_hash1, insert_hash2])

        # 処理実行
        with self.assertLogs('insert_gw_incidents.py') as cm:
            insert_gw_incidents.main()

        # ログ内容の確認
        expect_error_event_id = event_ids[0]
        expect_normal_event_id = event_ids[1]
        expect_incident_id = '1'

        self.assertEqual(cm.output, [
            'INFO:insert_gw_incidents.py:マスターモードのため、マスター動作実行',
            'INFO:insert_gw_incidents.py:イベント処理開始(1/2), gw_event_id=%s' % expect_error_event_id,
            'INFO:insert_gw_incidents.py:error報処理:インシデント登録しました。gw_incident_id=%s' % expect_incident_id,
            'INFO:insert_gw_incidents.py:error報処理:イベントID：%sとインシデントID：%sを紐づけました。' % (expect_error_event_id, expect_incident_id),
            'INFO:insert_gw_incidents.py:イベント処理(1/2)終了, gw_event_id=%s' % expect_error_event_id,
            'INFO:insert_gw_incidents.py:イベント処理開始(2/2), gw_event_id=%s' % expect_normal_event_id,
            'INFO:insert_gw_incidents.py:normal報処理:インシデントをクローズしました。gw_incident_id=%s, normal_event_id=%s, error_event_id=%s' % (expect_incident_id, expect_normal_event_id, expect_error_event_id),
            'INFO:insert_gw_incidents.py:normal報処理:イベントID：%sとインシデントID：%sを紐づけました。' % (expect_normal_event_id, expect_incident_id),
            'INFO:insert_gw_incidents.py:イベント処理(2/2)終了, gw_event_id=%s' % expect_normal_event_id,
            'INFO:insert_gw_incidents.py:1秒待機します。',
        ])

        # DB更新結果の確認
        error_event_result = HELPER.get_updated_gw_events_data(self.conn, expect_error_event_id)
        self.assertEqual(error_event_result['event_status'], int(gwcommon.GW_EVENT_STATUS_CLOSE))
        self.assertEqual(error_event_result['kisys_status'], gwcommon.GW_KISYS_STATUS_NOSEND_BY_HOSTGROUP)
        normal_event_result = HELPER.get_updated_gw_events_data(self.conn, expect_normal_event_id)
        self.assertEqual(normal_event_result['event_status'], int(gwcommon.GW_EVENT_STATUS_CLOSE))
        self.assertEqual(normal_event_result['kisys_status'], gwcommon.GW_KISYS_STATUS_NOSEND_BY_HOSTGROUP)
        incident_result = HELPER.get_updated_gw_incidents_data(self.conn, expect_incident_id)
        self.assertEqual(incident_result['normal_event_id'], expect_normal_event_id)
        self.assertEqual(incident_result['incident_status'], int(gwcommon.GW_INCIDENT_STATUS_CLOSE))

    # @unittest.skip('TESTSKIP')
    @patch('gwcommon.MY_DB', HELPER.MY_DB_LOCAL)
    def test_insert_info_norule(self):
        # モード設定
        HELPER.set_master_mode()

        # テストデータ投入
        now = datetime.datetime.now()
        insert_hash1 = get_insert_hash(now, gwcommon.GW_ALARM_STATUS_INFO, 'test_insert_info_norule')
        event_ids = HELPER.insert_event_data(self.conn, [insert_hash1])

        # 処理実行
        with self.assertLogs('insert_gw_incidents.py') as cm:
            insert_gw_incidents.main()

        # ログ内容の確認
        expect_event_id = event_ids[0]
        expect_incident_id = '1'

        self.assertEqual(cm.output, [
            'INFO:insert_gw_incidents.py:マスターモードのため、マスター動作実行',
            'INFO:insert_gw_incidents.py:イベント処理開始(1/1), gw_event_id=%s' % expect_event_id,
            'INFO:insert_gw_incidents.py:syserror, info, sec報処理:インシデント登録しました。gw_incident_id=%s' % expect_incident_id,
            'INFO:insert_gw_incidents.py:syserror, info, sec報処理:イベントID：%sとインシデントID：%sを紐づけました。' % (expect_event_id, expect_incident_id),
            'INFO:insert_gw_incidents.py:イベント処理(1/1)終了, gw_event_id=%s' % expect_event_id,
            'INFO:insert_gw_incidents.py:1秒待機します。',
        ])

        # DB更新結果の確認
        event_result = HELPER.get_updated_gw_events_data(self.conn, expect_event_id)
        self.assertEqual(event_result['event_status'], int(gwcommon.GW_EVENT_STATUS_CLOSE))
        incident_result = HELPER.get_updated_gw_incidents_data(self.conn, expect_incident_id)
        self.assertEqual(incident_result['error_event_id'], expect_event_id)
        self.assertEqual(incident_result['incident_status'], int(gwcommon.GW_INCIDENT_STATUS_CLOSE))

    # @unittest.skip('TESTSKIP')
    @patch('gwcommon.MY_DB', HELPER.MY_DB_LOCAL)
    def test_insert_sec_norule(self):
        # モード設定
        HELPER.set_master_mode()

        # テストデータ投入
        now = datetime.datetime.now()
        insert_hash1 = get_insert_hash(now, gwcommon.GW_ALARM_STATUS_SEC, 'test_insert_sec_norule')
        event_ids = HELPER.insert_event_data(self.conn, [insert_hash1])

        # 処理実行
        with self.assertLogs('insert_gw_incidents.py') as cm:
            insert_gw_incidents.main()

        # ログ内容の確認
        expect_event_id = event_ids[0]
        expect_incident_id = '1'

        self.assertEqual(cm.output, [
            'INFO:insert_gw_incidents.py:マスターモードのため、マスター動作実行',
            'INFO:insert_gw_incidents.py:処理対象イベント無し。',
            'INFO:insert_gw_incidents.py:1秒待機します。',
        ])

        # DB更新結果の確認
        event_result = HELPER.get_updated_gw_events_data(self.conn, expect_event_id)
        self.assertEqual(event_result['event_status'], int(gwcommon.GW_EVENT_STATUS_NEW))
        incident_result = HELPER.get_updated_gw_incidents_data(self.conn, expect_incident_id)
        self.assertEqual(incident_result, None)

    # @unittest.skip('TESTSKIP')
    @patch('gwcommon.MY_DB', HELPER.MY_DB_LOCAL)
    def test_insert_syserror_norule(self):
        # モード設定
        HELPER.set_master_mode()

        # テストデータ投入
        now = datetime.datetime.now()
        insert_hash1 = get_insert_hash(now, gwcommon.GW_ALARM_STATUS_SYSERROR, 'test_insert_syserror_norule')
        event_ids = HELPER.insert_event_data(self.conn, [insert_hash1])

        # 処理実行
        with self.assertLogs('insert_gw_incidents.py') as cm:
            insert_gw_incidents.main()

        # ログ内容の確認
        expect_event_id = event_ids[0]
        expect_incident_id = '1'

        self.assertEqual(cm.output, [
            'INFO:insert_gw_incidents.py:マスターモードのため、マスター動作実行',
            'INFO:insert_gw_incidents.py:処理対象イベント無し。',
            'INFO:insert_gw_incidents.py:1秒待機します。',
        ])

        # DB更新結果の確認
        event_result = HELPER.get_updated_gw_events_data(self.conn, expect_event_id)
        self.assertEqual(event_result['event_status'], int(gwcommon.GW_EVENT_STATUS_NEW))
        incident_result = HELPER.get_updated_gw_incidents_data(self.conn, expect_incident_id)
        self.assertEqual(incident_result, None)

    # @unittest.skip('TESTSKIP')
    @patch('gwcommon.MY_DB', HELPER.MY_DB_LOCAL)
    def test_insert_sysnormal_norule(self):
        # モード設定
        HELPER.set_master_mode()

        # テストデータ投入
        now = datetime.datetime.now()
        insert_hash1 = get_insert_hash(now, gwcommon.GW_ALARM_STATUS_SYSNORMAL, 'test_insert_sysnormal_norule')
        event_ids = HELPER.insert_event_data(self.conn, [insert_hash1])

        # 処理実行
        with self.assertLogs('insert_gw_incidents.py') as cm:
            insert_gw_incidents.main()

        # ログ内容の確認
        expect_event_id = event_ids[0]
        expect_incident_id = '1'

        self.assertEqual(cm.output, [
            'INFO:insert_gw_incidents.py:マスターモードのため、マスター動作実行',
            'INFO:insert_gw_incidents.py:処理対象イベント無し。',
            'INFO:insert_gw_incidents.py:1秒待機します。',
        ])

        # DB更新結果の確認
        event_result = HELPER.get_updated_gw_events_data(self.conn, expect_event_id)
        self.assertEqual(event_result['event_status'], int(gwcommon.GW_EVENT_STATUS_NEW))
        incident_result = HELPER.get_updated_gw_incidents_data(self.conn, expect_incident_id)
        self.assertEqual(incident_result, None)

    # @unittest.skip('TESTSKIP')
    @patch('gwcommon.MY_DB', HELPER.MY_DB_LOCAL)
    @patch('gwfunction.get_hostgroups_by_host')
    def test_patolamp_on_error_singly(self, mock_get_hostgroups_by_host):

        # ホストグループの種類
        hostgroups_by_patterns = [
            {
                'host_group': gwcommon.FLOOR_11TH_HOSTGROUP,
                'file_suffix': ''
            },
            {
                'host_group': gwcommon.FLOOR_12TH_HOSTGROUP,
                'file_suffix': '_' + gwcommon.FLOOR_12TH
            },
            {
                'host_group': gwcommon.HOWCOM_HOSTGROUP,
                'file_suffix': '_' + gwcommon.HOWCOM
            },
            {
                'host_group': gwcommon.VIP_HOSTGROUP,
                'file_suffix': '_' + gwcommon.VIP
            },
        ]

        test_pattern_name = 'test_patolamp_on_error_singly'
        HELPER.insert_test_rule(self.conn, gwcommon.GW_KISYS_STATUS_WAITING_5, test_pattern_name)

        for i, hostgroups_by_pattern in enumerate(hostgroups_by_patterns):
            with self.subTest('case%s hostgroup=%s' % (i, hostgroups_by_pattern)):
                host_group = hostgroups_by_pattern.get('host_group')

                mock_get_hostgroups_by_host.return_value = [
                    host_group
                ]

                # 確認対象のパトランプ
                patolamp = gwcommon.RED_PATOLAMP_FILE + hostgroups_by_pattern.get('file_suffix')
                patolamp_file_path = HELPER.PATOLAMP_FILE_PATH + patolamp

                # モード設定
                HELPER.set_master_mode()

                # テストデータ投入
                now = datetime.datetime.now()
                yesterday = now - datetime.timedelta(days=1)
                insert_hash = get_insert_hash(yesterday, gwcommon.GW_ALARM_STATUS_ERROR, test_pattern_name)
                event_ids = HELPER.insert_event_data(self.conn, [insert_hash])

                # 処理実行
                with self.assertLogs('insert_gw_incidents.py') as cm:
                    insert_gw_incidents.main()

                # ログ内容の確認
                expect_event_id = event_ids[0]
                expect_incident_id = i + 1

                self.assertEqual(cm.output, [
                    'INFO:insert_gw_incidents.py:マスターモードのため、マスター動作実行',
                    'INFO:insert_gw_incidents.py:イベント処理開始(1/1), gw_event_id=%s' % expect_event_id,
                    'INFO:insert_gw_incidents.py:error報処理:インシデント登録しました。gw_incident_id=%s' % expect_incident_id,
                    'INFO:insert_gw_incidents.py:パトランプフラグ(%s)を作成しました。' % patolamp_file_path,
                    'INFO:insert_gw_incidents.py:error報処理:キャンセル待ちタイムアウト、BAO連携しない gw_event_id=%s' % expect_event_id,
                    'INFO:insert_gw_incidents.py:イベント処理(1/1)終了, gw_event_id=%s' % expect_event_id,
                    'INFO:insert_gw_incidents.py:1秒待機します。',
                ])

                # パトランプファイルの存在チェック
                self.assertTrue(os.path.isfile(patolamp_file_path))

    # @unittest.skip('TESTSKIP')
    @patch('gwcommon.MY_DB', HELPER.MY_DB_LOCAL)
    @patch('gwfunction.get_hostgroups_by_host')
    def test_patolamp_on_error_normal_paired(self, mock_get_hostgroups_by_host):

        # ホストグループの種類
        hostgroups_by_patterns = [
            {
                'host_group': gwcommon.FLOOR_11TH_HOSTGROUP,
                'file_suffix': ''
            },
            {
                'host_group': gwcommon.FLOOR_12TH_HOSTGROUP,
                'file_suffix': '_' + gwcommon.FLOOR_12TH
            },
            {
                'host_group': gwcommon.HOWCOM_HOSTGROUP,
                'file_suffix': '_' + gwcommon.HOWCOM
            },
            {
                'host_group': gwcommon.VIP_HOSTGROUP,
                'file_suffix': '_' + gwcommon.VIP
            },
        ]
        test_pattern_name = 'test_patolamp_on_error_normal_paired'
        HELPER.insert_test_rule(self.conn, gwcommon.GW_KISYS_STATUS_WAITING_5, test_pattern_name)

        for i, hostgroups_by_pattern in enumerate(hostgroups_by_patterns):
            with self.subTest('case%s hostgroup=%s' % (i, hostgroups_by_pattern)):
                host_group = hostgroups_by_pattern.get('host_group')

                mock_get_hostgroups_by_host.return_value = [
                    host_group
                ]

                # 確認対象のパトランプ
                error_patolamp = gwcommon.RED_PATOLAMP_FILE + hostgroups_by_pattern.get('file_suffix')
                error_patolamp_file_path = HELPER.PATOLAMP_FILE_PATH + error_patolamp
                normal_patolamp = gwcommon.GREEN_PATOLAMP_FILE + hostgroups_by_pattern.get('file_suffix')
                normal_patolamp_file_path = HELPER.PATOLAMP_FILE_PATH + normal_patolamp

                # モード設定
                HELPER.set_master_mode()

                # テストデータ投入
                now = datetime.datetime.now()
                yesterday = now - datetime.timedelta(days=1)
                insert_hash1 = get_insert_hash(yesterday, gwcommon.GW_ALARM_STATUS_ERROR, test_pattern_name)
                insert_hash2 = get_insert_hash(now, gwcommon.GW_ALARM_STATUS_NORMAL, test_pattern_name)
                event_ids = HELPER.insert_event_data(self.conn, [insert_hash1, insert_hash2])

                # 処理実行
                with self.assertLogs('insert_gw_incidents.py') as cm:
                    insert_gw_incidents.main()

                # ログ内容の確認
                expect_error_event_id = event_ids[0]
                expect_normal_event_id = event_ids[1]
                expect_incident_id = i + 1

                self.assertEqual(cm.output, [
                    'INFO:insert_gw_incidents.py:マスターモードのため、マスター動作実行',
                    'INFO:insert_gw_incidents.py:イベント処理開始(1/2), gw_event_id=%s' % expect_error_event_id,
                    'INFO:insert_gw_incidents.py:error報処理:インシデント登録しました。gw_incident_id=%s' % expect_incident_id,
                    'INFO:insert_gw_incidents.py:パトランプフラグ(%s)を作成しました。' % error_patolamp_file_path,
                    'INFO:insert_gw_incidents.py:error報処理:キャンセル待ちタイムアウト、BAO連携しない gw_event_id=%s' % expect_error_event_id,
                    'INFO:insert_gw_incidents.py:イベント処理(1/2)終了, gw_event_id=%s' % expect_error_event_id,
                    'INFO:insert_gw_incidents.py:イベント処理開始(2/2), gw_event_id=%s' % expect_normal_event_id,
                    'INFO:insert_gw_incidents.py:normal報処理:インシデントをクローズしました。gw_incident_id=%s, normal_event_id=%s, error_event_id=%s' % (expect_incident_id, expect_normal_event_id, expect_error_event_id),
                    'INFO:insert_gw_incidents.py:パトランプフラグ(%s)を作成しました。' % normal_patolamp_file_path,
                    'INFO:insert_gw_incidents.py:normal報処理:キャンセル待ちタイムアウト、エラー報クローズしました gw_event_id=%s' % expect_error_event_id,
                    'INFO:insert_gw_incidents.py:normal報処理:キャンセル待ちタイムアウト、BAO連携しない gw_event_id=%s' % expect_normal_event_id,
                    'INFO:insert_gw_incidents.py:イベント処理(2/2)終了, gw_event_id=%s' % expect_normal_event_id,
                    'INFO:insert_gw_incidents.py:1秒待機します。',
                ])

                # パトランプファイルの存在チェック
                self.assertTrue(os.path.isfile(error_patolamp_file_path))
                self.assertTrue(os.path.isfile(normal_patolamp_file_path))

    # @unittest.skip('TESTSKIP')
    @patch('gwcommon.MY_DB', HELPER.MY_DB_LOCAL)
    def test_errorpattern_update_related_gw_events(self):

        # テストデータ投入
        # event_status=0のエラー報がひも付いているインシデントデータを作成
        now = datetime.datetime.now()
        insert_hash1 = get_insert_hash(now, gwcommon.GW_ALARM_STATUS_ERROR, 'test_errorpattern_update_related_gw_events')
        event_ids = HELPER.insert_event_data(self.conn, [insert_hash1])
        insert_hash1['error_event_id'] = event_ids[0]
        # insert_incident_data_errorpattern：エラー報のevent_status=0のままインシデント登録するメソッド
        HELPER.insert_incident_data_errorpattern(self.conn, [insert_hash1])

        # 処理実行
        with self.assertLogs('insert_gw_incidents.py') as cm:
            insert_gw_incidents.update_related_gw_events(gwcommon.GW_EVENT_STATUS_CLOSE, 1)

        # ログ内容の確認
        expect_error_event_id = event_ids[0]
        expect_incident_id = '1'

        self.assertEqual(cm.output, [
            'ERROR:insert_gw_incidents.py:update_related_gw_eventsでupdate結果が0件でした gw_incident_id=%s' % expect_incident_id
        ])

        # DB更新結果の確認
        error_event_result = HELPER.get_updated_gw_events_data(self.conn, expect_error_event_id)
        self.assertEqual(error_event_result['event_status'], int(gwcommon.GW_EVENT_STATUS_NEW))
        incident_result = HELPER.get_updated_gw_incidents_data(self.conn, expect_incident_id)
        self.assertEqual(incident_result['error_event_id'], expect_error_event_id)
        self.assertEqual(incident_result['incident_status'], int(gwcommon.GW_INCIDENT_STATUS_ACTIVE))

########################################################################
## Test Helper
########################################################################

def get_insert_hash(now, alarm_status, str):
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
    }

if __name__ == '__main__':
    unittest.main()

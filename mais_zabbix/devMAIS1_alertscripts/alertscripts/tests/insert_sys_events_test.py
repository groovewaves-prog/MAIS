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
import insert_sys_events
import gwcommon
import test_helper as HELPER

@patch('gwcommon.MY_USER', HELPER.MY_USER)
@patch('gwcommon.MY_PASSWD', HELPER.MY_PASSWD)
# @patch('gwcommon.MY_DB', HELPER.MY_DB_LOCAL)
class InsertSysEventsTest(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        # DB接続
        conn = HELPER.db_connect()
        self.maxDiff = None

        # DB close
        conn.close()

    @classmethod
    def tearDownClass(self):
        # DB接続
        conn = HELPER.db_connect()

        # テーブルの初期化
        HELPER.table_initializ(conn)

        # DB close
        conn.close()

    def setUp(self):
        # DB接続
        self.conn = HELPER.db_connect()

        # テーブルの初期化
        HELPER.table_initializ(self.conn)

        # 抑止フラグ削除
        flag_files = glob.glob(HELPER.BAOGW_DIR + '*' + '_db_ng')
        for flag_file in flag_files:
            os.remove(flag_file)

    def tearDown(self):
        # テーブルの初期化
        HELPER.table_initializ(self.conn)

        # DB close
        self.conn.close()

    # @unittest.skip('TESTSKIP')
    @patch('gwcommon.MY_DB', HELPER.MY_DB_LOCAL)
    def test_validate(self):
        # 送信データ
        now = datetime.datetime.now()
        insert_hash_base = get_insert_hash(now, gwcommon.GW_ALARM_STATUS_SYSERROR, 'testValidate')

        # 指定数の文字列作成用
        num_char = lambda n: 's' * n

        update_time = now.strftime("%Y-%m-%d %H:%M:%S")
        detected_host = gwcommon.DETECTED_HOST
        cmmon_alm_log = "発生ノード=" + detected_host + ", 発生時間=" + update_time + \
            ", お客様名=" + insert_hash_base.get('customer_name') + ", ホスト名=" + insert_hash_base.get('hostname')

        patterns = {
            'customer_name': [
                {
                    'value': '	',
                    'logs': [
                        'ERROR:insert_sys_events.py:customer_nameに規定外の文字が含まれます。：発生ノード= %s 発生時間= %s ' \
                            % (detected_host, update_time,),
                        'INFO:insert_sys_events.py:customer_nameに規定外の文字が含まれます。customer_name= %s' % ('	',),
                    ]
                },
                {
                    'value': num_char(128),
                    'logs': [
                        'ERROR:insert_sys_events.py:customer_nameの文字数オーバーです。：発生ノード= %s 発生時間= %s ' \
                            % (detected_host, update_time,),
                        'INFO:insert_sys_events.py:customer_nameの文字数オーバーです。customer_name= %s' % (num_char(128),),
                    ]
                },
            ],
            'hostname': [
                {
                    'value': '	',
                    'logs': [
                        'ERROR:insert_sys_events.py:hostnameに規定外の文字が含まれます。：発生ノード= %s 発生時間= %s お客様名= %s' \
                            % (detected_host, update_time, insert_hash_base.get('customer_name'),),
                        'INFO:insert_sys_events.py:hostnameに規定外の文字が含まれます。： hostname= %s' % ('	',),
                    ]
                },
                {
                    'value': num_char(257),
                    'logs': [
                        'ERROR:insert_sys_events.py:hostnameの文字数オーバーです。：発生ノード= %s 発生時間= %s お客様名= %s' \
                            % (detected_host, update_time, insert_hash_base.get('customer_name'),),
                        'INFO:insert_sys_events.py:hostnameの文字数が規定以上です hostname= %s' % (num_char(257),),
                    ]
                },
            ],
            'ci_name': [
                {
                    'value': '	',
                    'logs': [
                        'ERROR:insert_sys_events.py:ci_nameに規定外の文字が含まれます。 %s' % (cmmon_alm_log,),
                        'INFO:insert_sys_events.py:ci_nameに規定外の文字が含まれます %s' % ('	',),
                    ]
                },
                {
                    'value': num_char(257),
                    'logs': [
                        'ERROR:insert_sys_events.py:ci_nameの文字数が規定以上です。 %s' % (cmmon_alm_log,),
                        'INFO:insert_sys_events.py:ci_nameの文字数が規定以上です。 ci_name= %s' % (num_char(257),),
                    ]
                },
            ],
            'detected_time': [
                {
                    'value': 's',
                    'logs': [
                        'ERROR:insert_sys_events.py:detected_timeフォーマット異常です。 %s' % (cmmon_alm_log,),
                        'INFO:insert_sys_events.py:detected_timeフォーマット異常です。detected_time= %s' % ('s',),
                    ]
                },
                {
                    'value': '2020-02-30 99:99:99',
                    'logs': [
                        'ERROR:insert_sys_events.py:detected_timeフォーマット異常です。 %s' % (cmmon_alm_log,),
                        'INFO:insert_sys_events.py:detected_timeフォーマット異常です。detected_time= %s' % ('2020-02-30 99:99:99',),
                    ]
                },
            ],
            'customer_ci': [
                {
                    'value': 'テスト',
                    'logs': [
                        'ERROR:insert_sys_events.py:customer_ciに規定外の文字が含まれます。 %s' % (cmmon_alm_log,),
                        'INFO:insert_sys_events.py:customer_ciに規定外の文字が含まれます。customer_ci= %s' % ('テスト',),
                    ]
                },
                {
                    'value': num_char(65),
                    'logs': [
                        'ERROR:insert_sys_events.py:customer_ciの文字数オーバーです。 %s' % (cmmon_alm_log,),
                        'INFO:insert_sys_events.py:customer_ciの文字数オーバーです。customer_ci= %s' % (num_char(65),),
                    ]
                },
            ],
            'alarm_time': [
                {
                    'value': 's',
                    'logs': [
                        'ERROR:insert_sys_events.py:alarm_timeフォーマット異常です。 %s' % (cmmon_alm_log,),
                        'INFO:insert_sys_events.py:alarm_timeフォーマット異常です。alarm_time= %s' % ('s',),
                    ]
                },
                {
                    'value': '2020-02-30 99:99:99.999',
                    'logs': [
                        'ERROR:insert_sys_events.py:alarm_timeフォーマット異常です。 %s' % (cmmon_alm_log,),
                        'INFO:insert_sys_events.py:alarm_timeフォーマット異常です。alarm_time= %s' % ('2020-02-30 99:99:99.999',),
                    ]
                },
            ],
            'device': [
                {
                    'value': '	',
                    'logs': [
                        'ERROR:insert_sys_events.py:deviceに規定外の文字が含まれます。 %s' % (cmmon_alm_log,),
                        'INFO:insert_sys_events.py:deviceに規定外の文字が含まれます device= %s' % ('	',),
                    ]
                },
                {
                    'value': num_char(256),
                    'logs': [
                        'ERROR:insert_sys_events.py:deviceの文字数オーバーです。 %s' % (cmmon_alm_log,),
                        'INFO:insert_sys_events.py:deviceの文字数オーバーです。device= %s' % (num_char(256),),
                    ]
                },
            ],
            'alarm_status': [
                {
                    'value': gwcommon.GW_ALARM_STATUS_SYSERROR + 's',
                    'logs': [
                        'ERROR:insert_sys_events.py:alarm_statusが規定外です。 %s' % (cmmon_alm_log,),
                        'INFO:insert_sys_events.py:alarm_statusが規定外です。 alarm_status= %s' % (gwcommon.GW_ALARM_STATUS_SYSERROR + 's',),
                    ]
                },
            ],
            'summary': [
                {
                    'value': '	',
                    'logs': [
                        'ERROR:insert_sys_events.py:補足に規定外の文字が含まれます %s' % (cmmon_alm_log,),
                        'INFO:insert_sys_events.py:summaryに規定外の文字が含まれます summary= %s' % ('	',),
                    ]
                },
            ],
            'host': [
                {
                    'value': '	',
                    'logs': [
                        'ERROR:insert_sys_events.py:hostに規定外の文字が含まれます。 %s' % (cmmon_alm_log,),
                        'INFO:insert_sys_events.py:hostに規定外の文字が含まれます host= %s' % ('	',),
                    ]
                },
                {
                    'value': num_char(128),
                    'logs': [
                        'ERROR:insert_sys_events.py:hostの文字数オーバーです。 %s' % (cmmon_alm_log,),
                        'INFO:insert_sys_events.py:hostの文字数オーバーです。host= %s' % (num_char(128),),
                    ]
                },
            ],
        }

        for k, items in patterns.items():
            for item in items:
                with self.subTest('item=%s' % item):
                    # ベースになるデータをコピーし、送信データ書き換え
                    insert_hash = copy.deepcopy(insert_hash_base)
                    insert_hash[k] = item.get('value')

                    # insert_sys_events呼び出し時の第4引数に渡すメッセージの作成
                    message = create_message(insert_hash)

                    # 引数のセット
                    HELPER.set_sys_argv(message, 'insert_sys_events.py')

                    # 処理実行
                    with self.assertLogs('insert_sys_events.py') as cm:
                        with self.assertRaises(SystemExit): # exit()で終わっているのでSystemExitを監視
                            insert_sys_events.main()

                    # ログ内容の確認
                    self.assertEqual(cm.output, item.get('logs'))

    # @unittest.skip('TESTSKIP')
    @patch('gwcommon.MY_DB', HELPER.MY_DB_LOCAL)
    def test_validate_summary_over(self):
        summary_len = 10000

        # モード設定
        HELPER.set_test_mode()

        # 送信データ
        now = datetime.datetime.now()
        insert_hash = get_insert_hash(now, gwcommon.GW_ALARM_STATUS_SYSERROR, 'testValidateSummaryOver')
        insert_hash['summary'] = 's' * (summary_len + summary_len)

        # insert_sys_events呼び出し時の第4引数に渡すメッセージの作成
        message = create_message(insert_hash)

        # 引数のセット
        HELPER.set_sys_argv(message, 'insert_sys_events.py')

        # 処理実行
        with self.assertLogs('insert_sys_events.py') as cm:
            insert_sys_events.main()

        # ログ内容の確認
        expect_event_id = 1
        expect_incident_id = 1

        self.assertEqual(cm.output, [
            'INFO:insert_sys_events.py:summaryの文字数オーバーです。規定文字数以上をカットします。 %s' % insert_hash['summary'],
            'INFO:insert_sys_events.py:testモードのため、テストモードで動作実行',
            'INFO:insert_sys_events.py:Local DB[%s] 接続成功' % gwcommon.MY_HOST,
            'INFO:insert_sys_events.py:[End1] %s gw_events INSERT成功' % gwcommon.MY_HOST,
            'INFO:insert_sys_events.py:syserror報処理:インシデント登録しました。gw_incident_id=%s' % expect_incident_id,
            'INFO:insert_sys_events.py:gw_incident_id=%s' % expect_incident_id,
            'INFO:insert_sys_events.py:syserror報処理:イベントID：%sとインシデントID：%sを紐づけました。' % (expect_event_id, expect_incident_id),
        ])

        # データの登録確認
        insert_hash['summary'] = insert_hash.get('summary')[:summary_len]
        result = HELPER.get_insert_gw_events_data(self.conn, insert_hash, now)
        self.assertEqual(result[0], 1)
        result_incident = HELPER.get_updated_gw_incidents_data(self.conn, expect_incident_id)
        self.assertEqual(result_incident['error_event_id'], expect_event_id)

    # @unittest.skip('TESTSKIP')
    @patch('gwcommon.MY_DB', HELPER.MY_DB_LOCAL)
    def test_input_num_error(self):
        # モード設定
        HELPER.set_test_mode()

        # 送信データ
        now = datetime.datetime.now()
        insert_hash = get_insert_hash(now, gwcommon.GW_ALARM_STATUS_SYSERROR, 'testInputNumError')
        del insert_hash['device']

        # insert_sys_events呼び出し時の第4引数に渡すメッセージの作成
        message = '@!!!@'.join(insert_hash)

        # 引数のセット
        HELPER.set_sys_argv(message, 'insert_sys_events.py')

        # 処理実行
        with self.assertLogs('insert_sys_events.py') as cm:
            with self.assertRaises(SystemExit): # exit()で終わっているのでSystemExitを監視
                insert_sys_events.main()

        # ログ内容の確認
        update_time = now.strftime("%Y-%m-%d %H:%M:%S")
        detected_host = gwcommon.DETECTED_HOST
        self.assertEqual(cm.output, [
            'ERROR:insert_sys_events.py:受信項目数が不正です。：発生ノード= %s 発生時間= %s ' % (detected_host, update_time),
            'INFO:insert_sys_events.py:データ異常：デリミタにより分解したデータ数が14ではなく 9 です ',
        ])

        # データの登録確認
        result = HELPER.get_insert_gw_events_data(self.conn, insert_hash, now)
        self.assertEqual(result[0], 0)

    # @unittest.skip('TESTSKIP')
    @patch('gwcommon.MY_DB', HELPER.MY_DB_LOCAL)
    def test_test_mode(self):
        # モード設定
        HELPER.set_test_mode()

        # 送信データ
        now = datetime.datetime.now()
        insert_hash = get_insert_hash(now, gwcommon.GW_ALARM_STATUS_SYSERROR, 'testMode')

        # insert_sys_events呼び出し時の第4引数に渡すメッセージの作成
        message = create_message(insert_hash)

        # 引数のセット
        HELPER.set_sys_argv(message, 'insert_sys_events.py')

        # 処理実行
        with self.assertLogs('insert_sys_events.py') as cm:
            insert_sys_events.main()

        # ログ内容の確認
        expect_event_id = 1
        expect_incident_id = 1

        self.assertEqual(cm.output, [
            'INFO:insert_sys_events.py:testモードのため、テストモードで動作実行',
            'INFO:insert_sys_events.py:Local DB[%s] 接続成功' % gwcommon.MY_HOST,
            'INFO:insert_sys_events.py:[End1] %s gw_events INSERT成功' % gwcommon.MY_HOST,
            'INFO:insert_sys_events.py:syserror報処理:インシデント登録しました。gw_incident_id=%s' % expect_incident_id,
            'INFO:insert_sys_events.py:gw_incident_id=%s' % expect_incident_id,
            'INFO:insert_sys_events.py:syserror報処理:イベントID：%sとインシデントID：%sを紐づけました。' % (expect_event_id, expect_incident_id),
        ])

        # データの登録確認
        result = HELPER.get_insert_gw_events_data(self.conn, insert_hash, now)
        self.assertEqual(result[0], 1)
        result_incident = HELPER.get_updated_gw_incidents_data(self.conn, expect_incident_id)
        self.assertEqual(result_incident['error_event_id'], expect_event_id)

    # @unittest.skip('TESTSKIP')
    @patch('gwcommon.MY_DB', HELPER.MY_DB_LOCAL)
    def test_master_mode(self):
        # モード設定
        HELPER.set_master_mode()

        # 送信データ
        now = datetime.datetime.now()
        insert_hash = get_insert_hash(now, gwcommon.GW_ALARM_STATUS_SYSERROR, 'masterMode')

        # insert_sys_events呼び出し時の第4引数に渡すメッセージの作成
        message = create_message(insert_hash)

        # 引数のセット
        HELPER.set_sys_argv(message, 'insert_sys_events.py')

        # 処理実行
        with self.assertLogs('insert_sys_events.py') as cm:
            insert_sys_events.main()

        # ログ内容の確認
        expect_event_id = 1
        expect_incident_id = 1

        self.assertEqual(cm.output, [
            'INFO:insert_sys_events.py:マスターモードのたため、マスター動作実行',
            'INFO:insert_sys_events.py:Local DB[%s] 接続成功' % gwcommon.MY_HOST,
            'INFO:insert_sys_events.py:[End1] %s gw_events INSERT成功' % gwcommon.MY_HOST,
            'INFO:insert_sys_events.py:syserror報処理:インシデント登録しました。gw_incident_id=%s' % expect_incident_id,
            'INFO:insert_sys_events.py:gw_incident_id=%s' % expect_incident_id,
            'INFO:insert_sys_events.py:syserror報処理:イベントID：%sとインシデントID：%sを紐づけました。' % (expect_event_id, expect_incident_id),
        ])

        # データの登録確認
        result = HELPER.get_insert_gw_events_data(self.conn, insert_hash, now)
        self.assertEqual(result[0], 1)
        result_incident = HELPER.get_updated_gw_incidents_data(self.conn, expect_incident_id)
        self.assertEqual(result_incident['error_event_id'], expect_event_id)

    # @unittest.skip('TESTSKIP')
    @patch('gwcommon.REMOTE_HOST', HELPER.MY_HOST_REMOTE)
    @patch('gwcommon.MY_DB', HELPER.MY_DB_REMOTE)
    def test_slave_mode(self):
        # モード設定
        HELPER.set_slave_mode()

        # 送信データ
        now = datetime.datetime.now()
        insert_hash = get_insert_hash(now, gwcommon.GW_ALARM_STATUS_SYSERROR, 'slaveMode')

        # insert_sys_events呼び出し時の第4引数に渡すメッセージの作成
        message = create_message(insert_hash)

        # 引数のセット
        HELPER.set_sys_argv(message, 'insert_sys_events.py')

        # 処理実行
        with self.assertLogs('insert_sys_events.py') as cm:
            insert_sys_events.main()

        # ログ内容の確認
        expect_event_id = 1
        expect_incident_id = 1

        self.assertEqual(cm.output, [
            'INFO:insert_sys_events.py:スレーブモードのため、スレーブ動作実行',
            'INFO:insert_sys_events.py:Remote DB[%s] 接続成功' % gwcommon.REMOTE_HOST,
            'INFO:insert_sys_events.py:[End2] %s gw_events INSERT成功' % gwcommon.REMOTE_HOST,
            'INFO:insert_sys_events.py:syserror報処理:インシデント登録しました。gw_incident_id=%s' % expect_incident_id,
            'INFO:insert_sys_events.py:gw_incident_id=%s' % expect_incident_id,
            'INFO:insert_sys_events.py:syserror報処理:イベントID：%sとインシデントID：%sを紐づけました。' % (expect_event_id, expect_incident_id),
        ])

        # データの登録確認(local)
        result_local = HELPER.get_insert_gw_events_data(self.conn, insert_hash, now)
        self.assertEqual(result_local[0], 0)
        result_local_incident = HELPER.get_updated_gw_incidents_data(self.conn, expect_incident_id)
        self.assertEqual(result_local_incident, None)

        # データの登録確認(remote)
        conn_remote = HELPER.db_connect(HELPER.MY_HOST_REMOTE)
        result_remote = HELPER.get_insert_gw_events_data(conn_remote, insert_hash, now, HELPER.MY_DB_REMOTE + '.gw_events')
        self.assertEqual(result_remote[0], 1)
        result_remote_incident = HELPER.get_updated_gw_incidents_data(conn_remote, expect_incident_id, HELPER.MY_DB_REMOTE + '.gw_incidents')
        self.assertEqual(result_remote_incident['error_event_id'], expect_event_id)
        conn_remote.close()

    # @unittest.skip('TESTSKIP')
    @patch('gwcommon.REMOTE_HOST', 'remote_host')   # 接続失敗させる
    @patch('gwcommon.MY_DB', HELPER.MY_DB_LOCAL)
    def test_slave_mode_remote_ng(self):
        # モード設定
        HELPER.set_slave_mode()

        # 送信データ
        now = datetime.datetime.now()
        insert_hash = get_insert_hash(now, gwcommon.GW_ALARM_STATUS_SYSERROR, 'slaveModeRemoteNg')

        # insert_sys_events呼び出し時の第4引数に渡すメッセージの作成
        message = create_message(insert_hash)

        # 引数のセット
        HELPER.set_sys_argv(message, 'insert_sys_events.py')

        # 処理実行
        with self.assertLogs('insert_sys_events.py') as cm:
            with self.assertRaises(SystemExit): # exit()で終わっているのでSystemExitを監視
                insert_sys_events.main()

        # ログ内容の確認
        expect_flag_name = 'Remote_db_ng'

        self.assertEqual(cm.output, [
            'INFO:insert_sys_events.py:スレーブモードのため、スレーブ動作実行',
            'CRITICAL:insert_sys_events.py:Remote DB[%s] 接続失敗' % gwcommon.REMOTE_HOST,
            "INFO:insert_sys_events.py:2003 (HY000): Can't connect to MySQL server on '%s:3306' (110)" % gwcommon.REMOTE_HOST,
            'INFO:insert_sys_events.py:抑止フラグ(/var/lib/baogw/%s)を作成しました。' % expect_flag_name,
            'INFO:insert_sys_events.py:Remote_DBに情報挿入失敗。local_DBにrescue情報挿入します。',
            'INFO:insert_sys_events.py:Local DB[localhost] 接続成功',
            'INFO:insert_sys_events.py:[End3] %s gw_rescue_events INSERT成功' % gwcommon.MY_HOST,
        ])

        # データの登録確認(gw_rescue_events)
        result = HELPER.get_insert_gw_events_data(self.conn, insert_hash, now, 'gw_rescue_events')
        self.assertEqual(result[0], 1)

        # 抑止フラグの存在チェック
        self.assertTrue(os.path.isfile(HELPER.BAOGW_DIR + expect_flag_name))

    # @unittest.skip('TESTSKIP')
    @patch('gwcommon.MY_DB', HELPER.MY_DB_LOCAL)
    def test_insert_sec(self):
        # モード設定
        HELPER.set_master_mode()

        # 送信データ
        now = datetime.datetime.now()
        insert_hash = get_insert_hash(now, gwcommon.GW_ALARM_STATUS_SEC, 'insertSec')

        # insert_sys_events呼び出し時の第4引数に渡すメッセージの作成
        message = create_message(insert_hash)

        # 引数のセット
        HELPER.set_sys_argv(message, 'insert_sys_events.py')

        # 処理実行
        with self.assertLogs('insert_sys_events.py') as cm:
            insert_sys_events.main()

        # ログ内容の確認
        expect_event_id = 1
        expect_incident_id = 1

        self.assertEqual(cm.output, [
            'INFO:insert_sys_events.py:マスターモードのたため、マスター動作実行',
            'INFO:insert_sys_events.py:Local DB[%s] 接続成功' % gwcommon.MY_HOST,
            'INFO:insert_sys_events.py:[End1] %s gw_events INSERT成功' % gwcommon.MY_HOST,
            'INFO:insert_sys_events.py:syserror報処理:インシデント登録しました。gw_incident_id=%s' % expect_incident_id,
            'INFO:insert_sys_events.py:gw_incident_id=%s' % expect_incident_id,
            'INFO:insert_sys_events.py:syserror報処理:イベントID：%sとインシデントID：%sを紐づけました。' % (expect_event_id, expect_incident_id),
        ])

        # データの登録確認
        result = HELPER.get_insert_gw_events_data(self.conn, insert_hash, now)
        self.assertEqual(result[0], 1)
        result_event = HELPER.get_updated_gw_events_data(self.conn, expect_event_id)
        self.assertEqual(result_event['event_status'], int(gwcommon.GW_EVENT_STATUS_CLOSE))
        result_incident = HELPER.get_updated_gw_incidents_data(self.conn, expect_incident_id)
        self.assertEqual(result_incident['error_event_id'], expect_event_id)

    # @unittest.skip('TESTSKIP')
    @patch('gwcommon.MY_DB', HELPER.MY_DB_LOCAL)
    def test_insert_sysnormal(self):
        # モード設定
        HELPER.set_master_mode()

        # 送信データ
        now = datetime.datetime.now()
        insert_hash = get_insert_hash(now, gwcommon.GW_ALARM_STATUS_SYSNORMAL, 'insertSysnormal')

        # insert_sys_events呼び出し時の第4引数に渡すメッセージの作成
        message = create_message(insert_hash)

        # 引数のセット
        HELPER.set_sys_argv(message, 'insert_sys_events.py')

        # 処理実行
        with self.assertLogs('insert_sys_events.py') as cm:
            insert_sys_events.main()

        # ログ内容の確認
        expect_event_id = 1
        expect_incident_id = 1

        self.assertEqual(cm.output, [
            'INFO:insert_sys_events.py:マスターモードのたため、マスター動作実行',
            'INFO:insert_sys_events.py:Local DB[%s] 接続成功' % gwcommon.MY_HOST,
            'INFO:insert_sys_events.py:[End1] %s gw_events INSERT成功' % gwcommon.MY_HOST,
            'INFO:insert_sys_events.py:success: insert gw_incidentsテーブル',
            'INFO:insert_sys_events.py:sysnormal報処理:インシデント登録しました。gw_incident_id=%s' % expect_incident_id,
            'INFO:insert_sys_events.py:gw_incident_id=%s' % expect_incident_id,
            'INFO:insert_sys_events.py:sysnormal報処理:イベントID：%sとインシデントID：%sを紐づけました。' % (expect_event_id, expect_incident_id),
        ])

        # データの登録確認
        result = HELPER.get_insert_gw_events_data(self.conn, insert_hash, now)
        self.assertEqual(result[0], 1)
        result_event = HELPER.get_updated_gw_events_data(self.conn, expect_event_id)
        self.assertEqual(result_event['event_status'], int(gwcommon.GW_EVENT_STATUS_CLOSE))
        result_incident = HELPER.get_updated_gw_incidents_data(self.conn, expect_incident_id)
        self.assertEqual(result_incident['normal_event_id'], expect_event_id)

    # @unittest.skip('TESTSKIP')
    @patch('gwcommon.MY_DB', HELPER.MY_DB_LOCAL)
    def test_insert_syserror(self):
        # モード設定
        HELPER.set_master_mode()

        # 送信データ
        now = datetime.datetime.now()
        insert_hash = get_insert_hash(now, gwcommon.GW_ALARM_STATUS_SYSERROR, 'insertSyserror')

        # insert_sys_events呼び出し時の第4引数に渡すメッセージの作成
        message = create_message(insert_hash)

        # 引数のセット
        HELPER.set_sys_argv(message, 'insert_sys_events.py')

        # 処理実行
        with self.assertLogs('insert_sys_events.py') as cm:
            insert_sys_events.main()

        # ログ内容の確認
        expect_event_id = 1
        expect_incident_id = 1

        self.assertEqual(cm.output, [
            'INFO:insert_sys_events.py:マスターモードのたため、マスター動作実行',
            'INFO:insert_sys_events.py:Local DB[%s] 接続成功' % gwcommon.MY_HOST,
            'INFO:insert_sys_events.py:[End1] %s gw_events INSERT成功' % gwcommon.MY_HOST,
            'INFO:insert_sys_events.py:syserror報処理:インシデント登録しました。gw_incident_id=%s' % expect_incident_id,
            'INFO:insert_sys_events.py:gw_incident_id=%s' % expect_incident_id,
            'INFO:insert_sys_events.py:syserror報処理:イベントID：%sとインシデントID：%sを紐づけました。' % (expect_event_id, expect_incident_id),
        ])

        # データの登録確認
        result = HELPER.get_insert_gw_events_data(self.conn, insert_hash, now)
        self.assertEqual(result[0], 1)
        result_event = HELPER.get_updated_gw_events_data(self.conn, expect_event_id)
        self.assertEqual(result_event['event_status'], int(gwcommon.GW_EVENT_STATUS_CLOSE))
        result_incident = HELPER.get_updated_gw_incidents_data(self.conn, expect_incident_id)
        self.assertEqual(result_incident['error_event_id'], expect_event_id)

    # @unittest.skip('TESTSKIP')
    @patch('gwcommon.MY_DB', HELPER.MY_DB_LOCAL)
    def test_dup_check(self):
        # モード設定
        HELPER.set_master_mode()

        # 送信データ
        now = datetime.datetime.now()
        insert_hash = get_insert_hash(now, gwcommon.GW_ALARM_STATUS_SYSERROR, 'dupCheck')

        # 重複データ登録
        insert_hash['error_event_id'] = None
        insert_hash['normal_event_id'] = None
        insert_hash['op_comment'] = 'op_comment_dupCheck'
        insert_hash['project_code'] = 'project_codedupCheck'
        insert_hash['detected_host'] = gwcommon.DETECTED_HOST
        event_ids = HELPER.insert_event_data(self.conn, [insert_hash])
        insert_hash['error_event_id'] = event_ids[0]
        HELPER.insert_incident_data(self.conn, [insert_hash])

        # insert_sys_events呼び出し時の第4引数に渡すメッセージの作成
        message = create_message(insert_hash)

        # 引数のセット
        HELPER.set_sys_argv(message, 'insert_sys_events.py')

        # 処理実行
        with self.assertLogs('insert_sys_events.py') as cm:
            insert_sys_events.main()

        # ログ内容の確認
        expect_event_id = 2

        self.assertEqual(cm.output, [
            'INFO:insert_sys_events.py:マスターモードのたため、マスター動作実行',
            'INFO:insert_sys_events.py:Local DB[%s] 接続成功' % gwcommon.MY_HOST,
            'INFO:insert_sys_events.py:[End1] %s gw_events INSERT成功' % gwcommon.MY_HOST,
            'INFO:insert_sys_events.py:重複レコードです gw_event_id=%s, event_status=99 にUPDATE' % expect_event_id,
            'INFO:insert_sys_events.py:gw_incident_id=None'
        ])

        # データの登録確認
        result = HELPER.get_insert_gw_events_data(self.conn, insert_hash, now)
        self.assertEqual(result[0], 2)
        result_event = HELPER.get_updated_gw_events_data(self.conn, expect_event_id)
        self.assertEqual(result_event['event_status'], int(gwcommon.GW_EVENT_STATUS_DUP))

########################################################################
## Test Helper
########################################################################

def get_insert_hash(now, alarm_status, str):
    return {
        'summary': 'summary_%s' % str,
        'device': 'device_%s' % str,
        'detected_time': now.strftime("%Y.%m.%d %H:%M:%S"),
        'customer_ci': 'customer_ci%s' % str,
        'hostname': 'hostname_%s' % str,
        'ci_name': 'ci_name_%s' % str,
        'alarm_status': alarm_status,
        'customer_name': 'customer_name_%s' % str,
        'host': 'host_%s' % str,
        'alarm_time': now.strftime('%Y.%m.%d %H:%M:%S'),
    }

def create_message(insert_hash):
    expect_keys = [
        'post_system',
        'alarm_time',
        'hostname',
        'ci_name',
        'summary',
        'alarm_status',
        'empty',
        'device',
        'empty',
        'detected_time',
        'empty',
        'customer_ci',
        'customer_name',
        'host'
    ]
    insert_value = []
    for expect_key in expect_keys:
        if insert_hash.get(expect_key) is not None:
            insert_value.append(insert_hash[expect_key])
        else:
            insert_value.append('')
    return '@!!!@'.join(insert_value)

if __name__ == '__main__':
    unittest.main()

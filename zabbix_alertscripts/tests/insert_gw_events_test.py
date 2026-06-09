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
import insert_gw_events
import gwcommon
import test_helper as HELPER

@patch('gwcommon.MY_USER', HELPER.MY_USER)
@patch('gwcommon.MY_PASSWD', HELPER.MY_PASSWD)
# @patch('gwcommon.MY_DB', HELPER.MY_DB_LOCAL)
class InsertGwEventsTest(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        # DB接続
        conn = HELPER.db_connect()

        # テストデータ投入
        insert_test_data(conn)

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

        # パトランプ削除
        patolamp_files = glob.glob(HELPER.PATOLAMP_FILE_PATH + gwcommon.RED_PATOLAMP_FILE + '*')
        for patolamp_file in patolamp_files:
            os.remove(patolamp_file)

    def tearDown(self):
        # DB close
        self.conn.close()

    # @unittest.skip('TESTSKIP')
    @patch('gwcommon.MY_DB', HELPER.MY_DB_LOCAL)
    def test_validate(self):
        # 送信データ
        now = datetime.datetime.now()
        insert_hash_base = get_insert_hash(now, 'error', 'test_validate')

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
                        'ERROR:insert_gw_events.py:customer_nameに規定外の文字が含まれます。：発生ノード= %s 発生時間= %s ' \
                            % (detected_host, update_time,),
                        'INFO:insert_gw_events.py:customer_nameに規定外の文字が含まれます。customer_name= %s' % ('	',),
                    ]
                },
                {
                    'value': num_char(128),
                    'logs': [
                        'ERROR:insert_gw_events.py:customer_nameの文字数オーバーです。：発生ノード= %s 発生時間= %s ' \
                            % (detected_host, update_time,),
                        'INFO:insert_gw_events.py:customer_nameの文字数オーバーです。customer_name= %s' % (num_char(128),),
                    ]
                },
            ],
            'hostname': [
                {
                    'value': '	',
                    'logs': [
                        'ERROR:insert_gw_events.py:hostnameに規定外の文字が含まれます。：発生ノード= %s 発生時間= %s お客様名= %s' \
                            % (detected_host, update_time, insert_hash_base.get('customer_name'),),
                        'INFO:insert_gw_events.py:hostnameに規定外の文字が含まれます。： hostname= %s' % ('	',),
                    ]
                },
                {
                    'value': num_char(257),
                    'logs': [
                        'ERROR:insert_gw_events.py:hostnameの文字数オーバーです。：発生ノード= %s 発生時間= %s お客様名= %s' \
                            % (detected_host, update_time, insert_hash_base.get('customer_name'),),
                        'INFO:insert_gw_events.py:hostnameの文字数が規定以上です hostname= %s' % (num_char(257),),
                    ]
                },
            ],
            'ci_name': [
                {
                    'value': '	',
                    'logs': [
                        'ERROR:insert_gw_events.py:ci_nameに規定外の文字が含まれます。 %s' % (cmmon_alm_log,),
                        'INFO:insert_gw_events.py:ci_nameに規定外の文字が含まれます %s' % ('	',),
                    ]
                },
                {
                    'value': num_char(257),
                    'logs': [
                        'ERROR:insert_gw_events.py:ci_nameの文字数が規定以上です。 %s' % (cmmon_alm_log,),
                        'INFO:insert_gw_events.py:ci_nameの文字数が規定以上です。 ci_name= %s' % (num_char(257),),
                    ]
                },
            ],
            'detected_time': [
                {
                    'value': 's',
                    'logs': [
                        'ERROR:insert_gw_events.py:detected_timeフォーマット異常です。 %s' % (cmmon_alm_log,),
                        'INFO:insert_gw_events.py:detected_timeフォーマット異常です。detected_time= %s' % ('s',),
                    ]
                },
                {
                    'value': '2020-02-30 99:99:99',
                    'logs': [
                        'ERROR:insert_gw_events.py:detected_timeフォーマット異常です。 %s' % (cmmon_alm_log,),
                        'INFO:insert_gw_events.py:detected_timeフォーマット異常です。detected_time= %s' % ('2020-02-30 99:99:99',),
                    ]
                },
            ],
            'customer_ci': [
                {
                    'value': 'テスト',
                    'logs': [
                        'ERROR:insert_gw_events.py:customer_ciに規定外の文字が含まれます。 %s' % (cmmon_alm_log,),
                        'INFO:insert_gw_events.py:customer_ciに規定外の文字が含まれます。customer_ci= %s' % ('テスト',),
                    ]
                },
                {
                    'value': num_char(65),
                    'logs': [
                        'ERROR:insert_gw_events.py:customer_ciの文字数オーバーです。 %s' % (cmmon_alm_log,),
                        'INFO:insert_gw_events.py:customer_ciの文字数オーバーです。customer_ci= %s' % (num_char(65),),
                    ]
                },
            ],
            'alarm_time': [
                {
                    'value': 's',
                    'logs': [
                        'ERROR:insert_gw_events.py:alarm_timeフォーマット異常です。 %s' % (cmmon_alm_log,),
                        'INFO:insert_gw_events.py:alarm_timeフォーマット異常です。alarm_time= %s' % ('s',),
                    ]
                },
                {
                    'value': '2020-02-30@99:99:99.999',
                    'logs': [
                        'ERROR:insert_gw_events.py:alarm_timeフォーマット異常です。 %s' % (cmmon_alm_log,),
                        'INFO:insert_gw_events.py:alarm_timeフォーマット異常です。 alarm_time= %s' % ('2020-02-30 99:99:99.999',),
                    ]
                },
            ],
            'device': [
                {
                    'value': '	',
                    'logs': [
                        'ERROR:insert_gw_events.py:deviceに規定外の文字が含まれます。 %s' % (cmmon_alm_log,),
                        'INFO:insert_gw_events.py:deviceに規定外の文字が含まれます device= %s' % ('	',),
                    ]
                },
                {
                    'value': num_char(256),
                    'logs': [
                        'ERROR:insert_gw_events.py:deviceの文字数オーバーです。 %s' % (cmmon_alm_log,),
                        'INFO:insert_gw_events.py:deviceの文字数オーバーです。device= %s' % (num_char(256),),
                    ]
                },
            ],
            'alarm_status': [
                {
                    'value': gwcommon.GW_ALARM_STATUS_ERROR + 's',
                    'logs': [
                        'ERROR:insert_gw_events.py:alarm_statusが規定外です。 %s' % (cmmon_alm_log,),
                        'INFO:insert_gw_events.py:alarm_statusが規定外です。 alarm_status= %s' % (gwcommon.GW_ALARM_STATUS_ERROR + 's',),
                    ]
                },
            ],
            'summary': [
                {
                    'value': '	',
                    'logs': [
                        'ERROR:insert_gw_events.py:補足に規定外の文字が含まれます %s' % (cmmon_alm_log,),
                        'INFO:insert_gw_events.py:summaryに規定外の文字が含まれます summary= %s' % ('	',),
                    ]
                },
            ],
            'host': [
                {
                    'value': '	',
                    'logs': [
                        'ERROR:insert_gw_events.py:hostに規定外の文字が含まれます。 %s' % (cmmon_alm_log,),
                        'INFO:insert_gw_events.py:hostに規定外の文字が含まれます host= %s' % ('	',),
                    ]
                },
                {
                    'value': num_char(128),
                    'logs': [
                        'ERROR:insert_gw_events.py:hostの文字数オーバーです。 %s' % (cmmon_alm_log,),
                        'INFO:insert_gw_events.py:hostの文字数オーバーです。host= %s' % (num_char(128),),
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

                    # insert_gw_events呼び出し時の第4引数に渡すメッセージの作成
                    message = create_message(insert_hash)

                    # 引数のセット
                    HELPER.set_sys_argv(message, 'insert_gw_events.py')

                    # 処理実行
                    with self.assertLogs('insert_gw_events.py') as cm:
                        with self.assertRaises(SystemExit): # exit()で終わっているのでSystemExitを監視
                            insert_gw_events.main()

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
        insert_hash = get_insert_hash(now, 'error', 'test_validate_summary_over')
        insert_hash['summary'] = 's' * (summary_len + summary_len)

        # insert_gw_events呼び出し時の第4引数に渡すメッセージの作成
        message = create_message(insert_hash)

        # 引数のセット
        HELPER.set_sys_argv(message, 'insert_gw_events.py')

        # 処理実行
        with self.assertLogs('insert_gw_events.py') as cm:
            insert_gw_events.main()

        # ログ内容の確認
        self.assertEqual(cm.output, [
            'INFO:insert_gw_events.py:summaryの文字数オーバーです。規定文字数以上をカットします。 %s' % insert_hash['summary'],
            'INFO:insert_gw_events.py:testモードのため、テストモードで動作実行',
            'INFO:insert_gw_events.py:[End1] %s gw_events INSERT成功' % gwcommon.MY_HOST
        ])

        # データの登録確認
        insert_hash['summary'] = insert_hash.get('summary')[:summary_len]
        result = HELPER.get_insert_gw_events_data(self.conn, insert_hash, now)
        self.assertEqual(result[0], 1)

    # @unittest.skip('TESTSKIP')
    @patch('gwcommon.MY_DB', HELPER.MY_DB_LOCAL)
    def test_input_num_error(self):
        # モード設定
        HELPER.set_test_mode()

        # 送信データ
        now = datetime.datetime.now()
        insert_hash = get_insert_hash(now, 'error', 'test_input_num_error')
        del insert_hash['device']

        # insert_gw_events呼び出し時の第4引数に渡すメッセージの作成
        message = '@!!!@'.join(insert_hash)

        # 引数のセット
        HELPER.set_sys_argv(message, 'insert_gw_events.py')

        # 処理実行
        with self.assertLogs('insert_gw_events.py') as cm:
            insert_gw_events.main()

        # ログ内容の確認
        self.assertEqual(cm.output, [
            'INFO:insert_gw_events.py:testモードのため、テストモードで動作実行',
            'INFO:insert_gw_events.py:[End1] %s gw_events INSERT成功' % gwcommon.MY_HOST
        ])

        # データの登録確認
        time = now.strftime("%Y.%m.%d %H:%M:%S")
        split = message.split(gwcommon.GW_DELIMITER)
        customer_ci = split[len(split) - 2]
        customer_name = split[len(split) - 1]
        data_hash = {
            'alarm_time': time,
            'hostname': gwcommon.BAO_FORMAT_ERROR_HOST,
            'ci_name': gwcommon.BAO_FORMAT_ERROR_ALARM,
            'summary': gwcommon.FORMAT_ERROR_MESSAGE,
            'alarm_status': 'error',
            'device': gwcommon.BAO_FORMAT_ERROR_DEVICE,
            'detected_time': time,
            'customer_ci': customer_ci,
            'customer_name': customer_name,
            'host': '',
            'update_time': time,
            'detected_host': gwcommon.DETECTED_HOST,
        }
        result = HELPER.get_insert_gw_events_data(self.conn, data_hash, now)
        self.assertEqual(result[0], 1)

    # @unittest.skip('TESTSKIP')
    @patch('gwcommon.MY_DB', HELPER.MY_DB_LOCAL)
    def test_test_mode(self):
        # モード設定
        HELPER.set_test_mode()

        # 送信データ
        now = datetime.datetime.now()
        insert_hash = get_insert_hash(now, 'error', 'test_mode')

        # insert_gw_events呼び出し時の第4引数に渡すメッセージの作成
        message = create_message(insert_hash)

        # 引数のセット
        HELPER.set_sys_argv(message, 'insert_gw_events.py')

        # 処理実行
        with self.assertLogs('insert_gw_events.py') as cm:
            insert_gw_events.main()

        # ログ内容の確認
        self.assertEqual(cm.output, [
            'INFO:insert_gw_events.py:testモードのため、テストモードで動作実行',
            'INFO:insert_gw_events.py:[End1] %s gw_events INSERT成功' % gwcommon.MY_HOST
        ])

        # データの登録確認
        result = HELPER.get_insert_gw_events_data(self.conn, insert_hash, now)
        self.assertEqual(result[0], 1)

    # @unittest.skip('TESTSKIP')
    @patch('gwcommon.MY_DB', HELPER.MY_DB_LOCAL)
    # def test_master_mode(self):   # mock不使用Ver
    @patch('gwfunction.get_hostgroups_by_host')
    def test_master_mode(self, mock_get_hostgroups_by_host):
        mock_get_hostgroups_by_host.return_value = [
            gwcommon.FLOOR_11TH_HOSTGROUP
        ]

        # モード設定
        HELPER.set_master_mode()

        # 送信データ
        now = datetime.datetime.now()
        insert_hash = get_insert_hash(now, 'error', 'master_mode')

        # insert_gw_events呼び出し時の第4引数に渡すメッセージの作成
        message = create_message(insert_hash)

        # 引数のセット
        HELPER.set_sys_argv(message, 'insert_gw_events.py')

        # 処理実行
        with self.assertLogs('insert_gw_events.py') as cm:
            insert_gw_events.main()

        # ログ内容の確認
        self.assertEqual(cm.output, [
            'INFO:insert_gw_events.py:マスターモードのため、マスター動作実行',
            'INFO:insert_gw_events.py:パトランプフラグ(/var/lib/baogw/red_patolamp_on)を作成しました。',
            'INFO:insert_gw_events.py:[End2] %s gw_events INSERT成功' % gwcommon.MY_HOST
        ])

        # データの登録確認
        result = HELPER.get_insert_gw_events_data(self.conn, insert_hash, now)
        self.assertEqual(result[0], 1)

        # パトランプファイルの存在チェック
        self.assertTrue(os.path.isfile(HELPER.PATOLAMP_FILE_PATH + gwcommon.RED_PATOLAMP_FILE))

    # @unittest.skip('TESTSKIP')
    @patch('gwcommon.REMOTE_HOST', HELPER.MY_HOST_REMOTE)
    @patch('gwcommon.MY_DB', HELPER.MY_DB_REMOTE)
    def test_slave_mode(self):
        # モード設定
        HELPER.set_slave_mode()

        # 送信データ
        now = datetime.datetime.now()
        insert_hash = get_insert_hash(now, 'error', 'slave_mode')

        # insert_gw_events呼び出し時の第4引数に渡すメッセージの作成
        message = create_message(insert_hash)

        # 引数のセット
        HELPER.set_sys_argv(message, 'insert_gw_events.py')

        # 処理実行
        with self.assertLogs('insert_gw_events.py') as cm:
            insert_gw_events.main()

        # ログ内容の確認
        self.assertEqual(cm.output, [
            'INFO:insert_gw_events.py:スレーブモードのため、スレーブ動作実行',
            'INFO:insert_gw_events.py:remote DB[%s] 接続成功' % gwcommon.REMOTE_HOST,
            'INFO:insert_gw_events.py:[End3] %s gw_events INSERT成功' % gwcommon.REMOTE_HOST
        ])

        # データの登録確認(local)
        result = HELPER.get_insert_gw_events_data(self.conn, insert_hash, now)
        self.assertEqual(result[0], 0)

        # データの登録確認(remote)
        conn_remote = HELPER.db_connect(HELPER.MY_HOST_REMOTE)
        result = HELPER.get_insert_gw_events_data(self.conn, insert_hash, now, HELPER.MY_DB_REMOTE + '.gw_events')
        self.assertEqual(result[0], 1)
        conn_remote.close()

    # @unittest.skip('TESTSKIP')
    @patch('gwcommon.REMOTE_HOST', 'remote_host')   # 接続失敗させる
    @patch('gwcommon.MY_DB', HELPER.MY_DB_LOCAL)
    def test_slave_mode_remote_ng(self):
        # モード設定
        HELPER.set_slave_mode()

        # 送信データ
        now = datetime.datetime.now()
        insert_hash = get_insert_hash(now, 'error', 'slave_mode_remote_ng')

        # insert_gw_events呼び出し時の第4引数に渡すメッセージの作成
        message = create_message(insert_hash)

        # 引数のセット
        HELPER.set_sys_argv(message, 'insert_gw_events.py')

        # 処理実行
        with self.assertLogs('insert_gw_events.py') as cm:
            with self.assertRaises(SystemExit): # exit()で終わっているのでSystemExitを監視
                insert_gw_events.main()

        # ログ内容の確認
        self.assertEqual(cm.output, [
            'INFO:insert_gw_events.py:スレーブモードのため、スレーブ動作実行',
            'CRITICAL:insert_gw_events.py:remote DB[%s] 接続失敗、rescue 動作へ' % gwcommon.REMOTE_HOST,
            "INFO:insert_gw_events.py:2003 (HY000): Can't connect to MySQL server on '%s:3306' (110)" % gwcommon.REMOTE_HOST,
            'INFO:insert_gw_events.py:[End4] %s gw_rescue_events INSERT成功' % gwcommon.MY_HOST
        ])

        # データの登録確認(gw_rescue_events)
        result = HELPER.get_insert_gw_events_data(self.conn, insert_hash, now, 'gw_rescue_events')
        self.assertEqual(result[0], 1)

    # @unittest.skip('TESTSKIP')
    @patch('gwcommon.MY_DB', HELPER.MY_DB_LOCAL)
    @patch('gwfunction.get_hostgroups_by_host')
    def test_action_no_no_patolamp(self, mock_get_hostgroups_by_host):
        mock_get_hostgroups_by_host.return_value = [
            gwcommon.FLOOR_11TH_HOSTGROUP
        ]

        # モード設定
        HELPER.set_master_mode()

        for action in HELPER.NO_NOPATOLAMP_ACTION:
            with self.subTest('action=%s' % action):
                # DB接続
                # ループで回していると、setUpの接続だとうまくいかないので新しく接続
                conn = HELPER.db_connect()

                # 送信データ
                now = datetime.datetime.now()
                insert_hash = get_insert_hash(now, 'error', 'action_' + action)

                # insert_gw_events呼び出し時の第4引数に渡すメッセージの作成
                message = create_message(insert_hash)

                # 引数のセット
                HELPER.set_sys_argv(message, 'insert_gw_events.py')

                # 処理実行
                with self.assertLogs('insert_gw_events.py') as cm:
                    insert_gw_events.main()

                # ログ内容の確認（パトランプの出力ログなし）
                self.assertEqual(cm.output, [
                    'INFO:insert_gw_events.py:マスターモードのため、マスター動作実行',
                    'INFO:insert_gw_events.py:[End2] %s gw_events INSERT成功' % gwcommon.MY_HOST
                ])

                # データの登録確認
                result = HELPER.get_insert_gw_events_data(conn, insert_hash, now)
                self.assertEqual(result[0], 1)

                # パトランプファイルが作成されていない
                self.assertFalse(os.path.isfile(HELPER.PATOLAMP_FILE_PATH + gwcommon.RED_PATOLAMP_FILE))

                conn.close()

    # @unittest.skip('TESTSKIP')
    @patch('gwcommon.MY_DB', HELPER.MY_DB_LOCAL)
    @patch('gwfunction.get_hostgroups_by_host')
    def test_patolamp_on(self, mock_get_hostgroups_by_host):
        # アラートの種類
        alarm_status_patterns = [
            {
                'alarm_status': gwcommon.GW_ALARM_STATUS_ERROR,
                'patolamp_file': gwcommon.RED_PATOLAMP_FILE,
            },
            {
                'alarm_status': gwcommon.GW_ALARM_STATUS_INFO,
                'patolamp_file': gwcommon.RED_PATOLAMP_FILE,
            },
            {
                'alarm_status': gwcommon.GW_ALARM_STATUS_NORMAL,
                'patolamp_file': gwcommon.GREEN_PATOLAMP_FILE,
            },
        ]

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

        for alarm_status_pattern in alarm_status_patterns:
            for hostgroups_by_pattern in hostgroups_by_patterns:
                with self.subTest('alarm_status=%s, hostgroups=%s' % (alarm_status_pattern, hostgroups_by_pattern)):
                    alarm_status = alarm_status_pattern.get('alarm_status')
                    patolamp_file = alarm_status_pattern.get('patolamp_file')
                    host_group = hostgroups_by_pattern.get('host_group')

                    mock_get_hostgroups_by_host.return_value = [
                        host_group
                    ]

                    # 確認対象のパトランプ
                    patolamp = patolamp_file + hostgroups_by_pattern.get('file_suffix')
                    patolamp_file_path = HELPER.PATOLAMP_FILE_PATH + patolamp

                    # モード設定
                    HELPER.set_master_mode()

                    # 送信データ
                    now = datetime.datetime.now()
                    insert_hash = get_insert_hash(now, alarm_status, 'patolamp_on_%s_%s' % (alarm_status, patolamp))

                    # insert_gw_events呼び出し時の第4引数に渡すメッセージの作成
                    message = create_message(insert_hash)

                    # 引数のセット
                    HELPER.set_sys_argv(message, 'insert_gw_events.py')

                    # 処理実行
                    with self.assertLogs('insert_gw_events.py') as cm:
                        insert_gw_events.main()

                    # ログ内容の確認
                    self.assertEqual(cm.output, [
                        'INFO:insert_gw_events.py:マスターモードのため、マスター動作実行',
                        'INFO:insert_gw_events.py:パトランプフラグ(%s)を作成しました。' % patolamp_file_path,
                        'INFO:insert_gw_events.py:[End2] %s gw_events INSERT成功' % gwcommon.MY_HOST
                    ])

                    # パトランプファイルの存在チェック
                    self.assertTrue(os.path.isfile(patolamp_file_path))

########################################################################
## Test Helper
########################################################################

def get_insert_hash(now, alarm_status, str):
    return {
        'summary': 'summary_%s' % str,
        'device': 'device_%s' % str,
        'detected_time': now.strftime("%Y.%m.%d %H:%M:%S"),
        'customer_ci': 'customer_ci_%s' % str,
        'hostname': 'hostname_%s' % str,
        'ci_name': 'ci_name_%s' % str,
        'alarm_status': alarm_status,
        'customer_name': 'customer_name_%s' % str,
        'host': 'host_%s' % str,
        'alarm_time': now.strftime('%Y-%m-%d@%H:%M:%S.%f')[:-3]
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

def insert_test_data(conn):
    cur = conn.cursor()
    for action in HELPER.NO_NOPATOLAMP_ACTION:
        sql = "INSERT INTO gw_rules (rule_id, rule_status, rule_set, start_time, end_time, customer_name, hostname, ci_name, action_no, op_comment, create_user, update_user) \
            VALUES (NULL, '1', NULL, '2020-01-01 00:00:00', '2099-12-31 00:00:00', 'customer_name_action_%s', 'hostname_action_%s', 'ci_name_action_%s', %s, NULL, NULL, NULL)" \
            % (action, action, action, '%s')
        cur.execute(sql, (action,))
    cur.close()
    conn.commit()

if __name__ == '__main__':
    unittest.main()

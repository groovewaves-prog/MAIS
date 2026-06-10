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
import rescue_gw_events
import gwcommon
import test_helper as HELPER

@patch('gwcommon.MY_USER', HELPER.MY_USER)
@patch('gwcommon.MY_PASSWD', HELPER.MY_PASSWD)
# @patch('gwcommon.MY_DB', HELPER.MY_DB_LOCAL)
class RescueGwEventsTest(unittest.TestCase):

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
    def test_test_mode(self):
        # モード設定
        HELPER.set_test_mode()

        # 処理実行
        with self.assertLogs('rescue_gw_events.py') as cm:
            rescue_gw_events.main()

        # ログ内容の確認
        self.assertEqual(cm.output, [
            'INFO:rescue_gw_events.py:testモードのため、処理をスキップします。',
        ])

    # @unittest.skip('TESTSKIP')
    @patch('gwcommon.MY_DB', HELPER.MY_DB_LOCAL)
    def test_master_mode(self):   # mock不使用Ver
    # def test_master_mode(self, mock_get_hostgroups_by_host):
        # モード設定
        HELPER.set_master_mode()

        # 処理実行
        with self.assertLogs('rescue_gw_events.py') as cm:
            rescue_gw_events.main()

        # ログ内容の確認
        select_table_name = 'gw_rescue_events'
        search_condition = 'event_status=%s' % gwcommon.GW_EVENT_STATUS_NEW
        self.assertEqual(cm.output, [
            'INFO:rescue_gw_events.py:マスターモードのため、rescue未処理レコードをgw_eventsに挿入します。',
            'INFO:rescue_gw_events.py:select成功:[%s] %s %s ' % (gwcommon.MY_HOST, select_table_name, search_condition),
            'INFO:rescue_gw_events.py:rescue対象が見つからなかったため、処理を終了します。',
        ])

    # @unittest.skip('TESTSKIP')
    @patch('gwcommon.REMOTE_HOST', HELPER.MY_HOST_REMOTE)
    @patch('gwcommon.MY_DB', HELPER.MY_DB_REMOTE)
    def test_slave_mode(self):
        # モード設定
        HELPER.set_slave_mode()

        # 処理実行
        with self.assertLogs('rescue_gw_events.py') as cm:
            rescue_gw_events.main()

        # ログ内容の確認
        select_table_name = 'gw_rescue_events'
        search_condition = 'event_status=%s' % gwcommon.GW_EVENT_STATUS_NEW
        self.assertEqual(cm.output, [
            'INFO:rescue_gw_events.py:スレーブモードのため、rescue未処理レコードの処理状況を確認します。',
            'INFO:rescue_gw_events.py:select成功:[%s] %s %s ' % (gwcommon.MY_HOST, select_table_name, search_condition),
            'INFO:rescue_gw_events.py:rescue対象が見つからなかったため、処理を終了します。',
        ])

    # @unittest.skip('TESTSKIP')
    @patch('gwcommon.MY_DB', HELPER.MY_DB_LOCAL)
    def test_master_mode_insert(self):
        # モード設定
        HELPER.set_master_mode()

        # テストデータ投入
        now = datetime.datetime.now()
        insert_hash1 = get_insert_hash(now, 'error', 'test_master_mode_insert1')
        insert_hash2 = get_insert_hash(now, 'error', 'test_master_mode_insert2')
        insert_test_data(self.conn, [insert_hash1, insert_hash2])

        # 処理実行
        with self.assertLogs('rescue_gw_events.py') as cm:
            rescue_gw_events.main()

        # ログ内容の確認
        select_table_name = 'gw_rescue_events'
        search_condition = 'event_status=%s' % gwcommon.GW_EVENT_STATUS_NEW
        insert_table_name = 'gw_events'
        delete_table_name = 'gw_rescue_events'
        delete_condition1 = 'gw_event_id=1'
        delete_condition2 = 'gw_event_id=2'

        self.assertEqual(cm.output, [
            'INFO:rescue_gw_events.py:マスターモードのため、rescue未処理レコードをgw_eventsに挿入します。',
            'INFO:rescue_gw_events.py:select成功:[%s] %s %s ' % (gwcommon.MY_HOST, select_table_name, search_condition),
            'INFO:rescue_gw_events.py:INSERT成功:[%s] %s %s' % (gwcommon.MY_HOST, insert_table_name, make_insert_value(insert_hash1)),
            'INFO:rescue_gw_events.py:delete成功:[%s] %s %s' % (gwcommon.MY_HOST, delete_table_name, delete_condition1),
            'INFO:rescue_gw_events.py:INSERT成功:[%s] %s %s' % (gwcommon.MY_HOST, insert_table_name, make_insert_value(insert_hash2)),
            'INFO:rescue_gw_events.py:delete成功:[%s] %s %s' % (gwcommon.MY_HOST, delete_table_name, delete_condition2),
        ])


    # @unittest.skip('TESTSKIP')
    @patch('gwcommon.MY_DB', HELPER.MY_DB_LOCAL)
    def test_slave_mode_delete_rescue(self):
        # モード設定
        HELPER.set_slave_mode()

        # テストデータ投入
        now = datetime.datetime.now()
        insert_hash1 = get_insert_hash(now, 'error', 'test_slave_mode_delete_rescue1')
        insert_hash2 = get_insert_hash(now, 'error', 'test_slave_mode_delete_rescue2')
        insert_test_data(self.conn, [insert_hash1, insert_hash2], 'gw_events')
        insert_test_data(self.conn, [insert_hash1, insert_hash2])

        # 処理実行
        with self.assertLogs('rescue_gw_events.py') as cm:
            rescue_gw_events.main()

        # ログ内容の確認
        select_table_name = 'gw_rescue_events'
        search_condition = 'event_status=%s' % gwcommon.GW_EVENT_STATUS_NEW
        delete_table_name = 'gw_rescue_events'
        delete_condition1 = 'gw_event_id=1'
        delete_condition2 = 'gw_event_id=2'

        self.assertEqual(cm.output, [
            'INFO:rescue_gw_events.py:スレーブモードのため、rescue未処理レコードの処理状況を確認します。',
            'INFO:rescue_gw_events.py:select成功:[%s] %s %s ' % (gwcommon.MY_HOST, select_table_name, search_condition),
            'INFO:rescue_gw_events.py:delete成功:[%s] %s %s' % (gwcommon.MY_HOST, delete_table_name, delete_condition1),
            'INFO:rescue_gw_events.py:delete成功:[%s] %s %s' % (gwcommon.MY_HOST, delete_table_name, delete_condition2),
        ])

        # データの登録確認(gw_rescue_events)
        result1 = HELPER.get_insert_gw_events_data(self.conn, insert_hash1, now, 'gw_rescue_events')
        self.assertEqual(result1[0], 0)
        result2 = HELPER.get_insert_gw_events_data(self.conn, insert_hash2, now, 'gw_rescue_events')
        self.assertEqual(result2[0], 0)

    # @unittest.skip('TESTSKIP')
    @patch('gwcommon.MY_DB', HELPER.MY_DB_LOCAL)
    def test_slave_mode_not_delete_rescue(self):
        # モード設定
        HELPER.set_slave_mode()

        # テストデータ投入
        now = datetime.datetime.now()
        insert_hash1 = get_insert_hash(now, 'error', 'test_slave_mode_not_delete_rescue1')
        insert_hash2 = get_insert_hash(now, 'error', 'test_slave_mode_not_delete_rescue2')
        insert_test_data(self.conn, [insert_hash1, insert_hash2])

        # 処理実行
        with self.assertLogs('rescue_gw_events.py') as cm:
            rescue_gw_events.main()

        # ログ内容の確認
        select_table_name = 'gw_rescue_events'
        search_condition = 'event_status=%s' % gwcommon.GW_EVENT_STATUS_NEW

        self.assertEqual(cm.output, [
            'INFO:rescue_gw_events.py:スレーブモードのため、rescue未処理レコードの処理状況を確認します。',
            'INFO:rescue_gw_events.py:select成功:[%s] %s %s ' % (gwcommon.MY_HOST, select_table_name, search_condition),
            'INFO:rescue_gw_events.py:該当レコードがgw_eventsに見つからなかったため、次回処理に繰り越します。gw_event_id=1 update_time=%s detected_time=%s detected_host=%s customer_ci=%s customer_name=%s hostname=%s alarm_time=%s ci_name=%s device=%s alarm_status=%s summary=%s host=%s' % (insert_hash1['detected_time'], insert_hash1['detected_time'], insert_hash1['detected_host'], insert_hash1['customer_ci'], insert_hash1['customer_name'], insert_hash1['hostname'], insert_hash1['alarm_time'], insert_hash1['ci_name'], insert_hash1['device'], insert_hash1['alarm_status'], insert_hash1['summary'], HELPER.convert_str(insert_hash1['host'])),
            'INFO:rescue_gw_events.py:該当レコードがgw_eventsに見つからなかったため、次回処理に繰り越します。gw_event_id=2 update_time=%s detected_time=%s detected_host=%s customer_ci=%s customer_name=%s hostname=%s alarm_time=%s ci_name=%s device=%s alarm_status=%s summary=%s host=%s' % (insert_hash2['detected_time'], insert_hash2['detected_time'], insert_hash2['detected_host'], insert_hash2['customer_ci'], insert_hash2['customer_name'], insert_hash2['hostname'], insert_hash2['alarm_time'], insert_hash2['ci_name'], insert_hash2['device'], insert_hash2['alarm_status'], insert_hash2['summary'], HELPER.convert_str(insert_hash2['host'])),
        ])

        # データの登録確認(gw_rescue_events)
        result1 = HELPER.get_insert_gw_events_data(self.conn, insert_hash1, now, 'gw_rescue_events')
        self.assertEqual(result1[0], 1)
        result2 = HELPER.get_insert_gw_events_data(self.conn, insert_hash2, now, 'gw_rescue_events')
        self.assertEqual(result2[0], 1)

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
    }

def insert_test_data(conn, insert_hash_list, table = 'gw_rescue_events'):
    for insert_hash in insert_hash_list:
        cur = conn.cursor()
        insert_item = 'update_time, detected_time, detected_host, customer_ci, customer_name,\
                    hostname, alarm_time, ci_name, device, alarm_status, summary, host'
        insert_value = 'now(), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s'
        value = (insert_hash['detected_time'], insert_hash['detected_host'], insert_hash['customer_ci'],
            insert_hash['customer_name'], insert_hash['hostname'], insert_hash['alarm_time'],
            insert_hash['ci_name'], insert_hash['device'], insert_hash['alarm_status'], insert_hash['summary'], insert_hash['host'])
        sql = 'INSERT INTO %s (%s) VALUES (%s)' % (table, insert_item, insert_value)
        cur.execute(sql, value)
        cur.close()
    conn.commit()

def make_insert_value(found_rec):
    """
    insert_value作成用関数 結果をinsert_valueにて返信
    """
    insert_value = 'now(), "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s"' % \
    (found_rec['detected_time'], found_rec['detected_host'], found_rec['customer_ci'],\
    found_rec['customer_name'], found_rec['hostname'], found_rec['alarm_time'],\
    found_rec['ci_name'], found_rec['device'], found_rec['alarm_status'], found_rec['summary'], HELPER.convert_str(found_rec['host']))
    return insert_value

if __name__ == '__main__':
    unittest.main()

import datetime
import random
import os
import subprocess
import time

RANDOM_INSERT_SYSTEM = 'random_insert_system'
INSERT_GW_SCRIPT_PATH = '/usr/lib/zabbix/alertscripts/insert_gw_events.py'

irregular_date_time_list = ['2000/01/01 00:00:00.000000', '2100/01/01 00:00:00.000000']
alarm_status_list = ['error', 'error', 'normal', 'normal', 'normal']
customer_name_list = ['検証01', '検証02', '連携テスト', '連携テスト']
customer_ci_list = ['customer_ci']
hostname_list = ['no_rule', 'rule_10', 'rule_20', 'rule_30']
ci_name_list = ['ci_name']
device_list = ['device']
#customer_name_list = ['検証01', '検証02', '連携テスト']
#customer_ci_list = ['customer_ci_01', 'customer_ci_02', 'customer_ci_03']
#hostname_list = ['hostname_01', 'hostname_02', 'hostname_03']
#ci_name_list = ['ci_name_01', 'ci_name_02', 'ci_name_03']
#device_list = ['device_01', 'device_02', 'device_03']
summary_list = ['', 'summary']

def insert_event(insert_hash):
    insert_hash['post_system'] = RANDOM_INSERT_SYSTEM
    insert_hash['empty'] = ''


    expect_keys = ['post_system', 'alarm_time', 'hostname', 'ci_name', 'summary', 'alarm_status', 'empty', 'device', 'empty', 'detected_time', 'empty', 'customer_ci', 'customer_name', 'empty']
    insert_value = []
    for expect_key in expect_keys:
        if insert_hash.get(expect_key) is not None:
            insert_value.append(insert_hash[expect_key])
        else:
            print('Invalid hash. Missing key: %s' % expect_key)
            insert_value.append('')
    message = '@!!!@'.join(insert_value)

    filepath = INSERT_GW_SCRIPT_PATH
    script_file_name = os.path.basename(filepath)
    print('%s %s %s %s' % (filepath, script_file_name, '', message))
    subprocess.Popen(['python3', filepath, script_file_name, '', message])
    #subprocess.call(['python3', filepath, script_file_name, '', message])

def insert_random_event(insert_same_event_count):
    #if random.randint(0, 99) == 0: # 発生率1/100
    if random.randint(0, 19) == 0:
      timestamp =  datetime.datetime.strptime(random.choice(irregular_date_time_list), "%Y/%m/%d %H:%M:%S.%f")
    else:
      timestamp = datetime.datetime.now()
    insert_values = {
        'alarm_status': random.choice(alarm_status_list),
        'alarm_time': timestamp.strftime("%Y-%m-%d@%H:%M:%S.%f")[:-3],
        'detected_time': timestamp.strftime("%Y.%m.%d %H:%M:%S"),
        'customer_name': random.choice(customer_name_list),
        'hostname': random.choice(hostname_list),
        'customer_ci': random.choice(customer_ci_list),
        'ci_name': random.choice(ci_name_list),
        'device': random.choice(device_list),
        'summary': random.choice(summary_list)
    }

    for i in range(insert_same_event_count):
        insert_event(insert_values)


def main():
    while True:
        #random_post_same_request = random.choice([1, 2, 3])
        random_post_same_request = 1
        insert_random_event(random_post_same_request)

        #waiting_time = 0
        waiting_time = random.choice([0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                      1, 1, 1, 1, 1, 1, 1, 1, 1, 5])
        if waiting_time != 0:
            time.sleep(waiting_time)

if __name__ == '__main__':
    main()
    print('exit')

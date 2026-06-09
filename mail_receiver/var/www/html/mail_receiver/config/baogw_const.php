<?php
use App\View\Helper\InputSetHelper;


//セッション保持期間取得　ビューにも渡す
// $session_protected = (array) ($this->request->session());
// $config['SESSION_LIFETIME'] = $session_protected["\0*\0_lifetime"];

// $config['CURRENT_SERVER_ID']    = '129';
// $config['PRIMARY_SERVER_ID']    = '129';
// $config['CURRENT_SERVER_ID']    = '222';
$config['CURRENT_HOSTNAME']      = gethostname();

$curennt_server_ip               = $_SERVER['SERVER_ADDR'];
$config['CURRENT_SERVER_IP']     = $curennt_server_ip;
$config['CURRENT_SERVER_IP_4TH'] = InputSetHelper::explode('.', $curennt_server_ip)[3];

$config['CURRENT_SERVER_IP_4TH'] = '129';
$config['PRIMARY_SERVER_ID']     = '129'; //表示レコード条件
$config['SECOUNDARY_SERVER_ID']  = '130';


if ($config['CURRENT_SERVER_IP_4TH']== $config['PRIMARY_SERVER_ID']) {
    $flag_primary = true;
} else {
    $flag_primary = false;
}
$config['FLAG_PRIMARY'] = $flag_primary;


$config['ZBX_API_URL']           = 'http://' . $_SERVER['SERVER_ADDR'] . '/zabbix/api_jsonrpc.php';
// $config['PATLITE_STOP_PAGE']  = 'http://' . $_SERVER['SERVER_ADDR'] . '/baogw/gw-events/stop-patolite';
$config['PATLITE_STOP_PAGE']     = '/baogw/gw-events/stop-patolite';
// $config['PATLITE_STOP_SCRIPT']   = '/var/www/html/baogw/webroot/test.sh';
$config['PATLITE_STOP_SCRIPT']   = '/usr/local/bin/stop_blink_patolamp.sh';
$config['CURRENT_PRIMARY_FILE']  = '/var/lib/baogw/primary';
$config['CURRENT_TEST_FILE']  = '/var/lib/baogw/test';
$config['KISYS_URL']             = 'http://{0}/arsys/forms/kistm4vtmapvip1/TM_DuplicateCheck?F536870937={1}';
$config['KVN_IP']                = 'kisystm.kddi.com';
$config['KISYS_URL_OLD']         = 'http://{0}/arsys/forms/kisysap0/SHR%3ALandingConsole/Default+Adminstrator+View/'
                                 . '?mode=search&F304255500=HPD%3AHelp+Desk&F1000000076=FormOpenNoAppList&F303647600=SearchTicketWithQual&F304255610=%271000000161%27%3D%22{1}%22';
$config['KVN_IP_OLD']            = 'kisysweb0';
$config['KIDS_IP']               = '10.7.16.20';
$config['KOMPIRA_URL']           = 'https://{0}/.itos_ope/#/AlarmPortal/Incidents/{1}';
$config['KOMPIRA_IP']            = 'kompira';
$config['KOMPIRA_SEND_SUCCESS']  = 'Kompira連携成功';
$config['KOMPIRA_SEND_FAILURE']  = 'Kompira連携失敗';
$config['KOMPIRA_NOSEND']  = 'Kompira連携しません(BAOGW内設定)';

$config['CMDB_USERNAME']  = 'cmdbadmin';
$config['CMDB_PASSWORD']  = 'Csl0pe#9';
$config['CMDB_WEB_URL']   = 'https://slcmdbweb/cmdb';
$config['CMDB_BUILD_URL'] = 'https://slcmdbdb:8080/cmdbuild';
$config['CMDB_TIMEOUT']  = 300; // 5分で接続タイムアウト

//FLAG_NEW_DAY　と FLAG_NEW_HOURは、or条件
$config['FLAG_NEW_DAY']          = '0'; //1・・・1日以内
$config['FLAG_NEW_HOUR']         = '1'; //1・・・1時間以内

// $config['COLUMNS_RULES']  = ['1' =>'rule_id',
//                              '2' =>'rule_status',
//                              '3' =>'rule_set',
//                              '4' =>'start_time',
//                              '6' =>'end_time',
//                              '7' =>'customer_name',
//                              '8' =>'hostname',
//                              '9' =>'ci_name',
//                              '10'=>'action_no',
//                              '11'=>'actions',
//                             ];

$config['COLUMNS_RULES']  = ['rule_id'       =>'rule_id',
                             'rule_status'   =>'rule_status',
                             // 'rule_set'      =>'rule_set',
                             'start_time'    =>'start_time',
                             'end_time'      =>'end_time',
                             'customer_name' =>'customer_name',
                             'hostname'      =>'hostname',
                             'ci_name'       =>'ci_name',
                             'action_no'     =>'action_no',
                             'op_comment'    =>'op_comment',
                             'actions'       =>'actions',
                            ];

$config['COLUMNS_EVENTS']  = ['gw_event_id'   =>'gw_event_id',
                              'alarm_time_error' =>'alarm_time_error',
                              'alarm_time_normal'=>'alarm_time_normal',
                              'alarm_status'  =>'alarm_status',
                              'customer_name' =>'customer_name',
                              'hostname'      =>'hostname',
                              'ci_name'       =>'ci_name',
                              'summary_error' =>'summary_error',
                              'summary_normal'=>'summary_normal',
                              'ci_name'       =>'ci_name',
                              'device'        =>'device',
                              'detail_event'  =>'detail_event',
                              'actions'       =>'actions',
                            ];

$config['ALARM_STATUS_NAME'] = ['error_red'    =>'error_red',
                                'error_orange' =>'error_orange',
                                'error_yellow' =>'error_yellow',
                                'normal'    =>'normal',
                                'info'      =>'info',
                                'sec'       =>'sec',
                                'syserror'  =>'syserror',
                                'sysnormal' =>'sysnormal',
                               ];

$config['ALARM_STATUS_NAME_FOR_CSV'] = ['error_red'    =>'error_red',
                                        'error_orange' =>'error_orange',
                                        'error_yellow' =>'error_yellow',
                                        'normal'    =>'normal',
                                        ];

$config['RULE_SET_NAME'] = ['1'=>'1:チケット起票時',
                            '2'=>'2:チケットクローズ'];

$config['RULE_SET_DESC'] = ['1'=>'1:チケット起票時に使用されるルールです。',
                            '2'=>'2:チケットクローズに使用されるルールです。'];

$config['ACTION_NO_NAME'] = ['10'=>'10:K-ISYS起票しません（パトランプ鳴動します）',
                             '20'=>'20:K-ISYS起票とパトランプ鳴動しません',
                             '30'=>'30:キャンセル待ちします(5分)',
                             '31'=>'31:キャンセル待ちします(10分)',
                             '32'=>'32:キャンセル待ちします(15分)',
                             '33'=>'33:キャンセル待ちします(20分)',
                             '34'=>'34:キャンセル待ちします(25分)',
                             '35'=>'35:キャンセル待ちします(30分)',
                             // '80'=>'80:Kompira連携しません',
                             // '90'=>'90:K-ISYSメンテナンスです'
                            ];
 $config['ACTION_NO_DESC'] = ['10'=>'10:K-ISYS起票しません（パトランプ鳴動します）　（優先順位２）',
                              '20'=>'20:K-ISYS起票とパトランプ鳴動しません　（優先順位３）',
                              '30'=>'30:キャンセル待ちします(5分)　（優先順位４）',
                              '31'=>'31:キャンセル待ちします(10分)　（優先順位４）',
                              '32'=>'32:キャンセル待ちします(15分)　（優先順位４）',
                              '33'=>'33:キャンセル待ちします(20分)　（優先順位４）',
                              '34'=>'34:キャンセル待ちします(25分)　（優先順位４）',
                              '35'=>'35:キャンセル待ちします(30分)　（優先順位４）',
                              // '80'=>'80:Kompira連携しません',
                              // '90'=>'90:K-ISYSメンテナンスです　（優先順位１）'
                             ];

 $config['KISYS_SEND_STATUS'] = ['0'=>'',
                                 '1'=>'K-ISYS起票失敗',
                                 '2'=>'BAO無応答のためK-ISYS起票失敗',
                                 '9'=>'K-ISYS連携待ち中',
                                 '10'=>'K-ISYS起票しません(パトランプ鳴動します)(BAOGW内設定)',
                                 '20'=>'K-ISYS起票とパトランプ鳴動しません(BAOGW内設定)',
                                 '30'=>'キャンセル待ちします(5分)',
                                 '31'=>'キャンセル待ちします(10分)',
                                 '32'=>'キャンセル待ちします(15分)',
                                 '33'=>'キャンセル待ちします(20分)',
                                 '34'=>'キャンセル待ちします(25分)',
                                 '35'=>'キャンセル待ちします(30分)',
                                 '40'=>'時間内復旧(K-ISYS起票自動キャンセル)<br>',
                                 '41'=>'時間内復旧(K-ISYS起票自動キャンセル)<br>K-ISYS起票失敗',
                                 '42'=>'時間内復旧(K-ISYS起票自動キャンセル)<br>BAO無応答のためK-ISYS起票失敗',
                                 '43'=>'時間内復旧(K-ISYS起票しません)',
                                 '49'=>'K-ISYS連携待ち中',
                                 '50'=>'要対応（時間内未復旧）<br>',
                                 '51'=>'要対応（時間内未復旧）<br>K-ISYS起票失敗',
                                 '52'=>'要対応（時間内未復旧）<br>BAO無応答のためK-ISYS起票失敗',
                                 '53'=>'要対応（時間内未復旧）<br>K-ISYS起票しません',
                                 '59'=>'K-ISYS連携待ち中',
                                 '60'=>'',
                                 '61'=>'K-ISYS起票失敗',
                                 '62'=>'BAO無応答のためK-ISYS起票失敗',
                                 '69'=>'K-ISYS連携待ち中',
                                 '70'=>'',
                                 '71'=>'K-ISYS起票失敗',
                                 '72'=>'BAO無応答のためK-ISYS起票失敗',
                                 '79'=>'K-ISYS連携待ち中',
                                 '90'=>'K-ISYSメンテナンスです(BAOGW内設定)',
                                 '100'=>'K-ISYS起票しません(BAOGW内設定)',
                                ];

$config['KISYS_SEND_FAILURE_BY_ALARM_STATUS'] = ['error'=>[
                                                    '1'=>'K-ISYS発生起票失敗',
                                                    '2'=>'BAO無応答のためK-ISYS発生起票失敗',
                                                    '9'=>'K-ISYS連携待ち中（発生報）',
                                                    '41'=>'時間内復旧(K-ISYS起票自動キャンセル)<br>K-ISYS発生起票失敗',
                                                    '42'=>'時間内復旧(K-ISYS起票自動キャンセル)<br>BAO無応答のためK-ISYS発生起票失敗',
                                                    '49'=>'K-ISYS連携待ち中（発生報）',
                                                    '51'=>'要対応（時間内未復旧）<br>K-ISYS発生起票失敗',
                                                    '52'=>'要対応（時間内未復旧）<br>BAO無応答のためK-ISYS発生起票失敗',
                                                    '59'=>'K-ISYS連携待ち中（発生報）',
                                                    '61'=>'K-ISYS発生起票失敗',
                                                    '62'=>'BAO無応答のためK-ISYS発生起票失敗',
                                                    '69'=>'K-ISYS連携待ち中（発生報）',
                                                    '71'=>'K-ISYS発生起票失敗',
                                                    '72'=>'BAO無応答のためK-ISYS発生起票失敗',
                                                    '79'=>'K-ISYS連携待ち中（発生報）',
                                                ],
                                                'normal'=>[
                                                    '1'=>'K-ISYS復旧追記失敗',
                                                    '2'=>'BAO無応答のためK-ISYS復旧追記失敗',
                                                    '9'=>'K-ISYS連携待ち中（復旧報）',
                                                    '41'=>'時間内復旧(K-ISYS起票自動キャンセル)<br>K-ISYS復旧追記失敗',
                                                    '42'=>'時間内復旧(K-ISYS起票自動キャンセル)<br>BAO無応答のためK-ISYS復旧追記失敗',
                                                    '49'=>'K-ISYS連携待ち中（復旧報）',
                                                    '51'=>'要対応（時間内未復旧）<br>K-ISYS復旧追記失敗',
                                                    '52'=>'要対応（時間内未復旧）<br>BAO無応答のためK-ISYS復旧追記失敗',
                                                    '59'=>'K-ISYS連携待ち中（復旧報）',
                                                    '61'=>'K-ISYS復旧追記失敗',
                                                    '62'=>'BAO無応答のためK-ISYS復旧追記失敗',
                                                    '69'=>'K-ISYS連携待ち中（復旧報）',
                                                    '71'=>'K-ISYS復旧追記失敗',
                                                    '72'=>'BAO無応答のためK-ISYS復旧追記失敗',
                                                    '79'=>'K-ISYS連携待ち中（復旧報）',
                                                ],
                            ];

$config['SEND_STATUS'] = ['1'=>'K-ISYS起票成功',
                          '2'=>'K-ISYS発生起票失敗',
                          '3'=>'K-ISYS復旧追記失敗',
                          '10'=>'K-ISYS起票しません（パトランプ鳴動します）',
                          '20'=>'K-ISYS起票とパトランプ鳴動しません',
                          '30'=>'キャンセル待ちします',
                          '40'=>'時間内復旧（K-ISYS起票自動キャンセル）',
                          '50'=>'要対応（時間内未復旧）',
                          '81'=>'Kompira連携成功',
                          '82'=>'Kompira連携失敗',
                         ];

$config['HOWCOM_USER_GROUP']  = 'ハウコム運用者';
$config['HOWCOM_HOST_GROUP']  = 'ハウコム運用顧客';
$config['KDDI_MIYAZAKI']  = '宮崎ヘルプ';
$config['PATLITE_STOP_SCRIPT_HOWCOM']  = '/usr/local/bin/stop_blink_patolamp_howcom.sh';

$config['VIP_HOST_GROUP']  = 'VIP顧客';
$config['PATLITE_STOP_SCRIPT_VIP']  = '/usr/local/bin/stop_blink_patolamp_vip.sh';
$config['ALL_SEARCH_USER_GROUPS'] = ['SysEngineer',
                                     'OpeManager',
                                     'OpeEngineer',
                                     'SysManager',
                                     'Reader',
                                    ];

// テスト用
// $config['CURRENT_SERVER_IP_4TH'] = '222';
// $config['PRIMARY_SERVER_ID']     = '222';
// $config['FLAG_PRIMARY'] = false; //へっだー
// $config['CURRENT_PRIMARY_FILE']  = '/var/lib/baogw/primarys';

return $config;
?>

<?php
namespace App\Controller;

use Cake\Core\Exception\Exception;

class GwMergeExportData {

// ======================================================================================================================================================
public function merge_data($bao_gw_data, $cmdb_data) {
    $merged_data = Array();
    if ($cmdb_data['status'] != 200) {
        throw new \Cake\Core\Exception\CakeException(__("レスポンスが不正です。status code:") . $cmdb_data['status']);
    } else {
        for ($i=0; $i < count($bao_gw_data); $i++) {
            $gwEvent = $bao_gw_data[$i];
            $cmdb = $cmdb_data['results'][$i];
            $gwIncident = $gwEvent->gw_incident;
            $merged_data[] = array(
                '件名(案件名)' => array_key_exists('ProjectName', $cmdb) ? $cmdb['ProjectName'] : '',
                'KISYS会社名' => array_key_exists('CompanyName', $cmdb) ? $cmdb['CompanyName'] : '',
                'KISYS略称名' => $gwEvent->customer_ci,
                'ユーザホスト名' => array_key_exists('Hostname', $cmdb) ? $cmdb['Hostname'] : '',
                'ホスト名(監視サーバ登録)' => $gwEvent->hostname,
                'アラート発生日時' => ($gwEvent->alarm_status == 'error') ? $gwEvent->alarm_time : '',
                'アラート復旧日時' => ($gwEvent->alarm_status == 'normal') ? $gwEvent->alarm_time : '',
                'アラート種別' => $gwEvent->alarm_status,
                '国名' => array_key_exists('Country', $cmdb) ? $cmdb['Country'] : '',
                '拠点名' => array_key_exists('SiteName', $cmdb) ? $cmdb['SiteName'] : '',
                '住所(設置場所)' => array_key_exists('Address', $cmdb) ? $cmdb['Address'] : '',
                '回線ID(E番など)' => array_key_exists('CircuitNo', $cmdb) ? $cmdb['CircuitNo'] : '',
                '回線契約名義(会社名)' => array_key_exists('CircuitCustomer', $cmdb) ? $cmdb['CircuitCustomer'] : '',
                '回線エンドユーザ' => array_key_exists('CircuitEndUser', $cmdb) ? $cmdb['CircuitEndUser'] : '',
                '回線サービス種別' => array_key_exists('CircuitServiceType', $cmdb) ? $cmdb['CircuitServiceType'] : '',
                '回線種別' => array_key_exists('CircuitType', $cmdb) ? $cmdb['CircuitType'] : '',
                '回線責任部門' => array_key_exists('ConnectAria', $cmdb) ? $cmdb['ConnectAria'] : '',
                'アラート名' => $gwEvent->ci_name,
                'アラート詳細' => $gwEvent->summary,
                'KISYSインシデント番号' => is_null($gwIncident) ? '' : $gwIncident->kisys_incidentid,
                'BAOGW承認/未承認' => $gwEvent->checked_time,
                'BAOGW補記情報' => is_null($gwIncident) ? '' : $gwIncident->op_comment,
                'ホストに関する備考' => '',
                'イベントID' => $gwEvent->gw_event_id,
                'エラー種別' => $gwEvent->kisys_status,
            );
        }
    }
    return $merged_data;
}
}

<?php
namespace App\Controller;

use Cake\Core\Exception\Exception;

class GwMergeExportDataDmy {

// ======================================================================================================================================================
public function merge_data($bao_gw_data) {
    $merged_data = Array();
        for ($i=0; $i < count($bao_gw_data); $i++) {
            $gwEvent = $bao_gw_data[$i];
            $gwIncident = $gwEvent->gw_incident;
            $merged_data[] = array(
                '件名(案件名)' => 'ProjectName' . (string)($i+1),
                'KISYS会社名' => 'CompanyName' . (string)($i+1),
                'KISYS略称名' => $gwEvent->customer_ci,
                'ユーザホスト名' => 'Hostname' . (string)($i+1),
                'ホスト名(監視サーバ登録)' => $gwEvent->hostname,
                'アラート発生日時' => ($gwEvent->alarm_status == 'error') ? $gwEvent->alarm_time : '',
                'アラート復旧日時' => ($gwEvent->alarm_status == 'normal') ? $gwEvent->alarm_time : '',
                'アラート種別' => $gwEvent->alarm_status,
                '国名' => 'Country' . (string)($i+1),
                '拠点名' => 'SiteName' . (string)($i+1),
                '住所(設置場所)' => 'Address' . (string)($i+1),
                '回線ID(E番など)' => 'CircuitNo' . (string)($i+1),
                '回線契約名義(会社名)' => 'CircuitCustomer' . (string)($i+1),
                '回線エンドユーザ' => 'CircuitEndUser' . (string)($i+1),
                '回線サービス種別' => 'CircuitServiceType' . (string)($i+1),
                '回線種別' => 'CircuitType' . (string)($i+1),
                '回線責任部門' => 'ConnectAria' . (string)($i+1),
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
    return $merged_data;
}
}

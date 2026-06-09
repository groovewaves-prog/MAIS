<?php
namespace App\Controller;

use Cake\Core\Configure;

class GwRequestCMDB {

    public function request($data) {
        $ch = curl_init();
        $header = [
            'Content-Type: application/json',
        ];
        $data = array(
            "inputDataList" => $data,
        );
        $CMDB_WEB_URL = Configure::read("CMDB_WEB_URL");
        curl_setopt($ch, CURLOPT_URL, $CMDB_WEB_URL . '/api/getMachineInfo');
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($ch, CURLOPT_CUSTOMREQUEST, 'POST');
        curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($data, JSON_UNESCAPED_UNICODE));
        curl_setopt($ch, CURLOPT_HTTPHEADER, $header);
        curl_setopt($ch, CURLOPT_HEADER, true);
        curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, false);
        $CMDB_TIMEOUT = Configure::read("CMDB_TIMEOUT");
        curl_setopt($ch, CURLOPT_TIMEOUT, $CMDB_TIMEOUT);
        $curl_response = curl_exec($ch);
        $status_code = curl_getinfo($ch, CURLINFO_RESPONSE_CODE);
        $header_size = curl_getinfo($ch, CURLINFO_HEADER_SIZE);
        return array('curl_response' => $curl_response, 'status_code' => $status_code, 'header_size' => $header_size);
    }
}

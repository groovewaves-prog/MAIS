<?php
namespace App\Controller;

use App\Controller\GwFetchAlertEvent;
use App\Controller\GwMergeExportData;

//CMBD環境ある場合はこちらを生かす
//use App\Controller\GwRequestCMDB;

//CMBD環境ないときはこちらを生かす
use App\Controller\GwMergeExportDataDmy;

use Cake\Core\Exception\Exception;

class GwCreateExportData {

    private $fetchAlertEvent;
    private $cmdb;
    private $mergeExportData;

    public function __construct($fetchAlertEvent=null, $cmdb=null, $mergeExportData=null) {
        if ($fetchAlertEvent === null) {
            $this->fetchAlertEvent = new GwFetchAlertEvent();
        } else {
            $this->fetchAlertEvent = $fetchAlertEvent;
        }
        if ($cmdb === null) {
            $this->cmdb = new GwRequestCMDB();
        } else {
            $this->cmdb = $cmdb;
        }
        if ($mergeExportData === null) {

//CMBD環境ある場合はこちらを生かす
//            $this->mergeExportData = new GwMergeExportData();

//CMBD環境ないときはこちらを生かす
            $this->mergeExportData = new GwMergeExportDataDmy();

        } else {
            $this->mergeExportData = $mergeExportData;
        }
    }

    public function createExportData($filter) {
        $event_data = $this->_get_data_from_bao_gw($filter);

        if (count($event_data) == 0) {
            return array();
        }
        $search_list = Array();
        foreach ($event_data as $gwEvents) {
            $searchData = array(
                "Kisys" => $gwEvents->customer_ci,
                "FQDN" =>  $gwEvents->hostname,
            );
            $search_list[] = $searchData;
        }

//CMBD環境ある場合はこちらを生かす
//        $cmdb_data = $this->_get_data_from_cmdb($search_list);
//        return $this->mergeExportData->merge_data($event_data, $cmdb_data);

//CMBD環境ないときはこちらを生かす
        return $this->mergeExportData->merge_data($event_data);
    }

    function _get_data_from_bao_gw($filter) {
        return $this->fetchAlertEvent->get_gw_data($filter);
    }

    function _get_data_from_cmdb($data) {
        $result = $this->cmdb->request($data);
        $curl_response = $result['curl_response'];
        $status_code = $result['status_code'];
        $header_size = $result['header_size'];
        if ($curl_response == false) {
            throw new \Cake\Core\Exception\CakeException(__("サーバーからの応答がありません。"));
        }
        if ($status_code != 200) {
            throw new \Cake\Core\Exception\CakeException(__("レスポンスが不正です。status code:") . $status_code);
        }
        $response = $this->getResult($header_size, $curl_response);
        return $response;
    }

    /*
    * json情報整理
    *
    * 入力パラメータ:json情報
    * 出力パラメータ:ユーザー情報
    */
    public function getResult($header_size, $response) {
        $header = substr($response, 0, $header_size);
        $body = substr($response, $header_size);
        $result = json_decode($body, true);
        if($result == null) {
            // console.log("JsonError");
        }
        return $result;
    }
}

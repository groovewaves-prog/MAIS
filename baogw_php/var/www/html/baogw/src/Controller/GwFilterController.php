<?php
namespace App\Controller;
use App\View\Helper\InputSetHelper;

use App\Controller\AppController;
use Cake\Routing\Router;
use Cake\Core\Configure;
use Cake\Core\Exception\Exception;
use App\Controller\GwCreateExportData;
use SplFileObject;

class GwFilterController extends AppController{

    const SESSION_KEY_INDEX_URL = "gw_filter_index_url";
    const BEFORE_SEVEN_DAYS     = '-7 days';

    public function initialize(): void
    {
        parent::initialize();
        $this->loadComponent('Request');
    }

// ======================================================================================================================================================
    public function index() {
        // クエリストリングを含む現在のURL取得し、セッション設定
        $indexUrl=Router::reverse($this->getRequest(), true);
        $this->getRequest()->getSession()->write($this::SESSION_KEY_INDEX_URL, $indexUrl);

        // チェックボックス設定
        $ALARM_STATUS_NAME  = Configure::read("ALARM_STATUS_NAME_FOR_CSV");
        $this->set(compact('ALARM_STATUS_NAME'));
        // $SEND_STATUS  = Configure::read("SEND_STATUS");
        // $this->set(compact('SEND_STATUS'));
        // $COLUMNS_EVENTS    = Configure::read("COLUMNS_EVENTS");
        // $this->set(compact('COLUMNS_EVENTS'));

        // GETパラメータをControllerとView用の変数セットする
        $filter_val = $this->_get_filter_vals(array());
        $this->set(compact('filter_val'));

        //選択用ウインドウオープン用URL
        $currentUrl=InputSetHelper::str_replace("/index", "", Router::url('/gw-filter', true));
        $this->set(compact('currentUrl'));
    }

// ------------------------------------------------------------------------------------------------------------------------------------------------------
    public function exportCsv() {
        $this->autoRender = false;

        $exportData = new GwCreateExportData();
        $filter_val = $this->_get_filter_vals(array());
        try {
            $data = $exportData->createExportData($filter_val);
        } catch (\Cake\Core\Exception\CakeException $e) {
            $this->Flash->error($e->getMessage());
            return $this->redirect($this->referer());
        }
        if (count($data) == 0) {
            $this->Flash->error(__('出力対象が0件のためCSV出力に失敗しました。'));
            return $this->redirect($this->referer());
        }

        $filename = 'exportdata.csv';
        $fp = fopen('php://temp', 'r+b');

        fputcsv($fp, array_keys($data[0]), ',', '"', '\\');
        foreach($data as $val) {
            $str = InputSetHelper::str_replace("\r\n", " ", $val);
            $str = InputSetHelper::str_replace("\r", " ", $str);
            $str = InputSetHelper::str_replace("\n", " ", $str);
            fputcsv($fp, $str, ',', '"', '\\');
        }

        rewind($fp);
        $str = InputSetHelper::str_replace(PHP_EOL, "\r\n", stream_get_contents($fp));
        $str = mb_convert_encoding($str, 'SJIS-win', 'UTF-8');
        fclose($fp);

        $fp2 = fopen(TMP.DS.$filename, "w");
        fwrite($fp2, $str);
        fclose($fp2);

        $this->response = $this->response->withType('csv');
        $this->response = $this->response->withFile(TMP.DS.$filename, ['download' => true, 'name' => $filename]);
    }

    /**
     * [GETパラメータをControllerとView用の変数セットする]
     * @param  array $fileter_vals 変数
     * @return array $fileter_vals 変数
     */
    function _get_filter_vals($fileter_vals) {

        // $fileter_vals['gw_event_id']            = $this->Request->setRequest('gw_event_id');
        // $fileter_vals['gw_event_id_operetor']   = $this->Request->setRequest('gw_event_id_operetor');
        $alarm_time_from_init=date('Y/m/d H:i', strtotime($this::BEFORE_SEVEN_DAYS));
        $fileter_vals['alarm_time_from']        = $this->Request->setRequest('alarm_time_from',$alarm_time_from_init);
        $fileter_vals['alarm_time_to']          = $this->Request->setRequest('alarm_time_to');
        $fileter_vals['alarm_status']           = $this->Request->setRequest('alarm_status',['0'=>'0']);
        // $fileter_vals['approve_status']         = $this->Request->setRequest('approve_status', 3);
        $fileter_vals['customer_name']          = $this->Request->setRequest('customer_name');
        $fileter_vals['customer_name_operetor'] = $this->Request->setRequest('customer_name_operetor');
        // $fileter_vals['hostname']               = $this->Request->setRequest('hostname');
        // $fileter_vals['hostname_operetor']      = $this->Request->setRequest('hostname_operetor');
        // $fileter_vals['ci_name']                = $this->Request->setRequest('ci_name');
        // $fileter_vals['ci_name_operetor']       = $this->Request->setRequest('ci_name_operetor');
        // $fileter_vals['device']                 = $this->Request->setRequest('device');
        // $fileter_vals['device_operetor']        = $this->Request->setRequest('device_operetor');
        // $fileter_vals['summary']                = $this->Request->setRequest('summary');
        // $fileter_vals['summary_operetor']       = $this->Request->setRequest('summary_operetor');
        // $fileter_vals['op_comment']             = $this->Request->setRequest('op_comment');
        // $fileter_vals['op_comment_operetor']    = $this->Request->setRequest('op_comment_operetor');
        // $fileter_vals['kisys_status']           = $this->Request->setRequest('kisys_status',['0'=>'0']);
        // $fileter_vals['kisys_status_operetor']  = $this->Request->setRequest('kisys_status_operetor');
        // $fileter_vals['incidentid']             = $this->Request->setRequest('incidentid');
        // $fileter_vals['incidentid_operetor']    = $this->Request->setRequest('incidentid_operetor');
        // $fileter_vals['disp_col']               = $this->Request->setRequest('disp_col',['0'=>'0']);
        return $fileter_vals;
    }

    // ======================================================================================================================================================
    /**
     * [selectアクション]
     * @param  string $table_name  テーブル名
     * @param  string $fieald_name カラム名
     * @param  string $input_name  要素id
     */
    public function select($table_name, $fieald_name, $input_name=null) {

        $this->viewBuilder()->disableAutoLayout();
        $this->loadModel($table_name);

        $gwTables_find = $this->$table_name->find()->select($fieald_name)
            ->distinct([$fieald_name])->where([ $fieald_name . ' is not ' => null ])->where([ $fieald_name . ' is not ' => '' ]);
        // 運用者ごとの顧客表示制御対応
        $usrgrp_names = $this->getRequest()->getSession()->read('usrgrp_names');
        $customer_names = $this->getRequest()->getSession()->read('customer_names');
        $account_type = $this->getRequest()->getSession()->read('account_type');
        // ハウコム運用者はハウコム顧客のみを検索
        if (in_array(Configure::read("HOWCOM_USER_GROUP"), $usrgrp_names)) {
            if ($customer_names) {
                $gwTables_find = $this->_set_query_condition($gwTables_find, 'customer_name' , '15', $customer_names);
            } else {
                $gwTables_find = $this->_set_query_condition($gwTables_find, 'customer_name' , '15', '存在しない顧客名');
            }
        // Zabbix特権管理者かつ全顧客検索ユーザー以外は他の運用者の顧客以外を検索
        } elseif ($account_type != 3 && !array_intersect($usrgrp_names, Configure::read("ALL_SEARCH_USER_GROUPS"))) {
            $not_perfect=[];
            foreach (InputSetHelper::explode(',', $customer_names) as $customer_name) {
                if (trim($customer_name)) {
                    array_push($not_perfect, ['customer_name !=' => trim($customer_name)]);
                }
            }
            if ($not_perfect) {
                $gwTables_find->where(['and'=>$not_perfect]);
            }
        }
        $gwTables = $this->paginate($gwTables_find, ['limit' => 10000, 'maxLimit' => 10000]);

        $this->set('gwTables', $gwTables);
        $this->set('fieald_name', $fieald_name);
        if($input_name){
            $this->set('input_elm_id', $input_name);
        }else{
            $this->set('input_elm_id', $fieald_name);
        }

        $this->render('/layout/select/');
    }
// ------------------------------------------------------------------------------------------------------------------------------------------------------
}

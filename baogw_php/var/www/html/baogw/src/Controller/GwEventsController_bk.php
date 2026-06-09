<?php
namespace App\Controller;

use App\Controller\AppController;
use Cake\Routing\Router;
use Cake\Validation\Validator;
use Cake\Core\Configure;
use Cake\Core\Configure\Engine\PhpConfig;
use Cake\Event\Event;
use Cake\Datasource\ConnectionManager;
use App\View\Helper\InputSetHelper;

class GwEventsController extends AppController{

    const SESSION_KEY_IDS                 = "gw_events_bulk_update_ids";
    const SESSION_KEY_INDEX_URL           = "gw_events_index_url";
    const SESSION_KEY_ACCOUNT_ALIAS       = "account_alias";
    const BEFORE_SEVEN_DAYS               = '-7 days';
    const DELAY_TIME_LIMIT                = '-10 min';

    public function initialize(): void
    {
        parent::initialize();
        $this->loadComponent('Request');
        $this->loadComponent('CMDB');
    }
// ======================================================================================================================================================
/**
 * [初期処理]
 * @param  Event  $event
 */
function beforeFilter(\Cake\Event\EventInterface $event) {

        parent::beforeFilter($event);

        // Slaveサーバのアクション制御
        $action=$event->getSubject()->getRequest()->getParam('action');
        // index select stopPatolite 以外のアクション
        if ($action!='index' && $action!='select' && $action!='stopPatolite' && $action!='stopPatoliteHowcom' && $action!='stopPatoliteVip') {
            $CURRENT_PRIMARY_FILE = Configure::read("CURRENT_PRIMARY_FILE");
            $CURRENT_TEST_FILE = Configure::read("CURRENT_TEST_FILE");
            // Slaveサーバ
            if (!file_exists($CURRENT_PRIMARY_FILE) && !file_exists($CURRENT_TEST_FILE)) {
                $this->Flash->error(__('Primaryサーバでしか編集できません。'));
                return $this->redirect($this->referer());
            }
            // Reader
            $usrgrp_names = $this->getRequest()->getSession()->read('usrgrp_names');
            if (in_array('Reader', $usrgrp_names)) {
                $this->Flash->error(__('編集する権限がありません。'));
                return $this->redirect($this->referer());
            }
        }

        // 表示制御顧客リスト設定
        //zabbixバージョンアップによりGroupsがHstgrpに変更
        $this->loadModel('Hstgrp');
        $hosts_info = [];
        $check_names = [];
        // ハウコム顧客リスト取得
        $this->set('howcom_names', $check_names);
        //zabbixバージョンアップによりGroupsがHstgrpに変更
        $hosts_info = $this->Hstgrp->find()->contain(['HostInventory'])->where(['Hstgrp.name'=>Configure::read("HOWCOM_HOST_GROUP")])->toArray(); //const
        if ($hosts_info) {
            foreach ($hosts_info[0]['host_inventory'] as $host_inventory) {
                $check_names = array_merge($check_names, [$host_inventory['name']]);
                // ハウコム顧客リスト設定
                $this->set('howcom_names', $check_names);
            }
        }
        $this->set('howcom_user_group', Configure::read("HOWCOM_USER_GROUP"));

        // VIP顧客リスト取得
        $vip_names = [];
        $this->set('vip_names', $vip_names);
        //zabbixバージョンアップによりGroupsがHstgrpに変更
        $hosts_info = $this->Hstgrp->find()->contain(['HostInventory'])->where(['Hstgrp.name'=>Configure::read("VIP_HOST_GROUP")])->toArray(); //const
        if ($hosts_info) {
            foreach ($hosts_info[0]['host_inventory'] as $host_inventory) {
                $vip_names = array_merge($vip_names, [$host_inventory['name']]);
                // VIP顧客リスト設定
                $this->set('vip_names', $vip_names);
            }
        }

        // 顧客リストを検索条件用に変更し、セッション設定
        $this->getRequest()->getSession()->write('customer_names', implode(',', $check_names));
        // Zabbix権限を取得・設定
        $account_type = $this->getRequest()->getSession()->read('account_type');
        $this->set('account_type', $account_type);
        // 全顧客検索ユーザー設定
        $this->set('all_search_user_groups', Configure::read("ALL_SEARCH_USER_GROUPS"));

        //CMDB WEB URL
        $CMDB_WEB_URL = Configure::read("CMDB_WEB_URL");
        $this->set(compact('CMDB_WEB_URL'));

        $this->Security->setConfig('unlockedActions', ['stopPatolite', 'stopPatoliteHowcom', 'stopPatoliteVip', 'getCmdbInfo']);

    }

// ======================================================================================================================================================
    /**
     * [indexアクション]
     */
    public function index() {

        // クエリストリングを含む現在のURL取得し、セッション設定
        $indexUrl=Router::reverse($this->getRequest(), true);
        $this->getRequest()->getSession()->write($this::SESSION_KEY_INDEX_URL, $indexUrl );

        // resetアクションの場合、検索パラメータをリセットして、indexにリダイレクトする
        $submit_action = $this->Request->setRequest('submit_action');
        if ($submit_action == 'reset') {
            $this->_filter_reset();
            $this->Flash->success(__('検索結果をリセットしました。'));
        } elseif (!$this->Request->setRequest('sort')) {
            $this->_filter_reset();
        }

        // チェックボックス設定
        $ALARM_STATUS_NAME  = Configure::read("ALARM_STATUS_NAME");
        $this->set(compact('ALARM_STATUS_NAME'));
        $SEND_STATUS  = Configure::read("SEND_STATUS");
        $this->set(compact('SEND_STATUS'));
        $COLUMNS_EVENTS    = Configure::read("COLUMNS_EVENTS");
        $this->set(compact('COLUMNS_EVENTS'));

        //クエリビルド
        $this->loadModel('GwIncidents');
        $query_gwIncidents = $this->GwIncidents->find('all', [
            'contain' => ['ErrorEvents', 'NormalEvents', 'GwEvents'],
            ])
            ->select([
                'gw_incident_id',
                'incident_status',
                'update_time',
                'error_event_id',
                'normal_event_id',
                'detected_host',
                'customer_name',
                'hostname',
                'ci_name',
                'update_user',
                'op_comment',
                'project_code',
                'kisys_incidentid',
                'GwEvents.gw_event_id', // 関連テーブルのカラム読み込み アラーム一覧ソート用
                'GwEvents.event_status',
                'GwEvents.alarm_status',
                'GwEvents.device',
                'GwEvents.kisys_status',
                'ErrorEvents.alarm_time',
                'ErrorEvents.summary',
                'ErrorEvents.checked_time',
                'NormalEvents.alarm_time',
                'NormalEvents.summary',
                'NormalEvents.checked_time',
                'ErrorEvents.gw_event_id', // 関連テーブルのカラム読み込み アラーム一覧、イベント詳細画面表示用
                'ErrorEvents.alarm_status',
                'ErrorEvents.customer_ci',
                'ErrorEvents.device',
                'ErrorEvents.kisys_status',
                'ErrorEvents.event_status',
                'ErrorEvents.op_comment',
                'NormalEvents.gw_event_id',
                'NormalEvents.alarm_status',
                'NormalEvents.customer_ci',
                'NormalEvents.device',
                'NormalEvents.kisys_status',
                'NormalEvents.event_status',
                'NormalEvents.op_comment',
            ]);

        // GETパラメータをControllerとView用の変数セットする
        $filter_val=[];
        $filter_val = $this->_get_filter_vals($filter_val);

        // 検索条件を設定する
        $query_gwIncidents = $this->_set_filter_condtions($query_gwIncidents, $filter_val);

        // ページネーション用インスタンス生成
        $this->_gen_pagenate_instance($query_gwIncidents, $filter_val['display_count'], $filter_val['sort'], $filter_val['direction']);

        //選択用ウインドウオープン用URL
        $currentUrl=InputSetHelper::str_replace("/index", "", Router::url('/gw-events', true));
        $this->set(compact('currentUrl'));

        //一括チェック復元用配列作成
        if ($filter_val['to_check'] ==1){
            $bulk_update_ids = $this->getRequest()->getSession()->read($this::SESSION_KEY_IDS);
            $this->set('bulk_update_ids' , $bulk_update_ids);
        }

        // //オートコンプリート(jquery.ui)用配列生成
        // $this->_set_arrays_auto_compleate();

        //パトライト停止用スクリプト
        $PATLITE_STOP_PAGE = Configure::read("PATLITE_STOP_PAGE");
        $this->set(compact('PATLITE_STOP_PAGE'));

        // KISYSメンテナンス中の表示
        //クエリビルド
        $this->loadModel('GwRules');
        $query_kisys_mainte = $this->GwRules->find('all')->select([
            'rule_id',
            'rule_status',
            'rule_set',
            'start_time',
            'end_time',
            'customer_name',
            'hostname',
            'ci_name',
            'action_no',
            'op_comment',
            'create_user',
            'update_user',
        ]);

        // 検索条件を設定する
        $mainte_time = date('Y-m-d H:i:s');
        $query_kisys_mainte->where([['GwRules.rule_status' => '1']]);
        $query_kisys_mainte->where([['GwRules.customer_name' => 'KISYS']]);
        $query_kisys_mainte->where([['GwRules.start_time <=' => $mainte_time]]);
        $query_kisys_mainte->where(['GwRules.end_time >=' => $mainte_time]);
        $query_kisys_mainte->where(['GwRules.hostname' => '*']);
        $query_kisys_mainte->where(['GwRules.ci_name' => '*']);
        $query_kisys_mainte->where(['GwRules.action_no' => '90']);
        $query_kisys_mainte->order(['GwRules.rule_id' => 'DESC']);
        $kisysMainte = $query_kisys_mainte->all();

        if ($kisysMainte->isEmpty()) {
            // ルール適用されていなかったら何もしない
        } else {
            // ルール適用されていたらフラグを渡す
            $kisysMainteFlag = 'kisysMainteFlag';
            $this->set(compact('kisysMainteFlag'));
        }

        //定数を表示
        $KDDI_MIYAZAKI = Configure::read("KDDI_MIYAZAKI");
        $this->set(compact('KDDI_MIYAZAKI'));

    }

// ------------------------------------------------------------------------------------------------------------------------------------------------------
    /**
     * [検索パラメータをリセットして、indexにリダイレクトする]
     */
    function _filter_reset(){
        //リセットしても引き継ぎたいデータだけsetして、再リダイレクトする
        $filter_form_opened     = $this->Request->setRequest('filter_form_opened');
        $display_count          = $this->Request->setRequest('display_count');
        $alarm_time_from_init=date('Y/m/d H:i', strtotime($this::BEFORE_SEVEN_DAYS));

        $params = [];
        if (!empty($filter_form_opened)) {
            $params['filter_form_opened'] = $filter_form_opened;
        }
        if (!empty($display_count)) {
            $params['display_count'] = $display_count;
        }
        $params['sort'] = 'GwIncidents.update_time';
        $params['direction'] = 'DESC';
        $params['submit_action'] = 'search';
        $params['alarm_time_error_from'] = $alarm_time_from_init;
        $params['alarm_time_normal_from'] = $alarm_time_from_init;

        $this->redirect([
                          'action'                   => 'index',
                          '?' => $params
                        ]);
    }



// ------------------------------------------------------------------------------------------------------------------------------------------------------
    /**
     * [GETパラメータをControllerとView用の変数セットする]
     * @param  array $fileter_vals 変数
     * @return array $fileter_vals 変数
     */
    function _get_filter_vals($fileter_vals) {

        $fileter_vals['filter_form_opened']     = $this->Request->setRequest('filter_form_opened', 1);
        $fileter_vals['display_count']          = $this->Request->setRequest('display_count',100);
        $fileter_vals['sort']                   = $this->Request->setRequest('sort', 'GwIncidents.update_time');
        $fileter_vals['direction']              = $this->Request->setRequest('direction', 'DESC');
        $fileter_vals['to_check']               = $this->Request->setRequest('to_check',0);
        $fileter_vals['refresh']                = $this->Request->setRequest('refresh', 1);
        $fileter_vals['gw_event_id']            = $this->Request->setRequest('gw_event_id');
        if (!empty($fileter_vals['gw_event_id'])) {
            $fileter_vals['gw_event_id']            = (string)((int)$fileter_vals['gw_event_id']);
        }
        $fileter_vals['gw_event_id_operetor']   = $this->Request->setRequest('gw_event_id_operetor');
        $alarm_time_from_init=date('Y/m/d H:i', strtotime($this::BEFORE_SEVEN_DAYS));
        
        // CakePHP4のPaginatorの動作が変わり$this->Paginator->numbers();で<a href=・・・を生成した際
        // 入力値が空にの項目のクエリ文字列が出力されないようになっている
        // そのため'alarm_time_error_from'と'alarm_time_normal_from'に$alarm_time_from_initが設定されてしまい
        // 結果$this->paginate呼び出しで検索結果＝０件となりエラーとなった
        // プログラム構造としてここで$alarm_time_from_init(システム日付の一週間前）を設定するのは不要であることと
        // ルール一覧ではここでは第二引数に$alarm_time_from_iniは指定しておらず、想定通りの正しい動作であるため
        // 仮にルール一覧と同じにする
        //$fileter_vals['alarm_time_error_from']  = $this->Request->setRequest('alarm_time_error_from',$alarm_time_from_init);
        $fileter_vals['alarm_time_error_from']  = $this->Request->setRequest('alarm_time_error_from');
        $fileter_vals['alarm_time_error_to']    = $this->Request->setRequest('alarm_time_error_to');
        //$fileter_vals['alarm_time_normal_from'] = $this->Request->setRequest('alarm_time_normal_from',$alarm_time_from_init);
        $fileter_vals['alarm_time_normal_from'] = $this->Request->setRequest('alarm_time_normal_from');
        $fileter_vals['alarm_time_normal_to']   = $this->Request->setRequest('alarm_time_normal_to');
        $fileter_vals['alarm_status']           = $this->Request->setRequest('alarm_status',['0'=>'0']);
        $fileter_vals['approve_status']         = $this->Request->setRequest('approve_status', 3);
        $fileter_vals['customer_name']          = $this->Request->setRequest('customer_name');
        $fileter_vals['customer_name_operetor'] = $this->Request->setRequest('customer_name_operetor');
        $fileter_vals['hostname']               = $this->Request->setRequest('hostname');
        $fileter_vals['hostname_operetor']      = $this->Request->setRequest('hostname_operetor');
        $fileter_vals['ci_name']                = $this->Request->setRequest('ci_name');
        $fileter_vals['ci_name_operetor']       = $this->Request->setRequest('ci_name_operetor');
        $fileter_vals['device']                 = $this->Request->setRequest('device');
        $fileter_vals['device_operetor']        = $this->Request->setRequest('device_operetor');
        $fileter_vals['summary_error']          = $this->Request->setRequest('summary_error');
        $fileter_vals['summary_error_operetor'] = $this->Request->setRequest('summary_error_operetor');
        $fileter_vals['summary_normal']         = $this->Request->setRequest('summary_normal');
        $fileter_vals['summary_normal_operetor']= $this->Request->setRequest('summary_normal_operetor');
        $fileter_vals['op_comment']             = $this->Request->setRequest('op_comment');
        $fileter_vals['op_comment_operetor']    = $this->Request->setRequest('op_comment_operetor');
        $fileter_vals['kisys_status']           = $this->Request->setRequest('kisys_status',['0'=>'0']);
        $fileter_vals['incidentid']             = $this->Request->setRequest('incidentid');
        $fileter_vals['incidentid_operetor']    = $this->Request->setRequest('incidentid_operetor');
        $fileter_vals['disp_col']               = $this->Request->setRequest('disp_col',['0'=>'0']);

        return $fileter_vals;
    }

// ------------------------------------------------------------------------------------------------------------------------------------------------------
    /**
     * [検索条件を設定する]
     * @param object $query_gwIncidents  クエリ
     * @param array $filter_val       変数
     * @return object $query_gwIncidents クエリ
     */
    function _set_filter_condtions($query_gwIncidents, $filter_val) {

        // 自ホスト受信アラーム判定用IPアドレス
        $CURRENT_SERVER_ID    = Configure::read("CURRENT_SERVER_IP_4TH");

        //重複イベントを除く
        $query_gwIncidents->matching('GwEvents', function ($q) {
            return $q->where(['GwEvents.event_status is not' => '99']);
        });

        //下記よりフォームの条件式に従い、条件式追加
        $query_gwIncidents = $this->_set_query_condition($query_gwIncidents, 'GwEvents.gw_event_id', $filter_val['gw_event_id_operetor'], $filter_val['gw_event_id']);

        $select_alarm_time_condition = [];
        $select_error_alarm_time_condition = [];

        // gw_events絞り込み用
        $eventsAlarmTimeFrom = null;
        $eventsAlarmTimeTo = null;

        $str_alarm_time_error_from = InputSetHelper::str_replace(["\n","\r"], "", $filter_val['alarm_time_error_from']);
        if($str_alarm_time_error_from){
            $alarm_time_error_from_obj = new \DateTime($str_alarm_time_error_from);
            array_push($select_error_alarm_time_condition, ['ErrorEvents.alarm_time >=' => $alarm_time_error_from_obj->format('Y/m/d H:i:s')]);
            $eventsAlarmTimeFrom = $alarm_time_error_from_obj->format('Y/m/d H:i:s');
        }
        $str_alarm_time_error_to = InputSetHelper::str_replace(["\n","\r"], "", $filter_val['alarm_time_error_to']);
        if($str_alarm_time_error_to){
            $alarm_time_error_to_obj = new \DateTime($str_alarm_time_error_to);
            array_push($select_error_alarm_time_condition, ['ErrorEvents.alarm_time <=' => $alarm_time_error_to_obj->format('Y/m/d H:i:s')]);
            $eventsAlarmTimeTo = $alarm_time_error_to_obj->format('Y/m/d H:i:s');
        }
        if ($select_error_alarm_time_condition != []) {
            array_push($select_alarm_time_condition, ['and' => $select_error_alarm_time_condition]);
        }

        $select_normal_alarm_time_condition = [];
        $str_alarm_time_normal_from = InputSetHelper::str_replace(["\n","\r"], "", $filter_val['alarm_time_normal_from']);
        if($str_alarm_time_normal_from){
            $alarm_time_normal_from_obj = new \DateTime($str_alarm_time_normal_from);
            array_push($select_normal_alarm_time_condition, ['NormalEvents.alarm_time >=' => $alarm_time_normal_from_obj->format('Y/m/d H:i:s')]);

            // 発生日時・復旧日時を比較し過去のものを採用する（発生日時が指定なしの場合は復旧日時を採用）
            $fromDate = $alarm_time_normal_from_obj->format('Y/m/d H:i:s');
            if (is_null($eventsAlarmTimeFrom) || $eventsAlarmTimeFrom > $fromDate) {
                $eventsAlarmTimeFrom = $fromDate;
            }
        }
        $str_alarm_time_normal_to = InputSetHelper::str_replace(["\n","\r"], "", $filter_val['alarm_time_normal_to']);
        if($str_alarm_time_normal_to){
            $alarm_time_normal_to_obj = new \DateTime($str_alarm_time_normal_to);
            array_push($select_normal_alarm_time_condition, ['NormalEvents.alarm_time <=' => $alarm_time_normal_to_obj->format('Y/m/d H:i:s')]);

            // 発生日時・復旧日時を比較し未来のものを採用する（発生日時が指定なしの場合は復旧日時を採用）
            $toDate = $alarm_time_normal_to_obj->format('Y/m/d H:i:s');
            if (is_null($eventsAlarmTimeTo) || $eventsAlarmTimeTo < $toDate) {
                $eventsAlarmTimeTo = $toDate;
            }
        }
        if ($select_normal_alarm_time_condition != []) {
            array_push($select_alarm_time_condition, ['and' => $select_normal_alarm_time_condition]);
        }

        if ($select_alarm_time_condition) {
            $query_gwIncidents->where(['or' => $select_alarm_time_condition]);
        }

        if ($eventsAlarmTimeFrom) {
            $query_gwIncidents->where(['GwEvents.alarm_time >=' => $eventsAlarmTimeFrom]);
        }

        if ($eventsAlarmTimeTo) {
            $query_gwIncidents->where(['GwEvents.alarm_time <=' => $eventsAlarmTimeTo]);
        }

        $checkbox_count_alarm_status = 0;
        $select_alarm_status = [];
        foreach ($filter_val['alarm_status'] as $alarm_status){
            if ($alarm_status != '0'){
                // アラーム種別：error（赤）
                if ($alarm_status == 'error_red') {
                    array_push($select_alarm_status, [
                        'and' => [
                            ['GwEvents.alarm_status' =>'error'], ['GwEvents.event_status !=' =>'2'],
                            ['GwEvents.kisys_status !=' =>'10'], ['GwEvents.kisys_status !=' =>'20'], ['GwEvents.kisys_status !=' =>'30'],
                            ['GwEvents.kisys_status !=' =>'31'], ['GwEvents.kisys_status !=' =>'32'], ['GwEvents.kisys_status !=' =>'33'],
                            ['GwEvents.kisys_status !=' =>'34'], ['GwEvents.kisys_status !=' =>'35'],
                            ['GwEvents.kisys_status !=' =>'40'], ['GwEvents.kisys_status !=' =>'40,0'], ['GwEvents.kisys_status !=' =>'40,1'], ['GwEvents.kisys_status !=' =>'40,80'], ['GwEvents.kisys_status !=' =>'41'], ['GwEvents.kisys_status !=' =>'42'], ['GwEvents.kisys_status !=' =>'43'],
                            ['GwEvents.kisys_status !=' =>'60'], ['GwEvents.kisys_status !=' =>'60,0'], ['GwEvents.kisys_status !=' =>'60,1'], ['GwEvents.kisys_status !=' =>'60,80'], ['GwEvents.kisys_status !=' =>'61'], ['GwEvents.kisys_status !=' =>'62'],
                            ['GwEvents.kisys_status !=' =>'70'], ['GwEvents.kisys_status !=' =>'70,0'], ['GwEvents.kisys_status !=' =>'70,1'], ['GwEvents.kisys_status !=' =>'70,80'], ['GwEvents.kisys_status !=' =>'71'], ['GwEvents.kisys_status !=' =>'72']
                        ]
                    ]);
                }
                // アラーム種別：error（橙）
                if ($alarm_status == 'error_orange') {
                    array_push($select_alarm_status, [
                        'and' => [
                            ['GwEvents.alarm_status' =>'error'], ['GwEvents.event_status' =>'2'],
                            ['GwEvents.kisys_status !=' =>'10'], ['GwEvents.kisys_status !=' =>'20'], ['GwEvents.kisys_status !=' =>'30'],
                            ['GwEvents.kisys_status !=' =>'31'], ['GwEvents.kisys_status !=' =>'32'], ['GwEvents.kisys_status !=' =>'33'],
                            ['GwEvents.kisys_status !=' =>'34'], ['GwEvents.kisys_status !=' =>'35'],
                            ['GwEvents.kisys_status !=' =>'40'], ['GwEvents.kisys_status !=' =>'40,0'], ['GwEvents.kisys_status !=' =>'40,1'], ['GwEvents.kisys_status !=' =>'40,80'], ['GwEvents.kisys_status !=' =>'41'], ['GwEvents.kisys_status !=' =>'42'], ['GwEvents.kisys_status !=' =>'43'],
                            ['GwEvents.kisys_status !=' =>'60'], ['GwEvents.kisys_status !=' =>'60,0'], ['GwEvents.kisys_status !=' =>'60,1'], ['GwEvents.kisys_status !=' =>'60,80'], ['GwEvents.kisys_status !=' =>'61'], ['GwEvents.kisys_status !=' =>'62'],
                            ['GwEvents.kisys_status !=' =>'70'], ['GwEvents.kisys_status !=' =>'70,0'], ['GwEvents.kisys_status !=' =>'70,1'], ['GwEvents.kisys_status !=' =>'70,80'], ['GwEvents.kisys_status !=' =>'71'], ['GwEvents.kisys_status !=' =>'72']
                        ]
                    ]);
                }
                // アラーム種別：error（黄）
                if ($alarm_status == 'error_yellow') {
                    array_push($select_alarm_status, [
                        'and' => [
                            ['GwEvents.alarm_status' =>'error'],
                            'or' => [
                                ['GwEvents.kisys_status' =>'10'], ['GwEvents.kisys_status' =>'20'], ['GwEvents.kisys_status' =>'30'],
                                ['GwEvents.kisys_status' =>'31'], ['GwEvents.kisys_status' =>'32'], ['GwEvents.kisys_status' =>'33'],
                                ['GwEvents.kisys_status' =>'34'], ['GwEvents.kisys_status' =>'35'],
                                ['GwEvents.kisys_status' =>'40'], ['GwEvents.kisys_status' =>'40,0'], ['GwEvents.kisys_status' =>'40,1'], ['GwEvents.kisys_status' =>'40,80'], ['GwEvents.kisys_status' =>'41'], ['GwEvents.kisys_status' =>'42'], ['GwEvents.kisys_status' =>'43'],
                                ['GwEvents.kisys_status' =>'60'], ['GwEvents.kisys_status' =>'60,0'], ['GwEvents.kisys_status' =>'60,1'], ['GwEvents.kisys_status' =>'60,80'], ['GwEvents.kisys_status' =>'61'], ['GwEvents.kisys_status' =>'62'],
                                ['GwEvents.kisys_status' =>'70'], ['GwEvents.kisys_status' =>'70,0'], ['GwEvents.kisys_status' =>'70,1'], ['GwEvents.kisys_status' =>'70,80'], ['GwEvents.kisys_status' =>'71'], ['GwEvents.kisys_status' =>'72']
                            ]
                        ]
                    ]);
                }
                // アラーム種別：error（赤）、error（橙）、error（黄）以外
                if ($alarm_status != 'error_red' && $alarm_status != 'error_orange' && $alarm_status != 'error_yellow') {
                    array_push($select_alarm_status, [['GwEvents.alarm_status' => $alarm_status]]);
                }
                $checkbox_count_alarm_status = $checkbox_count_alarm_status + 1;
            }
        }
        // 1つ以上チェックされているかつ、ボックスの数より少なければ検索条件に加える。
        $ALARM_STATUS_NAME     = Configure::read("ALARM_STATUS_NAME");
        if ($checkbox_count_alarm_status >=1 &&
        $checkbox_count_alarm_status < count($ALARM_STATUS_NAME)) {
            if ($select_alarm_status != []) {
                $query_gwIncidents->where(['or' => $select_alarm_status]);
            }
        }

        $checkbox_count_kisys_status = 0;
        $select_kisys_status = [];
        foreach ($filter_val['kisys_status'] as $kisys_status){
          // K-ISYS起票成功
          if ($kisys_status == '1'){
            $select_kisys_status = array_merge($select_kisys_status, [['GwEvents.kisys_status' =>'0']]);
            $select_kisys_status = array_merge($select_kisys_status, [['GwEvents.kisys_status' =>'0,0']]);
            $select_kisys_status = array_merge($select_kisys_status, [['GwEvents.kisys_status' =>'0,1']]);
            $select_kisys_status = array_merge($select_kisys_status, [['GwEvents.kisys_status' =>'0,80']]);
            $select_kisys_status = array_merge($select_kisys_status, [['GwEvents.kisys_status' =>'40']]);
            $select_kisys_status = array_merge($select_kisys_status, [['GwEvents.kisys_status' =>'50,0']]);
            $select_kisys_status = array_merge($select_kisys_status, [['GwEvents.kisys_status' =>'50,1']]);
            $select_kisys_status = array_merge($select_kisys_status, [['GwEvents.kisys_status' =>'50,80']]);
            $select_kisys_status = array_merge($select_kisys_status, [['GwEvents.kisys_status' =>'60,0']]);
            $select_kisys_status = array_merge($select_kisys_status, [['GwEvents.kisys_status' =>'60,1']]);
            $select_kisys_status = array_merge($select_kisys_status, [['GwEvents.kisys_status' =>'60,80']]);
            $select_kisys_status = array_merge($select_kisys_status, [['GwEvents.kisys_status' =>'70,0']]);
            $select_kisys_status = array_merge($select_kisys_status, [['GwEvents.kisys_status' =>'70,1']]);
            $select_kisys_status = array_merge($select_kisys_status, [['GwEvents.kisys_status' =>'70,80']]);
            $checkbox_count_kisys_status = $checkbox_count_kisys_status + 1;
          // K-ISYS発生連携失敗
          } elseif ($kisys_status == '2'){
            $select_kisys_status = array_merge($select_kisys_status, [['and' => [['GwEvents.alarm_status' =>'error'],['GwEvents.kisys_status' =>'1']]]]);
            $select_kisys_status = array_merge($select_kisys_status, [['and' => [['GwEvents.alarm_status' =>'error'],['GwEvents.kisys_status' =>'2']]]]);
            $select_kisys_status = array_merge($select_kisys_status, [['and' => [['GwEvents.alarm_status' =>'error'],['GwEvents.kisys_status' =>'41']]]]);
            $select_kisys_status = array_merge($select_kisys_status, [['and' => [['GwEvents.alarm_status' =>'error'],['GwEvents.kisys_status' =>'42']]]]);
            $select_kisys_status = array_merge($select_kisys_status, [['and' => [['GwEvents.alarm_status' =>'error'],['GwEvents.kisys_status' =>'51']]]]);
            $select_kisys_status = array_merge($select_kisys_status, [['and' => [['GwEvents.alarm_status' =>'error'],['GwEvents.kisys_status' =>'52']]]]);
            $select_kisys_status = array_merge($select_kisys_status, [['and' => [['GwEvents.alarm_status' =>'error'],['GwEvents.kisys_status' =>'61']]]]);
            $select_kisys_status = array_merge($select_kisys_status, [['and' => [['GwEvents.alarm_status' =>'error'],['GwEvents.kisys_status' =>'62']]]]);
            $select_kisys_status = array_merge($select_kisys_status, [['and' => [['GwEvents.alarm_status' =>'error'],['GwEvents.kisys_status' =>'71']]]]);
            $select_kisys_status = array_merge($select_kisys_status, [['and' => [['GwEvents.alarm_status' =>'error'],['GwEvents.kisys_status' =>'72']]]]);
            $checkbox_count_kisys_status = $checkbox_count_kisys_status + 1;
          // K-ISYS復旧連携失敗
        } elseif ($kisys_status == '3'){
            $select_kisys_status = array_merge($select_kisys_status, [['and' => [['GwEvents.alarm_status' =>'normal'],['GwEvents.kisys_status' =>'1']]]]);
            $select_kisys_status = array_merge($select_kisys_status, [['and' => [['GwEvents.alarm_status' =>'normal'],['GwEvents.kisys_status' =>'2']]]]);
            $select_kisys_status = array_merge($select_kisys_status, [['and' => [['GwEvents.alarm_status' =>'normal'],['GwEvents.kisys_status' =>'41']]]]);
            $select_kisys_status = array_merge($select_kisys_status, [['and' => [['GwEvents.alarm_status' =>'normal'],['GwEvents.kisys_status' =>'42']]]]);
            $select_kisys_status = array_merge($select_kisys_status, [['and' => [['GwEvents.alarm_status' =>'normal'],['GwEvents.kisys_status' =>'51']]]]);
            $select_kisys_status = array_merge($select_kisys_status, [['and' => [['GwEvents.alarm_status' =>'normal'],['GwEvents.kisys_status' =>'52']]]]);
            $select_kisys_status = array_merge($select_kisys_status, [['and' => [['GwEvents.alarm_status' =>'normal'],['GwEvents.kisys_status' =>'61']]]]);
            $select_kisys_status = array_merge($select_kisys_status, [['and' => [['GwEvents.alarm_status' =>'normal'],['GwEvents.kisys_status' =>'62']]]]);
            $select_kisys_status = array_merge($select_kisys_status, [['and' => [['GwEvents.alarm_status' =>'normal'],['GwEvents.kisys_status' =>'71']]]]);
            $select_kisys_status = array_merge($select_kisys_status, [['and' => [['GwEvents.alarm_status' =>'normal'],['GwEvents.kisys_status' =>'72']]]]);
            $checkbox_count_kisys_status = $checkbox_count_kisys_status + 1;
          // K-ISYS起票しません（パトランプ鳴動します）
          } elseif ($kisys_status == '10'){
            $select_kisys_status = array_merge($select_kisys_status, [['GwEvents.kisys_status' =>'10']]);
            $select_kisys_status = array_merge($select_kisys_status, [['GwEvents.kisys_status' =>'20']]);
            $checkbox_count_kisys_status = $checkbox_count_kisys_status + 1;
          // K-ISYS起票とパトランプ鳴動しません
          } elseif ($kisys_status == '20'){
            $select_kisys_status = array_merge($select_kisys_status, [['GwEvents.kisys_status' =>'20']]);
            $checkbox_count_kisys_status = $checkbox_count_kisys_status + 1;
          // キャンセル待ちします
          } elseif ($kisys_status == '30'){
            $select_kisys_status = array_merge($select_kisys_status, [['GwEvents.kisys_status' =>'30']]);
            $select_kisys_status = array_merge($select_kisys_status, [['GwEvents.kisys_status' =>'31']]);
            $select_kisys_status = array_merge($select_kisys_status, [['GwEvents.kisys_status' =>'32']]);
            $select_kisys_status = array_merge($select_kisys_status, [['GwEvents.kisys_status' =>'33']]);
            $select_kisys_status = array_merge($select_kisys_status, [['GwEvents.kisys_status' =>'34']]);
            $select_kisys_status = array_merge($select_kisys_status, [['GwEvents.kisys_status' =>'35']]);
            $checkbox_count_kisys_status = $checkbox_count_kisys_status + 1;
          // 時間内復旧（K-ISYS起票自動キャンセル）
          } elseif ($kisys_status == '40'){
            $select_kisys_status = array_merge($select_kisys_status, [['GwEvents.kisys_status' =>'40']]);
            $select_kisys_status = array_merge($select_kisys_status, [['GwEvents.kisys_status' =>'40,0']]);
            $select_kisys_status = array_merge($select_kisys_status, [['GwEvents.kisys_status' =>'40,1']]);
            $select_kisys_status = array_merge($select_kisys_status, [['GwEvents.kisys_status' =>'40,80']]);
            $select_kisys_status = array_merge($select_kisys_status, [['GwEvents.kisys_status' =>'41']]);
            $select_kisys_status = array_merge($select_kisys_status, [['GwEvents.kisys_status' =>'42']]);
            $select_kisys_status = array_merge($select_kisys_status, [['GwEvents.kisys_status' =>'43']]);
            $checkbox_count_kisys_status = $checkbox_count_kisys_status + 1;
          // 要対応（時間内未復旧）
          } elseif ($kisys_status == '50'){
            $select_kisys_status = array_merge($select_kisys_status, [['GwEvents.kisys_status' =>'50']]);
            $select_kisys_status = array_merge($select_kisys_status, [['GwEvents.kisys_status' =>'50,0']]);
            $select_kisys_status = array_merge($select_kisys_status, [['GwEvents.kisys_status' =>'50,1']]);
            $select_kisys_status = array_merge($select_kisys_status, [['GwEvents.kisys_status' =>'50,80']]);
            $select_kisys_status = array_merge($select_kisys_status, [['GwEvents.kisys_status' =>'51']]);
            $select_kisys_status = array_merge($select_kisys_status, [['GwEvents.kisys_status' =>'52']]);
            $select_kisys_status = array_merge($select_kisys_status, [['GwEvents.kisys_status' =>'53']]);
            $checkbox_count_kisys_status = $checkbox_count_kisys_status + 1;
          // Kompira連携成功
          } elseif ($kisys_status == '81'){
            $select_kisys_status = array_merge($select_kisys_status, [['GwEvents.kisys_status' =>'0,0']]);
            $select_kisys_status = array_merge($select_kisys_status, [['GwEvents.kisys_status' =>'50,0']]);
            $select_kisys_status = array_merge($select_kisys_status, [['GwEvents.kisys_status' =>'60,0']]);
            $select_kisys_status = array_merge($select_kisys_status, [['GwEvents.kisys_status' =>'70,0']]);
            $checkbox_count_kisys_status = $checkbox_count_kisys_status + 1;
          // Kompira連携失敗
          } elseif ($kisys_status == '82'){
            $select_kisys_status = array_merge($select_kisys_status, [['GwEvents.kisys_status' =>'0,1']]);
            $select_kisys_status = array_merge($select_kisys_status, [['GwEvents.kisys_status' =>'50,1']]);
            $select_kisys_status = array_merge($select_kisys_status, [['GwEvents.kisys_status' =>'60,1']]);
            $select_kisys_status = array_merge($select_kisys_status, [['GwEvents.kisys_status' =>'70,1']]);
            $checkbox_count_kisys_status = $checkbox_count_kisys_status + 1;
          }
        }

        $SEND_STATUS     = Configure::read("SEND_STATUS");
        if ($checkbox_count_kisys_status >=1 &&
        $checkbox_count_kisys_status < count($SEND_STATUS)) {
            if ($select_kisys_status != []) {
                $query_gwIncidents->where(['or' => $select_kisys_status]);
            }
        }

        if ($filter_val['approve_status']=="1"){//未承認
            $query_gwIncidents = $this->_set_query_condition($query_gwIncidents, 'GwEvents.checked_time', '98', ''); //未承認
        } elseif ($filter_val['approve_status']=="2"){//承認済み
            $query_gwIncidents = $this->_set_query_condition($query_gwIncidents, 'GwEvents.checked_time', '99', ''); //承認済み
        }

        // 運用者ごとの顧客表示制御対応
        $usrgrp_names = $this->getRequest()->getSession()->read('usrgrp_names');
        $customer_names = $this->getRequest()->getSession()->read('customer_names');
        $account_type = $this->getRequest()->getSession()->read('account_type');
        // ハウコム運用者はハウコム顧客のみを検索
        if (in_array(Configure::read("HOWCOM_USER_GROUP"), $usrgrp_names)) {
            if ($customer_names) {
                $query_gwIncidents = $this->_set_query_condition($query_gwIncidents, 'GwIncidents.customer_name', '15', $customer_names);
            } else {
                $query_gwIncidents = $this->_set_query_condition($query_gwIncidents, 'GwIncidents.customer_name', '15', '存在しない顧客名');
            }
        // Zabbix特権管理者かつ全顧客検索ユーザー以外は他の運用者の顧客以外を検索
        } elseif ($account_type != 3 && !array_intersect($usrgrp_names, Configure::read("ALL_SEARCH_USER_GROUPS"))) {
            $not_perfect=[];
            foreach (InputSetHelper::explode(',', $customer_names) as $customer_name){
                if (trim($customer_name)){
                    array_push($not_perfect, ['GwIncidents.customer_name !=' => trim($customer_name)]);
                }
            }
            if ($not_perfect) {
                $query_gwIncidents->where(['and'=>$not_perfect]);
            }
        }

        $query_gwIncidents = $this->_set_query_condition($query_gwIncidents, 'GwIncidents.customer_name', $filter_val['customer_name_operetor'] , $filter_val['customer_name']);
        $query_gwIncidents = $this->_set_query_condition($query_gwIncidents, 'GwIncidents.hostname', $filter_val['hostname_operetor'] , $filter_val['hostname']);
        $query_gwIncidents = $this->_set_query_condition($query_gwIncidents, 'GwIncidents.ci_name', $filter_val['ci_name_operetor'] , $filter_val['ci_name']);
        $query_gwIncidents = $this->_set_query_condition($query_gwIncidents, 'GwEvents.device', $filter_val['device_operetor'] , $filter_val['device']);
        $query_gwIncidents = $this->_set_query_condition($query_gwIncidents, 'ErrorEvents.summary', $filter_val['summary_error_operetor'] , $filter_val['summary_error']);
        $query_gwIncidents = $this->_set_query_condition($query_gwIncidents, 'NormalEvents.summary', $filter_val['summary_normal_operetor'] , $filter_val['summary_normal']);
        $query_gwIncidents = $this->_set_query_condition($query_gwIncidents, 'GwIncidents.op_comment', $filter_val['op_comment_operetor'] , $filter_val['op_comment']);
        $query_gwIncidents = $this->_set_query_condition($query_gwIncidents, 'GwIncidents.kisys_incidentid', $filter_val['incidentid_operetor'] , $filter_val['incidentid']);

        return $query_gwIncidents->distinct('GwIncidents.gw_incident_id');
    }

// ------------------------------------------------------------------------------------------------------------------------------------------------------
    /**
     * [検索条件設定関数]
     * @param object $query_gwIncidents  クエリ
     * @param string $field              カラム名
     * @param string $operetor           検索パターン
     * @param string $operands           検索値
     * @return object $query_gwIncidents クエリ
     */
    function _set_query_condition($query_gwIncidents, $field, $operetor, $operands){

        //検索値が無いか、Null検索でない場合は、検索条件を追加しない
        if ($operands=='' && $operetor!='98' && $operetor!='99'){
            return $query_gwIncidents;
        }

        $operands   = InputSetHelper::str_replace(["\n","\r"], "", $operands);    //改行削除
        $a_operands = InputSetHelper::explode(',', $operands);                    //配列化

        //'13'=>'を含む', '14'=>'を含まない', '15'=>'完全一致', '23'=>'完全一致', '24'=>'以上', '25'=>'以下', '33'=>'以降', '34'=>'以前', '35'=>'完全一致'
        $operetor_candidate = ['13'=>' collate utf8_unicode_ci LIKE', '14'=>' collate utf8_unicode_ci NOT LIKE', '15'=>'',
                             '23'=>''  , '24'=>'>='    , '25'=>'<=',
                            //  '33'=>'>=', '34'=>'<='    , '35'=>'',
                             '98'=>'IS', '99'=>'IS NOT',
                           ];

        $query_operator = $operetor_candidate[$operetor];
        $this->set('query_operator', $query_operator);

        if($operetor=='13'){
            $like=[];
            foreach ($a_operands as $operand){
                if (InputSetHelper::mb_strlen(trim($operand)) > 0){
                    array_push($like, [$field . ' ' . $query_operator => '%' .trim($operand) . '%']);
                }
            }
            $query_gwIncidents->where(['or'=>$like]);

        } elseif($operetor=='14'){
            $not_like=[];
            foreach ($a_operands as $operand){
                if (InputSetHelper::mb_strlen(trim($operand)) > 0){
                    array_push($not_like, [$field . ' ' . $query_operator => '%' .trim($operand) . '%']);
                }
            }
            $query_gwIncidents->where(['and'=>$not_like]);

        } elseif ($operetor=='98'){
            $query_gwIncidents->where(['or'=>[
                                          [$field . ' ' . $query_operator => ""],
                                          [$field . ' ' . $query_operator => NULL]
                                      ]
                                ]);

        } elseif ($operetor=='99'){
            $query_gwIncidents->where(['and'=>[
                                          [$field . ' ' . $query_operator => ""],
                                          [$field . ' ' . $query_operator => NULL]
                                      ]
                                ]);

        } else {
            $perfect=[];
            foreach ($a_operands as $operand){
                if (InputSetHelper::mb_strlen(trim($operand)) > 0){
                    array_push($perfect, [$field . ' ' . $query_operator => trim($operand)]);
                }
            }
            $query_gwIncidents->where(['or'=>$perfect]);

        }

        return $query_gwIncidents;
    }

// ------------------------------------------------------------------------------------------------------------------------------------------------------
    /**
     * [ページネーション用インスタンス生成]
     * @param  object $query_gwIncidents クエリ
     * @param  int    $display_count  表示件数
     * @param  string $sort           ソートキー
     * @param  string $direction      昇順降順
     */
    function _gen_pagenate_instance($query_gwIncidents, $display_count, $sort=null, $direction=null){

        $this->paginate=[
            'contain' => ['ErrorEvents', 'NormalEvents', 'GwEvents'],
            'limit' => $display_count,
            'maxLimit' => 1000,
            'sortableFields' => [ // 関連テーブルのカラムは明示的にホワイトリストに登録することでPagenate->sort()できる
                'GwIncidents.update_time',
                'GwEvents.gw_event_id',
                'ErrorEvents.alarm_time',
                'NormalEvents.alarm_time',
                'GwEvents.alarm_status',
                'GwIncidents.customer_name',
                'GwIncidents.hostname',
                'GwIncidents.ci_name',
                'ErrorEvents.summary',
                'NormalEvents.summary',
                'GwEvents.device',
                'GwIncidents.op_comment',
            ],
            // 'order' => [$sort => $direction]
        ];
        $gwIncidents = $this->paginate($query_gwIncidents);
        $this->set(compact('gwIncidents'));
    }

// ------------------------------------------------------------------------------------------------------------------------------------------------------
    /**
     * [ページネーション用インスタンス生成（ソート条件付き）]
     * @param  object $query_gwIncidents クエリ
     * @param  int    $display_count  表示件数
     * @param  string $sort           ソートキー
     * @param  string $direction      昇順降順
     */
    function _gen_pagenate_instance_with_sort($query_gwIncidents, $display_count, $sort=null, $direction=null){

        $this->paginate=[
            'contain' => ['ErrorEvents', 'NormalEvents', 'GwEvents'],
            'limit' => $display_count,
            'maxLimit' => 1000,
            'sortableFields' => [
                'GwIncidents.update_time',
                'GwEvents.gw_event_id',
                'ErrorEvents.alarm_time',
                'NormalEvents.alarm_time',
                'GwEvents.alarm_status',
                'GwIncidents.customer_name',
                'GwIncidents.hostname',
                'GwIncidents.ci_name',
                'ErrorEvents.summary',
                'NormalEvents.summary',
                'GwEvents.device',
                'GwIncidents.op_comment',
            ],
            'order' => [$sort => $direction]
        ];
        $gwIncidents = $this->paginate($query_gwIncidents);
        $this->set(compact('gwIncidents'));
    }

// ------------------------------------------------------------------------------------------------------------------------------------------------------
  /**
   * [オートコンプリート(jquery.ui)用配列生成]
   */
  function _set_arrays_auto_compleate(){

      $list_customer_name = $this->GwEvents->disp('customer_name')->find('list')
                              ->distinct(['GwIncidents.customer_name'])->where(['customer_name is not ' => null ])->toArray();
      $list_hostname      = $this->GwEvents->disp('hostname')->find('list')
                              ->distinct(['GwIncidents.hostname'])->where(['hostname is not ' => null ])->toArray();
      $list_device        = $this->GwEvents->disp('device')->find('list')
                              ->distinct(['GwEvents.device'])->where(['device is not ' => null ])->toArray();
      $list_ci_name       = $this->GwEvents->disp('ci_name')->find('list')
                              ->distinct(['GwIncidents.ci_name'])->where(['GwIncidents.ci_name is not ' => null ])->toArray();

      //json_encodeの為の、keyの降り直し
      $list_customer_name = array_values($list_customer_name);
      $list_hostname      = array_values($list_hostname);
      $list_device        = array_values($list_device);
      $list_ci_name       = array_values($list_ci_name);

      $list_customer_name = json_encode($list_customer_name, JSON_HEX_TAG | JSON_HEX_AMP | JSON_HEX_APOS | JSON_HEX_QUOT);
      $list_hostname      = json_encode($list_hostname     , JSON_HEX_TAG | JSON_HEX_AMP | JSON_HEX_APOS | JSON_HEX_QUOT);
      $list_device        = json_encode($list_device       , JSON_HEX_TAG | JSON_HEX_AMP | JSON_HEX_APOS | JSON_HEX_QUOT);
      $list_ci_name       = json_encode($list_ci_name      , JSON_HEX_TAG | JSON_HEX_AMP | JSON_HEX_APOS | JSON_HEX_QUOT);

      $this->set('list_customer_name', $list_customer_name);
      $this->set('list_hostname'     , $list_hostname);
      $this->set('list_device'       , $list_device);
      $this->set('list_ci_name'      , $list_ci_name);

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

// ======================================================================================================================================================
    /**
     * [editアクション]
     * @param  string $id イベントID
     */
    public function edit($id = null) {
        $this->loadModel('GwIncidents');
        $gwIncident = $this->GwIncidents->get($id, ['contain' => ['ErrorEvents', 'NormalEvents', 'GwEvents']]);
        $error_event = $gwIncident->error_event;
        $normal_event = $gwIncident->normal_event;
        if (is_null($error_event) && is_null($normal_event)) {
            // gwEventsにしかアラーム情報がない
            foreach ($gwIncident->gw_events as $gw_event) {
                if ($gw_event->alarm_status == 'error') {
                    $error_event = $gw_event;
                } else if ($gw_event->alarm_status == 'normal') {
                    $normal_event = $gw_event;
                } else if ($gw_event->alarm_status == 'sysnormal') {
                    $normal_event = $gw_event;
                } else { // syserror, info, sec
                    $error_event = $gw_event;
                }
            }
        }

        //putリクエストとの場合は、更新処理を走らせる
        if ($this->getRequest()->is(['patch', 'post', 'put'])) {
            $error_event_new = $this->_make_save_event($error_event);
            $normal_event_new = $this->_make_save_event($normal_event);
            $incident_new = $this->_make_save_incident($gwIncident, $error_event_new, $normal_event_new);
            if (is_null($incident_new) and is_null($error_event_new) and is_null($normal_event_new)) {
                $this->Flash->error(__('情報に更新がありません。'));
            } else {
                $isFailed = false;
                if (!$this->_save_record('GwIncidents', $incident_new) or
                    !$this->_save_record('GwEvents', $error_event_new) or
                    !$this->_save_record('GwEvents', $normal_event_new)){
                        $isFailed = true;
                }
                if (!$isFailed) {
                    $this->Flash->success(__('The gw event has been saved.'));
                } else {
                    $this->Flash->error(__('The gw event could not be saved. Please, try again.'));
                }
            }

            $this->_set_refer_url();
            return $this->redirect($this->getRequest()->getSession()->read($this::SESSION_KEY_INDEX_URL));
        }
        //レコード表示
        $this->set(compact('gwIncident'));
        $this->set(compact('normal_event'));
        $this->set(compact('error_event'));
        //アラーム一覧画面の検索後の戻りURLのセット
        $this->_set_refer_url();

        //定数を表示
        $KDDI_MIYAZAKI = Configure::read("KDDI_MIYAZAKI");
        $this->set(compact('KDDI_MIYAZAKI'));

    }

    // ======================================================================================================================================================
    /**
     * [sendKisysアクション]
     * @param  string $id イベントID
     */
    public function sendKisys($id) {
        $this->autoRender = false;

        $gwEvent = $this->GwEvents->get($id, ['contain' => ['GwIncidents'] ]);
        if($gwEvent->alarm_status == 'normal' && InputSetHelper::mb_strlen($gwEvent->gw_incident->kisys_incidentid) == 0) {
            $this->Flash->error(__('INC番号が未起票です。'));
            return $this->redirect($this->referer());
        }
        $new_kisys_status = $this->_choose_kisys_status($gwEvent);
        if (is_null($new_kisys_status)) {
            if ($gwEvent->alarm_status == 'error') {
                $this->Flash->error(__('現在発生起票できません。'));
                return $this->redirect($this->referer());
            } else {
                $this->Flash->error(__('現在復旧追記できません。'));
                return $this->redirect($this->referer());
            }
        }
        try {
            $gwEvent->kisys_status = $new_kisys_status;
            $this->GwEvents->saveOrFail($gwEvent);
        } catch (\Cake\ORM\Exception\PersistenceFailedException $e) {
            if ($gwEvent->alarm_status == 'error') {
                $this->Flash->error(__('発生起票に失敗しました。'));
                return $this->redirect($this->referer());
            } else {
                $this->Flash->error(__('復旧追記に失敗しました。'));
                return $this->redirect($this->referer());
            }
        }
        return $this->redirect($this->referer());
    }

    function _choose_kisys_status($gwEvent){
        $kisys_status_old = $gwEvent->kisys_status;
        $fail_pattern = ['0', '40', '50', '60', '70', '90', '30', '31', '32', '33', '34', '35']; //手動起票対象外
        $kisys_status_norule = ['1', '2', '100']; //9
        $kisys_status_rule40 = ['41', '42', '43']; //49
        $kisys_status_rule50 = ['51', '52', '53']; //59
        $kisys_status_rule10 = ['10', '61', '62']; //69
        $kisys_status_rule20 = ['20', '71', '72']; //79

        if (($gwEvent->alarm_status == 'normal') && (is_null($kisys_status_old))) {
            // ノーマル報かつkisys_statusがnullの場合、エラー報のkisys_statusを参照する
            $error_event_id = $gwEvent->gw_incident->error_event_id;
            $errorGwEvent = $this->GwEvents->get($error_event_id);
            $error_event_kisys_status = $errorGwEvent->kisys_status;
            // エラー報のkisys_statusで$kisys_status_oldを上書きする
            $kisys_status_old = $error_event_kisys_status;
            // パターンに起票成功パターンを追加して上書きする
            $fail_pattern = ['90', '30', '31', '32', '33', '34', '35']; //手動起票対象外
            $kisys_status_norule = ['0', '1', '2', '100']; //9
            $kisys_status_rule40 = ['40', '41', '42', '43']; //49
            $kisys_status_rule50 = ['50', '51', '52', '53']; //59
            $kisys_status_rule10 = ['10', '60', '61', '62']; //69
            $kisys_status_rule20 = ['20', '70', '71', '72']; //79
        }
        if (in_array($kisys_status_old, $fail_pattern)) {
            return null;
        } elseif (in_array($kisys_status_old, $kisys_status_norule)) {
            return '9';
        } elseif (in_array($kisys_status_old, $kisys_status_rule40)) {
            return '49';
        } elseif (in_array($kisys_status_old, $kisys_status_rule50)) {
            return '59';
        } elseif (in_array($kisys_status_old, $kisys_status_rule10)) {
            return '69';
        } elseif (in_array($kisys_status_old, $kisys_status_rule20)) {
            return '79';
        }
        return null;
    }

// ------------------------------------------------------------------------------------------------------------------------------------------------------
    /**
     * [更新処理]
     * @param  GwEvent $gwEvent_old 変更前のエンティティ
     * @return GwEvent $gwEvent_new 変更後のエンティティ、変更がなければnull
     */
    function _make_save_event($gwEvent_old){
        if (is_null($gwEvent_old)) {
            return null;
        }

        $update_on        = false;
        $old_checked_time = $gwEvent_old->checked_time;

        //既存の承認状態と差異があるか
        $gwEvent_new      = $this->GwEvents->patchEntity($gwEvent_old, $this->getRequest()->getData());
        $new_checked_time = $gwEvent_new->CheckedTime;

        //承認する かつ 既存で承認時間が入っていなければ、承認書き込み
        if ($new_checked_time=='1' && !$old_checked_time) {
            $now = new \DateTime();
            $gwEvent_new->update_time = $now;
            $gwEvent_new->checked_time = $now;
            $account_full_name=$this->getRequest()->getSession()->read('account_full_name');
            $gwEvent_new->checked_user = $account_full_name;
            $update_on = true;

        //承認戻す かつ 既存で承認時間が入っていれば、承認消去
        } elseif ($new_checked_time=='2' && $old_checked_time) {
            $now = new \DateTime();
            $gwEvent_new->update_time = $now;
            $gwEvent_new->checked_time = null;
            $gwEvent_new->checked_user = null;
            $update_on = true;
        }

        if ($update_on==false){
            return null;
        }
        return $gwEvent_new;
    }

// ------------------------------------------------------------------------------------------------------------------------------------------------------
    /**
     * [更新処理]
     * @param  GwIncident $gwIncident_old 変更前のエンティティ
     * @param  GwEvent    $error_evevnt_new 変更後のエンティティ、変更がなければnull
     * @param  GwEvent    $normal_evevnt_new 変更後のエンティティ、変更がなければnull
     * @return GwIncident $gwIncident_new 変更後のエンティティ、変更がなければnull
     */
    function _make_save_incident($gwIncident_old, $error_event_new, $normal_event_new){
        if (is_null($gwIncident_old) and is_null($error_event_new) and is_null($normal_event_new)) {
            return null;
        }

        $update_on       = false;
        $old_op_comment  = $gwIncident_old->op_comment;

        //既存の補記情報と差異があるか
        $this->loadModel('GwIncidents');
        $gwIncident_new  = $this->GwIncidents->patchEntity($gwIncident_old, $this->getRequest()->getData());
        $new_op_comment  = InputSetHelper::str_replace("\r", "", $gwIncident_new->op_comment);

        if ($old_op_comment != $new_op_comment){
            $gwIncident_new->update_time = new \DateTime();
            $account_full_name=$this->getRequest()->getSession()->read('account_full_name');
            $gwIncident_new->update_user = $account_full_name;
            $update_on = true;
        }

        if (!$update_on){
            if (is_null($error_event_new) and is_null($normal_event_new)) {
                return null;
            } else { // 承認状態の変更があった場合、gwIncidents の update_time も更新する
                $gwIncident_new->update_time = new \DateTime();
                $update_on = true;
            }
        }
        return $gwIncident_new;
    }

// ------------------------------------------------------------------------------------------------------------------------------------------------------
    /**
     * [更新処理]
     * @param  string $table_name  テーブル名
     * @param  Entity $new_record  変更後のエンティティ
     * @return bool 保存成功ならtrue、失敗ならfalse
     *
     */
    function _save_record($table_name, $new_record){
        if (is_null($new_record)) {
            return true;
        }
        $this->loadModel($table_name);
        return $this->$table_name->save($new_record);
    }
// ------------------------------------------------------------------------------------------------------------------------------------------------------
    /**
     * [to_checkパラメータ設定]
     */
    function _set_refer_url(){

        $indexUrl  = $this->getRequest()->getSession()->read($this::SESSION_KEY_INDEX_URL);
        //sessionにURLが保存されているか
        // if (!is_null($indexUrl) ){
            //すでにto_checkパラメータがある場合は追加しない
            if (strpos($indexUrl,'to_check') ){
                $this->set("indexUrl", $indexUrl);
            }else{
                //クエリストリングがあるかないか
                if (strpos($indexUrl,'?') ){
                    $this->set("indexUrl", $indexUrl . "&to_check=1"); //ある
                }else{
                    $this->set("indexUrl", $indexUrl . "?to_check=1"); //ない
                }
            }
        // }else{
        //   $this->set("indexUrl", '/gw-events/');
        // }
    }
// ------------------------------------------------------------------------------------------------------------------------------------------------------
    /**
     * [クエリパラメータ変更]
     * @param  string $key   クエリパラメータのkey
     * @param  string $value クエリパラメータのvalue
     */
    function _change_refer_url($key, $value){
        $indexUrl  = $this->getRequest()->getSession()->read($this::SESSION_KEY_INDEX_URL);
        $indexUrl  = preg_replace("/" . $key . "=(\w|\d|\.)+/", $key . "=" . $value, $indexUrl);
        $this->getRequest()->getSession()->write($this::SESSION_KEY_INDEX_URL, $indexUrl );
    }
// ======================================================================================================================================================
    /**
     * [bulkUpdateアクション]
     */
    public function bulkUpdate(){
        $bulk_update_ids=[];
        //postリクエストの場合、一括更新IDセッション設定
        if (array_key_exists('BulkUpdate', $this->getRequest()->getData())){
          $bulk_update_ids=[];
          $this->_set_session_bulkupdate_ids($bulk_update_ids);
        }

        $bulk_update_ids = $this->getRequest()->getSession()->read($this::SESSION_KEY_IDS);
        $this->loadModel('GwIncidents');
        $query_gwIncidents = null;
        //クエリビルド
        if (count($bulk_update_ids)==0){
            $this->set('disabled', true);       //エレメント無効化
            $query_gwIncidents = $this->GwIncidents->find('all', [
                'contain' => ['ErrorEvents', 'NormalEvents', 'GwEvents'],
                'conditions' => ['GwIncidents.gw_incident_id IS ' => NULL],
                ]); //０件インスタンス
            $this->set('gwIncidents', '');

            $this->Flash->error(__('前の画面に戻り、一括更新するレコードを選択してください。'));

        } else {
            $this->set('disabled', false);      //エレメント有効化
            $query_gwIncidents = $this->GwIncidents->find('all', [
                'contain' => ['ErrorEvents', 'NormalEvents', 'GwEvents'],
                'conditions' => ['GwIncidents.gw_incident_id IN' => $bulk_update_ids],
                ])->enableAutoFields(true);
            // GwEvents に対して matching() してLEFT JOINさせないとなぜか contain の指定が効かない
            $query_gwIncidents->matching('GwEvents', function ($q) {
                return $q->where(['GwEvents.event_status is not' => '99']);
            })
            ->distinct('GwIncidents.gw_incident_id');
        }

        // ソート条件引継ぎ
        if ($this->getRequest()->is('post')) {
          $sort = $this->getRequest()->getData()['sort'];
          $direction = $this->getRequest()->getData()['direction'];
        } elseif ($this->getRequest()->is('get')) {
          if (count($this->getRequest()->getQueryParams()) == 0) {
            $sort = null;
            $direction = null;
          } else {
            $sort = $this->Request->setRequest('sort');
            $this->_change_refer_url('sort', $sort);
            $direction = $this->Request->setRequest('direction');
            $this->_change_refer_url('direction', $direction);
          }
        }
        $this->_gen_pagenate_instance_with_sort($query_gwIncidents, 1000, $sort, $direction);
        // to_checkパラメータ設定
        $this->_set_refer_url();

        //定数を表示
        $KDDI_MIYAZAKI = Configure::read("KDDI_MIYAZAKI");
        $this->set(compact('KDDI_MIYAZAKI'));

    }

// ------------------------------------------------------------------------------------------------------------------------------------------------------
    /**
     * [一括更新IDセッション設定]
     * @param array $bulk_update_ids 一括更新ID
     */
    function _set_session_bulkupdate_ids($bulk_update_ids){

        // チェックが入っているIDを配列に格納
        foreach ($this->getRequest()->getData()['BulkUpdate'] as $key => $val){
          if ($val==1){
            array_push($bulk_update_ids, $key);
          }
        }
        //セッションに格納
        $this->getRequest()->getSession()->write($this::SESSION_KEY_IDS, $bulk_update_ids);
    }

// ======================================================================================================================================================
    /**
     * [bulkUpdateSaveアクション]
     */
    public function bulkUpdateSave(){

        $this->viewBuilder()->disableAutoLayout();
        $this->autoRender = false;

        //更新情報の取得
        $update_value = $this->_get_update_request();

        if (count($update_value) == 0) {
            $this->Flash->error(__('一括更新する情報を1項目以上入力してください。'));
            return $this->redirect(['action' => 'bulkUpdate']);

        } else {
            $bulk_update_ids = $this->getRequest()->getSession()->read($this::SESSION_KEY_IDS);
            $event_ids_query = $this->GwEvents->find('list', [
                'conditions' => ['gw_incident_id IN' => $bulk_update_ids],
                'valueField' => 'gw_event_id'
                ]);
            $event_ids = array_values($event_ids_query->toArray());
            if ($event_ids && array_key_exists('event', $update_value)){
                $this->GwEvents->updateAll($update_value['event'], ['GwEvents.gw_event_id IN' => $event_ids]);
            }

            if ($bulk_update_ids && array_key_exists('incident', $update_value)){
                $this->loadModel('GwIncidents');
                $this->GwIncidents->updateAll($update_value['incident'], ['GwIncidents.gw_incident_id IN' => $bulk_update_ids]);
            }

            $this->Flash->success(__('一括更新しました。'));
            return $this->redirect($this->getRequest()->getSession()->read($this::SESSION_KEY_INDEX_URL));
        }

    }

// ------------------------------------------------------------------------------------------------------------------------------------------------------
    /**
     * [更新情報の取得]
     * @return array $update_value 更新情報
     */
    function _get_update_request(){
        $approve    = $this->getRequest()->getData()['BulkUpdate']['Approve'];
        $op_comment = $this->getRequest()->getData()['op_comment'];
        $op_comment = InputSetHelper::str_replace("\r", "", $op_comment);
        $update_value = [];
        $now = date('Y/m/d H:i:s');

        if ($approve!=""){
            $update_value['incident']['update_time'] = $now;
            if ($approve=='1') {
                $update_value['event']['update_time'] = $now;
                $update_value['event']['checked_time'] = $now;
                $alias=$this->getRequest()->getSession()->read($this::SESSION_KEY_ACCOUNT_ALIAS);
                $account_full_name=$this->getRequest()->getSession()->read('account_full_name');
                $update_value['event']['checked_user'] = $account_full_name;

            } elseif ($approve=='2') {
                $update_value['event']['update_time'] = $now;
                $update_value['event']['checked_time'] = null;
                $update_value['event']['checked_user'] = null;
            }
          $Confirm_Messages = __("承認:") . $approve;
        }

        if ($op_comment != ""){
            $update_value['incident']['op_comment'] = $op_comment;
            $update_value['incident']['update_time'] = $now;

            $alias=$this->getRequest()->getSession()->read($this::SESSION_KEY_ACCOUNT_ALIAS);
            $update_value['incident']['update_user'] = $alias;
            $Confirm_Messages = __("補記情報:") .$op_comment;
        }
        return $update_value;
    }

// ======================================================================================================================================================
    /**
     * [stopPatoliteアクション]
     * @return
     */
    function stopPatolite() {

        $result=1; //1以上はスクリプト実行失敗。
        $this->autoRender = FALSE;
        if($this->getRequest()->is('ajax')) {
            $PATLITE_STOP_SCRIPT = Configure::read("PATLITE_STOP_SCRIPT");
            exec($PATLITE_STOP_SCRIPT, $array, $result);
        }
        echo $result;
        return;

    }

// ======================================================================================================================================================
    /**
     * [stopPatoliteHowcomアクション]
     * @return
     */
    function stopPatoliteHowcom() {

        $result=1; //1以上はスクリプト実行失敗。
        $this->autoRender = FALSE;
        if($this->getRequest()->is('ajax')) {
            $PATLITE_STOP_SCRIPT = Configure::read("PATLITE_STOP_SCRIPT_HOWCOM");
            exec($PATLITE_STOP_SCRIPT, $array, $result);
        }
        echo $result;
        return;

    }

// ======================================================================================================================================================
    /**
     * [stopPatoliteVipアクション]
     * @return
     */
    function stopPatoliteVip() {

        $result=1; //1以上はスクリプト実行失敗。
        $this->autoRender = FALSE;
        if($this->getRequest()->is('ajax')) {
            $PATLITE_STOP_SCRIPT = Configure::read("PATLITE_STOP_SCRIPT");
            exec($PATLITE_STOP_SCRIPT, $array, $result);
        }
        echo $result;
        return;

    }

// ======================================================================================================================================================
    /*
     * [getCmdbInfoアクション]
     * 顧客略称及びホスト名よりCMDB情報を取得する
     * @return json CMDB情報
     */
    function getCmdbInfo() {
        $this->autoRender = FALSE;
        $this->response->withCharset('UTF-8');
        $this->response->withType('json');

        // postリクエストの場合
        if ($this->getRequest()->is('post')) {
            // CMDB情報
            $cmdb_data = [];
            $cmdb_data['project_id'] = '';
            $cmdb_data['machine_id'] = '';
            // パラメータ取得
            $customer_ci = $this->getRequest()->getData()['customer_ci'];
            $hostname = $this->getRequest()->getData()['hostname'];
            // ユーザ情報取得
            $CMDB_USERNAME = Configure::read('CMDB_USERNAME');
            $CMDB_PASSWORD = Configure::read('CMDB_PASSWORD');
            $auth = $this->CMDB->getAuth($CMDB_USERNAME, $CMDB_PASSWORD);
            // プロジェクト情報取得
            $project = $this->CMDB->getProject($customer_ci, $auth);
            if (!$project['data']) {
                $this->response->withStringBody(json_encode($cmdb_data));
                return;
            }
            $project_id = $project['data'][0]['_id'];
            $cmdb_data['project_id'] = $project_id;
            // 機器情報取得
            $machineInfomations = $this->CMDB->getMachineInfo($hostname, $project_id, $auth);
            $machineInfo = $machineInfomations['data'];
            if ($machineInfo && count($machineInfo) > 0) {
                $cmdb_data['machine_id'] = $machineInfo[0]['_id'];
                $this->response->withStringBody(json_encode($cmdb_data));
                return;
            }
            $this->response->withStringBody(json_encode($cmdb_data));
            return;
        }
        return;
    }

// ======================================================================================================================================================
    /**
     * [openCmdbInfoアクション]
     * 顧客略称よりプロジェクト情報を取得し、CMDB情報画面を表示する
     * @param  string $customer_ci 顧客略称
     */
    function openCmdbInfo($customer_ci) {
        $this->viewBuilder()->disableAutoLayout();

        // CMDB情報
        $monitoring = '';
        $monitoring_access = '';
        $sub_monitoring = '';
        $sub_monitoring_access = '';
        // ユーザ情報取得
        $CMDB_USERNAME = Configure::read('CMDB_USERNAME');
        $CMDB_PASSWORD = Configure::read('CMDB_PASSWORD');
        $auth = $this->CMDB->getAuth($CMDB_USERNAME, $CMDB_PASSWORD);
        // プロジェクト情報取得
        $project = $this->CMDB->getProject($customer_ci, $auth);
        if ($project['data']) {
            $monitoring = $project['data'][0]['Monitoring'];
            $monitoring_access = $project['data'][0]['MonitoringAccess'];
            $sub_monitoring = $project['data'][0]['SubMonitoring'];
            $sub_monitoring_access = $project['data'][0]['SubMonitoringAccess'];
        }
        // CMDB情報設定
        $this->set('monitoring', $monitoring);
        $this->set('monitoring_access', $monitoring_access);
        $this->set('sub_monitoring', $sub_monitoring);
        $this->set('sub_monitoring_access', $sub_monitoring_access);
        // CMDB情報画面表示
        $this->render('/layout/cmdb_info/');
    }

// ======================================================================================================================================================
    /**
     * [openDelayedEventsアクション]
     * delayed対象一覧画面を表示する
     */
    function openDelayedEvents() {
        $this->viewBuilder()->disableAutoLayout();

        //クエリビルド
        $this->loadModel('GwEvents');
        $query_delayedEvents = $this->GwEvents->find('all')->select([
            'gw_event_id',
            'event_status',
            'update_time',
            'gw_incident_id',
            'detected_time',
            'detected_host',
            'customer_ci',
            'customer_name',
            'hostname',
            'alarm_time',
            'ci_name',
            'device',
            'alarm_status',
            'summary',
            'checked_time',
            'checked_user',
            'op_comment',
        ]);

        // 検索条件を設定する check_delayed_events.py と同じ条件
        $delayed_time_limit=date('Y/m/d H:i:s', strtotime($this::DELAY_TIME_LIMIT));
        $query_delayedEvents->where([['GwEvents.update_time <' => $delayed_time_limit]]);
        $query_delayedEvents->where([['GwEvents.event_status' => '0']]);
        $query_delayedEvents->order(['GwEvents.update_time' => 'DESC']);
        $delayedEvents = $query_delayedEvents->all();
        $this->set(compact('delayedEvents'));
        // delayed対象一覧画面表示
        $this->render('/layout/delayed_events/');
    }

//Class End
}

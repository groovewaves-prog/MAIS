<?php
namespace App\Controller;

use App\Controller\AppController;
use Cake\Routing\Router;
use Cake\Validation\Validator;
use Cake\Core\Configure;
use Cake\Core\Configure\Engine\PhpConfig;
use Cake\Event\Event;
use Cake\Datasource\ConnectionManager;
use Cake\I18n\FrozenTime;
use App\View\Helper\InputSetHelper;

class GwRulesController extends AppController {

  const SESSION_KEY_IDS             = "gw_rules_bulk_update_ids";
  const SESSION_KEY_INDEX_URL       = "gw_rules_index_url";
  const SESSION_KEY_ACCOUNT_ALIAS   = "account_alias";
  // 重複ルールチェック用クエリ
  const GET_RULE_ID = "
  SELECT
      rule_id,
      rules_customer_name,
      rules_hostname,
      rules_ci_name,
      rules_action_no,
      exists_hostname,
      exists_ci_name
  FROM
    (
    SELECT
        rules.rule_id AS rule_id,
        rules.customer_name AS rules_customer_name,
        rules.hostname AS rules_hostname,
        rules.ci_name AS rules_ci_name,
        rules.action_no AS rules_action_no,
        (
        CASE
            WHEN rules.hostname is NULL THEN 0
            WHEN :hostname = '*' THEN 1
            WHEN rules.hostname = '*' THEN 1
            WHEN :hostname = rules.hostname THEN 1
            WHEN LOCATE('*', :hostname) >= 1 AND LOCATE('*', rules.hostname) >= 1 AND LOCATE(:hostname_t, TRIM('*' FROM rules.hostname)) >= 1 THEN 1
            WHEN LOCATE('*', :hostname) >= 1 AND LOCATE('*', rules.hostname) >= 1 AND LOCATE(TRIM('*' FROM rules.hostname), :hostname_t) >= 1 THEN 1
            WHEN :hostname REGEXP '^\\\*.*\\\*$' AND LOCATE(:hostname_t, TRIM('*' FROM rules.hostname)) >= 1 THEN 1
            WHEN :hostname REGEXP '.*\\\*$' AND LOCATE(:hostname_t, TRIM('*' FROM rules.hostname)) = 1 THEN 1
            WHEN :hostname REGEXP '^\\\*.*' AND :hostname_t = RIGHT(TRIM('*' FROM rules.hostname), CHAR_LENGTH(:hostname_t)) THEN 1
            WHEN rules.hostname REGEXP '^\\\*.*\\\*$' AND LOCATE(TRIM('*' FROM rules.hostname), :hostname_t) >= 1 THEN 1
            WHEN rules.hostname REGEXP '.*\\\*$' AND LOCATE(TRIM('*' FROM rules.hostname), :hostname_t) = 1 THEN 1
            WHEN rules.hostname REGEXP '^\\\*.*' AND TRIM('*' FROM rules.hostname) = RIGHT(:hostname_t, CHAR_LENGTH(TRIM('*' FROM rules.hostname))) THEN 1
            ELSE 0
        END
        ) AS exists_hostname,
        (
        CASE
            WHEN rules.ci_name is NULL THEN 0
            WHEN :ci_name = '*' THEN 1
            WHEN rules.ci_name = '*' THEN 1
            WHEN :ci_name = rules.ci_name THEN 1
            WHEN LOCATE('*', :ci_name) >= 1 AND LOCATE('*', rules.ci_name) >= 1 AND LOCATE(:ci_name_t, TRIM('*' FROM rules.ci_name)) >= 1 THEN 1
            WHEN LOCATE('*', :ci_name) >= 1 AND LOCATE('*', rules.ci_name) >= 1 AND LOCATE(TRIM('*' FROM rules.ci_name), :ci_name_t) >= 1 THEN 1
            WHEN :ci_name REGEXP '^\\\*.*\\\*$' AND LOCATE(:ci_name_t, TRIM('*' FROM rules.ci_name)) >= 1 THEN 1
            WHEN :ci_name REGEXP '.*\\\*$' AND LOCATE(:ci_name_t, TRIM('*' FROM rules.ci_name)) = 1 THEN 1
            WHEN :ci_name REGEXP '^\\\*.*' AND :ci_name_t = RIGHT(TRIM('*' FROM rules.ci_name), CHAR_LENGTH(:ci_name_t)) THEN 1
            WHEN rules.ci_name REGEXP '^\\\*.*\\\*$' AND LOCATE(TRIM('*' FROM rules.ci_name), :ci_name_t) >= 1 THEN 1
            WHEN rules.ci_name REGEXP '.*\\\*$' AND LOCATE(TRIM('*' FROM rules.ci_name), :ci_name_t) = 1 THEN 1
            WHEN rules.ci_name REGEXP '^\\\*.*' AND TRIM('*' FROM rules.ci_name) = RIGHT(:ci_name_t, CHAR_LENGTH(TRIM('*' FROM rules.ci_name))) THEN 1
            ELSE 0
        END
        ) AS exists_ci_name
    FROM gw_rules rules
    WHERE
        rules.rule_status = :rule_status
        AND rules.customer_name = :customer_name
        AND rules.start_time <= :end_time
        AND rules.end_time >= :start_time
        AND rules.action_no LIKE CONCAT(LEFT(:action_no, 1), '%')
    ) AS tmp
  WHERE
      exists_hostname = 1 AND exists_ci_name = 1
  ";

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
      // index select 以外のアクション
      if ($action!='index' && $action!='select') {
          $CURRENT_PRIMARY_FILE = Configure::read("CURRENT_PRIMARY_FILE");
          $CURRENT_TEST_FILE = Configure::read("CURRENT_TEST_FILE");
          // Slaveサーバ
          if (!file_exists($CURRENT_PRIMARY_FILE) && !file_exists($CURRENT_TEST_FILE)) {
              $this->Flash->error(__('Primaryサーバでしか編集できません。'));
              return $this->redirect(['action' => 'index']);
          }
          // Zabbixユーザー
          $account_type = $this->getRequest()->getSession()->read('account_type');
          if ($account_type == 1) {
              $this->Flash->error(__('登録または編集する権限がありません。'));
              return $this->redirect($this->referer());
          }
      }

      // 制御顧客リスト設定
      //zabbixバージョンアップによりGroupsがHstgrpに変更
      $this->loadModel('Hstgrp');
      $hosts_info =[];
      $check_names =[];
      // ハウコム顧客リスト取得
      $this->set('howcom_names', $check_names);
      //zabbixバージョンアップによりGroupsがHstgrpに変更
      $hosts_info = $this->Hstgrp->find()->contain(['HostInventory'])->where(['Hstgrp.name'=>Configure::read("HOWCOM_HOST_GROUP")])->toArray(); //const
      if ($hosts_info) {
          foreach ($hosts_info[0]['host_inventory'] as $host_inventory){
              $check_names = array_merge($check_names, [$host_inventory['name']]);
              // ハウコム顧客リスト設定
              $this->set('howcom_names', $check_names);
          }
      }
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
      $this->getRequest()->getSession()->write('check_names', $check_names);
      // 全顧客検索ユーザー設定
      $this->set('all_search_user_groups', Configure::read("ALL_SEARCH_USER_GROUPS"));
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
      if ($submit_action == 'reset' ) {
          $this->_filter_reset();
      }

      // チェックボックス設定
      $ACTION_NO_NAME    = Configure::read("ACTION_NO_NAME");
      $this->set(compact('ACTION_NO_NAME'));
      $RULE_SET_NAME     = Configure::read("RULE_SET_NAME");
      $this->set(compact('RULE_SET_NAME'));
      $COLUMNS_RULES     = Configure::read("COLUMNS_RULES");
      $this->set(compact('COLUMNS_RULES'));

      $RULE_SET_DESC     = Configure::read("RULE_SET_DESC");
      $this->set(compact('RULE_SET_DESC'));
      $ACTION_NO_DESC    = Configure::read("ACTION_NO_DESC");
      $this->set(compact('ACTION_NO_DESC'));

      //GETパラメータをControllerとView用の変数セットする
      $filter_val=[];
      $filter_val = $this->_get_filter_vals($filter_val);

      //クエリビルド
      $query_gwRules = $this->GwRules->find();
      $query_gwRules = $this->_set_filter_condtions($query_gwRules, $filter_val);

      $account_type = $this->getRequest()->getSession()->read('account_type');
      // Zabbix特権管理者はアクションNo:80,90を表示する
      if ($account_type == 3) {
          $ACTION_NO_NAME = $ACTION_NO_NAME + ['90'=>'90:K-ISYSメンテナンスです'];
          $ACTION_NO_DESC = $ACTION_NO_DESC + ['90'=>'90:K-ISYSメンテナンスです　（優先順位１）'];
          $this->set(compact('ACTION_NO_NAME'));
          $this->set(compact('ACTION_NO_DESC'));
      // Zabbix特権管理者以外はアクションNo:80,90を表示しない
      } else {
          $not_perfect=[];
          array_push($not_perfect, ['action_no != 80']);
          array_push($not_perfect, ['action_no != 90']);
          $query_gwRules->where(['and'=>$not_perfect]);
      }

      //ページネーション用インスタンス生成
      $this->_gen_pagenate_instance($query_gwRules, $filter_val['display_count']);

      //選択用ウインドウオープン用URL
      $currentUrl=InputSetHelper::str_replace("/index", "", Router::url('/gw-rules', true));
      $this->set(compact('currentUrl'));

      //定数を表示
      $KDDI_MIYAZAKI = Configure::read("KDDI_MIYAZAKI");
      $this->set(compact('KDDI_MIYAZAKI'));

      // //一括チェック復元用配列作成
      // if ($filter_val['to_check'] ==1){
      //     $bulk_update_ids = $this->request->session()->read($this::SESSION_KEY_IDS);
      //     $this->set('bulk_update_ids' , $bulk_update_ids);
      // }

      // //オートコンプリート(jquery.ui)用配列生成
      // $this->_set_arrays_auto_compleate();





    }

// ------------------------------------------------------------------------------------------------------------------------------------------------------
    /**
     * [検索パラメータをリセットして、indexにリダイレクトする]
     */
    function _filter_reset(){
        //リセットしても引き継ぎたいデータだけsetして、再リダイレクトする
        $filter_form_opened     =$this->Request->setRequest('filter_form_opened');
        $display_count          =$this->Request->setRequest('display_count');
        $this->redirect(['action'             => 'index' ,
                         '?' => [
                           'filter_form_opened' => $filter_form_opened ,
                           'display_count'      => $display_count ,
                           'rule_status'        => '1' ,
                           'submit_action'      => 'search'
                         ]
                        ]);
    }

// ------------------------------------------------------------------------------------------------------------------------------------------------------
    /**
     * [GETパラメータをControllerとView用の変数セットする]
     * @param  array $fileter_vals 変数
     * @return array $fileter_vals 変数
     */
    function _get_filter_vals($fileter_vals) {

      $fileter_vals['filter_form_opened']     = $this->Request->setRequest('filter_form_opened',1);
      $fileter_vals['display_count']          = $this->Request->setRequest('display_count',100);
      $fileter_vals['sort']                   = $this->Request->setRequest('sort');
      $fileter_vals['direction']              = $this->Request->setRequest('direction');
      $fileter_vals['to_check']               = $this->Request->setRequest('to_check',0);
      $fileter_vals['rule_id']                = $this->Request->setRequest('rule_id');
      if (!empty($fileter_vals['rule_id'])) {
        $fileter_vals['rule_id']                = (string)((int)$fileter_vals['rule_id']);
      }
      $fileter_vals['rule_id_operetor']       = $this->Request->setRequest('rule_id_operetor');
      $fileter_vals['rule_status']            = $this->Request->setRequest('rule_status',1);
      $fileter_vals['rule_set']               = $this->Request->setRequest('rule_set',['0'=>'0']);
      $fileter_vals['start_time_from']        = $this->Request->setRequest('start_time_from');
      $fileter_vals['start_time_to']          = $this->Request->setRequest('start_time_to');
      $fileter_vals['end_time_from']          = $this->Request->setRequest('end_time_from');
      $fileter_vals['end_time_to']            = $this->Request->setRequest('end_time_to');
      $fileter_vals['customer_name']          = $this->Request->setRequest('customer_name');
      $fileter_vals['customer_name_operetor'] = $this->Request->setRequest('customer_name_operetor');
      $fileter_vals['hostname']               = $this->Request->setRequest('hostname');
      $fileter_vals['hostname_operetor']      = $this->Request->setRequest('hostname_operetor');
      $fileter_vals['ci_name']                = $this->Request->setRequest('ci_name');
      $fileter_vals['ci_name_operetor']       = $this->Request->setRequest('ci_name_operetor');
      $fileter_vals['action_no']              = $this->Request->setRequest('action_no',['0'=>'0']);
      $fileter_vals['op_comment']                = $this->Request->setRequest('op_comment');
      $fileter_vals['op_comment_operetor']       = $this->Request->setRequest('op_comment_operetor');
      $fileter_vals['disp_col']               = $this->Request->setRequest('disp_col',['0'=>'0']);

      return $fileter_vals;
    }

// ------------------------------------------------------------------------------------------------------------------------------------------------------
    /**
     * [検索条件を設定する]
     * @param object $query_gwRules  クエリ
     * @param array $filter_val      変数
     * @return object $query_gwRules クエリ
     */
    function _set_filter_condtions($query_gwRules, $filter_val) {

        //フォームの条件式に従い、条件式追加
        $query_gwRules = $this->_set_query_condition($query_gwRules, 'rule_id' , $filter_val['rule_id_operetor'] , $filter_val['rule_id']);

        if ($filter_val['rule_status']=="2"){
            $query_gwRules = $this->_set_query_condition($query_gwRules, 'rule_status' , '15' , "1"); //有効ルール
        } elseif ($filter_val['rule_status']=="3"){
            $query_gwRules = $this->_set_query_condition($query_gwRules, 'rule_status' , '15' , "0"); //無効ルール
        }

        $query_gwRules = $this->_set_query_condition($query_gwRules, 'start_time'    , '24' , $filter_val['start_time_from']);
        $query_gwRules = $this->_set_query_condition($query_gwRules, 'start_time'    , '25' , $filter_val['start_time_to']);

        $query_gwRules = $this->_set_query_condition($query_gwRules, 'end_time'      , '24' , $filter_val['end_time_from']);
        $query_gwRules = $this->_set_query_condition($query_gwRules, 'end_time'      , '25' , $filter_val['end_time_to']);

        $query_gwRules = $this->_set_query_condition($query_gwRules, 'customer_name' , $filter_val['customer_name_operetor'] , $filter_val['customer_name']);
        $query_gwRules = $this->_set_query_condition($query_gwRules, 'hostname'      , $filter_val['hostname_operetor']      , $filter_val['hostname']);
        $query_gwRules = $this->_set_query_condition($query_gwRules, 'ci_name'       , $filter_val['ci_name_operetor']       , $filter_val['ci_name']);
        $query_gwRules = $this->_set_query_condition($query_gwRules, 'op_comment'    , $filter_val['op_comment_operetor']    , $filter_val['op_comment']);

        $select_rule_set =[];
        foreach ($filter_val['rule_set'] as $rule_set){
            if ($rule_set >= 1){
                $select_rule_set = array_merge($select_rule_set, [['rule_set' =>$rule_set]]);
            }
        }
        // 1つ以上チェックされているかつ、ボックスの数より少なければ検索条件に加える。
        $RULE_SET_NAME     = Configure::read("RULE_SET_NAME");
        if (count($select_rule_set) >=1 &&
            count($select_rule_set) < count($RULE_SET_NAME)) {

                $query_gwRules->where([ 'or' => $select_rule_set ]);
        }

        $select_action_no =[];
        foreach ($filter_val['action_no'] as $action_no){
            if ($action_no >= 1){
                $select_action_no = array_merge($select_action_no, [['action_no' =>$action_no]]);
            }
        }
        // 1つ以上チェックされているかつ、ボックスの数より少なければ検索条件に加える。
        $ACTION_NO_NAME    = Configure::read("ACTION_NO_NAME");
        if (count($select_action_no) >= 1 &&
            count($select_action_no) < count($ACTION_NO_NAME)) {

            $query_gwRules->where([ 'or' => $select_action_no ]);
        }

        // 運用者ごとの顧客表示制御対応
        $usrgrp_names = $this->getRequest()->getSession()->read('usrgrp_names');
        $customer_names = $this->getRequest()->getSession()->read('customer_names');
        $account_type = $this->getRequest()->getSession()->read('account_type');
        $this->set('account_type', $account_type);
        // ハウコム運用者はハウコム顧客のみを検索
        if (in_array(Configure::read("HOWCOM_USER_GROUP"), $usrgrp_names)) {
            if ($customer_names) {
                $query_gwRules = $this->_set_query_condition($query_gwRules, 'customer_name' , '15', $customer_names);
            } else {
                $query_gwRules = $this->_set_query_condition($query_gwRules, 'customer_name' , '15', '存在しない顧客名');
            }
        // Zabbix特権管理者かつ全顧客検索ユーザー以外は他の運用者の顧客以外を検索
        } elseif ($account_type != 3 && !array_intersect($usrgrp_names, Configure::read("ALL_SEARCH_USER_GROUPS"))) {
            $not_perfect=[];
            foreach (InputSetHelper::explode(',', $customer_names) as $customername) {
                if (trim($customername)) {
                    array_push($not_perfect, ['customer_name !=' => trim($customername)]);
                }
            }
            if ($not_perfect) {
                $query_gwRules->where(['and'=>$not_perfect]);
            }
        }

        return $query_gwRules;

    }



// ------------------------------------------------------------------------------------------------------------------------------------------------------
    /**
     * [検索条件設定関数]
     * @param object $query_gwRules  クエリ
     * @param string $field          カラム名
     * @param string $operetor       検索パターン
     * @param string $operands       検索値
     * @return object $query_gwRules クエリ
     */
    function _set_query_condition($query_gwRules, $field, $operetor, $operands){

      //検索値が無いか、Null検索でない場合は、検索条件を追加しない
      if ($operands=='' && $operetor!='98' && $operetor!='99'){
        return $query_gwRules;
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
          $query_gwRules->where(['or'=>$like]);

      } elseif($operetor=='14'){
          $not_like=[];
          foreach ($a_operands as $operand){
              if (InputSetHelper::mb_strlen(trim($operand)) > 0){
                array_push($not_like, [$field . ' ' . $query_operator => '%' .trim($operand) . '%']);
              }
          }
          $query_gwRules->where(['and'=>$not_like]);

      } elseif ($operetor=='98' || $operetor=='99'){
          $query_gwRules->where(['or'=>[
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

          $query_gwRules->where(['or'=>$perfect]);

      }

      return $query_gwRules;
    }

// ------------------------------------------------------------------------------------------------------------------------------------------------------
    /**
     * [ページネーション用インスタンス生成]
     * @param  object $query_gwRules クエリ
     * @param  int    $display_count 表示件数
     */
    function _gen_pagenate_instance($query_gwRules, $display_count){

        $this->paginate=[
            'limit' => $display_count,
            'maxLimit' => 1000,
            // 'order' => ['alarm_time' =>'DESC']
        ];
        $gwRules = $this->paginate($query_gwRules);
        $this->set(compact('gwRules'));
    }

// ------------------------------------------------------------------------------------------------------------------------------------------------------
    /**
     * [オートコンプリート(jquery.ui)用配列生成]
     */
    function _set_arrays_auto_compleate(){

        $list_customer_name = $this->GwRules->disp('customer_name')->find('list')
                                ->distinct(['GwRules.customer_name'])->where(['customer_name is not ' => null ])->toArray();
        $list_hostname      = $this->GwRules->disp('hostname')->find('list')
                                ->distinct(['GwRules.hostname'])->where(['hostname is not ' => null ])->toArray();
        $list_ci_name       = $this->GwRules->disp('ci_name')->find('list')
                                ->distinct(['GwRules.ci_name'])->where(['ci_name is not ' => null ])->toArray();

        //json_encodeの為の、keyの降り直し
        $list_customer_name = array_values($list_customer_name);
        $list_hostname      = array_values($list_hostname);
        $list_ci_name       = array_values($list_ci_name);

        $list_customer_name = json_encode($list_customer_name, JSON_HEX_TAG | JSON_HEX_AMP | JSON_HEX_APOS | JSON_HEX_QUOT);
        $list_hostname      = json_encode($list_hostname     , JSON_HEX_TAG | JSON_HEX_AMP | JSON_HEX_APOS | JSON_HEX_QUOT);
        $list_ci_name       = json_encode($list_ci_name      , JSON_HEX_TAG | JSON_HEX_AMP | JSON_HEX_APOS | JSON_HEX_QUOT);

        $this->set('list_customer_name', $list_customer_name);
        $this->set('list_hostname'     , $list_hostname);
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
            ->distinct([$fieald_name])->where([ $fieald_name . ' is not ' => null ]);
            // ->where([ $fieald_name . ' is not ' => '' ]);
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
        $gwTables = $this->paginate($gwTables_find);

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
     * [selectCondsアクション]
     * @param  string $table_name  テーブル名
     * @param  string $fieald_name カラム名
     * @param  string $conds       検索条件（顧客名,ホスト名,アラーム名）
     */
    public function selectConds($table_name, $fieald_name, $conds) {
        $conditions = InputSetHelper::explode("," ,$conds);
        $customer_name = $conditions[0];
        $hostname = $conditions[1];
        $ci_name = $conditions[2];
        if ($fieald_name == 'customer_name') {
          $customer_name = '';
        } else {
          $customer_name = trim($customer_name, '*');
        }
        if ($fieald_name == 'hostname') {
          $hostname = '';
        } else {
          $hostname = trim($hostname, '*');
        }
        if ($fieald_name == 'ci_name') {
          $ci_name = '';
        } else {
          $ci_name = trim($ci_name, '*');
        }

        $this->viewBuilder()->disableAutoLayout();
        $this->loadModel($table_name);

        $gwTables_find = $this->$table_name->find()->select([$fieald_name,'customer_ci'])
            ->distinct([$fieald_name])->where([ $fieald_name . ' is not ' => null ]);
        if ($customer_name) {
          $gwTables_find->where([['GwEvents.customer_name LIKE ' => '%' . $customer_name . '%']]);
        }
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
        if ($hostname && $hostname != "*"){
          $gwTables_find->where([['GwEvents.hostname LIKE ' => '%' . $hostname . '%']]);
        }
        if ($ci_name && $ci_name != "*"){
          $gwTables_find->where([['GwEvents.ci_name LIKE ' => '%' . $ci_name . '%']]);
        }
        $gwTables = $this->paginate($gwTables_find);

        // ホスト名選択ボタン押下時（顧客名入力ありかつアラーム名入力なし）、CMDB情報から取得したホスト名も表示する
        if ($fieald_name == 'hostname' && $customer_name && !$ci_name) {
            $arrays_hostname = [];
            // ユーザ情報取得
            $CMDB_USERNAME = Configure::read('CMDB_USERNAME');
            $CMDB_PASSWORD = Configure::read('CMDB_PASSWORD');
            $auth = $this->CMDB->getAuth($CMDB_USERNAME, $CMDB_PASSWORD);

            // イベントテーブル検索結果分、繰り返す
            foreach ($gwTables as $gwTable):
                // 重複するホスト名ない場合、ホスト名リストに追加する
                if (!in_array(["hostname"=>$gwTable['hostname']], $arrays_hostname)) {
                    array_push($arrays_hostname, ["hostname"=>$gwTable['hostname']]);
                }
                // プロジェクト情報取得
                $project = $this->CMDB->getProject($gwTable['customer_ci'], $auth);
                $project_data = $project['data'];
                if ($project_data == Null or count($project_data) == 0) {
                    continue;
                }
                $project_id = $project_data[0]['_id'];
                $cmdb_data['project_id'] = $project_id;
                // 機器情報取得
                $machineInfo = $this->CMDB->getMachineInfo($hostname, $project_id, $auth);
                if ($machineInfo) {
                    foreach ($machineInfo['data'] as $data):
                        // 重複するホスト名ない場合、ホスト名リストに追加する
                        if (!in_array(["hostname"=>$data['FQDN']], $arrays_hostname)) {
                            array_push($arrays_hostname, ["hostname"=>$data['FQDN']]);
                        }
                    endforeach;    
                }
            endforeach;

            $gwTables = $arrays_hostname;
        }

        $this->set('gwTables', $gwTables);
        $this->set('fieald_name', $fieald_name);
        $this->set('input_elm_id', $fieald_name);

        $this->render('/layout/select/');
    }

// ======================================================================================================================================================
    /**
     * [editアクション]
     * @param  string $id イベントID
     */
    public function edit($id = null) {

        //選択用ウインドウオープン用URL
        $currentUrl=preg_replace('/\/edit.*/', '', Router::url('', true));
        $this->set(compact('currentUrl'));

        // $gwRule = $this->GwRules->get($id, ['contain' => []]);
        $gwRule = $this->GwRules->get($id, ['aaaa']);

        if ($this->getRequest()->is(['patch', 'post', 'put'])) {
            $this->_save_record($gwRule,$id);
        }

        //Selectボックス用 Option
        $ACTION_NO_NAME    = Configure::read("ACTION_NO_NAME");
        $this->set(compact('ACTION_NO_NAME'));
        $RULE_SET_NAME    = Configure::read("RULE_SET_NAME");
        $this->set(compact('RULE_SET_NAME'));

        $RULE_SET_DESC    = Configure::read("RULE_SET_DESC");
        $this->set(compact('RULE_SET_DESC'));
        $ACTION_NO_DESC    = Configure::read("ACTION_NO_DESC");
        $this->set(compact('ACTION_NO_DESC'));

        // Zabbix特権管理者はアクションNo:90を表示する
        $account_type = $this->getRequest()->getSession()->read('account_type');
        if ($account_type == 3) {
            $ACTION_NO_NAME = $ACTION_NO_NAME + ['90'=>'90:K-ISYSメンテナンスです'];
            $ACTION_NO_DESC = $ACTION_NO_DESC + ['90'=>'90:K-ISYSメンテナンスです　（優先順位１）'];
            $this->set(compact('ACTION_NO_NAME'));
            $this->set(compact('ACTION_NO_DESC'));
        }

        //レコード表示
        $this->set(compact('gwRule'));
        //アラーム一覧画面の検索後の戻りURLのセット
        $this->_set_refer_url();

        //定数を表示
        $KDDI_MIYAZAKI = Configure::read("KDDI_MIYAZAKI");
        $this->set(compact('KDDI_MIYAZAKI'));

    }

// ------------------------------------------------------------------------------------------------------------------------------------------------------
/**
 * [更新処理]
 * @param  GwRule $gwRule エンティティ
 * @param  string $id     ルールID
 */
function _save_record($gwRule, $id){


  // $validator = new Validator();
  // $validator->lessThan('start_time', $gwRule->end_time, '終了日時より前の日時を設定してください。');
  // $validator->greaterThan('start_time', $gwRule->end_time, '終了日時より前の日時を設定してください。');

  $gwRule = $this->GwRules->patchEntity($gwRule, $this->getRequest()->getData());
  $alias=$this->getRequest()->getSession()->read($this::SESSION_KEY_ACCOUNT_ALIAS);
  $gwRule->update_user = $alias;
  $gwRule->op_comment = InputSetHelper::str_replace("\r", "", $gwRule->op_comment);

  // 日付型がpatchEntityでは取り込まれないため
  $gwRule->start_time = new FrozenTime($this->getRequest()->getData()['start_time']);
  $gwRule->end_time = new FrozenTime($this->getRequest()->getData()['end_time']);

  if($gwRule->start_time >= $gwRule->end_time){
      $this->Flash->error(__('適用開始日時は適用終了日時より前の日時を設定してください。'));
      return;
  }

  // 運用者ごとの顧客登録制御対応
  $usrgrp_names = $this->getRequest()->getSession()->read('usrgrp_names');
  $check_names = $this->getRequest()->getSession()->read('check_names');
  $account_type = $this->getRequest()->getSession()->read('account_type');
  // ハウコム運用者はハウコム顧客以外の顧客を登録不可
  if (in_array(Configure::read("HOWCOM_USER_GROUP"), $usrgrp_names)) {
      if ($check_names && !in_array($gwRule->customer_name, $check_names)) {
          $this->Flash->error(__('この顧客名は登録出来ません。'));
          return;
      }
  // Zabbix特権管理者かつ全顧客検索ユーザー以外は他の運用者の顧客を登録不可
  } elseif ($account_type != 3 && !array_intersect($usrgrp_names, Configure::read("ALL_SEARCH_USER_GROUPS"))) {
      if ($check_names && in_array($gwRule->customer_name, $check_names)) {
          $this->Flash->error(__('この顧客名は登録出来ません。'));
          return;
      }
  }

  $rule_set = InputSetHelper::explode(':', $gwRule->rule_set);
  $action_no = InputSetHelper::explode(':',$gwRule->action_no);
  // $exist_gwRules = $this->GwRules->find()
  //                   ->where(['rule_status ' => $gwRule->rule_status ])
  //                   ->where(['customer_name ' => $gwRule->customer_name ])
  //                   // ->where(['rule_set'       => $rule_set[0] ])
  //                   ->where(['action_no'      => $action_no[0] ])
  //                   ->where(['start_time <='  => $gwRule->end_time ])
  //                   ->where(['end_time   >='  => $gwRule->start_time ]);
  //
  //                   if ($gwRule->hostname != "*"){
  //                     $exist_gwRules = $exist_gwRules->where( ['or' => [
  //                                                                     ['hostname'       => $gwRule->hostname ],
  //                                                                     ['hostname'       => "*" ],
  //                                                                   ]] );
  //                   }
  //                   if ($gwRule->ci_name != "*"){
  //                     $exist_gwRules = $exist_gwRules->where(['or' => [
  //                                                                       ['ci_name'       => $gwRule->ci_name ],
  //                                                                       ['ci_name'       => "*" ],
  //                                                                     ]] );
  //                   }
  //
  //                   $exist_gwRules = $exist_gwRules->select('rule_id')->toArray();
  $connection = ConnectionManager::get('default');
  $hostname_t = trim($gwRule->hostname, '*');
  $ci_name_t = trim($gwRule->ci_name, '*');
  $array = [
    'rule_status' => 1,
    'customer_name' => $gwRule->customer_name,
    'hostname' => $gwRule->hostname,
    'ci_name' => $gwRule->ci_name,
    'start_time' => $gwRule->start_time,
    'end_time' => $gwRule->end_time,
    'action_no' => $action_no[0],
    'hostname_t' => $hostname_t,
    'ci_name_t' => $ci_name_t
  ];
  // 重複ルールチェック実行
  $exist_gwRules = $connection->execute($this::GET_RULE_ID, $array)->fetchAll('assoc');

  $target_rule_id = null;
  // 更新可能フラグ
  $flag_update=false;
  if(count($exist_gwRules)==0){
      $flag_update=true;
  }elseif(count($exist_gwRules)==1){
    if($exist_gwRules['0']['rule_id']==$gwRule->rule_id) {
      $flag_update=true;
    } else {
      $target_rule_id = $exist_gwRules['0']['rule_id'];
    }
  }else{
    foreach ($exist_gwRules as $exist_gwRule){
      if ($exist_gwRule['rule_id']!=$gwRule->rule_id){
        $target_rule_id = $exist_gwRule['rule_id'];
        break;
      }
    }
  }

  // ルールが無効以外または更新可能の場合
  if(!$gwRule->rule_status || $flag_update) {
      if ($this->GwRules->save($gwRule)) {
          $this->Flash->success(__('The gw rule has been saved.', $id));
          return $this->redirect($this->getRequest()->getSession()->read($this::SESSION_KEY_INDEX_URL));
          // return $this->redirect(['action' => 'index']);
      } else {
          $this->Flash->error(__('The gw rule could not be saved. Please, try again.', $id));
      }

  }else{
    $this->Flash->error(__('ルールID{0}と重複するルールの為、登録できません。', $target_rule_id));
    $this->Flash->error(__('同じ、顧客名、ホスト名、アラーム名、アクションNoを重複する期間で追加することはできません。'));

  }

}
// ------------------------------------------------------------------------------------------------------------------------------------------------------
    /**
     * [to_checkパラメータ設定]
     */
    function _set_refer_url(){

        $indexUrl  = $this->getRequest()->getSession()->read($this::SESSION_KEY_INDEX_URL);
        //sessionにURLが保存されているか

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

    }
// ======================================================================================================================================================
    /**
     * [bulkUpdateアクション] 現在未使用
     */
    public function bulkUpdate(){


      //選択用ウインドウオープン用URL
      $currentUrl=preg_replace('/\/bulk-update.*/', '', Router::url('', true));
      $this->set(compact('currentUrl'));

      //Selectボックス用 Option



      $ACTION_NO_NAME=array_merge([''=>'変更なし'], Configure::read("ACTION_NO_NAME"));
      $this->set(compact('ACTION_NO_NAME'));

      $RULE_SET_NAME=array_merge([''=>'変更なし'], Configure::read("RULE_SET_NAME"));
      $this->set(compact('RULE_SET_NAME'));

      $RULE_SET_DESC    = Configure::read("RULE_SET_DESC");
      $this->set(compact('RULE_SET_DESC'));

      $ACTION_NO_DESC    = Configure::read("ACTION_NO_DESC");
      $this->set(compact('ACTION_NO_DESC'));

      if (array_key_exists('BulkUpdate', $this->getRequest()->getData())){
        $bulk_update_ids=[];
        $this->_set_session_bulkupdate_ids($bulk_update_ids);
      }

      $bulk_update_ids = $this->getRequest()->getSession()->read($this::SESSION_KEY_IDS);

      //クエリビルド
      if (count($bulk_update_ids)==0){
        $this->set('disabled', true);       //エレメント無効化
        $query_gwRules = $this->GwRules->find('all',['conditions'=> ['rule_id ' => false ]]); //０件インスタンス
        $this->set('gwEvent', '');
        $this->Flash->error(__('前の画面に戻り、一括更新するレコードを選択してください。'));

      } else {
        $this->set('disabled', false);      //エレメント有効化
        $query_gwRules = $this->GwRules->find('all',['conditions'=> ['rule_id IN' => $bulk_update_ids ] ] );
      }

      $this->_gen_pagenate_instance($query_gwRules, 1000);
      $this->_set_refer_url();

    }

// ------------------------------------------------------------------------------------------------------------------------------------------------------
    /**
     * [一括更新IDセッション設定] 現在未使用
     * @param array $bulk_update_ids 一括更新ID
     */
    function _set_session_bulkupdate_ids($bulk_update_ids){

        // チェックが入っているIDを配列に格納
        // var_dump($this->request->data);
        foreach ($this->getRequest()->getDara()['BulkUpdate'] as $key => $val){
          if ($val==1){
            array_push($bulk_update_ids, $key);
          }
        }
        //セッションに格納
        $this->getRequest()->getSession()->write($this::SESSION_KEY_IDS, $bulk_update_ids);
    }




// ======================================================================================================================================================
    /**
     * [bulkUpdateSaveアクション] 現在未使用
     */
    public function bulkUpdateSave(){

      $this->viewBuilder()->disableAutoLayout();
      $this->autoRender = false;

      //更新情報の取得
      $update_value = $this->_get_update_request();
      if (is_null($update_value)){
        $this->Flash->error('一括更新する情報を1項目以上入力してください。');
        return $this->redirect(['action' => 'bulkUpdate']);

      } else {
        // if (!is_null($confirm_messages)){
        //
        // }
      }

      // $validator = $this->_validation();
      // $errors=$validator->errors($update_value);

      if(!empty($errors) ){
        //連想配列で取り出す
        $error_messages="";
        foreach ($errors as $pkey => $pval){
          foreach ($pval as $ckey => $cval){

                if ($pkey =='rule_status') { $pkey   = InputSetHelper::str_replace('rule_status'  , 'ルールステータス', $pkey); }
            elseif ($pkey =='rule_set') { $pkey      = InputSetHelper::str_replace('rule_set'     , 'ルールセット'    , $pkey); }
            elseif ($pkey =='start_time') { $pkey    = InputSetHelper::str_replace('start_time'   , '適用開始日時'    , $pkey); }
            elseif ($pkey =='end_time') { $pkey      = InputSetHelper::str_replace('end_time'     , '終了日時'        , $pkey); }
            elseif ($pkey =='customer_name') { $pkey = InputSetHelper::str_replace('customer_name', '顧客名'          , $pkey); }
            elseif ($pkey =='hostname') { $pkey      = InputSetHelper::str_replace('hostname'     , 'ホスト名'        , $pkey); }
            elseif ($pkey =='ci_name') { $pkey       = InputSetHelper::str_replace('ci_name'      , 'CI名'           , $pkey); }
            elseif ($pkey =='action_no') { $pkey     = InputSetHelper::str_replace('action_no'    , 'アクションNo'    , $pkey); }
            $error_messages .= $pkey . ' : ' . $cval . '<br>';
          }
        }
        $this->Flash->error($error_messages);
        // var_dump($errors);
        // var_dump($error_messages);

      } else {
        $ids          = $this->getRequest()->getSession()->read($this::SESSION_KEY_IDS);
        $ids          = ['rule_id IN' => $ids];
        var_dump($ids);

        //idsがないupdateallは許可しない。
        if ($ids){
          $this->GwRules->updateAll($update_value, $ids);
        }else{
          $this->Flash->error(__('不明なエラーです。'));
        }


      }
      return $this->redirect(['action' => 'bulkUpdate']);

    }
// ------------------------------------------------------------------------------------------------------------------------------------------------------
    /**
     * [更新情報の取得] 現在未使用
     * @return array $update_value 更新情報
     */
    function _get_update_request(){

        $update_value = '';

        $rule_status   = $this->getRequest()->getData()['rule_status'];
        $rule_set      = $this->getRequest()->getData()['rule_set'];
        $start_time    = $this->getRequest()->getData()['start_time'];
        $end_time      = $this->getRequest()->getData()['end_time'];
        $customer_name = $this->getRequest()->getData()['customer_name'];
        $host_name     = $this->getRequest()->getData()['hostname'];
        $ci_Name       = $this->getRequest()->getData()['ci_name'];
        $action_no     = $this->getRequest()->getData()['action_no'];

        $update_value =null;
        if ($rule_status   != ""){ $update_value['rule_status']   = $rule_status;   }
        if ($rule_set      != ""){ $update_value['rule_set']      = $rule_set;      }
        if ($start_time    != ""){ $update_value['start_time']    = $start_time;    }
        if ($end_time      != ""){ $update_value['end_time']      = $end_time;      }
        if ($customer_name != ""){ $update_value['customer_name'] = $customer_name; }
        if ($host_name     != ""){ $update_value['hostname']      = $host_name;     }
        if ($ci_Name       != ""){ $update_value['ci_name']       = $ci_Name;       }
        if ($action_no     != ""){ $update_value['action_no']     = $action_no;     }

        return $update_value;
    }

// ======================================================================================================================================================
/**
 * [addアクション]
 */
public function add() {

    //選択用ウインドウオープン用URL
    $currentUrl=preg_replace('/\/add.*/', '', Router::url('', true));
    $this->set(compact('currentUrl'));
    $gwRule = $this->GwRules->newEmptyEntity();
    $gwRule->rule_status = '1';

    if ($this->getRequest()->is('post')) {
        $gwRule = $this->GwRules->patchEntity($gwRule, $this->getRequest()->getData());
        $alias=$this->getRequest()->getSession()->read($this::SESSION_KEY_ACCOUNT_ALIAS);
        $gwRule->create_user = $alias;
        $gwRule->update_user = $alias;
        $gwRule->op_comment = InputSetHelper::str_replace("\r", "", $gwRule->op_comment);
        // var_dump($gwRule->toArray());

        // 日付型がpatchEntityでは取り込まれないため
        $gwRule->start_time = new FrozenTime($this->getRequest()->getData()['start_time']);
        $gwRule->end_time = new FrozenTime($this->getRequest()->getData()['end_time']);

        $flag_add = true;
        if($gwRule->start_time >= $gwRule->end_time){
            $this->Flash->error(__('適用開始日時は適用終了日時より前の日時を設定してください。'));
            $flag_add = false;
        }

        // 運用者ごとの顧客登録制御対応
        $usrgrp_names = $this->getRequest()->getSession()->read('usrgrp_names');
        $check_names=$this->getRequest()->getSession()->read('check_names');
        $account_type = $this->getRequest()->getSession()->read('account_type');
        // ハウコム運用者はハウコム顧客以外の顧客を登録不可
        if (in_array(Configure::read("HOWCOM_USER_GROUP"), $usrgrp_names)) {
            if ($check_names && !in_array($gwRule->customer_name, $check_names)) {
                $this->Flash->error(__('この顧客名は登録出来ません。'));
                $flag_add = false;
            }
        // Zabbix特権管理者かつ全顧客検索ユーザー以外は他の運用者の顧客を登録不可
        } elseif ($account_type != 3 && !array_intersect($usrgrp_names, Configure::read("ALL_SEARCH_USER_GROUPS"))) {
            if ($check_names && in_array($gwRule->customer_name, $check_names)) {
                $this->Flash->error(__('この顧客名は登録出来ません。'));
                $flag_add = false;
            }
        }

        if ($flag_add){

            $rule_set = InputSetHelper::explode(':', $gwRule->rule_set);
            $action_no = InputSetHelper::explode(':',$gwRule->action_no);
            // $exist_gwRules = $this->GwRules->find()
            //                  ->where(['rule_status ' => $gwRule->rule_status ])
            //                   ->where(['customer_name ' => $gwRule->customer_name ])
            //                   // ->where(['rule_set'       => $rule_set[0] ])
            //                   ->where(['action_no'      => $action_no[0] ])
            //                   ->where(['start_time <='  => $gwRule->end_time ])
            //                   ->where(['end_time   >='  => $gwRule->start_time ]);
            //
            //                   if ($gwRule->hostname != "*"){
            //                     $exist_gwRules = $exist_gwRules->where( ['or' => [
            //                                                                     ['hostname'       => $gwRule->hostname ],
            //                                                                     ['hostname'       => "*" ],
            //                                                                   ]] );
            //                   }
            //                   if ($gwRule->ci_name != "*"){
            //                     $exist_gwRules = $exist_gwRules->where(['or' => [
            //                                                                       ['ci_name'       => $gwRule->ci_name ],
            //                                                                       ['ci_name'       => "*" ],
            //                                                                     ]] );
            //                   }
            //
            //                   $exist_gwRules = $exist_gwRules->select('rule_id')->toArray();
            $connection = ConnectionManager::get('default');
            $hostname_t = trim($gwRule->hostname, '*');
            $ci_name_t = trim($gwRule->ci_name, '*');
            $array = [
                'rule_status' => 1,
                'customer_name' => $gwRule->customer_name,
                'hostname' => $gwRule->hostname,
                'ci_name' => $gwRule->ci_name,
                'start_time' => $gwRule->start_time,
                'end_time' => $gwRule->end_time,
                'action_no' => $action_no[0],
                'hostname_t' => $hostname_t,
                'ci_name_t' => $ci_name_t
            ];
            // 重複ルールチェック実行
            $exist_gwRules = $connection->execute($this::GET_RULE_ID, $array)->fetchAll('assoc');

            // ルールが有効かつ重複ルールが存在する場合
            if($gwRule->rule_status && isset($exist_gwRules['0']['rule_id'])) {
                $this->Flash->error(__('ルールID{0}と重複するルールの為、登録できません。', $exist_gwRules['0']['rule_id']));
                $this->Flash->error(__('同じ、顧客名、ホスト名、アラーム名、アクションNoを重複する期間で追加することはできません。'));
            }else{
                if ($this->GwRules->save($gwRule)) {
                  $this->Flash->success(__('The gw rule has been added.',$gwRule->rule_id));
                  return $this->redirect($this->getRequest()->getSession()->read($this::SESSION_KEY_INDEX_URL));
                }else{
                  $this->Flash->error(__('The gw rule could not be added. Please, try again.',""));
                }
            }
        }
    }

    //Selectボックス用 Option
    $ACTION_NO_NAME    = Configure::read("ACTION_NO_NAME");
    $this->set(compact('ACTION_NO_NAME'));
    $RULE_SET_NAME    = Configure::read("RULE_SET_NAME");
    $this->set(compact('RULE_SET_NAME'));

    $RULE_SET_DESC    = Configure::read("RULE_SET_DESC");
    $this->set(compact('RULE_SET_DESC'));
    $ACTION_NO_DESC    = Configure::read("ACTION_NO_DESC");
    $this->set(compact('ACTION_NO_DESC'));

    // Zabbix特権管理者はアクションNo:90を表示する
    $account_type = $this->getRequest()->getSession()->read('account_type');
    if ($account_type == 3) {
        $ACTION_NO_NAME = $ACTION_NO_NAME + ['90'=>'90:K-ISYSメンテナンスです'];
        $ACTION_NO_DESC = $ACTION_NO_DESC + ['90'=>'90:K-ISYSメンテナンスです　（優先順位１）'];
        $this->set(compact('ACTION_NO_NAME'));
        $this->set(compact('ACTION_NO_DESC'));
    }

    $this->set(compact('gwRule'));
    // $this->set('_serialize', ['gwRule']);
    $indexUrl  = $this->getRequest()->getSession()->read('index.url');
    if (!is_null($indexUrl) && strpos($indexUrl,'action') ){
      $this->set("indexUrl", $indexUrl . "&to_check=1");
    }else{
      $this->set("indexUrl", '/gw-rules');
    }
    // var_dump($indexUrl);
}



//Class End
}

<?php
namespace App\Controller;
use Cake\Core\Configure;
use App\View\Helper\InputSetHelper;
use Cake\Log\Log;

class GwFetchAlertEvent extends AppController {

    public function get_gw_data($filter) {
        $this->loadModel('GwEvents');
        //クエリビルド
        $query_gwEvents = $this->GwEvents->find('all', ['contain' => ['GwIncidents'] ])->select(['gw_event_id',
                                                                                                'event_status',
                                                                                                'customer_ci',
                                                                                                'customer_name',
                                                                                                'hostname',
                                                                                                'alarm_time',
                                                                                                'ci_name',
                                                                                                'device',
                                                                                                'alarm_status',
                                                                                                'summary',
                                                                                                'checked_time',
                                                                                                'op_comment',
                                                                                                'kisys_status',
                                                                                                'GwIncidents.kisys_incidentid',
                                                                                                'GwIncidents.op_comment',
                                                                                                ]);
        // 検索条件を設定する
        $query_gwEvents = $this->set_filter_condtions($query_gwEvents, $filter);
        $query_gwEvents->order(['GwEvents.update_time' => 'DESC']);
        $query_gwEvents->limit(10000);
        return $query_gwEvents->toArray();
    }

    /**
     * [検索条件を設定する]
     * @param object $query_gwEvents  クエリ
     * @param array $filter_val       検索条件　ex. ['status_code' => '200', ...]
     * @return object $query_gwEvents クエリ
     */
    public function set_filter_condtions($query_gwEvents, $filter_val) {

        // 自ホスト受信アラーム判定用IPアドレス
        $CURRENT_SERVER_ID    = Configure::read("CURRENT_SERVER_IP_4TH");

        //99重複イベントをあらかじめ除く条件式
        //イベントステータスが0かつ、自分のIPアドレス
        $query_gwEvents->where(['OR' => [[  ['GwEvents.event_status' =>'0'],
                                            ['GwEvents.detected_host' =>$CURRENT_SERVER_ID] ],
                                         ['GwEvents.event_status' =>'1'],
                                         ['GwEvents.event_status' =>'2'],
                                         ['GwEvents.event_status' =>'3']
                                        ]
                               ]);

        //重複イベントを除く
        $query_gwEvents->where([['GwEvents.event_status is not' =>'99']]);

        //下記よりフォームの条件式に従い、条件式追加
        /*
        $query_gwEvents = $this->_set_query_condition($query_gwEvents, 'GwEvents.gw_event_id' , $filter_val['gw_event_id_operetor'] , $filter_val['gw_event_id']);

        */
        $str_alarm_time_from = InputSetHelper::str_replace(["\n","\r"], "", $filter_val['alarm_time_from']);
        if($str_alarm_time_from){
          $alarm_time_from_obj = new \DateTime($str_alarm_time_from);
          $query_gwEvents = $this->_set_query_condition($query_gwEvents, 'GwEvents.alarm_time'  , '24' , $alarm_time_from_obj->format('Y/m/d H:i:s'));
        }

        $str_alarm_time_to = InputSetHelper::str_replace(["\n","\r"], "", $filter_val['alarm_time_to']);
        if($str_alarm_time_to){
          $alarm_time_to_obj = new \DateTime($str_alarm_time_to);
          $query_gwEvents = $this->_set_query_condition($query_gwEvents, 'GwEvents.alarm_time'  , '25' , $alarm_time_to_obj->format('Y/m/d H:i:s'));
        }

        $checkbox_count_alarm_status = 0;
        $select_alarm_status =[];
        foreach ($filter_val['alarm_status'] as $alarm_status){
            if ($alarm_status != '0'){
                // アラーム種別：error（赤）
                if ($alarm_status == 'error_red') {
                    array_push($select_alarm_status, [
                        'and' => [
                            ['alarm_status' =>'error'], ['GwEvents.event_status !=' =>'2'],
                            ['kisys_status !=' =>'10'], ['kisys_status !=' =>'20'], ['kisys_status !=' =>'30'],
                            ['kisys_status !=' =>'31'], ['kisys_status !=' =>'32'], ['kisys_status !=' =>'33'],
                            ['kisys_status !=' =>'34'], ['kisys_status !=' =>'35'],
                            ['kisys_status !=' =>'40'], ['kisys_status !=' =>'41'], ['kisys_status !=' =>'42']
                        ]
                    ]);
                }
                // アラーム種別：error（橙）
                if ($alarm_status == 'error_orange') {
                    array_push($select_alarm_status, [
                        'and' => [
                            ['alarm_status' =>'error'], ['GwEvents.event_status' =>'2'],
                            ['kisys_status !=' =>'10'], ['kisys_status !=' =>'20'], ['kisys_status !=' =>'30'],
                            ['kisys_status !=' =>'31'], ['kisys_status !=' =>'32'], ['kisys_status !=' =>'33'],
                            ['kisys_status !=' =>'34'], ['kisys_status !=' =>'35'],
                            ['kisys_status !=' =>'40'], ['kisys_status !=' =>'41'], ['kisys_status !=' =>'42']
                        ]
                    ]);
                }
                // アラーム種別：error（黄）
                if ($alarm_status == 'error_yellow') {
                    array_push($select_alarm_status, [
                        'and' => [
                            ['alarm_status' =>'error'],
                            'or' => [
                                ['kisys_status' =>'10'], ['kisys_status' =>'20'], ['kisys_status' =>'30'],
                                ['kisys_status' =>'31'], ['kisys_status' =>'32'], ['kisys_status' =>'33'],
                                ['kisys_status' =>'34'], ['kisys_status' =>'35'],
                                ['kisys_status' =>'40'], ['kisys_status' =>'41'], ['kisys_status' =>'42']
                            ]
                        ]
                    ]);
                }
                // アラーム種別：error（赤）、error（橙）、error（黄）以外
                if ($alarm_status != 'error_red' && $alarm_status != 'error_orange' && $alarm_status != 'error_yellow') {
                    array_push($select_alarm_status, [['alarm_status' =>$alarm_status]]);
                }
                $checkbox_count_alarm_status = $checkbox_count_alarm_status + 1;
            }
        }
        /*
        $checkbox_count_kisys_status = 0;
        $select_kisys_status =[];
        foreach ($filter_val['kisys_status'] as $kisys_status){
          // K-ISYS起票成功
          if ($kisys_status == '1'){
            $select_kisys_status = array_merge($select_kisys_status, [['kisys_status' =>'0,0']]);
            $select_kisys_status = array_merge($select_kisys_status, [['kisys_status' =>'0,1']]);
            $select_kisys_status = array_merge($select_kisys_status, [['kisys_status' =>'0,80']]);
            $select_kisys_status = array_merge($select_kisys_status, [['kisys_status' =>'40']]);
            $select_kisys_status = array_merge($select_kisys_status, [['kisys_status' =>'50,0']]);
            $select_kisys_status = array_merge($select_kisys_status, [['kisys_status' =>'50,1']]);
            $select_kisys_status = array_merge($select_kisys_status, [['kisys_status' =>'50,80']]);
            $checkbox_count_kisys_status = $checkbox_count_kisys_status + 1;
          // K-ISYS起票失敗
          } elseif ($kisys_status == '2'){
            $select_kisys_status = array_merge($select_kisys_status, [['kisys_status' =>'1']]);
            $select_kisys_status = array_merge($select_kisys_status, [['kisys_status' =>'2']]);
            $select_kisys_status = array_merge($select_kisys_status, [['kisys_status' =>'41']]);
            $select_kisys_status = array_merge($select_kisys_status, [['kisys_status' =>'42']]);
            $select_kisys_status = array_merge($select_kisys_status, [['kisys_status' =>'51']]);
            $select_kisys_status = array_merge($select_kisys_status, [['kisys_status' =>'52']]);
            $checkbox_count_kisys_status = $checkbox_count_kisys_status + 1;
          // K-ISYS起票しません（パトランプ鳴動します）
          } elseif ($kisys_status == '10'){
            $select_kisys_status = array_merge($select_kisys_status, [['kisys_status' =>'10']]);
            $select_kisys_status = array_merge($select_kisys_status, [['kisys_status' =>'20']]);
            $checkbox_count_kisys_status = $checkbox_count_kisys_status + 1;
          // K-ISYS起票とパトランプ鳴動しません
          } elseif ($kisys_status == '20'){
            $select_kisys_status = array_merge($select_kisys_status, [['kisys_status' =>'20']]);
            $checkbox_count_kisys_status = $checkbox_count_kisys_status + 1;
          // キャンセル待ちします
          } elseif ($kisys_status == '30'){
            $select_kisys_status = array_merge($select_kisys_status, [['kisys_status' =>'30']]);
            $select_kisys_status = array_merge($select_kisys_status, [['kisys_status' =>'31']]);
            $select_kisys_status = array_merge($select_kisys_status, [['kisys_status' =>'32']]);
            $select_kisys_status = array_merge($select_kisys_status, [['kisys_status' =>'33']]);
            $select_kisys_status = array_merge($select_kisys_status, [['kisys_status' =>'34']]);
            $select_kisys_status = array_merge($select_kisys_status, [['kisys_status' =>'35']]);
            $checkbox_count_kisys_status = $checkbox_count_kisys_status + 1;
          // 時間内復旧（K-ISYS起票自動キャンセル）
          } elseif ($kisys_status == '40'){
            $select_kisys_status = array_merge($select_kisys_status, [['kisys_status' =>'40']]);
            $select_kisys_status = array_merge($select_kisys_status, [['kisys_status' =>'41']]);
            $select_kisys_status = array_merge($select_kisys_status, [['kisys_status' =>'42']]);
            $checkbox_count_kisys_status = $checkbox_count_kisys_status + 1;
          // 要対応（時間内未復旧）
          } elseif ($kisys_status == '50'){
            $select_kisys_status = array_merge($select_kisys_status, [['kisys_status' =>'50,0']]);
            $select_kisys_status = array_merge($select_kisys_status, [['kisys_status' =>'50,1']]);
            $select_kisys_status = array_merge($select_kisys_status, [['kisys_status' =>'50,80']]);
            $select_kisys_status = array_merge($select_kisys_status, [['kisys_status' =>'51']]);
            $select_kisys_status = array_merge($select_kisys_status, [['kisys_status' =>'52']]);
            $checkbox_count_kisys_status = $checkbox_count_kisys_status + 1;
          // Kompira連携成功
          } elseif ($kisys_status == '81'){
            $select_kisys_status = array_merge($select_kisys_status, [['kisys_status' =>'0,0']]);
            $select_kisys_status = array_merge($select_kisys_status, [['kisys_status' =>'50,0']]);
            $checkbox_count_kisys_status = $checkbox_count_kisys_status + 1;
          // Kompira連携失敗
          } elseif ($kisys_status == '82'){
            $select_kisys_status = array_merge($select_kisys_status, [['kisys_status' =>'0,1']]);
            $select_kisys_status = array_merge($select_kisys_status, [['kisys_status' =>'50,1']]);
            $checkbox_count_kisys_status = $checkbox_count_kisys_status + 1;
          }
        }
        */
        // 1つ以上チェックされているかつ、ボックスの数より少なければ検索条件に加える。
        $ALARM_STATUS_NAME     = Configure::read("ALARM_STATUS_NAME_FOR_CSV");
        if ($checkbox_count_alarm_status >=1 &&
            $checkbox_count_alarm_status < count($ALARM_STATUS_NAME)) {

                $query_gwEvents->where([ 'or' => $select_alarm_status ]);
        }
        // アラーム種別：syserror, sysnormal, info, secはCSV出力対象にふくめない
        $query_gwEvents->where([['GwEvents.alarm_status is not' =>'syserror']]);
        $query_gwEvents->where([['GwEvents.alarm_status is not' =>'sysnormal']]);
        $query_gwEvents->where([['GwEvents.alarm_status is not' =>'info']]);
        $query_gwEvents->where([['GwEvents.alarm_status is not' =>'sec']]);
        /*
        $SEND_STATUS     = Configure::read("SEND_STATUS");
        if ($checkbox_count_kisys_status >=1 &&
            $checkbox_count_kisys_status < count($SEND_STATUS)) {

                $query_gwEvents->where([ 'or' => $select_kisys_status ]);
        }

        if ($filter_val['approve_status']=="1"){
            $gwRules_find = $this->_set_query_condition($query_gwEvents, 'GwEvents.checked_time' , '98'                   , ''); //未承認
        } elseif ($filter_val['approve_status']=="2"){
            $gwRules_find = $this->_set_query_condition($query_gwEvents, 'GwEvents.checked_time' , '99'                   , ''); //承認済み
        }
        */
        // 運用者ごとの顧客表示制御対応
        $usrgrp_names = $this->getRequest()->getSession()->read('usrgrp_names');
        $customer_names = $this->getRequest()->getSession()->read('customer_names');
        $account_type = $this->getRequest()->getSession()->read('account_type');
        // ハウコム運用者はハウコム顧客のみを検索
        if (in_array(Configure::read("HOWCOM_USER_GROUP"), $usrgrp_names)) {
            if ($customer_names) {
                $query_gwEvents = $this->_set_query_condition($query_gwEvents, 'GwEvents.customer_name' , '15', $customer_names);
            } else {
                $query_gwEvents = $this->_set_query_condition($query_gwEvents, 'GwEvents.customer_name' , '15', '存在しない顧客名');
            }
        // Zabbix特権管理者かつ全顧客検索ユーザー以外は他の運用者の顧客以外を検索
        } elseif ($account_type != 3 && !array_intersect($usrgrp_names, Configure::read("ALL_SEARCH_USER_GROUPS"))) {
            $not_perfect=[];
            foreach (InputSetHelper::explode(',', $customer_names) as $customer_name){
                if (trim($customer_name)){
                    array_push($not_perfect, ['GwEvents.customer_name !=' => trim($customer_name)]);
                }
            }
            if ($not_perfect) {
                $query_gwEvents->where(['and'=>$not_perfect]);
            }
        }

        $query_gwEvents = $this->_set_query_condition($query_gwEvents, 'GwEvents.customer_name' , $filter_val['customer_name_operetor'] , $filter_val['customer_name']);
        // $query_gwEvents = $this->_set_query_condition($query_gwEvents, 'GwEvents.hostname' , $filter_val['hostname_operetor'] , $filter_val['hostname']);
        // $query_gwEvents = $this->_set_query_condition($query_gwEvents, 'GwEvents.ci_name' , $filter_val['ci_name_operetor'] , $filter_val['ci_name']);
        // $query_gwEvents = $this->_set_query_condition($query_gwEvents, 'GwEvents.device' , $filter_val['device_operetor'] , $filter_val['device']);
        // $query_gwEvents = $this->_set_query_condition($query_gwEvents, 'GwEvents.summary' , $filter_val['summary_operetor'] , $filter_val['summary']);
        // $query_gwEvents = $this->_set_query_condition($query_gwEvents, 'GwEvents.op_comment' , $filter_val['op_comment_operetor'] , $filter_val['op_comment']);
        // $query_gwEvents = $this->_set_query_condition($query_gwEvents, 'GwIncidents.kisys_incidentid' , $filter_val['incidentid_operetor'] , $filter_val['incidentid']);

        return $query_gwEvents;
    }

        /**
     * [検索条件設定関数]
     * @param object $query_gwEvents  クエリ
     * @param string $field           カラム名
     * @param string $operetor        検索パターン
     * @param string $operands        検索値
     * @return object $query_gwEvents クエリ
     */
    function _set_query_condition($query_gwEvents, $field, $operetor, $operands){

        //検索値が無いか、Null検索でない場合は、検索条件を追加しない
        if ($operands=='' && $operetor!='98' && $operetor!='99'){
            return $query_gwEvents;
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
            $query_gwEvents->where(['or'=>$like]);

        } elseif($operetor=='14'){
            $not_like=[];
            foreach ($a_operands as $operand){
                if (InputSetHelper::mb_strlen(trim($operand)) > 0){
                    array_push($not_like, [$field . ' ' . $query_operator => '%' .trim($operand) . '%']);
                }
            }
            $query_gwEvents->where(['and'=>$not_like]);

        } elseif ($operetor=='98'){
            $query_gwEvents->where(['or'=>[
                                          [$field . ' ' . $query_operator => ""],
                                          [$field . ' ' . $query_operator => NULL]
                                      ]
                                ]);

        } elseif ($operetor=='99'){
            $query_gwEvents->where(['and'=>[
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
            $query_gwEvents->where(['or'=>$perfect]);

        }

        return $query_gwEvents;
    }

}

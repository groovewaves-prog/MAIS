<?php
namespace App\View\Helper;


use Cake\View\Helper;
use Cake\Core\Configure;

use Cake\Log\Log;

class InputSetHelper extends Helper{

    public $helpers = ['Html','Form','Paginator', 'Text'];

    const TEXTAREA  = ['type'=>'textarea',
                        'wrap'=>'on',
                        'rows'=>'1',
                        'maxlength' => 1000,
                        'label' => ['style'=> 'cursor:text;'],
                        ];


    const SELECT_DISP  = ['type'=>'select',
                             'label'=>false,
                             'div'=>false,
                            //  'options' => ['5'=>'5件表示','10'=>'10件表示', '20'=>'20件表示', '50'=>'50件表示', '100'=>'100件表示',
                                            // '200'=>'200件表示', '500'=>'500件表示', '1000'=>'1000件表示'],
                             'onchange'=> 'this.form.submit(""); value="search"',
                             'style'   => 'display:inline',
                             'class'=>'selectbox',
                            ];

    const SELECT_NUM = ['type'=>'select',
                        'selected'=> '1',
                        'label' => ['style'=> 'cursor:text;'],
                        // 'options'=>['23'=>'完全一致', '24'=>'以上', '25'=>'以下'],
                        'class'=>'selectbox',
                        ];

    const SELECT_DATE = ['type'=>'select',
                        'selected'=> '1',
                        'label' => ['style'=> 'cursor:text;'],
                        // 'options'=>['24'=>'以降', '25'=>'以前', '23'=>'完全一致'],
                        'class'=>'selectbox',
                        ];

    const SELECT_STR = ['type'=>'select',
                        'selected'=> '1',
                        'label' => ['style'=> 'cursor:text;'],
                        // 'options'=>['13'=>'を含む', '14'=>'を含まない', '15'=>'完全一致', '98'=>'空白セル', '99'=>'非空白セル'],
                        'class'=>'selectbox',
                        ];

// ======================================================================================================================================================
    public function index(array $config) {
        parent::initial($config);
    }

// ======================================================================================================================================================
    public function selectdispCount($id, $display_count) {

        $return_html = "";

        $options = ['5'=>__('Display {0} records','5'),     '10'=>__('Display {0} records','10'),
                    '20'=>__('Display {0} records','20'),   '50'=>__('Display {0} records','50'),
                    '100'=>__('Display {0} records','100'), '200'=>__('Display {0} records','200'),
                    '500'=>__('Display {0} records','500'), '1000'=>__('Display {0} records','1000')];
        $select_options=$this::SELECT_DISP;
        $select_options['options'] = $options;

        $operand_settings = array_merge($select_options, ['name'=>$id, 'id'=>$id, 'value'=>$display_count ]);
        $return_html= $this->Form->input($id,$operand_settings);

        return $return_html;
    }
// ======================================================================================================================================================
    public function txtBx($operand_id, $operand_init_val, $opertor_init_val, $val_type,
                            $select_url=null, $select_model=null, $select_column=null) {

        $btn_color = 'btn_blue';
        $operetor_id = $operand_id . '_operetor';

        if ($val_type == "num"){
            $select_options = $this::SELECT_NUM;
            $options = ['23'=>__('equal'), '24'=>__('less than or equal to'), '25'=>__('greater than or equal to')];
            $select_options['options'] = $options;

        } elseif ($val_type == "date"){
            $select_options = $this::SELECT_DATE;
            $options = ['24'=>__('after'), '25'=>__('before'), '23'=>__('equal')];
            $select_options['options'] = $options;
        } elseif ($val_type == "str"){
            $select_options = $this::SELECT_STR;
            $options = ['13'=>__('include'), '14'=>__('not include'), '15'=>__('equal'), '98'=>__('blank'), '99'=>__('not blank')];
            $select_options['options'] = $options;
            $select_options['onChange'] = 'disable_operetor("#' . $operetor_id . '", "#' . $operand_id . '")';
        }

        $operand_settings  = array_merge($this::TEXTAREA, ['name'=>$operand_id,  'id'=>$operand_id,  'value'=>$operand_init_val]);
        $operetor_settings = array_merge($select_options, ['name'=>$operetor_id, 'id'=>$operetor_id, 'value'=>$opertor_init_val]);
        $operetor_initial_key = key($select_options['options']);

        $return_html = __($operand_id);
        if($select_url && $select_model && $select_column){
            $return_html .= ' ' . $this->Html->link( __('Select') ,'javascript:void(0)', ['class'=>$btn_color, 'onClick'=>'openWindowSelect("' . $select_url . '" , "' . $select_model . '", "' . $select_column . '");return false;']);
        }
        $return_html .= $this->Form->input('', $operand_settings);
        $return_html .= $this->Form->input('', $operetor_settings);
        $return_html .= $this->Html->link( __('Clear') ,'javascript:void(0)', ['class'=>$btn_color,
            'onClick'=>'del_text("' . $operand_id . '");
                        del_select("' . $operetor_id . '","' . $operetor_initial_key . '");
                        disable_operetor("#' . $operetor_id . '", "#' . $operand_id . '");
                        return false;'
                        ]);

        return $return_html;

    }

// ======================================================================================================================================================
    public function dtFromTo($operand_id, $operand_from_init_val, $operand_to_init_val, $from_label=null, $to_label=null) {

        $btn_color = 'btn_blue';

        $operetor_from_id = $operand_id . '_from';
        $operetor_to_id   = $operand_id . '_to';

        $operand_from_settings = array_merge($this::TEXTAREA, ['class'=>'datetimepicker', 'name'=>$operetor_from_id, 'id'=>$operetor_from_id, 'value'=>$operand_from_init_val]);
        $operand_to_settings   = array_merge($this::TEXTAREA, ['class'=>'datetimepicker', 'name'=>$operetor_to_id,   'id'=>$operetor_to_id,   'value'=>$operand_to_init_val]);

        $return_html  = $this->Form->control($from_label, $operand_from_settings);
        $return_html .= $this->Form->control($to_label, $operand_to_settings);
        $return_html .= $this->Html->link( __('Clear') ,'javascript:void(0)', ['class'=>$btn_color, 'onClick'=>'del_text("' . $operetor_from_id . '"); del_text("' . $operetor_to_id . '");return false;']);
        return $return_html;
    }

// ======================================================================================================================================================
    public function chkBxGrpHideBtn($col_name, $CHECKBOX_NO, $checked_values) {

        $btn_color = 'btn_yellow';
        $all_check_id = 'all_check_' . $col_name;

        $js_onClicks = 'all_checking("' . $col_name . '", this.checked);';
        foreach ($CHECKBOX_NO as $key => $val){
            $js_onClicks .= 'hideColumn(".col_' . $key . '", this.checked);';
        }

        // $return_html  = __($col_name);
        // $return_html = '<td colspan="' . count($CHECKBOX_NO) . '">' . $this::chkBx($all_check_id, '', $all_check_id, '', 1,
        //                                         $js_onClicks, $btn_color);
        // $return_html .= '</td><tr>';
        $return_html = '';

        //生成するチェックボックスのcheked の総合値 を調べる
        //cheked の総合値 == すべてのチェックが外れている
        $total_checked=0;
        foreach ($CHECKBOX_NO as $key => $val){
            // $checked_valuesに keyと同じ値があればcheckあり
            $checked =0;
            if (in_array($key, $checked_values)) {
                $checked = 1;
            }
            $total_checked = $total_checked + $checked;
        }

        //チェックボックスを生成する
        foreach ($CHECKBOX_NO as $key => $val){

            // $checked_valuesに keyと同じ値があればcheckあり
            $checked =0;
            if (in_array($key, $checked_values)) {
                $checked = 1;
            }

            $chkbx_id  = $col_name . "[]" . "_" . $key;
            $get_name  = $col_name . "[]";
            $get_value = $key;
            $classes   = $col_name;
            if ($total_checked==0){
                //すべてのチェックが外れている場合は、すべてチェックする
                $checked = 1;
            }

            if ($key == "detail_event") {
                $return_html .= '<td colspan="2">';
            } else {
                $return_html .= '<td>';
            }
            $return_html .= $this::chkBx($chkbx_id,
                                         $classes,
                                         $get_name,
                                         $get_value,
                                         $checked,
                                         'hideColumn(".col_' . $key . '", this.checked)',
                                         'chkbx_col_' . $key,
                                         'highlight_on("#disp_col_' . $key . '_label",  ".col_' . $key . '");'
                                         . 'highlight_on("#disp_col_' . $key . '_label",  ".chkbx_col_' . $key . '");',
                                         'highlight_off("#disp_col_' . $key . '_label", ".col_' . $key . '");'
                                         . 'highlight_off("#disp_col_' . $key . '_label", ".chkbx_col_' . $key . '");') . '</td>';
        }

        return $return_html . '</tr>';

    }

// ======================================================================================================================================================
    public function chkBxGrp($col_name, $CHECKBOX_NO, $checked_values) {

        $btn_color = 'btn_yellow';
        $all_check_id = 'all_check_' . $col_name;

        $return_html  = __($col_name);
        $return_html .= $this::chkBx($all_check_id, '', $all_check_id, '', 1,
                                        'all_checking("' . $col_name . '", this.checked);', $btn_color);

        //生成するチェックボックスのcheked の総合値 を調べる
        //cheked の総合値 == すべてのチェックが外れている
        $total_checked=0;
        foreach ($CHECKBOX_NO as $key => $val){
            // $checked_valuesに keyと同じ値があればcheckあり
            $checked =0;
            if (in_array($key, $checked_values)) {
                $checked = 1;
            }
            $total_checked = $total_checked + $checked;
        }

        //チェックボックスを生成する
        foreach ($CHECKBOX_NO as $key => $val){

            // $checked_valuesに keyと同じ値があればcheckあり
            $checked =0;
            if (in_array($key, $checked_values)) {
                $checked = 1;
            }

            $chkbx_id  = $col_name . "[]" . "_" . $key;
            $get_name  = $col_name . "[]";
            $get_value = $key;
            $classes   = $col_name;
            if ($total_checked==0){
                //すべてのチェックが外れている場合は、すべてチェックする
                $return_html .= $this::chkBx($chkbx_id, $classes, $get_name, $get_value, 1);
            } else {
                $return_html .= $this::chkBx($chkbx_id, $classes, $get_name, $get_value, $checked);
            }
        }

        return $return_html;

    }

// ======================================================================================================================================================
    public function chkBx($chkbx_id, $classes, $get_name, $get_value, $checked, $onClick=null,
    						$label_class=null, $onMouseOver=null, $onMouseOut=null) {

        $label_id = $chkbx_id . '_label';

        $return_html = $this->Form->control('check',
                                            ['type'    =>'checkbox',
                                             'label'   => __($chkbx_id),
                                             'id'      => $chkbx_id,
                                             'name'    => $get_name,
                                             'value'   => $get_value,
                                             'checked' => $checked,
                                             'class'   => $classes,
                                             'onClick' => $onClick,
                                             'label'   => ['text'        =>__($chkbx_id),
                                                           'id'          => $label_id,
                                                           'class'       => $label_class,
                                                           'onMouseOver' => $onMouseOver,
                                                           'onMouseOut'  => $onMouseOut,
                                                          ]
                                            ]
                                         );
        return $return_html;
    }

// ======================================================================================================================================================
    public function radioBtns($operand_id, $operand_init_val, $option_words) {

        $i=1;
        $options=[];
        foreach ($option_words as $key => $val){
            array_push($options, ['text'=>$val, 'value'=>$i]);
            $i++;
        }

        $return_html = $this->Form->control( __($operand_id), [
                             'legend' => false,
                             'name' => $operand_id,
                             'type' => 'radio',
                             'value' => $operand_init_val,
                             'label' => ['style'=> 'cursor:text;'],
                             'options' => $options
                            ]);
        return $return_html;
    }

// ======================================================================================================================================================
    public function actionButtons() {
        $btn = 'btn_brown';

        $return_html  = __('Actions') . "<br>";

        // 二重送信防止Disable処理時の Button GET送信用 hidden
        $return_html .= $this::hiddens([['submit_action'=>"search"]]);

        $return_html .= $this->Form->button(__('search'),['name'=>'submit_action',
                                                          'value'=>'search',
                                                          'class'=>$btn . ' js-submit',
                                                          'onClick'=>"$('#submit_action').val('search');"]) . "<br>";
        $return_html .= $this->Form->button(__('reset'), ['name'=>'submit_action',
                                                          'value'=>'reset',
                                                          'class'=>$btn . ' js-submit',
                                                          'onClick'=>"$('#submit_action').val('reset');"]);
        return $return_html;

    }

// ======================================================================================================================================================
    // exsample [['filter_form_opened'=>$filter_form_opened], ...]
    public function hiddens($ids_init_vals) {

        $return_html ="";
            foreach ($ids_init_vals as $key => $name){
                $id        = key($name);
                $init_vals = $name[$id];
                // var_dump($id . $init_vals);
                $return_html .= $this->Form->hidden($id,['value'=>$init_vals, 'id' => $id]);
            }

        return $return_html;
    }

// ======================================================================================================================================================
    public function pagenator() {

        $return_html = '</br><div class="paginator"> <ul class="pagination" style="display:inline">';
        $return_html .= $this->Paginator->first('<< ' . __('first'));
        $return_html .= $this->Paginator->prev('< ' . __('previous'));
        $return_html .= $this->Paginator->numbers();
        $return_html .= $this->Paginator->next(__('next') . ' >');
        $return_html .= $this->Paginator->last(__('last') . ' >>');
        $return_html .= '</ul><p class="right">';
        $return_html .= $this->Paginator->counter(__('Page {{page}} of {{pages}}, showing {{current}} record(s) out of {{count}} total'));
        $return_html .= '</p></div>';
        return $return_html;

    }

// ======================================================================================================================================================
    public function genShortMsg($msg, $length) {

        $short_msg="";
        if (InputSetHelper::mb_strlen($msg) > $length){
          $short_msg = InputSetHelper::str_replace("\n", "<br>", mb_substr($msg, 0, $length)) . " ... ";
        } else {
          $short_msg=InputSetHelper::str_replace("\n", "<br>", $msg);
        }
        return $short_msg;
    }
// ======================================================================================================================================================
    public function newFlag($now_time_jst, $alarm_time_jst, $checked ,$less_than_d, $less_than_h) {

        $css_class = 'flag_new';

        $interval = $now_time_jst->diff($alarm_time_jst);

        if($checked ==null
            && ($interval->format('%a')==$less_than_d && $interval->format('%h')<$less_than_h)) {

            $return_html='<span style="display: inline-block;" class="' . $css_class . '"> New</span>';

        }else {
            $return_html='';
        }

        return $return_html;
    }

    // ======================================================================================================================================================
        public function kisysUrl($kisys_status) {
            $return_html ="";
            if (preg_match("/^INC[0-9]{12}$/", $kisys_status)) {
              $KISYS_URL = Configure::read("KISYS_URL_OLD");
              $IP_ADRESS = Configure::read("KVN_IP_OLD");
              // $IP_ADRESS = Configure::read("KIDS_IP");

              $KISYS_URL = __($KISYS_URL, $IP_ADRESS, $kisys_status);
              // $return_html = $this->Html->link( $kisys_status, '#', ['class'=>'link_style', 'onClick'=>'openWindowKisys("' . $KISYS_URL . '")']);
              $return_html = $this->Html->link( $kisys_status, 'javascript:void(0)', ['class'=>'link_style', 'onClick'=>'window.open("' . $KISYS_URL . '", "kisys_url");return false;']);
            } else {
              $return_html = $kisys_status;
            }

            return $return_html;
        }

// ======================================================================================================================================================
    public function sendStatusUrl($error_send_status, $normal_send_status, $kisys_incidentid, $class) {
        $return_html ='';
        if (is_null($error_send_status) && is_null($normal_send_status)) {
            return $return_html;
        }

        $error_status_code = is_null($error_send_status) ? '' : InputSetHelper::explode(',', $error_send_status)[0];
        $normal_status_code = is_null($normal_send_status) ? '' : InputSetHelper::explode(',', $normal_send_status)[0];
        $KISYS_SEND_SUCCESS_STATUS_CODE = ['0', '40', '50', '60', '70'];
        $send_error_success = in_array($error_status_code, $KISYS_SEND_SUCCESS_STATUS_CODE);
        $send_normal_success = in_array($normal_status_code, $KISYS_SEND_SUCCESS_STATUS_CODE);
        $KISYS_SENDING_STATUS_CODE = ['9', '49', '59', '69', '79'];
        $sending_normal = in_array($normal_status_code, $KISYS_SENDING_STATUS_CODE);

        $ERROR_KISYS_HTML = $this->sendStatusKisysUrl($error_send_status, $kisys_incidentid, $class, 'error');
        $NORMAL_KISYS_HTML = $this->sendStatusKisysUrl($normal_send_status, $kisys_incidentid, $class, 'normal');
        if ($send_normal_success) { // 単発復旧成功 or 障害復旧両方成功
            $KOMPIRA_HTML = $this->sendStatusKompiraUrl($normal_send_status, $kisys_incidentid, $class);
            $return_html = $NORMAL_KISYS_HTML . '<br>' . $KOMPIRA_HTML;
        } elseif (!$send_error_success) {
            if (is_null($error_send_status)) { // 単発復旧失敗
                $return_html = $NORMAL_KISYS_HTML;
            } else {
                if ($sending_normal) { // 障害復旧で障害復旧起票待ち or 障害復旧で障害失敗復旧起票待ち
                    $return_html = $ERROR_KISYS_HTML . '<br>' . $NORMAL_KISYS_HTML;
                } else { // 単発障害失敗 or 障害復旧で障害失敗
                    $return_html = $ERROR_KISYS_HTML;
                }
            }
        } else {
            if (is_null($normal_send_status)) { // 単発障害成功
                $KOMPIRA_HTML = $this->sendStatusKompiraUrl($error_send_status, $kisys_incidentid, $class);
                $return_html = $ERROR_KISYS_HTML . '<br>' . $KOMPIRA_HTML;
            } else { // 障害復旧で障害成功復旧失敗 or 障害復旧で障害成功復旧起票待ち
                $return_html = $ERROR_KISYS_HTML . '<br>' . $NORMAL_KISYS_HTML;
            }
        }
        return $return_html;
    }

// ======================================================================================================================================================
    public function sendStatusKisysUrl($send_status, $kisys_incidentid, $class, $alarm_status) {
        $KISYS_HTML ='';
        if (is_null($send_status)) {
            return $KISYS_HTML;
        }
        $KISYS_SEND_STATUS = Configure::read("KISYS_SEND_STATUS");
        $status_code = InputSetHelper::explode(',', $send_status);
        if (count($status_code) > 0 && array_key_exists($status_code[0], $KISYS_SEND_STATUS)) {
            $KISYS_HTML = $KISYS_SEND_STATUS[$status_code[0]];
            $KISYS_SEND_SUCCESS_STATUS_CODE = ['0', '40', '50', '60', '70'];
            $KISYS_SEND_FAILURE_BY_ALARM_STATUS = Configure::read("KISYS_SEND_FAILURE_BY_ALARM_STATUS");
            if (!is_null($kisys_incidentid) && in_array($status_code[0], $KISYS_SEND_SUCCESS_STATUS_CODE)) {
                if (preg_match("/INC[0-9]{12}/", $kisys_incidentid)) {
                    $KISYS_URL = __(Configure::read("KISYS_URL_OLD"), Configure::read("KVN_IP_OLD"), $kisys_incidentid);
                    $KISYS_HTML = $KISYS_HTML . $this->Html->link($kisys_incidentid, 'javascript:void(0)', ['class' => $class, 'onClick' => 'window.open("' . $KISYS_URL . '", "kisys_url");return false;']);
                } elseif (preg_match("/IT[0-9]{4}\-[0-9]{8}/", $kisys_incidentid)) {
                    $KISYS_URL = __(Configure::read("KISYS_URL"), Configure::read("KVN_IP"), $kisys_incidentid);
                    $KISYS_HTML = $KISYS_HTML . $this->Html->link($kisys_incidentid, 'javascript:void(0)', ['class' => $class, 'onClick' => 'window.open("' . $KISYS_URL . '", "kisys_url");return false;']);
                }
            } elseif (array_key_exists($status_code[0], $KISYS_SEND_FAILURE_BY_ALARM_STATUS[$alarm_status])) {
                $KISYS_HTML = $KISYS_SEND_FAILURE_BY_ALARM_STATUS[$alarm_status][$status_code[0]];
            }
        } else {
            // 送信状況をコード化する前のデータ表示用
            $KISYS_HTML = $this->kisysUrl($send_status);
        }
        return $KISYS_HTML;
    }

// ======================================================================================================================================================
    public function sendStatusKompiraUrl($send_status, $kisys_incidentid, $class) {
        $KOMPIRA_HTML ='';
        if (is_null($send_status)) {
            return $KOMPIRA_HTML;
        }
        $status_code = InputSetHelper::explode(',', $send_status);
        if (count($status_code) > 1) {
            if (!is_null($kisys_incidentid) && $status_code[1] == '0') {
                $KOMPIRA_SEND_SUCCESS = Configure::read("KOMPIRA_SEND_SUCCESS");
                $KOMPIRA_URL = Configure::read("KOMPIRA_URL");
                $KOMPIRA_IP = Configure::read("KOMPIRA_IP");
                $KOMPIRA_URL = __($KOMPIRA_URL, $KOMPIRA_IP, $kisys_incidentid);
                $KOMPIRA_HTML = $this->Html->link($KOMPIRA_SEND_SUCCESS, 'javascript:void(0)', ['class'=>"' . $class . '", 'onClick'=>'window.open("' . $KOMPIRA_URL . '", "kompira_url");return false;']);
            } elseif ($status_code[1] == '80') {
                $KOMPIRA_NOSEND = Configure::read("KOMPIRA_NOSEND");
                $KOMPIRA_HTML = $KOMPIRA_NOSEND;
            } else {
                $KOMPIRA_SEND_FAILURE = Configure::read("KOMPIRA_SEND_FAILURE");
                $KOMPIRA_HTML = $KOMPIRA_SEND_FAILURE;
            }
        }
        return $KOMPIRA_HTML;
    }

    // mb_strlenのラッパーメソッド
    // 　第一引数にnullが指定された場合、0を返すようにした
    public static function mb_strlen(?string $string, ?string $encoding = null): int {
        if ($string === null) {
            return 0;
        } else {
            return mb_strlen($string, $encoding);
        }
    }

    // str_replaceのラッパーメソッド
    // 　第三引数にnullが指定された場合、''として処理するようにした
    public static function str_replace(
        array|string $search,
        arrra|string $replace,
        string|array|null $subject,
        int &$count = null) : string|array { 

        $wk_subject = $subject;

        if ($wk_subject === null) {
            $wk_subject = '';
        }

        return str_replace($search, $replace, $wk_subject, $count);
    }

    // explodeのラッパーメソッド
    // 　第二引数にnullが指定された場合、''として処理するようにした
    public static function explode(
        string $separator,
        string|null $string,
        int $limit = PHP_INT_MAX) {

        $wk_string = $string;
        if ($wk_string == null) {
            $wk_string = '';
        }

        return explode($separator, $wk_string, $limit);
    }
}

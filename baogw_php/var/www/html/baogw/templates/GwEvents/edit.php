<?php
use App\View\Helper\InputSetHelper;
?>
<?php
    $col_event_id = '';
    $col_customer_ci = '';
    $col_device = '';
    $approve_bg = '';
    if (!is_null($error_event) and !is_null($normal_event)) {
        $col_event_id = $error_event->gw_event_id;
        $col_customer_ci = $error_event->customer_ci;
        $col_device = $error_event->device;
        if (!is_null($normal_event->checked_time)) {
            $approve_bg = 'row_color_approved';
        }
    } else if (!is_null($error_event)) {
        $col_event_id = $error_event->gw_event_id;
        $col_customer_ci = $error_event->customer_ci;
        $col_device = $error_event->device;
        if (!is_null($error_event->checked_time)) {
            $approve_bg = 'row_color_approved';
        }
    } else if (!is_null($normal_event)) {
        $col_event_id = $normal_event->gw_event_id;
        $col_customer_ci = $normal_event->customer_ci;
        $col_device = $normal_event->device;
        if (!is_null($normal_event->checked_time)) {
            $approve_bg = 'row_color_approved';
        }
    }
?>

<div class="gwEvents form large-12 medium-12 columns content width_inherit" id="main_content">
    <h3><div class="navi_reffer"><?= $this->Html->link(__('Main Menu'), ['controller'=>'mainMenu','action' => 'index']) ?></div> >
        <div class="navi_reffer"><?= $this->Html->link(__('Gw Events'), $indexUrl ) ?></div>
        <div class="navi_current"><?=  ' > '. __('イベント詳細')?></div></h3>

    <fieldset>
        <legend><?= __('イベントID：') . $col_event_id  . ' ' . __('イベント詳細');   ?>
            <?php
            $now_time = new DateTime();
            $alarm_time = null;
            $checked_time = null;
            if (!is_null($normal_event)) {
                $alarm_time = new DateTime($normal_event->alarm_time->format('Y/m/d H:i:s'));
                $checked_time = $normal_event->checked_time;
            } else if (!is_null($error_event)) {
                $alarm_time = new DateTime($error_event->alarm_time->format('Y/m/d H:i:s'));
                $checked_time = $error_event->checked_time;
            }
            ?>
            <?= $newflag=$this->InputSet->newFlag($now_time, $alarm_time, $checked_time, $FLAG_NEW_DAY, $FLAG_NEW_HOUR); ?>
        </legend>
        <table class="edit-table">
            <tr>
                <th scope="row"><?= __('error_event_id') ?></th>
                <th scope="row"><?= __('normal_event_id') ?></th>
                <th scope="row"><?= __('alarm_time_error') ?></th>
                <th scope="row"><?= __('Error Detected Time') ?></th>
                <th scope="row"><?= __('alarm_time_normal') ?></th>
                <th scope="row"><?= __('Normal Detected Time') ?></th>
                <th scope="row"><?= __('Detected Host') ?></th>
            </tr>
            <tr>
                <td><?php if(!is_null($error_event)) {
                    echo h($error_event->gw_event_id);
                } ?>
                    <!-- ハウコムフラグ -->
                    <?php
                        if(($account_type == 3 || array_intersect($usrgrp_names, $all_search_user_groups)) && in_array($gwIncident->customer_name, $howcom_names)){
                            echo '<span style="display: inline-block;" class="flag_howcom">' . $KDDI_MIYAZAKI . '</span>';
                        }
                    ?>
                    <!-- VIPフラグ -->
                    <?php
                        if(in_array($gwIncident->customer_name, $vip_names)){
                            echo '<span style="display: inline-block;" class="flag_jp1">JP1</span>';
                        }
                    ?>
                </td>
                <td><?php if(!is_null($normal_event)) {
                    echo h($normal_event->gw_event_id);
                } ?>
                    <!-- ハウコムフラグ -->
                    <?php
                        if(($account_type == 3 || array_intersect($usrgrp_names, $all_search_user_groups)) && in_array($gwIncident->customer_name, $howcom_names)){
                            echo '<span style="display: inline-block;" class="flag_howcom">' . $KDDI_MIYAZAKI . '</span>';
                        }
                    ?>
                    <!-- VIPフラグ -->
                    <?php
                        if(in_array($gwIncident->customer_name, $vip_names)){
                            echo '<span style="display: inline-block;" class="flag_jp1">JP1</span>';
                        }
                    ?>
                </td>
                <td><?php if(!is_null($error_event)) {
                    echo $error_event->alarm_time->format('Y/m/d H:i:s');
                } ?></td>
                <td><?php if(!is_null($error_event)) {
                    echo $error_event->detected_time->format('Y/m/d H:i:s');
                } ?></td>
                <td><?php if(!is_null($normal_event)) {
                    echo $normal_event->alarm_time->format('Y/m/d H:i:s');
                } ?></td>
                <td><?php if(!is_null($normal_event)) {
                    echo $normal_event->detected_time->format('Y/m/d H:i:s');
                } ?></td>
                <td><?= $this->Number->format($gwIncident->detected_host) ?></td>

            </tr>
            <tr>
                <th scope="row" colspan="2"><?= __('Customer Name') ?></th>
                <th scope="row" colspan="2"><?= __('Hostname') ?></th>
                <th scope="row" colspan="2"><?= __('Ci Name') ?></th>
                <th scope="row"><?= __('device') ?></th>
            </tr>
            <tr>
                <?php if($col_customer_ci=="OPSUPPSYS"): ?>
                    <td colspan="2"><?= h($gwIncident->customer_name) ?></td>
                <?php else: ?>
                    <td colspan="2">
                        <?= $this->Html->link($gwIncident->customer_name, "javascript:void(0)", ["onClick"=>"openWindowCMDB('".$CMDB_WEB_URL."','customer_name','".$col_customer_ci."','');return false;"]); ?>
                    </td>
                <?php endif; ?>
                <?php if($col_customer_ci=="OPSUPPSYS"): ?>
                    <td colspan="2"><?= h($gwIncident->hostname) ?></td>
                <?php else: ?>
                    <td colspan="2">
                        <?= $this->Html->link($gwIncident->hostname, "javascript:void(0)", ["onClick"=>"openWindowCMDB('".$CMDB_WEB_URL."','hostname','".$col_customer_ci."','".$gwIncident->hostname."');return false;"]); ?>
                    </td>
                <?php endif; ?>
                <td colspan="2"><?= h($gwIncident->ci_name) ?></td>
                <?php if($col_customer_ci=="OPSUPPSYS"): ?>
                    <td><?= h($col_device) ?></td>
                <?php else: ?>
                    <td>
                        <?= $this->Html->link($col_device, "javascript:void(0)", ["onClick"=>"openWindowCMDB('".$CMDB_WEB_URL."','device','".$col_customer_ci."','".$gwIncident->hostname."');return false;"]); ?>
                    </td>
                <?php endif; ?>
            </tr>
            <tr>
                <th scope="row" colspan="7"><?= __('Summary Error') ?></th>
            </tr>
            <tr>
                <td colspan="7"><?php if(!is_null($error_event)) {
                    echo h($error_event->summary);
                } ?></td>
            </tr>
            <tr>
                <th scope="row" colspan="7"><?= __('Summary Normal') ?></th>
            </tr>
            <tr>
                <td colspan="7"><?php if(!is_null($normal_event)) {
                    echo h($normal_event->summary);
                } ?></td>
            </tr>
        </table>
    </fieldset>


    <?= $this->Form->create(null, ['onsubmit'=>'return confirm_save(' . $gwIncident . ',' . $error_event . ',' . $normal_event . ');']) ?>
    <fieldset>
        <legend><?= __('イベントID：') . $col_event_id  . ' ' . __('Edit Gw Event');   ?></legend>
        <table class="edit-table">
            <tr>
                <th></th>
                <th scope="row" colspan="1"><?= __('Check Error') ?></th>
                <th scope="row" colspan="1"><?= __('Check Normal') ?></th>
                <th scope="row" colspan="1"><?= __('Update Op Comment') ?></th>
                <th scope="row" colspan="4"><?= __('Op Comment') ?></th>
            </tr>
            <tr>
                <td><?= __('Date And Time') ?></td>
                <td class="<?= $approve_bg ?>" colspan="1"><?php if(!is_null($error_event) and !is_null($error_event->checked_time)) {
                    echo h($error_event->checked_time->format('Y/m/d H:i:s'));
                } ?></td>
                <td class="<?= $approve_bg ?>" colspan="1"><?php if(!is_null($normal_event) and !is_null($normal_event->checked_time)) {
                    echo h($normal_event->checked_time->format('Y/m/d H:i:s'));
                } ?></td>
                <td class="<?= $approve_bg ?>" colspan="1"><?php if(!is_null($gwIncident->update_user)) {
                    echo h($gwIncident->update_time->format('Y/m/d H:i:s'));
                } ?></td>
                <td colspan="4" rowspan="2"><?php echo InputSetHelper::str_replace("\n", '<br>', h($gwIncident->op_comment)); ?></td>
            </tr>
            <tr>
                <td><?= __('User') ?></td>
                <td class="<?= $approve_bg ?>" colspan="1"><?php if(!is_null($error_event)) {
                    echo h($error_event->checked_user);
                } ?></td>
                <td class="<?= $approve_bg ?>" colspan="1"><?php if(!is_null($normal_event)) {
                    echo h($normal_event->checked_user);
                } ?></td>
                <td class="<?= $approve_bg ?>" colspan="1"><?php if(!is_null($gwIncident->update_user)) {
                    echo h($gwIncident->update_user);
                } ?></td>
            </tr>
            <tr>
                <td colspan="3">
                  <?= $this->Form->input( __('Approve Edit'), array(
                                           'legend' => false,
                                           'name' => 'CheckedTime',
                                           'type' => 'radio',
                                           'value' => "",
                                           'label' => array('style'=> 'cursor:text;'),
                                           'options' => [
                                             ['text'=>__('変更しない'),'value'=>""],
                                             ['text'=>__('承認する'),'value'=>1],
                                             ['text'=>__('承認解除'),'value'=>2]
                                           ],
                                           'id' =>'Checked_time'

                  ));?>
                </td>
                <td colspan="4">
                  <div class="inline">現在 </div><div id="op_comment_str_count" class="inline"></div><div class="inline">文字記入されています。 512文字まで入力できます。</div>
                  <?= $this->Html->link( __('PIC') ,'javascript:void(0)', ['class'=>'btn_blue', 'onClick'=>'add_text("#op-comment", "' . $account_full_name . '");return false;']); ?>
                  <?php
                    echo $this->Form->control('op_comment',
                                              ['label' => ['style'=> 'cursor:text;'],
                                               'type'=>'textarea',
                                               'value'=>$gwIncident->op_comment,
                                               ]);
                  ?>
                </td>
                <td colspan="1"><div class="width_inherit"><?= $this->Form->button(__('Submit'),['class'=>'btn_brown']) ?></div></td>
            </tr>
        </table>
    </fiedlset>
    <?= $this->Form->end() ?>

    <fieldset>
        <legend><?= __('KISYS 起票');   ?></legend>
        <table class="edit-table-small">
            <tr><th></th><th><?= __('Error') ?></th><th><?= __('Normal') ?></th></tr>
            <tr><th scope="row"><?= __('Event Status') ?></th>
                <td><?php if(!is_null($error_event)) {
                    echo $this->Number->format($error_event->event_status);
                } ?></td>
                <td><?php if(!is_null($normal_event)) {
                    echo $this->Number->format($normal_event->event_status);
                } ?></td></tr>
            <tr><th scope="row"><?= __('Gw Incident Id') ?></th>
                <td colspan="2"><?= $gwIncident->gw_incident_id ?></td></tr>
            <tr><th scope="row"><?= __('Incident Status') ?></th>
                <td colspan="2"><?= $gwIncident->incident_status ?></td></tr>
            <tr><th scope="row"><?= __('Kisys Incidentid') ?></th>
                <td colspan="2"><?= $gwIncident->kisys_incidentid ?></td></tr>
            <tr><th scope="row"><?= __('Kisys Status') ?></th>
            <?php
                $not_show_send_button_event_status = [0, 99];
                $not_show_send_button_alarm_status = ['syserror', 'sysnormal', 'sec', 'info']; ?>
                <td><?php if(!is_null($error_event)) {
                    if (in_array($error_event->event_status, $not_show_send_button_event_status)) {
                        echo $this->InputSet->sendStatusKisysUrl(h($error_event->kisys_status), h($gwIncident->kisys_incidentid), 'link_style', 'error');
                    } else if (in_array($error_event->alarm_status, $not_show_send_button_alarm_status)) {
                        echo $this->InputSet->sendStatusKisysUrl(h($error_event->kisys_status), h($gwIncident->kisys_incidentid), 'link_style', 'error');
                    } else {
                        $not_show_send_button_kisys_status = ['9', '49', '59', '69', '79'];
                        $status_code = InputSetHelper::explode(',', h($error_event->kisys_status));
                        // error報自身がKISYS連携中かどうか
                        $has_been_send_kisys = (count($status_code) > 0 && in_array($status_code[0], $not_show_send_button_kisys_status));
                        if (!$has_been_send_kisys && InputSetHelper::mb_strlen($gwIncident->kisys_incidentid) == 0) {
                            echo $this->Html->link(__('Send Error'), array('action'=>'sendKisys', $error_event->gw_event_id), array('class'=>'btn_small_red', 'confirm'=>'K-ISYS起票する'));
                            echo '<br>';
                            echo $this->InputSet->sendStatusKisysUrl(h($error_event->kisys_status), h($gwIncident->kisys_incidentid), 'link_style', 'error');
                        } else {
                            echo $this->InputSet->sendStatusKisysUrl(h($error_event->kisys_status), h($gwIncident->kisys_incidentid), 'link_style', 'error');
                            echo '<br>';
                            echo $this->InputSet->sendStatusKompiraUrl(h($error_event->kisys_status), h($gwIncident->kisys_incidentid), 'link_style', 'error');
                        }
                    }
                }
                ?></td>
                <td><?php if(!is_null($normal_event)) {
                    if (in_array($normal_event->event_status, $not_show_send_button_event_status)) {
                        echo $this->InputSet->sendStatusKisysUrl(h($normal_event->kisys_status), h($gwIncident->kisys_incidentid), 'link_style', 'normal');
                    } else if (in_array($normal_event->alarm_status, $not_show_send_button_alarm_status)) {
                        echo $this->InputSet->sendStatusKisysUrl(h($normal_event->kisys_status), h($gwIncident->kisys_incidentid), 'link_style', 'normal');
                    } else {
                        if (InputSetHelper::mb_strlen($gwIncident->kisys_incidentid) == 0) {
                            echo $this->InputSet->sendStatusKisysUrl(h($normal_event->kisys_status), h($gwIncident->kisys_incidentid), 'link_style', 'normal');
                        } else {
                            $not_show_send_button_kisys_status = ['0', '40', '50', '60', '70', '9', '49', '59', '69', '79'];
                            $status_code = InputSetHelper::explode(',', h($normal_event->kisys_status));
                            // normal報自身がKISYS連携済み&連携中かどうか
                            $has_been_send_kisys = (count($status_code) > 0 && in_array($status_code[0], $not_show_send_button_kisys_status));
                            if ($has_been_send_kisys) {
                                echo $this->InputSet->sendStatusKisysUrl(h($normal_event->kisys_status), h($gwIncident->kisys_incidentid), 'link_style', 'normal');
                                echo '<br>';
                                echo $this->InputSet->sendStatusKompiraUrl(h($error_event->kisys_status), h($gwIncident->kisys_incidentid), 'link_style');
                            } else {
                                echo $this->Html->link(__('Update Normal'), array('action'=>'sendKisys', $normal_event->gw_event_id), array('class'=>'btn_green', 'confirm'=>'K-ISYS追記する'));
                                echo '<br>';
                                echo $this->InputSet->sendStatusKisysUrl(h($normal_event->kisys_status), h($gwIncident->kisys_incidentid), 'link_style', 'normal');
                            }
                        }
                    }
                } ?></td></tr>
            <tr><th scope="row" ><?= __('Update Time') ?></th>
                <td><?php if(!is_null($error_event)) {
                    echo $error_event->update_time->format('Y/m/d H:i:s');
                } ?></td>
                <td><?php if(!is_null($normal_event)) {
                    echo $normal_event->update_time->format('Y/m/d H:i:s');
                } ?></td></tr>
        </table>
    </fieldset>

</div>

<!-- 担当者情報入力 -->
<script>
  function add_text(elm_id, text){

    dt = new Date();
    now=dtFormat(dt);

    dt_text = now + " - " + text;
    exsist_text = $(elm_id).val();
    sum_text = dt_text + "\n" + exsist_text;

    exsist_text_count = exsist_text.length;
    dt_text_count = dt_text.length;
    sum_count = sum_text.length;

    if (exsist_text_count==0){
      $(elm_id).val(now + " - " + text);
    } else if (sum_count >= 512) {
      $(elm_id).val(sum_text.slice(0, 512));
    }else{
      $(elm_id).val(sum_text);
    }
    count_strings("#op-comment","#op_comment_str_count");
    var psconsole = $('#op-comment');
    psconsole.scrollTop(
        psconsole[0].scrollHeight - psconsole.height()
    );
  }
</script>

<!-- 比較用日付フォーマット -->
<script>
  function dtFormat(obj_dt){
      var y = obj_dt.getFullYear();
      var m = obj_dt.getMonth() + 1;
      var d = obj_dt.getDate();
      var w = obj_dt.getDay();
      var h = obj_dt.getHours();
      var n = obj_dt.getMinutes();

      // 「月」と「日」で1桁だったときに頭に 0 をつける
      if (m < 10) { m = '0' + m; }
      if (d < 10) { d = '0' + d; }
      if (w < 10) { w = '0' + w; }
      if (h < 10) { h = '0' + h; }
      if (n < 10) { n = '0' + n; }

      // フォーマットを整形してコンソールに出力
      return y + '/' + m + '/' + d + ' ' + h + ':' + n;
  }

</script>

<!-- 文字数カウント表示 -->
<script>
  count_strings("#op-comment","#op_comment_str_count");
  $("#op-comment").bind("change keyup",function(){
          count_strings("#op-comment", "#op_comment_str_count");});
</script>

<!-- 確認メッセージ -->
<script>

  function confirm_save(gwIncident, errorEvent, normalEvent){

    not_change = $('#checkedtime').prop('checked');
    do_check   = $('#checkedtime-1').prop('checked');
    rm_check   = $('#checkedtime-2').prop('checked');

    checked_time_last = null;
    if (errorEvent && normalEvent) {
        checked_time_last = normalEvent['checked_time'];
    } else if (errorEvent) {
        checked_time_last = errorEvent['checked_time'];
    } else if (normalEvent) {
        checked_time_last = normalEvent['checked_time'];
    }

    if (checked_time_last) {
        checked_time_last = "承認する";
    } else {
        checked_time_last = "承認解除";
    }

    if (not_change) {
      checked_time_input = checked_time_last;
    } else if (rm_check) {
      checked_time_input = '承認解除';
    } else if (do_check) {
      checked_time_input = '承認する';
    }

    action_no_input        = $('#op-comment').val();
    action_no_last         = gwIncident['op_comment'];
    action_no_last         = action_no_last.replace(/\r/g, "");

    var update = false;
    if(action_no_input    != action_no_last)    { update=true; }
    if(checked_time_input != checked_time_last) { update=true; }


    if (!update){
        alert('<?= __('変更されていません') ?>');
        return false;
    }
    if (!window.confirm('<?= __('更新してもよろしいですか？') ?>')) {
        return false;
    }
  };

</script>

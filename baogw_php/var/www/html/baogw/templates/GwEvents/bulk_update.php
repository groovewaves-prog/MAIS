<?php
use App\View\Helper\InputSetHelper;
?>
<div class="large-12 medium-12 columns content width_inherit" id="main_content">
    <h3><div class="navi_reffer"><?= $this->Html->link(__('Main Menu'), ['controller'=>'mainMenu','action' => 'index']) ?></div> >
        <div class="navi_reffer"><?= $this->Html->link(__('Gw Events'), $indexUrl ) ?></div>
        <div class="navi_current"><?= ' > ' . __('一括更新画面') ?></div></h3>

    <!-- 一覧 -->
    <table cellpadding="0" class="float_th">
        <thead>
            <tr>
                <th scope="col"><?= $this->Paginator->sort('GwEvents.gw_event_id', __('gw_event_id'), ['direction'=>'desc'])   ?></th>
                <th scope="col"><?= $this->Paginator->sort('ErrorEvents.alarm_time', __('alarm_time_error'), ['direction'=>'desc'])   ?></th>
                <th scope="col"><?= $this->Paginator->sort('NormalEvents.alarm_time', __('alarm_time_normal'), ['direction'=>'desc'])   ?></th>
                <th scope="col"><?= $this->Paginator->sort('GwEvents.alarm_status', __('alarm_status'), ['direction'=>'desc'])   ?></th>
                <th scope="col"><?= $this->Paginator->sort('GwIncidents.customer_name', __('customer_name'), ['direction'=>'desc'])   ?></th>
                <th scope="col"><?= $this->Paginator->sort('GwIncidents.hostname', __('hostname'), ['direction'=>'desc'])   ?></th>
                <th scope="col"><?= $this->Paginator->sort('GwIncidents.ci_name', __('ci_name'), ['direction'=>'desc'])   ?></th>
                <th scope="col"><?= $this->Paginator->sort('ErrorEvents.summary', __('summary_error'), ['direction'=>'desc'])   ?></th>
                <th scope="col"><?= $this->Paginator->sort('NormalEvents.summary', __('summary_normal'), ['direction'=>'desc'])   ?></th>
                <th scope="col"><?= $this->Paginator->sort('GwEvents.device', __('device'), ['direction'=>'desc'])   ?></th>
                <th scope="col"><?= $this->Paginator->sort('GwIncidents.op_comment', __('op_comment'), ['direction'=>'desc'])   ?></th>
                <th scope="col"><?= __('Kisys Status') ?></th>
            </tr>
        </thead>

        <tbody>
          <?php
              $now_time = new DateTime();
          ?>
            <?php foreach ($gwIncidents as $gwIncident): ?>
                <?php
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
                    $col_event_id = '';
                    $col_alarm_status = '';
                    $col_customer_ci = '';
                    $col_device = '';
                    if (isset($error_event)) { // エラーあり
                        $col_event_id = $error_event->gw_event_id;
                        $col_alarm_status = $error_event->alarm_status;
                        $col_customer_ci = $error_event->customer_ci;
                        $col_device = $error_event->device;
                    } else if (isset($normal_event)) { // ノーマルのみ
                        $col_event_id = $normal_event->gw_event_id;
                        $col_alarm_status = $normal_event->alarm_status;
                        $col_customer_ci = $normal_event->customer_ci;
                        $col_device = $normal_event->device;
                    }
                    ?>
                <?php
                  $color_cancel = ["10", "20", "30", "31", "32", "33", "34", "35", "40", "41", "42", "43", "49", "60", "61", "62", "69", "70", "71", "72", "79"];
                  $status_code = [];
                  if (!is_null($error_event)) {
                      $status_code = InputSetHelper::explode(',', h($error_event->kisys_status));
                  } else if (!is_null($normal_event)) {
                      $status_code = InputSetHelper::explode(',', h($normal_event->kisys_status));
                  }
                  $tr_class = '';
                  if (!is_null($error_event) and in_array($status_code[0], $color_cancel)) {
                      $tr_class = 'row_color_cancel';
                  } elseif (!is_null($error_event) and !is_null($normal_event)) {
                      $tr_class = 'row_color_paired';
                  } elseif (!is_null($error_event) and $error_event->event_status==2 and $error_event->alarm_status=='error') {
                      $tr_class = 'row_color_paired';
                  } elseif (is_null($error_event) and !is_null($normal_event) and $normal_event->alarm_status=='normal') {
                      $tr_class = 'row_color_normal';
                  } elseif (preg_match("/^90/", $status_code[0])) {
                      $tr_class = 'row_color_maintenance';
                  } else {
                      $tr_class = 'row_color_' . h($col_alarm_status);
                  }
                  $tr_approved = '';
                  if (!is_null($error_event) and !is_null($normal_event)) {
                      if (!is_null($normal_event->checked_time)) {
                          $tr_approved = ' row_color_approved';
                      }
                  } else if (!is_null($error_event)) {
                      if (!is_null($error_event->checked_time)) {
                          $tr_approved = ' row_color_approved';
                      }
                  } else if (!is_null($normal_event)) {
                      if (!is_null($normal_event->checked_time)) {
                          $tr_approved = ' row_color_approved';
                      }
                  }
              ?>
                <tr class="<?= $tr_class . $tr_approved; ?>">
                    <td><?= h($col_event_id) ?>
                      <?php
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
                    }
                    ?></td>
                    <td><?php if(!is_null($normal_event)) {
                        echo $normal_event->alarm_time->format('Y/m/d H:i:s');
                    }
                    ?></td>
                    <td><?= h($col_alarm_status) ?></td>
                    <?php if($col_customer_ci=="OPSUPPSYS"): ?>
                        <td><?= h($gwIncident->customer_name) ?></td>
                    <?php else: ?>
                        <td>
                            <?= $this->Html->link($gwIncident->customer_name, "javascript:void(0)", ["onClick"=>"openWindowCMDB('".$CMDB_WEB_URL."','customer_name','".$col_customer_ci."','');return false;","class"=>"underbar"]); ?>
                        </td>
                    <?php endif; ?>
                    <?php if($col_customer_ci=="OPSUPPSYS"): ?>
                        <td><?= h($gwIncident->hostname) ?></td>
                    <?php else: ?>
                        <td>
                            <?= $this->Html->link($gwIncident->hostname, "javascript:void(0)", ["onClick"=>"openWindowCMDB('".$CMDB_WEB_URL."','hostname','".$col_customer_ci."','".$gwIncident->hostname."');return false;","class"=>"underbar"]); ?>
                        </td>
                    <?php endif; ?>
                    <td><?= h($gwIncident->ci_name) ?></td>
                    <td><?php if(!is_null($error_event)) {
                        echo h($error_event->summary);
                    }
                    ?></td>
                    <td><?php if(!is_null($normal_event)) {
                        echo h($normal_event->summary);
                    }
                    ?></td>
                    <?php if($col_customer_ci=="OPSUPPSYS"): ?>
                        <td class="col_device"><?= h($col_device) ?></td>
                    <?php else: ?>
                        <td class="col_device">
                            <?= $this->Html->link($col_device, "javascript:void(0)", ["onClick"=>"openWindowCMDB('".$CMDB_WEB_URL."','device','".$col_customer_ci."','".$gwIncident->hostname."');return false;","class"=>"underbar"]); ?>
                        </td>
                    <?php endif; ?>
                    <td class="col_op_comment"><?php echo InputSetHelper::str_replace("\n", '<br>', h($gwIncident->op_comment));?></td>
                    <td class="col_actions"><?php
                        $error_send_status = is_null($error_event) ? null : $error_event->kisys_status;
                        $normal_send_status = is_null($normal_event) ? null : $normal_event->kisys_status;
                        echo $this->InputSet->sendStatusUrl(h($error_send_status), h($normal_send_status), h($gwIncident->kisys_incidentid), 'underbar');
                  ?></td>
                </tr>
            <?php endforeach; ?>
        </tbody>
    </table>

    <table class="edit-table">
      <tr>
        <th colspan="2"><?= __('Approve Edit') ?>  </th>
        <th colspan="10"><?= __('Op Comment') ?>  </th>
      </tr>
      <tr>
        <?= $this->Form->create(null, ['type'=>'post','url'=>['controller'=>'GwEvents','action'=>'bulkUpdateSave'],
                                                'onsubmit'=>'return confirm_save();'])?>

        <td colspan="2">
          <?= $this->Form->input( __('Approve Edit'), [
                                   'legend' => false,
                                   'name' => 'BulkUpdate[Approve]',
                                   'type' => 'radio',
                                   'value' => "",
                                   'label' => ['style'=> 'cursor:text;'],
                                   'options' => [
                                       ['text'=>__('変更しない'),'value'=>""],
                                       ['text'=>__('承認する'),'value'=>1],
                                       ['text'=>__('承認解除'),'value'=>2]
                                   ],
                                   'disabled' =>$disabled,
                                   'id' =>'Approve'
          ]);?>
        </td>
        <td colspan="10">
          <div class="inline">現在 </div><div id="op_comment_str_count" class="inline"></div><div class="inline">文字記入されています。 512文字まで入力できます。</div>
          <?= $this->Html->link( __('PIC') ,'javascript:void(0)', ['class'=>'btn_blue', 'onClick'=>'add_text("#op_comment", "' . $account_full_name . '");return false;']); ?>
          <?=                      $this->Form->control('op_comment',
                                                        ['label' => ['style'=> 'cursor:text;'],
                                                         'type'=>'textarea',
                                                         'disabled' =>$disabled,
                                                         'id' =>'op_comment',
                                                         'value'=>'',
                                                         'placeholder'=>__('空白で更新しても補記情報を削除することはできません。')
                                                       ]);
          ?>
        </td>
      </tr>
      </tbody>
    </table>

    <div class="btn_container left"><?= $this->Form->button(__('BulkUpdate'),['disabled'=>$disabled,'class'=>'btn_brown']) ?></div>
    <?= $this->Form->end(); ?>



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
        count_strings("#op_comment","#op_comment_str_count");
        var psconsole = $('#op_comment');
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

<!-- テーブルタイトル固定 Common -->
<script>
    $(window).scroll(function () {  $('table.float_th').floatThead({top:44});  });
</script>



<!-- 文字数カウント表示 -->
<script>
  count_strings("#op_comment","#op_comment_str_count");
  $("#op_comment").bind("change keyup",function(){
          count_strings("#op_comment", "#op_comment_str_count");});
</script>

<!-- 確認メッセージ GwEvents bulkupdate-->
<script>

  function confirm_save(){

    var update=false;
    var confirm_messages="";
    checked_time_flag = $("[name=BulkUpdate\\\[Approve\\\]]:checked").val();

    if(checked_time_flag != ''){
      update=true;
      if (checked_time_flag == 1){
        checked_time='承認する'
      } else {
        checked_time='承認解除'
      }
      confirm_messages += '\n' + '<?= __('承認：') ?>' + checked_time;
    }

    if($('#op_comment').val() != ''){
        update=true;
        confirm_messages += '\n' + '<?= __('補記情報：') ?>' + $('#op_comment').val();
    }

    if (update==false){
        alert('<?= __('更新情報がありません。') ?>');
        return false;
    }
    if (!window.confirm('<?= __('下記へ一括更新を実行してもよろしいですか？') ?>' + '\n' + confirm_messages)) {
        return false;
    }
  };
</script>


</div>

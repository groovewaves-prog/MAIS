<?php
?>

<div class="form large-9 medium-12 content" id="main_content">
  <h3><div class="navi_reffer"><?= $this->Html->link(__('Main Menu'), ['controller'=>'mainMenu','action' => 'index']) ?></div> >
      <div class="navi_reffer"><?= $this->Html->link(__('Gw Rules'), $indexUrl ) ?></div>
      <div class="navi_current"><?=  ' > '. __('Edit Gw Rule')?></div></h3>

    <?= $this->Form->create($gwRule, ['onsubmit'=>'return confirm_save(' . $gwRule . ');']) ?>
    <fieldset>
        <!-- <legend>ID：<?= $gwRule->rule_id  . ' ' . __('Edit Gw Rule');   ?></legend> -->
        <legend>ID：<?= $gwRule->rule_id  . ' ' . __('Edit Gw Rule');   ?>
        <!-- ハウコムフラグ -->
        <?php
            if(($account_type == 3 || array_intersect($usrgrp_names, $all_search_user_groups)) && in_array($gwRule->customer_name, $howcom_names)){
                echo '<span style="display: inline-block;" class="flag_howcom">' . $KDDI_MIYAZAKI . '</span>';
            }
        ?>
        <!-- VIPフラグ -->
        <?php
            if(in_array($gwRule->customer_name, $vip_names)){
                echo '<span style="display: inline-block;" class="flag_jp1">JP1</span>';
            }
        ?>
        </legend>
        <table class="edit">
            <tr>
              <td colspan="1"><?= $this->Form->control('rule_status',['label'=>'有効']); ?></td>
              <td colspan="2"><?= $this->Form->control('start_time', ['type'=>'text', 'class'=>'datetimepicker']); ?></td>
              <td colspan="2"><?=  $this->Form->control('end_time',  ['type'=>'text', 'class'=>'datetimepicker']); ?></td>
            </tr>
            <tr>
              <td  colspan="3" style="vertical-align: top;">
                <!-- <?= $this->Html->link( __('Select') ,'#', ['class'=>'btn_blue' , 'onClick'=>'openWindowSelect("' . $currentUrl . '", "GwRules", "rule_set")']); ?> -->
                <!-- <?= $this->Form->control('rule_set',['id'=>'rule_set']); ?> -->
                <?= $this->Form->input('rule_set', ['type'=>'select',
                                                    'id' =>'rule_set',
                                                    'selected'=> '1',
                                                    'value'=>$gwRule->rule_set,
                                                    'options'=>$RULE_SET_NAME,
                                                    // 'options'=>['1'=>'1:チケット起票時','2'=>'2:チケットクローズ'],
                                                    'class'=>'display_none',
                                                   ]);
                ?>
                <?= $this->Html->link( __('Select') ,'javascript:void(0)', ['class'=>'btn_blue', 'onClick'=>'openWindowSelectConds("' . $currentUrl . '", "GwEvents", "customer_name");return false;']); ?>
                <?= $this->Form->control('customer_name', ['id'=>'customer_name']); ?>
                <?= $this->Html->link( __('Select') ,'javascript:void(0)', ['class'=>'btn_blue', 'onClick'=>'openWindowSelectConds("' . $currentUrl . '", "GwEvents", "hostname");return false;']); ?>
                <?= $this->Form->control('hostname', ['id'=>'hostname']); ?>
                <?= $this->Html->link( __('Select') ,'javascript:void(0)', ['class'=>'btn_blue', 'onClick'=>'openWindowSelectConds("' . $currentUrl . '", "GwEvents", "ci_name");return false;']); ?>
                <?= $this->Form->control('ci_name', ['id'=>'ci_name']); ?>
                <div><?= __('GwRules Description') ?></div>
              </td>
              <td colspan="3">
                <!-- <?= $this->Html->link( __('Select') ,'#', ['class'=>'btn_blue', 'onClick'=>'openWindowSelect("' . $currentUrl . '", "GwRules", "action_no")']); ?> -->
                <!-- <?= $this->Form->control('action_no', ['id'=>'action_no']); ?> -->
                <!-- <?= $this->Form->control('action_no', ['type'=>'text'])?> -->
                <?= $this->Form->control('action_no', ['type'=>'select',
                                                    'id' =>'action_no',
                                                    'value'=>$gwRule->action_no,
                                                    'options'=>$ACTION_NO_NAME,
                                                    'onchange'=>'action_no_onchange()'
                                                    // 'options'=>['0'=>'0:BAOへ送信', '1'=>'1:BAOへ送信しない',
                                                    //             '2'=>'2:キャンセルステータス',
                                                    //             '3'=>'3:クローズステータス','4'=>'4:K-ISYSメンテナンス'],
                                                   ]);
                   foreach ($ACTION_NO_DESC as $key => $value){
                      echo $value. "<br>";
                   }
                ?>
              </td>
            </tr>
            <tr>
              <td colspan="5">
                <?= $this->Form->control('op_comment', ['label' => ['style' => 'cursor:text;',
                                                                    'text' => '補記情報（4000文字以内。最初の30文字までは一覧に表示されます。）',
                                                                   ],
                                                        'type'=>'textarea',
                                                        'maxlength' => 4000,
                                                       ]);
                ?>
              <td>
            </tr>
        </table>
    </fieldset>
    <div style="width:200px"><?= $this->Form->button(__('saveas'),['class'=>'btn_brown']) ?></div>
    <?= $this->Form->end() ?>

<!-- 日付カレンダー入力 Common-->
<script>
    $.datetimepicker.setLocale('ja');
    $('.datetimepicker').datetimepicker();
</script>

<!-- アクションNo onchange-->
<script>
  $(function(){
    action_no_onchange();
  });
  function action_no_onchange(){
    if ($('#action_no').val() == '90') {
      $('#customer_name').val('KISYS');
      $('#hostname').val('*');
      $('#ci_name').val('*');
      $('#customer_name').attr('readonly',true);
      $('#hostname').attr('readonly',true);
      $('#ci_name').attr('readonly',true);
      $('.btn_blue').addClass('btn-disabled');
    } else if ($('#action_no').val() == '80') {
      $('#customer_name').val('Kompira');
      $('#hostname').val('*');
      $('#ci_name').val('*');
      $('#customer_name').attr('readonly',true);
      $('#hostname').attr('readonly',true);
      $('#ci_name').attr('readonly',true);
      $('.btn_blue').addClass('btn-disabled');
    } else {
      $('#customer_name').attr('readonly',false);
      $('#hostname').attr('readonly',false);
      $('#ci_name').attr('readonly',false);
      $('.btn_blue').removeClass('btn-disabled');
    }
  };
</script>

<!-- 確認メッセージ -->
<script>
  function confirm_save(gwRule){

    if($('#rule-status').prop('checked')){
        rule_status_input='有効';
     } else {
        rule_status_input='無効';
    }
    // alert($('#rule-status').prop('checked'))
    // rule_set_input      = $('#rule_set').val();
    rule_set_input      = $('#rule_set option:selected').text()
    if ($('#start-time').val()){
        start_time_input    = new Date($('#start-time').val());
        start_time_input    = dtFormat(start_time_input);
    }else{
        start_time_input ="未設定"
    }
    if ($('#end-time').val()){
        end_time_input      = new Date($('#end-time').val());
        end_time_input    = dtFormat(end_time_input);
    }else{
        end_time_input ="未設定"
    }

    customer_name_input = $('#customer_name').val();
    hostname_input      = $('#hostname').val();
    ci_name_input       = $('#ci_name').val();
    // action_no_input     = $('#action_no').val();
    action_no_input =$('#action_no option:selected').text();
    op_comment_input =$('#op-comment').val();

    // start_time_last = gwRule['start_time'].replace('T0',' ').replace('T',' ').replace(/-/g,'/');
    if(gwRule['rule_status']==false ){ rule_status_last='無効';} else { rule_status_last='有効'; }

    rule_set_last      = gwRule['rule_set_disp'];

    if (gwRule['start_time']){
        start_time_last    = new Date(gwRule['start_time']);
        start_time_last    = dtFormat(start_time_last);
    }else{
        start_time_last ="未設定"
    }

    if (gwRule['end_time']){
        end_time_last      = new Date(gwRule['end_time']);
        end_time_last      = dtFormat(end_time_last);
    }else{
        end_time_last ="未設定"
    }
    customer_name_last = gwRule['customer_name'];
    hostname_last      = gwRule['hostname'];
    ci_name_last       = gwRule['ci_name'];
    action_no_last     = gwRule['action_no_disp'];
    op_comment_last    = gwRule['op_comment'];
    // alert(gwRule['start_time'] + '->' + start_time_last + '->' +start_time_input);

    var confirm_messages="";
    if(rule_status_input    != rule_status_last)  { confirm_messages += '\n' + '<?= __('ルールステータス：') ?>' + rule_status_last   + ' -> ' + rule_status_input; }
    // if(rule_set_input       != rule_set_last)     { confirm_messages += '\n' + '<?= __('ルールセット    ：') ?>' + rule_set_last      + ' -> ' + rule_set_input; }
    if(start_time_input     != start_time_last)   { confirm_messages += '\n' + '<?= __('適用開始日時    ：') ?>' + start_time_last    + ' -> ' + start_time_input; }
    if(end_time_input       != end_time_last)     { confirm_messages += '\n' + '<?= __('適用終了日時    ：') ?>'  + end_time_last      + ' -> ' + end_time_input; }
    if(customer_name_input  != customer_name_last){ confirm_messages += '\n' + '<?= __('顧客名          ：') ?>'  + customer_name_last + ' -> ' + customer_name_input; }
    if(hostname_input       != hostname_last)     { confirm_messages += '\n' + '<?= __('ホスト名        ：') ?>' + hostname_last      + ' -> ' + hostname_input; }
    if(ci_name_input        != ci_name_last)      { confirm_messages += '\n' + '<?= __('アラーム名      ：') ?>' + ci_name_last       + ' -> ' + ci_name_input; }
    if(action_no_input      != action_no_last)    { confirm_messages += '\n' + '<?= __('アクションNo    ：') ?>' + action_no_last     + ' -> ' + action_no_input; }
    if(op_comment_input     != op_comment_last)   { confirm_messages += '\n' + '<?= __('補記情報        ：') ?>' + op_comment_last    + ' -> ' + op_comment_input; }

    if (confirm_messages == ''){
        alert('変更されていません');
        return false;
    }
    if (!window.confirm( '<?= __('下記情報の更新を実行してもよろしいですか？') ?>' + '\n' + confirm_messages)) {
        return false;
    }
  };
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
  // 「年」「月」「日」「曜日」を Date オブジェクトから取り出してそれぞれに代入
</script>

</div>

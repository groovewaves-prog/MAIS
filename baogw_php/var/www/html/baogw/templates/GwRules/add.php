<?php
?>

<div class="gwRules form large-9 medium-12 columns content" id="main_content">
  <h3><div class="navi_reffer"><?= $this->Html->link(__('Main Menu'), ['controller'=>'mainMenu','action' => 'index']) ?></div> >
      <div class="navi_reffer"><?= $this->Html->link(__('Gw Rules'), $indexUrl ) ?></div>
      <div class="navi_current"><?=  ' > '. __('Add Gw Rule')?></div></h3>

    <?= $this->Form->create($gwRule, ['onsubmit'=>'return confirm_save();']) ?>
    <fieldset>
        <legend><?= __('Add Gw Rule') ?></legend>
        <table class="edit">
            <tr>
              <td colspan="1"><?= $this->Form->control('rule_status',['label'=>'有効']); ?></td>
              <td colspan="2"><?= $this->Form->control('start_time', ['type'=>'text', 'class'=>'datetimepicker']); ?></td>
              <td colspan="2"><?= $this->Form->control('end_time',   ['type'=>'text', 'class'=>'datetimepicker']); ?></td>
            </tr>
            <tr>
              <td colspan="3" style="vertical-align: top;">
                  <!-- <?= $this->Html->link( __('Select') ,'#', ['class'=>'btn_blue' , 'onClick'=>'openWindowSelect("' . $currentUrl . '", "GwRules", "rule_set")']); ?> -->
                  <!-- <?= $this->Form->control('rule_set',['id'=>'rule_set']); ?> -->
                  <?= $this->Form->control('rule_set', ['type'=>'select',
                                                      'id' =>'rule_set',
                                                      'selected'=> '1',

                                                      'options'=>$RULE_SET_NAME,
                                                      // 'options'=>[''=>'変更なし', '1'=>'1:チケット起票時','2'=>'2:チケットクローズ'],
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
                  <!-- <?=  $this->Html->link( __('Select') ,'#', ['class'=>'btn_blue', 'onClick'=>'openWindowSelect("' . $currentUrl . '", "GwRules", "action_no")']); ?> -->
                  <!-- <?=  $this->Form->control('action_no', ['id'=>'action_no']); ?> -->

                  <?= $this->Form->control('action_no', ['type'=>'select',
                                                      'id' =>'action_no',
                                                      'selected'=> '',
                                                      'options'=>$ACTION_NO_NAME,
                                                      'onchange'=>'action_no_onchange()'
                                                      // 'options'=>[''=>'変更なし', '0'=>'0:BAOへ送信', '1'=>'1:BAOへ送信しない',
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
                                                          'type' => 'textarea',
                                                          'maxlength' => 4000,
                                                         ]);
                  ?>
              <td>
            </tr>
        </table>
        <div style="width:200px"><?= $this->Form->button(__('Submit'),['class'=>'btn_brown']) ?></div>
    </fieldset>
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
      function confirm_save(){
        if (!window.confirm( '<?= __('新規ルールを登録してもよろしいですか？') ?>')) {
            return false;
        }
      };

    </script>
</div>

<?php
use App\View\Helper\InputSetHelper;
?>

<div class="large-12 medium-12 columns content width_inherit" id="main_content">

    <h3><div class="navi_reffer"><?= $this->Html->link(__('Main Menu'), ['controller'=>'mainMenu','action' => 'index']) ?></div> >
        <div class="navi_current"><?= __('Gw Rules') ?></div>
        <div class="navi_reffer navi_shortcut"><?= $this->Html->link(__('Add Gw Rule'), ['action' => 'add']) ?></div></h3>
    <!-- 検索 -->
    <?= $this->Form->create(null, ['class'=>'js-form', 'type'=>'get','url'=>['controller'=>'GwRules','action'=>'index']])?>
    <?php //フィルタフォームの開閉、ソート、オーダの保持
        $hiddens=[['filter_form_opened'=>$filter_form_opened],['sort'=>$sort],['direction'=>$direction]];
        echo $this->InputSet->hiddens($hiddens);
    ?>

    <div class="filter-title btn_blue" id="js-slide_btn"
            onclick="do_slide('#js-slide_btn', '#js-slide_bx','#filter_form_opened')">[<?= __('ルール検索') ?>] ▲閉じる </div>
    <div class="filter-title"><?= $this->InputSet->selectdispCount('display_count', $display_count); ?> </div>





    <div id="js-slide_bx">
        <table class="filter">
            <tr><td colspan="10" class="filter-subtitle"><?= __('ルール検索') ?></td></tr>
            <tr class="filter-condition">
                <td><?= $this->InputSet->txtBx    ("rule_id"      , $rule_id, $rule_id_operetor, "num"); ?></td>
                <td><?= $this->InputSet->radioBtns("rule_status"  , $rule_status, [__('両方'),__('有効ルール'),__('無効ルール')]);?></td>
                <!-- <td><?= $this->InputSet->chkBxGrp ('rule_set'     , $RULE_SET_NAME, $rule_set);?></td> -->
                <td><?= $this->InputSet->dtFromTo ("start_time"   , $start_time_from, $start_time_to, __('start_time_from'),__('start_time_to')); ?></td>
                <td><?= $this->InputSet->dtFromTo ("end_time"     , $end_time_from, $end_time_to, __('end_time_from'),__('end_time_to')); ?></td>
                <td><?= $this->InputSet->txtBx    ("customer_name", $customer_name, $customer_name_operetor, "str", $currentUrl, "GwRules", "customer_name"); ?></td>
                <td><?= $this->InputSet->txtBx    ("hostname"     , $hostname, $hostname_operetor, "str", $currentUrl, "GwRules", "hostname"); ?></td>
                <td><?= $this->InputSet->txtBx    ("ci_name"      , $ci_name, $ci_name_operetor, "str", $currentUrl, "GwRules", "ci_name"); ?></td>
                <td><?= $this->InputSet->chkBxGrp ('action_no'    , $ACTION_NO_NAME, $action_no);?></td>
                <td><?= $this->InputSet->txtBx    ("op_comment"   , $op_comment, $op_comment_operetor, "str"); ?></td>
                <td><?= $this->InputSet->actionButtons(); ?></td>
            </tr>
            <tr>
                <td colspan="10" class="filter-subtitle"><?= __('列の 表示 / 非表示') ?></td>
            </tr>
            <tr class="filter-condition">
                <?= $this->InputSet->chkBxGrpHideBtn('disp_col', $COLUMNS_RULES, $disp_col);?>
            </tr>
        </table>
        <?= $this->Form->end(); ?>
    </div>



    <!-- ページネーション -->
    <?= $this->InputSet->pagenator()?>

    <!-- ルール一覧 -->
    <!-- <?= $this->Form->create(null, ['class'=>'js-form', 'type'=>'post','url'=>['controller'=>'GwRules','action'=>'bulkUpdate']])?> -->
        <table class="float_th">
            <thead>
                <tr>
                    <th scope="col" class="col_rule_id"><div>   <?= $this->Paginator->sort('rule_id') ?>
                        <!-- <?= $this->InputSet->chkBx('all_check_flag_bulk_update', '', '', '',  0,
                                                    'all_checking("flag_bulk_update", this.checked);', 'btn_yellow'); ?> -->
                    <th scope="col" class="col_rule_status">    <?= $this->Paginator->sort('rule_status')   ?></th>
                    <!-- <th scope="col" class="col_rule_set">       <?= $this->Paginator->sort('rule_set')      ?></th> -->
                    <th scope="col" class="col_start_time">     <?= $this->Paginator->sort('start_time')    ?></th>
                    <th scope="col" class="col_end_time">       <?= $this->Paginator->sort('end_time')      ?></th>
                    <th scope="col" class="col_customer_name">  <?= $this->Paginator->sort('customer_name') ?></th>
                    <th scope="col" class="col_hostname">       <?= $this->Paginator->sort('hostname')      ?></th>
                    <th scope="col" class="col_ci_name">        <?= $this->Paginator->sort('ci_name')       ?></th>
                    <th scope="col" class="col_action_no">      <?= $this->Paginator->sort('action_no')     ?></th>
                    <th scope="col" class="col_op_comment">     <?= $this->Paginator->sort('op_comment')    ?></th>
                    <th scope="col" class="col_actions">        <?= __('Actions')           ?></th>
                </tr>
            </thead>

            <tbody>
                <?php foreach ($gwRules as $gwRule): ?>
                <tr>
                    <td class="col_rule_id">
                        <!-- <?=$this->Form->checkbox('BulkUpdate.' . $gwRule->rule_id,
                                                  ['class' => 'flag_bulk_update',
                                                      'id' => 'id' . $gwRule->rule_id
                                                ]);?> -->
                        <?= $this->Form->label('id' . $gwRule->rule_id, $gwRule->rule_id) ?>
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
                    </td>

                    <td class="col_rule_status">    <?= h($gwRule->rule_status) ? __('Yes') : __('No'); ?></td>
                    <!-- <td class="col_rule_set">       <?= h($gwRule->rule_set) ?></td> -->
                    <td class="col_start_time">     <?= h($gwRule->start_time->format('Y/m/d H:i:s')) ?></td>
                    <td class="col_end_time">       <?= h($gwRule->end_time->format('Y/m/d H:i:s')) ?></td>
                    <td class="col_customer_name">  <?= h($gwRule->customer_name) ?></td>
                    <td class="col_hostname">       <?= h($gwRule->hostname) ?></td>
                    <td class="col_ci_name">        <?= h($gwRule->ci_name) ?></td>
                    <td class="col_action_no">      <?= h($gwRule->action_no) ?></td>
                    <td class="col_op_comment">
                      <span>
                        <?=  $this->InputSet->genShortMsg(h($gwRule->op_comment), 30); ?>
                        <?php if($gwRule->op_comment and InputSetHelper::mb_strlen($gwRule->op_comment) > 30):?>
                        <span class="popup"><?= h($gwRule->op_comment) ?></span>
                        <?php endif; ?>
                      </span>
                    </td>
                    <td class="col_actions"><?= $this->Html->link(__('Edit'), ['action' => 'edit', $gwRule->rule_id],['class'=>'btn_green']) ?></td>
                </tr>
                <?php endforeach; ?>
            </tbody>
        </table>

        <!-- ページネーション -->
        <?= $this->InputSet->pagenator()?>

        <!-- <?= $this->Form->button(__('To BulkUpdate'),['style'=>'width:200px;height:75px;padding:0px;','class'=>'btn_brown js-submit']) ?> -->
        <!-- <?= $this->Form->end(); ?> -->
</div>

<!-- アコーディオン GwEvents GwRules index -->
<script>
    init_slide('#js-slide_btn', '#js-slide_bx','#filter_form_opened');
</script>

<!-- <?php if($to_check=="1"): ?>
    <!-- 一括チェックボックス復元 GwEvents GwRules index -->
    <script>
      restore_check_boxs('#id', <?= $to_check; ?>, <?php echo json_encode($bulk_update_ids, JSON_HEX_TAG | JSON_HEX_AMP | JSON_HEX_APOS | JSON_HEX_QUOT); ?>);
    </script>
<?php endif; ?> -->

<!-- 日付カレンダー入力 Common-->
<script>
    $.datetimepicker.setLocale('ja');
    $('.datetimepicker').datetimepicker();
</script>

<!-- テーブルタイトル固定 Common -->
<script>
    $(window).scroll(function () {  $('table.float_th').floatThead({top:44});  });
</script>

<!-- アラーム検索の検索方式で 空白/非空白選択時 に検索値をdisableにする(復元用) -->
<script>
    disable_operetor('#customer_name_operetor', '#customer_name');
    disable_operetor('#hostname_operetor'     , '#hostname');
    disable_operetor('#ci_name_operetor'      , '#ci_name');
</script>

<!-- 行の非表示機能復元 GwEvents-->
<script>
    <?php if(count($disp_col)>1):?>
    hideColumn(".col_rule_id",       "" + <?= in_array('rule_id',       $disp_col) ?> + "");
    hideColumn(".col_rule_status",   "" + <?= in_array('rule_status',   $disp_col) ?> + "");
    hideColumn(".col_rule_set",      "" + <?= in_array('rule_set',      $disp_col) ?> + "");
    hideColumn(".col_start_time",    "" + <?= in_array('start_time',    $disp_col) ?> + "");
    hideColumn(".col_end_time",      "" + <?= in_array('end_time',      $disp_col) ?> + "");
    hideColumn(".col_customer_name", "" + <?= in_array('customer_name', $disp_col) ?> + "");
    hideColumn(".col_hostname",      "" + <?= in_array('hostname',      $disp_col) ?> + "");
    hideColumn(".col_ci_name",       "" + <?= in_array('ci_name',       $disp_col) ?> + "");
    hideColumn(".col_action_no",     "" + <?= in_array('action_no',     $disp_col) ?> + "");
    hideColumn(".col_actions",       "" + <?= in_array('actions',       $disp_col) ?> + "");
    <?php endif; ?>
</script>


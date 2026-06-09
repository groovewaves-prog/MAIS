<?php
?>

<div class="gwEvents index columns content width_inherit" id="main_content" >

    <h3><div class="navi_reffer" ><?= $this->Html->link(__('Main Menu'), ['controller'=>'mainMenu','action' => 'index',]) ?></div> >
        <div class="navi_current"><?= __('CSV出力') ?></div></h3>
    <?php
        echo $this->Html->link('CSV出力', array('action'=>'exportCsv','?'=>$filter_val), array('class'=>'btn_green', 'confirm'=>'CSV出力する'));
        // echo $this->Html->link('CSV出力', array('action'=>'exportCsv'), array('class'=>'btn_green', 'confirm'=>'CSV出力する'));
    ?>
    <?= $this->Form->create(null, ['class'=>'js-form', 'type'=>'get', 'url'=>['controller'=>'GwFilter','action'=>'index',]])?>
        <table class="filter">
            <tr><td colspan="12" class="filter-subtitle"><?= __('アラーム検索') ?></td></tr>
            <tr class="filter-condition">
                <td><?= $this->InputSet->dtFromTo("alarm_time", $alarm_time_from, $alarm_time_to,__('alarm_time_from'),__('alarm_time_to')); ?></td>
                <td><?= $this->InputSet->chkBxGrp('alarm_status', $ALARM_STATUS_NAME, $alarm_status);?></td>
                <td><?= $this->InputSet->txtBx("customer_name", $customer_name, $customer_name_operetor, "str", $currentUrl, "GwEvents", "customer_name"); ?></td>
                <td><?= $this->InputSet->actionButtons(); ?></td>
            </tr>
        </table>
    <?= $this->Form->end(); ?>
</div>

<!-- 日付カレンダー入力 Common-->
<script>
    $.datetimepicker.setLocale('ja');
    $('.datetimepicker').datetimepicker();
</script>

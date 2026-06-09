<?php
?>

<div class="index columns content width_inherit" id="main_content">

    <h3><div class="navi_reffer"><?= $this->Html->link(__('Main Menu'), ['controller'=>'mainMenu','action' => 'index',]) ?></div> >
        <div class="navi_current"><?= __('Gw Rescue Events') ?></div></h3>

    <!-- イベント一覧 -->
    <?= $this->Form->create(null, ['type'=>'get','url'=>['controller'=>'GwRescueEvents','action'=>'index',]])?>

    <div class="filter-title"><?= $this->InputSet->selectdispCount('display_count', $display_count); ?> </div>
    <div class="btn_blue" onclick="window.location.reload();">画面更新 </div>

    <!-- ページネーション -->
    <?= $this->InputSet->pagenator()?>

    <table class="float_th">
        <thead>
            <tr>
                <th scope="col" class="col_gw_event_id">    <?= $this->Paginator->sort('gw_event_id') ?>
                </th>
                <th scope="col" class="col_alarm_time">     <?= $this->Paginator->sort('alarm_time') ?><br><br></th>
                <th scope="col" class="col_alarm_status">   <?= $this->Paginator->sort('alarm_status') ?><br><br></th>
                <th scope="col" class="col_customer_name">  <?= $this->Paginator->sort('customer_name') ?><br><br></th>
                <th scope="col" class="col_hostname">       <?= $this->Paginator->sort('hostname') ?><br><br></th>
                <th scope="col" class="col_ci_name">        <?= $this->Paginator->sort('ci_name') ?><br><br></th>
                <th scope="col" class="col_summary">        <?= $this->Paginator->sort('summary') ?><br><br></th>
                <th scope="col" class="col_device">         <?= $this->Paginator->sort('device') ?><br><br></th>
            </tr>
        </thead>
        <tbody>
            <?php
                $now_time = new DateTime();
            ?>
            <?php foreach ($gwEvents as $gwEvent): ?>
            <?php
                $relation=$gwEvent->gw_incident;
                if(!is_null($relation)){
                    $kisys_status = h($relation->kisys_status);
                } else {
                    $kisys_status ="";
                }
                if(!is_null($gwEvent->checked_time)){
                    $tr_class = 'row_color_approved';
                } elseif (strpos($kisys_status,'6') !== false){
                    $tr_class = 'row_color_cancel';
                } else{
                    $tr_class = 'row_color_' . h($gwEvent->alarm_status);
                }
            ?>
            <tr class=<?= $tr_class ?>>
                <td class="col_gw_event_id">
                    <?= $this->Form->label('id' . $gwEvent->gw_event_id, $gwEvent->gw_event_id ) ?>
                    <?php
                        $alarm_time = new DateTime($gwEvent->alarm_time->format('Y/m/d H:i:s'));
                    ?>
                    <?= $newflag=$this->InputSet->newFlag($now_time, $alarm_time, $gwEvent->checked_time, $FLAG_NEW_DAY, $FLAG_NEW_HOUR); ?>
                </td>
                <td class="col_alarm_time">   <?= $alarm_time->format('Y/m/d H:i:s'); ?></td>
                <td class="col_alarm_status"> <?= h($gwEvent->alarm_status) ?>        </td>
                <td class="col_customer_name"><?= h($gwEvent->customer_name) ?>       </td>
                <td class="col_hostname">     <?= h($gwEvent->hostname) ?>            </td>
                <td class="col_ci_name">      <?= h($gwEvent->ci_name) ?>             </td>
                <td class="col_summary">      <?= h($gwEvent->summary) ?>             </td>
                <td class="col_device">       <?= h($gwEvent->device) ?>              </td>
            </tr>
            <?php endforeach; ?>
        </tbody>
    </table>

    <!-- ページネーション -->
    <?= $this->InputSet->pagenator()?>

    <?= $this->Form->end(); ?>

</div>


<!-- テーブルタイトル固定 Common -->
<script>
    $(window).scroll(function () {  $('table.float_th').floatThead({top:44});  });
</script>







<!--  -->

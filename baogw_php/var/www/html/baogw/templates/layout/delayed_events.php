<?= $this->Html->script('jquery')?>
<?= $this->Html->css('base') ?>
<?= $this->Html->css('cake') ?>
<?= $this->Html->css('baogw.css') ?>
<?php if($FLAG_PRIMARY): ?>
    <?= $this->Html->css('baogw-pri') ?>
    <link rel="icon" href="/baogw/favicon-pri.ico"/>
<?php else: ?>
    <?= $this->Html->css('baogw-sec') ?>
    <link rel="icon" href="/baogw/favicon-sec.ico"/>
<?php endif; ?>

<!-- イベント一覧 -->
<table class="float_th">
    <thead>
        <tr>
            <th scope="col" class="col_gw_event_id">    <?= __('gw_event_id') ?><br><br></th>
            <th scope="col" class="col_alarm_time"><?= __('alarm_time_error') ?><br><br></th>
            <th scope="col" class="col_alarm_status">   <?= __('alarm_status') ?><br><br></th>
            <th scope="col" class="col_customer_name">  <?= __('customer_name') ?><br><br></th>
            <th scope="col" class="col_hostname">       <?= __('hostname') ?><br><br></th>
            <th scope="col" class="col_ci_name">        <?= __('ci_name') ?><br><br></th>
            <th scope="col" class="col_summary">  <?= __('summary_error') ?><br><br></th>
            <th scope="col" class="col_device">         <?= __('device') ?><br><br></th>
        </tr>
    </thead>
    <tbody>
        <?php foreach ($delayedEvents as $gwEvent): ?>
            <?php
                $tr_class = 'row_color_' . h($gwEvent->alarm_status);
            ?>
            <tr class="<?= $tr_class ?>">
                <td class="col_gw_event_id">
                    <?= $gwEvent->gw_event_id ?>
                    <!-- ハウコムフラグ -->
                    <?php
                        if(($account_type == 3 || array_intersect($usrgrp_names, $all_search_user_groups)) && in_array($gwEvent->customer_name, $howcom_names)){
                            echo '<span style="display: inline-block;" class="flag_howcom">HOWCOM</span>';
                        }
                    ?>
                    <!-- VIPフラグ -->
                    <?php
                        if(in_array($gwEvent->customer_name, $vip_names)){
                            echo '<span style="display: inline-block;" class="flag_jp1">JP1</span>';
                        }
                    ?>
                </td>
                <td class="col_alarm_time">
                <?php
                    echo $gwEvent->alarm_time->format('Y/m/d H:i:s');
                ?></td>
                <td class="col_alarm_status"> <?= h($gwEvent->alarm_status) ?></td>
                <?php if($gwEvent->customer_ci=="OPSUPPSYS"): ?>
                    <td class="col_customer_name"><?= h($gwEvent->customer_name) ?></td>
                <?php else: ?>
                    <td class="col_customer_name">
                        <?= $this->Html->link($gwEvent->customer_name, "javascript:void(0)", ["onClick"=>"openWindowCMDB('".$CMDB_WEB_URL."','customer_name','".$gwEvent->customer_ci."','');return false;","class"=>"underbar"]); ?>
                    </td>
                <?php endif; ?>
                <?php if($gwEvent->customer_ci=="OPSUPPSYS"): ?>
                    <td class="col_hostname"><?= h($gwEvent->hostname) ?></td>
                <?php else: ?>
                    <td class="col_hostname">
                        <?= $this->Html->link($gwEvent->hostname, "javascript:void(0)", ["onClick"=>"openWindowCMDB('".$CMDB_WEB_URL."','hostname','".$gwEvent->customer_ci."','".$gwEvent->hostname."');return false;","class"=>"underbar"]); ?>
                    </td>
                <?php endif; ?>
                <td class="col_ci_name"><?= h($gwEvent->ci_name) ?></td>
                <td class="col_summary">
                <?php 
                    echo $this->InputSet->genShortMsg(h($gwEvent->summary), 50);
                ?></td>
                <?php if($gwEvent->customer_ci=="OPSUPPSYS"): ?>
                    <td class="col_device"><?= h($gwEvent->device) ?></td>
                <?php else: ?>
                    <td class="col_device">
                        <?= $this->Html->link($gwEvent->device, "javascript:void(0)", ["onClick"=>"openWindowCMDB('".$CMDB_WEB_URL."','device','".$gwEvent->customer_ci."','".$gwEvent->hostname."');return false;","class"=>"underbar"]); ?>
                    </td>
                <?php endif; ?>
            </tr>
        <?php endforeach; ?>
    </tbody>
</table>

</div>

<!-- テーブルタイトル固定 Common -->
<script>
    $(window).scroll( function(){
            $('table.float_th').floatThead({top:44});
    });
</script>

<button class="btn_blue" onclick="window.close();" style="width:200px;height:45px;margin:10px;">閉じる</button>

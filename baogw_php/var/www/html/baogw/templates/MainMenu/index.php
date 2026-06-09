<?php
?>

<div class="columns content width_inherit" id="main_content">

    <h3><?= __('Main Menu') ?></h3>
    <h3 class="main_menu"><?= $this->Html->link(__('Gw Events'), ['controller' => 'GwEvents',  'action' => 'index', ]); ?></h3>
    <h3 class="main_menu"><?= $this->Html->link(__('CSV出力'), ['controller' => 'GwFilter',  'action' => 'index', ]); ?></h3>
    <h3 class="main_menu"><?= $this->Html->link(__('Gw Rules'), ['controller' => 'GwRules', 'action' => 'index', ]) ?></h3>
    <h3 class="main_menu"><?= $this->Html->link(__('Gw Rescue Events'), ['controller' => 'GwRescueEvents',  'action' => 'index', ]); ?></h3>
    <h3 class="main_menu"><?= $this->Html->link(__('Gw Rescue Incidents'), ['controller' => 'GwRescueIncidents',  'action' => 'index', ]); ?></h3>
    <?php if ($account_type == 3) : ?>
        <h3 class="main_menu"><a href="/mail_receiver/mail-references?zabbix-username=<?= $account_alias ?>" target="_blank">メール連携管理画面</a></h3>
    <?php endif; ?>

</div>

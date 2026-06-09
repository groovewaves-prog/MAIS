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

<table style="border:solid;">
    <tr style="border-bottom:solid;"><td style="font-weight:bold; width:250px;"><?= __('【監視サーバ（正）】') ?></td><td><?= $monitoring ?></td></tr>
    <tr style="border-bottom:solid;"><td style="font-weight:bold; width:250px;"><?= __('【監視サーバアクセス方式（正）】') ?></td><td><?= $monitoring_access ?></td></tr>
    <tr style="border-bottom:solid;"><td style="font-weight:bold; width:250px;"><?= __('【監視サーバ（副）】') ?></td><td><?= $sub_monitoring ?></td></tr>
    <tr style="border-bottom:solid;"><td style="font-weight:bold; width:250px;"><?= __('【監視サーバアクセス方式（副）】') ?></td><td><?= $sub_monitoring_access ?></td></tr>
</table>
<button class="btn_blue" onclick="window.close();" style="width:200px;height:45px;margin:10px;">閉じる</button>

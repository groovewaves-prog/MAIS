<?php
$this->assign('tab_title', 'add');
$this->Html->css('baorw_cp', ['block' => true]);
?>

<h1>新規追加画面</h1>

<h3>
    <div class="navi_reffer">
        <?= $this->Html->link('一覧画面', ['controller' => 'MailReferences', 'action' => 'index']); ?>
    </div>
    <div class="navi_current"> > 新規追加画面</div>
</h3>


<div id="backbottun_margin">
    <?php

    echo $this->Form->create($mailReference, ['novalidate' => true, 'id' => 'mail_reference_form']);

    echo $this->Form->control('customer_name', ['label' => '顧客名称']);
    echo $this->Form->control('customer_ci', ['label' => '顧客名称略称']);
    echo $this->Form->control('ci_name', ['label' => 'アラーム名']);
    echo $this->Form->control('sender_mail_address', ['label' => 'メールアドレス']);

    echo $this->Form->control('type', [
        'type' => 'select',
        'label' => 'タイプ',
        'options' => [
            'error' => 'error',
            'normal' => 'normal',
        ],
        'multiple' => false,
        'empty' => '選択してください'
    ]);

    echo $this->element('MailReferences/macth_condition', [
        'mailReference' => $mailReference,
    ]);

    ?>

    <button type="submit">登録</button>

    <!-- フォームの終了 -->
    <?= $this->Form->end(); ?>

</div>

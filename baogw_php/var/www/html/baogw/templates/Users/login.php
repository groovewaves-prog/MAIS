<?php
?>

<div class="users form large-5 medium-7 columns">
    <?= $this->Form->create(null,['id'=>'login']) ?>
    <fieldset>
        <legend><?= __('Login') ?></legend>
        <?php
            echo $this->Form->control('username');
            echo $this->Form->control('password');
        ?>
    </fieldset>
    <div class="right btn_container"><?= $this->Form->button(__('Login'),['id'=>'loginbtn', 'class'=>'btn_brown']) ?></div>
    <?= $this->Form->end() ?>
</div>

<!-- 二重ログイン防止 -->
<script type="text/javascript">
    $("#login").submit(function(){
	       $("#loginbtn").prop('disabled', true);
    })
</script>

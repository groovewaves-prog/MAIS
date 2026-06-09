<?php
// $cakeDescription = 'CakePHP: the rapid development php framework';
$cakeDescription  = 'MAIS - ';
?>
<!DOCTYPE html>
<html>
<head>
    <?php if( $this->fetch('title')=='GwEvents' && $action =='index') : ?>
      <?php $refresh=(int)$this->getRequest()->getSession()->read('account_refresh');  ?>
      <!-- <meta http-equiv="refresh" content=<?= $refresh ?>> -->
    <?php endif; ?>

    <?= $this->Html->charset() ?>

    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title> <?= $cakeDescription ?> <?= $this->fetch('title') ?> -  <?= $action ?></title>

        <!-- // $this->Html->meta('icon') -->

    <?= $this->Html->css('base');?>
    <?= $this->Html->css('cake');?>
    <?= $this->Html->css('baogw') ?>


    <?php if($FLAG_PRIMARY): ?>
        <?= $this->Html->css('baogw-pri') ?>
        <link rel="icon" href="/baogw/favicon-pri.ico"/>
        <?php $TITLE="BAO Gateway Primary"; ?>
    <?php else: ?>
        <?= $this->Html->css('baogw-sec') ?>
        <link rel="icon" href="/baogw/favicon-sec.ico"/>
        <?php $TITLE="BAO Gateway Secondary"; ?>
    <?php endif; ?>

    <?= $this->Html->css('jquery.datetimepicker.min')?>
    <?= $this->Html->css('jquery-ui.min')?>
    <?= $this->Html->css('style.min')?>


    <?= $this->fetch('meta') ?>
    <?= $this->fetch('css') ?>
    <?= $this->Html->script('jquery')?>
    <?= $this->Html->script('jquery-ui.min')?>
    <?= $this->Html->script('jquery.datetimepicker.full.min')?>
    <?= $this->Html->script('jquery.floatThead')?>
    <?= $this->Html->script('baogw_funcs') ?>
    <?= $this->Html->script('dist/jstree.min') ?>
    <?= $this->fetch('script') ?>
</head>
<body>
    <nav id="js-top_bar" class="top-bar expanded head_range" data-topbar role="navigation">
        <ul class="title-area medium-2 columns" style="width:28%">
            <li class="name" style="background:">
            <h1 style="font-size:24px;margin:0px">
                <?= $this->Html->link(__($TITLE) . ' (' . $MASTER_SLAVE . ')', ['controller'=>'mainMenu','action' => 'index']) ?>
            </h1>
            </li>
        </ul>
        <div class="top-bar-section head_range" >
            <ul class="left">
              <li class="head_tip"><?= __('接続サーバ名：')?><br><?=  $CURRENT_HOSTNAME . '(' . $CURRENT_SERVER_IP . ')'?></li>
              <?php if($account_type_name) : ?>
              <li class="head_tip"><?= __('LoginID') . ": " .  $account_type_name . '<br>' . $account_full_name  ?></li>

            </ul>
            <ul class="right">
                <?php if(isset($kisysMainteFlag) == true) : ?>
                <li class="kisys_mainte">KISYSメンテナンス中</li>
                <?php endif; ?>
                <li class="head_tip">
                    <?php if( $this->fetch('title')=='GwEvents' && $action =='index') : ?>
                        <div id="time_refresh" style="float:left"></div>
                    <?php endif; ?>
                </li>
                <li class="name" style="float:right"><?= $this->Html->link(__('logout'), ['controller'=>'users','action'=>'logout'], ['style'=>'width:inherit;']) ?></li>
                <?php endif; ?>
            </ul>
        </div>
    </nav>
    <?= $this->Flash->render() ?>
    <div class="container clearfix">
        <?= $this->fetch('content') ?>
    </div>

    <footer style="text-align:center;background-color:#01545b;color:#ffffff;width:100%;left:0px;bottom:0px;position:fixed !important;">
        <p style="margin-bottom:0px;">COPYRIGHT © KDDI CORPORATION, ALL RIGHTS RESERVED.</p>
    </footer>
</body>

<?php if(isset($refresh)): ?>
<!-- Common JS Tail リフレッシュ表示 -->
<script>
    var refresh = <?= $refresh ?>;
    var count_refresh = refresh;
    var timer_id = null;
    var time_refresh = $("#time_refresh");
    var auto_refresh = $("#auto_refresh");

    // デフォルトチェック入りのときここから読み込みされる
    if (auto_refresh.prop("checked")) {
        setTimer();
    }

    // onclickで発火したときはbaogw_funcsからsetTimerが呼ばれる
    function setTimer() {
        timer_id = setInterval(countup_refresh, 1000);
        setTimeout(countup_refresh, 0);
    }

    // setIntervalの停止処理
    function deleteTimer() {
        time_refresh.text('');
        count_refresh = refresh;
        clearInterval(timer_id);
    }

    // カウントダウン処理
    // カウント終了またはチェック無しのときdeleteTimerが呼ばれてsetIntervalが止まる
    function countup_refresh() {
        if (auto_refresh.prop("checked")) {
            if (count_refresh > 0){
                time_refresh.text('次の自動リフレッシュまで' + count_refresh-- + '秒です。');
            } else {
                // カウント終了、タイマーを削除してからリロード
                deleteTimer();
                location.reload();
            }
        } else {
            // チェックがなかったらタイマー削除
            deleteTimer();
        }
    }

</script>
<?php endif; ?>

<!-- ページヘッダー固定 -->
<script>
  $(window).on('scroll', function() {
      $('#js-top_bar').toggleClass('fixed', $(this).scrollTop() > 45);
  });
</script>

<!-- 二重submit防止用 disabled処理 -->
<script type="text/javascript">
    $(".js-form").submit(function(){
	    $(".js-submit").prop('disabled', true);
        // $(".js-submit").prop('disabled', false);
    })
</script>

</html>

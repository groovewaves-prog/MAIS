<?php
use App\View\Helper\InputSetHelper;
?>
<?php
// phpinfo();
?>

<div class="gwEvents index columns content width_inherit" id="main_content" >



    <h3><div class="navi_reffer" ><?= $this->Html->link(__('Main Menu'), ['controller'=>'mainMenu','action' => 'index',]) ?></div> >
        <div class="navi_current"><?= __('Gw Events') ?></div></h3>

    <div border=1 class="btn_container_right">
        <?php
            echo $this->Html->link( __('Delayed Events') ,'#', ['id'=>'delayed_events','class'=>'btn_mediumvioletred', 'style'=>'font-size:1rem;', 'onclick'=>'openWindowDelayedEvents();']);
        ?>
    </div>

    <!-- 検索 -->
    <?= $this->Form->create(null, ['class'=>'js-form', 'type'=>'get', 'url'=>['controller'=>'GwEvents','action'=>'index',]])?>
    <?php  //フィルタフォームの開閉、ソート、オーダの保持
        $hiddens=[['filter_form_opened'=>$filter_form_opened],['sort'=>$sort],['direction'=>$direction],['refresh'=>$refresh]];
        echo $this->InputSet->hiddens($hiddens);
    ?>

    <div class="filter-title btn_blue" id="js-slide_btn"
            onclick="do_slide('#js-slide_btn', '#js-slide_bx','#filter_form_opened')"><?= __('[アラーム検索] ▲閉じる') ?></div>
    <div class="filter-title"><?= $this->InputSet->selectdispCount('display_count', $display_count); ?> </div>
    <!-- パトライトストップ -->
    <div border=1 class="btn_container right">
        <?php
            if ($account_type == 3 || array_intersect($usrgrp_names, $all_search_user_groups) || !array_intersect($usrgrp_names, $other_user_group)) {
                echo $this->Html->link( __('パトライトストップ') ,'#', ['id'=>'patolight_stop','class'=>'btn_red', 'style'=>'font-size:1rem;', 'onclick'=>'stop_patolite("' . $PATLITE_STOP_PAGE . '" );']);
            }
        ?>
    </div>
    <!-- パトライトストップ(VIP) -->
    <div border=1 class="btn_container_mid right">
        <?php
            if ($account_type == 3 || array_intersect($usrgrp_names, $all_search_user_groups) || !array_intersect($usrgrp_names, $other_user_group)) {
                echo $this->Html->link( __('パトライトストップ(VIP)') ,'#', ['id'=>'patolight_stop','class'=>'btn_red', 'style'=>'font-size:1rem;', 'onclick'=>'stop_patolite("' . $PATLITE_STOP_PAGE . '-vip" );']);
            }
        ?>
    </div>
    <!-- パトライトストップ(HOWCOM) -->
    <div border=1 class="btn_container_mid right">
        <?php
            if ($account_type == 3 || array_intersect($usrgrp_names, $all_search_user_groups) || in_array($howcom_user_group, $usrgrp_names)) {
                echo $this->Html->link( __("パトライトストップ($KDDI_MIYAZAKI)") ,'#', ['id'=>'patolight_stop_howcom','class'=>'btn_red', 'style'=>'font-size:1rem;', 'onclick'=>'stop_patolite("' . $PATLITE_STOP_PAGE . '-howcom" );']);
            }
        ?>
    </div>
    <div class="filter-title">
      <?=$this->Form->control(__('auto_refresh'),
                                ['type' =>'checkbox',
                                  'id'   =>'auto_refresh',
                                  'name' =>'auto_refresh',
                                  'onClick' => 'do_refresh("#auto_refresh","#refresh")',
                                  'label'=>['style'=>'font-size:1rem;',
                                           ]
                                ]
                           ); ?>
    </div>
    <div border=1 class="filter-title">
        <?= $this->Html->link( __('リフレッシュ') ,'#', ['class'=>'btn_blue', 'onclick'=>'location.reload()']);?>
    </div>

    <div id="js-slide_bx">
    <table class="filter">
        <tr><td colspan="13" class="filter-subtitle"><?= __('アラーム検索') ?></td></tr>
        <tr class="filter-condition">
            <td rowspan="2"><?= $this->InputSet->txtBx("gw_event_id", $gw_event_id, $gw_event_id_operetor, "num"); ?></td>
            <td rowspan="2"><?= $this->InputSet->dtFromTo("alarm_time_error", $alarm_time_error_from, $alarm_time_error_to,__('alarm_time_error_from'),__('alarm_time_error_to')) ?></td>
            <td rowspan="2"><?= $this->InputSet->dtFromTo("alarm_time_normal", $alarm_time_normal_from, $alarm_time_normal_to,__('alarm_time_normal_from'),__('alarm_time_normal_to') )?></td>
            <td rowspan="2"><?= $this->InputSet->chkBxGrp('alarm_status', $ALARM_STATUS_NAME, $alarm_status);?></td>
            <td rowspan="2"><?= $this->InputSet->txtBx("customer_name", $customer_name, $customer_name_operetor, "str", $currentUrl, "GwIncidents", "customer_name"); ?></td>
            <td rowspan="2"><?= $this->InputSet->txtBx("hostname", $hostname, $hostname_operetor, "str", $currentUrl, "GwIncidents", "hostname"); ?></td>
            <td rowspan="2"><?= $this->InputSet->txtBx("ci_name", $ci_name, $ci_name_operetor, "str", $currentUrl, "GwIncidents", "ci_name"); ?></td>
            <td rowspan="2"><?= $this->InputSet->txtBx("summary_error", $summary_error, $summary_error_operetor, "str"); ?></td>
            <td rowspan="2"><?= $this->InputSet->txtBx("summary_normal", $summary_normal, $summary_normal_operetor, "str"); ?></td>
            <td rowspan="2"><?= $this->InputSet->txtBx("device", $device, $device_operetor, "str", $currentUrl, "GwEvents", "device"); ?></td>
            <td>
            <?= $this->InputSet->radioBtns("approve_status", $approve_status, ["未承認","承認済み","両方"]);?>
            <div style="margin-top:20px;"></div>
            </td>
            <td rowspan="2"><?= $this->InputSet->chkBxGrp ("kisys_status", $SEND_STATUS, $kisys_status);?></td>
            <td rowspan="2">
              <?= $this->InputSet->txtBx("incidentid", $incidentid, $incidentid_operetor, "str"); ?>
              <div style="margin-top:70px;"><?= $this->InputSet->actionButtons(); ?></div>
              <div><?= __('Reset Description') ?></div>
            </td>
        </tr>
        <tr class="filter-condition">
          <td>
            <?= $this->InputSet->txtBx("op_comment", $op_comment, $op_comment_operetor, "str"); ?>
          </td>
        </tr>
        <tr>
          <td colspan="13" class="filter-subtitle"><?= __('列の 表示 / 非表示') ?></td>
        </tr>
        <tr class="filter-condition">
          <?= $this->InputSet->chkBxGrpHideBtn('disp_col', $COLUMNS_EVENTS, $disp_col);?>
        </tr>
    </table>
    <?= $this->Form->end(); ?>
    </div>

    <!-- ページネーション -->
    <?= $this->InputSet->pagenator()?>

    <!-- イベント一覧 -->
    <?= $this->Form->create(null, ['class'=>'js-form', 'type'=>'post','url'=>['controller'=>'GwEvents','action'=>'bulkUpdate']])?>
    <?php  //ソート、オーダの保持
        $hiddens=[['sort'=>$sort],['direction'=>$direction]];
        echo $this->InputSet->hiddens($hiddens);
    ?>
    <?= $this->InputSet->chkBx('all_check_flag_bulk_update', '', '', '',  0,
                                'all_checking("flag_bulk_update", this.checked);', 'btn_yellow left'); ?>
    <?= $this->Form->button(__('To BulkUpdate'),['style'=>'width:300px;height:25px;padding:0px;margin-left:10px;','class'=>'btn_brown js-submit']) ?>
    <table class="float_th">
        <thead>
            <tr>
                <th scope="col" class="col_check_flag"><?= __('チェック') ?><br><br></th>
                <th scope="col" class="col_gw_event_id">    <?= $this->Paginator->sort('GwEvents.gw_event_id', __('gw_event_id'), ['direction'=>'desc']) ?><br><br></th>
                <th scope="col" class="col_alarm_time_error"><?= $this->Paginator->sort('ErrorEvents.alarm_time', __('alarm_time_error'), ['direction'=>'desc']) ?><br><br></th>
                <th scope="col" class="col_alarm_time_normal"><?= $this->Paginator->sort('NormalEvents.alarm_time', __('alarm_time_normal'), ['direction'=>'desc']) ?><br><br></th>
                <th scope="col" class="col_alarm_status">   <?= $this->Paginator->sort('GwEvents.alarm_status', __('alarm_status'), ['direction'=>'desc']) ?><br><br></th>
                <th scope="col" class="col_customer_name">  <?= $this->Paginator->sort('GwIncidents.customer_name', __('customer_name'), ['direction'=>'desc']) ?><br><br></th>
                <th scope="col" class="col_hostname">       <?= $this->Paginator->sort('GwIncidents.hostname', __('hostname'), ['direction'=>'desc']) ?><br><br></th>
                <th scope="col" class="col_ci_name">        <?= $this->Paginator->sort('GwIncidents.ci_name', __('ci_name'), ['direction'=>'desc']) ?><br><br></th>
                <th scope="col" class="col_summary_error">  <?= $this->Paginator->sort('ErrorEvents.summary', __('summary_error'), ['direction'=>'desc']) ?><br><br></th>
                <th scope="col" class="col_summary_normal"> <?= $this->Paginator->sort('NormalEvents.summary', __('summary_normal'), ['direction'=>'desc']) ?><br><br></th>
                <th scope="col" class="col_device">         <?= $this->Paginator->sort('GwEvents.device', __('device'), ['direction'=>'desc']) ?><br><br></th>
                <th scope="col" class="col_detail_event">   <?= __('Detail Event') ?><br><br></th>
                <th scope="col" class="col_actions actions"><?= __('Actions') ?><br><br></th>
            </tr>
        </thead>
        <tbody>
            <?php
                $now_time = new DateTime();
            ?>
            <?php foreach ($gwIncidents as $gwIncident): ?>
                <?php
                    $error_event = $gwIncident->error_event;
                    $normal_event = $gwIncident->normal_event;
                    if (is_null($error_event) && is_null($normal_event)) {
                        // gwEventsにしかアラーム情報がない
                        foreach ($gwIncident->gw_events as $gw_event) {
                            if ($gw_event->alarm_status == 'error') {
                                $error_event = $gw_event;
                            } else if ($gw_event->alarm_status == 'normal') {
                                $normal_event = $gw_event;
                            } else if ($gw_event->alarm_status == 'sysnormal') {
                                $normal_event = $gw_event;
                            } else { // syserror, info, sec
                                $error_event = $gw_event;
                            }
                        }
                    }
                    $col_event_id = '';
                    $col_alarm_status = '';
                    $col_customer_ci = '';
                    $col_device = '';
                    if (!is_null($error_event)) { // エラーあり
                        $col_event_id = $error_event->gw_event_id;
                        $col_alarm_status = $error_event->alarm_status;
                        $col_customer_ci = $error_event->customer_ci;
                        $col_device = $error_event->device;
                    } else if (!is_null($normal_event)) { // ノーマルのみ
                        $col_event_id = $normal_event->gw_event_id;
                        $col_alarm_status = $normal_event->alarm_status;
                        $col_customer_ci = $normal_event->customer_ci;
                        $col_device = $normal_event->device;
                    }
                ?>
                <?php
                    $color_cancel = ["10", "20", "30", "31", "32", "33", "34", "35", "40", "41", "42", "43", "49", "60", "61", "62", "69", "70", "71", "72", "79"];
                    $status_code = [];
                    if (!is_null($error_event)) {
                        $status_code = InputSetHelper::explode(',', h($error_event->kisys_status));
                    } else if (!is_null($normal_event)) {
                        $status_code = InputSetHelper::explode(',', h($normal_event->kisys_status));
                    }
                    $tr_class = '';
                    if (!is_null($error_event) and in_array($status_code[0], $color_cancel)) {
                        $tr_class = 'row_color_cancel';
                    } elseif (!is_null($error_event) and !is_null($normal_event)) {
                        $tr_class = 'row_color_paired';
                    } elseif (!is_null($error_event) and $error_event->event_status==2 and $error_event->alarm_status=='error') {
                        $tr_class = 'row_color_paired';
                    } elseif (is_null($error_event) and !is_null($normal_event) and $normal_event->alarm_status=='normal') {
                        $tr_class = 'row_color_normal';
                    } elseif (preg_match("/^90/", $status_code[0])) {
                        $tr_class = 'row_color_maintenance';
                    } else {
                        $tr_class = 'row_color_' . h($col_alarm_status);
                    }
                    $tr_approved = '';
                    if (!is_null($error_event) and !is_null($normal_event)) {
                        if (!is_null($normal_event->checked_time)) {
                            $tr_approved = ' row_color_approved';
                        }
                    } else if (!is_null($error_event)) {
                        if (!is_null($error_event->checked_time)) {
                            $tr_approved = ' row_color_approved';
                        }
                    } else if (!is_null($normal_event)) {
                        if (!is_null($normal_event->checked_time)) {
                            $tr_approved = ' row_color_approved';
                        }
                    }
                ?>
                <tr class="<?= $tr_class . $tr_approved; ?>">
                    <td class="col_check_flag">
                        <?=$this->Form->checkbox('BulkUpdate.' . $gwIncident->gw_incident_id,
                                                    ['class' => 'flag_bulk_update',
                                                        'id' => 'id' . $gwIncident->gw_incident_id
                                                ]);?>
                        <?php
                            $alarm_time = null;
                            $checked_time = null;
                            if (!is_null($normal_event)) {
                                $alarm_time = new DateTime($normal_event->alarm_time->format('Y/m/d H:i:s'));
                                $checked_time = $normal_event->checked_time;
                            } else if (!is_null($error_event)) {
                                $alarm_time = new DateTime($error_event->alarm_time->format('Y/m/d H:i:s'));
                                $checked_time = $error_event->checked_time;
                            }
                        ?>
                        <?= $newflag=$this->InputSet->newFlag($now_time, $alarm_time, $checked_time, $FLAG_NEW_DAY, $FLAG_NEW_HOUR); ?>
                    </td>
                    <td class="col_gw_event_id">
                        <?= $this->Form->label('id' . $col_event_id, $col_event_id ) ?>
                        <!-- ハウコムフラグ -->
                        <?php
                            if(($account_type == 3 || array_intersect($usrgrp_names, $all_search_user_groups)) && in_array($gwIncident->customer_name, $howcom_names)){
                                echo '<span style="display: inline-block;" class="flag_howcom">' . $KDDI_MIYAZAKI . '</span>';
                            }
                        ?>
                        <!-- VIPフラグ -->
                        <?php
                            if(in_array($gwIncident->customer_name, $vip_names)){
                                echo '<span style="display: inline-block;" class="flag_jp1">JP1</span>';
                            }
                        ?>
                    </td>
                    <td class="col_alarm_time_error">
                    <?php if(!is_null($error_event)) {
                        echo $error_event->alarm_time->format('Y/m/d H:i:s');
                    }
                    ?></td>
                    <td class="col_alarm_time_normal">
                    <?php if(!is_null($normal_event)) {
                        echo $normal_event->alarm_time->format('Y/m/d H:i:s');
                    }
                    ?></td>
                    <td class="col_alarm_status"> <?= h($col_alarm_status) ?></td>
                    <?php if($col_customer_ci=="OPSUPPSYS"): ?>
                        <td class="col_customer_name"><?= h($gwIncident->customer_name) ?></td>
                    <?php else: ?>
                        <td class="col_customer_name">
                            <?= $this->Html->link($gwIncident->customer_name, "javascript:void(0)", ["onClick"=>"openWindowCMDB('".$CMDB_WEB_URL."','customer_name','".$col_customer_ci."','');return false;","class"=>"underbar"]); ?>
                        </td>
                    <?php endif; ?>
                    <?php if($col_customer_ci=="OPSUPPSYS"): ?>
                        <td class="col_hostname"><?= h($gwIncident->hostname) ?></td>
                    <?php else: ?>
                        <td class="col_hostname">
                            <?= $this->Html->link($gwIncident->hostname, "javascript:void(0)", ["onClick"=>"openWindowCMDB('".$CMDB_WEB_URL."','hostname','".$col_customer_ci."','".$gwIncident->hostname."');return false;","class"=>"underbar"]); ?>
                        </td>
                    <?php endif; ?>
                    <td class="col_ci_name"><?= h($gwIncident->ci_name) ?></td>
                    <td class="col_summary_error">
                    <?php if(!is_null($error_event)) {
                        echo $this->InputSet->genShortMsg(h($error_event->summary), 50);
                    }
                    ?></td>
                    <td class="col_summary_normal">
                    <?php if(!is_null($normal_event)) {
                        echo $this->InputSet->genShortMsg(h($normal_event->summary), 50);
                    }
                    ?></td>
                    <?php if($col_customer_ci=="OPSUPPSYS"): ?>
                        <td class="col_device"><?= h($col_device) ?></td>
                    <?php else: ?>
                        <td class="col_device">
                            <?= $this->Html->link($col_device, "javascript:void(0)", ["onClick"=>"openWindowCMDB('".$CMDB_WEB_URL."','device','".$col_customer_ci."','".$gwIncident->hostname."');return false;","class"=>"underbar"]); ?>
                        </td>
                    <?php endif; ?>
                    <td class="col_detail_event">   <?= $this->Html->link(__('Detail'), ['action'=>'edit', $gwIncident->gw_incident_id],['class'=>'btn_green',]) ?><br>
                    <?php
                        $error_send_status = is_null($error_event) ? null : $error_event->kisys_status;
                        $normal_send_status = is_null($normal_event) ? null : $normal_event->kisys_status;
                        echo $this->InputSet->sendStatusUrl(h($error_send_status), h($normal_send_status), h($gwIncident->kisys_incidentid), 'underbar');
                    ?>
                    </td>
                    <td class="col_actions actions">
                    <?php
                        // // 1:Active, 2:Close 以外のアラートはKISYS起票しないため、ボタン表示しない
                        // // 0:New はキャンセル待ちアラートとして一覧に表示されるため、ボタンだけ非表示としている
                        $not_show_send_button_event_status = [0, 99];
                        $not_show_send_button_alarm_status = ['syserror', 'sysnormal', 'sec', 'info'];
                        if (!is_null($error_event)) {
                            if (in_array($error_event->event_status, $not_show_send_button_event_status)) {
                                // ボタン非表示
                            } else if (in_array($error_event->alarm_status, $not_show_send_button_alarm_status)) {
                                // ボタン非表示
                            } else {
                                $not_show_send_button_kisys_status = ['9', '49', '59', '69', '79'];
                                $status_code = InputSetHelper::explode(',', h($error_event->kisys_status));
                                // error報自身がKISYS連携中かどうか
                                $has_been_send_kisys = (count($status_code) > 0 && in_array($status_code[0], $not_show_send_button_kisys_status));
                                if (!$has_been_send_kisys && InputSetHelper::mb_strlen($gwIncident->kisys_incidentid) == 0) {
                                    echo $this->Html->link(__('Send Error'), array('action'=>'sendKisys', $error_event->gw_event_id), array('class'=>'btn_small_red', 'confirm'=>'K-ISYS起票する'));
                                } else {
                                    // ボタン非表示
                                }
                            }
                        }
                        if (!is_null($normal_event)) {
                            if (in_array($normal_event->event_status, $not_show_send_button_event_status)) {
                                // ボタン非表示
                            } else if (in_array($normal_event->alarm_status, $not_show_send_button_alarm_status)) {
                                // ボタン非表示
                            } else {
                                if (InputSetHelper::mb_strlen($gwIncident->kisys_incidentid) == 0) {
                                    // ボタン非表示
                                } else {
                                    $not_show_send_button_kisys_status = ['0', '40', '50', '60', '70', '9', '49', '59', '69', '79'];
                                    $status_code = InputSetHelper::explode(',', h($normal_event->kisys_status));
                                    // normal報自身がKISYS連携済みor連携中かどうか
                                    $has_been_send_kisys = (count($status_code) > 0 && in_array($status_code[0], $not_show_send_button_kisys_status));
                                    if ($has_been_send_kisys) {
                                        // ボタン非表示
                                    } else {
                                        echo $this->Html->link(__('Update Normal'), array('action'=>'sendKisys', $normal_event->gw_event_id), array('class'=>'btn_green', 'confirm'=>'K-ISYS追記する'));
                                    }
                                }
                            }
                        }
                    ?><br>
                    </td>
                </tr>
            <?php endforeach; ?>
        </tbody>
    </table>

    <!-- ページネーション -->
    <?= $this->InputSet->pagenator()?>

    <?= $this->Form->button(__('To BulkUpdate'),['style'=>'width:200px;height:75px;padding:0px;','class'=>'btn_brown js-submit']) ?>
    <?= $this->Form->end(); ?>

</div>



<!-- アラーム検索の検索方式で 空白/非空白選択時 に検索値をdisableにする(復元用) -->
<script>
    disable_operetor('#customer_name_operetor', '#customer_name');
    disable_operetor('#hostname_operetor'     , '#hostname');
    disable_operetor('#ci_name_operetor'      , '#ci_name');
    disable_operetor('#summary_error_operetor', '#summary_error');
    disable_operetor('#summary_normal_operetor', '#summary_normal');
    disable_operetor('#device_operetor'       , '#device');
    disable_operetor('#op_comment_operetor'   , '#op_comment');
    disable_operetor('#kisys_status_operetor' , '#kisys_status');
</script>

<!-- アコーディオン GwEvents GwRules index -->
<script>
    init_slide('#js-slide_btn', '#js-slide_bx','#filter_form_opened');
</script>

<?php if($to_check=="1"): ?>
<!-- 一括チェックボックス復元 GwEvents GwRules index -->
<script>
    restore_check_boxs('#id', <?= $to_check; ?>, <?php echo json_encode($bulk_update_ids, JSON_HEX_TAG | JSON_HEX_AMP | JSON_HEX_APOS | JSON_HEX_QUOT); ?>);
</script>
<?php endif; ?>

<!-- 日付カレンダー入力 Common-->
<script>
    $.datetimepicker.setLocale('ja');
    $('.datetimepicker').datetimepicker();
</script>

<!-- テーブルタイトル固定 Common -->
<script>
    $(window).scroll( function(){
            // $('table.float_th').floatThead({top:44});
            $('table.float_th').floatThead({top:44});
    });
</script>


<!-- 行の非表示機能復元 GwEvents-->
<script>
    <?php if(count($disp_col)>1):?>
    hideColumn(".col_gw_event_id",   "" + <?= in_array('gw_event_id',   $disp_col) ?> + "");
    hideColumn(".col_alarm_time_error",    "" + <?= in_array('alarm_time_error',    $disp_col) ?> + "");
    hideColumn(".col_alarm_time_normal",    "" + <?= in_array('alarm_time_normal',    $disp_col) ?> + "");
    hideColumn(".col_alarm_status",  "" + <?= in_array('alarm_status',  $disp_col) ?> + "");
    hideColumn(".col_checked_time",  "" + <?= in_array('checked_time',  $disp_col) ?> + "");
    hideColumn(".col_customer_name", "" + <?= in_array('customer_name', $disp_col) ?> + "");
    hideColumn(".col_hostname",      "" + <?= in_array('hostname',      $disp_col) ?> + "");
    hideColumn(".col_ci_name",       "" + <?= in_array('ci_name',       $disp_col) ?> + "");
    hideColumn(".col_device",        "" + <?= in_array('device',        $disp_col) ?> + "");
    hideColumn(".col_summary_error", "" + <?= in_array('summary_error', $disp_col) ?> + "");
    hideColumn(".col_summary_normal","" + <?= in_array('summary_normal',$disp_col) ?> + "");
    hideColumn(".col_actions",       "" + <?= in_array('actions',       $disp_col) ?> + "");
    <?php endif; ?>
    $('.col_check_flag').css('width','50px');
</script>

<!-- パトライトストップ -->
<script>
function stop_patolite(url) {
    // if (!window.confirm( '<?= __('パトライトを止めますか？') ?>' )) {
    //     return false;
    // }
    $.ajax({
        url: url,
        // url: '/baogw/gw-events/stop-patolite',
        type: "POST",
        data: { name : "" },
        dataType: "text",
        success : function(response){
            if (response > 0) {
                alert('<?= __('停止失敗:スクリプトファイルが存在しない、または実行権限が無い可能性があります。') ?>')
            }
        },
        error: function(){
            alert('<?= __('停止失敗:ページが存在しない可能性があります。') ?>');
        }
    });
}
</script>

<?php if($refresh=="1"): ?>
<!-- チェックボックス復元 -->
<script>
    $('#auto_refresh').prop('checked', true);
</script>
<?php endif; ?>

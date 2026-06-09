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

<button class="btn_blue" onclick="window.close();" style="width:200px;height:45px;margin:10px;">キャンセル</button>
<?= $this->Form->input( __($fieald_name), array('type' => 'text', 'name' => $fieald_name, 'id' => 'searchWord', 'style'=> 'width:95%;margin:auto;', 'label' => ['style'=> 'cursor:text;padding-left:10px;'],));?>
<table id="result">
    <tr><th scope="col"><?= $this->Paginator->sort($fieald_name) ?></th></tr>
    <?php foreach ($gwTables as $gwTable):; $fieald=h($gwTable[$fieald_name]);?>
    <tr><td><?= $this->Html->link( htmlspecialchars_decode($fieald, ENT_QUOTES) ,'#',['class'=>'link_style',
                                                 'onClick'=>'setFormInput("' . $fieald  . '", "' . $input_elm_id . '")']);?></td></tr>
    <?php endforeach; ?>
</table>

<script>
function setFormInput(select_name, input_elm_id) {

    if (select_name != "") {
        if (!window.opener || window.opener.closed){
            window.alert('メインウィンドウが見当たりません。');

        } else {

            select_name = htmlspecialchars_decode(select_name);
            input_type=window.opener.document.getElementById(input_elm_id).type
            if (input_type == 'textarea'){
                now_value = window.opener.document.getElementById(input_elm_id).value
                input_value = now_value + select_name + ",\n";
            } else {
                input_value = select_name;
            }
            window.opener.document.getElementById(input_elm_id).value = input_value;
        }
    }
    window.close();
}

function htmlspecialchars_decode(ch){
    ch = ch.replace(/&amp;/g, '&')
    ch = ch.replace(/&lt;/g, '<')
    ch = ch.replace(/&gt;/g, '>')
    ch = ch.replace(/&quot;/g, '"')
    ch = ch.replace(/&apos;/g, "'")
    ch = ch.replace(/&#039;/g, "'")
    return ch ;
}
</script>

<script>
    //リアルタイム検索用関数生成
    searchWord = function () {
                var searchText = $(this).val(),
                    targetText;

                $('#result tr').each(function(){
                  $(this).children().each(function(){
                    targetText = $(this).not('th').text();
                    if (targetText) {
                      if (targetText.indexOf(searchText) == -1) {
                        $(this)[0].style.display='none';
                      } else {
                        $(this)[0].style.display='';
                      }
                    }
                  });
                });
    };

    //searchWordの実行
    $('#searchWord').on('input', searchWord);
</script>

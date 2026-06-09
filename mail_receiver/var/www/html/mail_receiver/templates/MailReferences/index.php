<?php
use Cake\Core\Configure;
use Cake\Routing\Router;

$this->assign('tab_title', 'index');
$this->Html->css('baorw_cp', ['block' => true]);
?>

<title>MailReferences</title>

<h1>一覧画面</h1>

<p class="navi_reffer">
    <?= $this->Html->link('新規追加', ['controller' => 'MailReferences', 'action' => 'add']); ?>
</p>

<?= $this->Form->create(null, ['type' => 'get']) ?>
<table class="filter">
    <tr>
        <td colspan="3" class="filter-subtitle">検索</td>
    </tr>
    <tr class="filter-condition">
        <td>
            <?=
                $this->Form->control('customer_name', [
                    'label' => '顧客名称',
                    'value' => $this->getRequest()->getQuery('customer_name')
                ]);
            ?>
            <p>を含む</p>
        </td>
        <td>
            <?=
                $this->Form->control('sender_mail_address', [
                    'label' => 'メールアドレス',
                    'value' => $this->getRequest()->getQuery('sender_mail_address')
                ]);
            ?>
            <p>を含む</p>
        </td>
        <td>
            <button type="submit">検索</button>
        </td>
    </tr>
</table>
<?= $this->Form->end() ?>

<table class="float_th">
    <tr>
        <th style="width:70px;"><?= $this->Paginator->sort('MailReferences.id', 'ID'); ?></th>
        <th><?= $this->Paginator->sort('MailReferences.customer_name', '顧客名称'); ?></th>
        <th><?= $this->Paginator->sort('MailReferences.customer_ci', '顧客名称略称'); ?></th>
        <th><?= $this->Paginator->sort('MailReferences.ci_name', 'アラーム名'); ?></th>
        <th><?= $this->Paginator->sort('MailReferences.sender_mail_address', 'メールアドレス'); ?></th>
        <th><?= $this->Paginator->sort('MailReferences.type', 'タイプ'); ?></th>
        <th><?= $this->Paginator->sort('MailReferences.analysis_conditions', '分析条件'); ?></th>
        <th><?= $this->Paginator->sort('MailReferences.update_time', '最終更新時間'); ?></th>
        <th>編集画面へ</th>
        <th>削除</th>
    </tr>

    <?php foreach ($mailReferences as $mailreference) : ?>
        <tr>
            <td><?= $mailreference->id ?></td>
            <td style="word-wrap:break-word;">
                <?= $mailreference->customer_name ?>
            </td>
            <td style="word-wrap:break-word;">
                <?= $mailreference->customer_ci ?>
            </td>
            <td style="word-wrap:break-word;">
                <?= $mailreference->ci_name ?>
            </td>
            <td style="word-wrap:break-word;">
                <?= $mailreference->sender_mail_address ?>
            </td>
            <td>
                <?= $mailreference->type ?>
            </td>
            <td style="word-wrap:break-word;">
                <?php
                    $matchConditions = Configure::read('matchConditions');

                    // JSONをオブジェクトに変換
                    $analysisConditions = json_decode($mailreference->analysis_conditions);

                    // オブジェクトから各フォームのデータを切り取って変数に格納
                    $subject = implode('、', $analysisConditions->title->keyword);
                    $subjectMatchCondition = isset($matchConditions[$analysisConditions->title->search_type])
                        ? $matchConditions[$analysisConditions->title->search_type] : null;
                    $body = implode('、', $analysisConditions->content->keyword);
                    $bodyMatchCondition = isset($matchConditions[$analysisConditions->content->search_type])
                        ? $matchConditions[$analysisConditions->content->search_type] : null;

                    // 分析条件表示テンプレート作成
                    $analysisConditionsDisplay =
                        "件名：{$subject}<br>
                        一致条件：{$subjectMatchCondition}<br>
                        本文：{$body}<br>
                        一致条件：{$bodyMatchCondition}";

                    // テンプレートにはめたものを表示
                    echo $analysisConditionsDisplay;
                ?>
            </td>
            <td>
                <?= $mailreference->update_time ?>
            </td>
            <td>
                <p>
                    <?= $this->Html->link('編集する', ['controller' => 'MailReferences', 'action' => 'edit', $mailreference->id]); ?>
                </p>
            </td>
            <td>
                <?= $this->Form->postLink(
                        '削除',
                        ['action' => 'delete', $mailreference->id],
                        ['confirm' => 'id' . $mailreference->id . 'のレコードを削除してもよいですか？']
                    ); ?>
            </td>
        </tr>
    <?php endforeach; ?>

</table>

<div id="pageNumber">
    <div>
        <ul class="pagination">
            <li>
                <?php
                if ($this->Paginator->hasPrev()) {
                    echo $this->Paginator->prev('< 前へ');
                }
                ?>
            </li>
            <li>
                <?php
                if ($this->Paginator->hasNext()) {
                    echo $this->Paginator->next('次へ >');
                }
                ?>
            </li>
        </ul>
    </div>
    <div><?= $this->Paginator->counter('{{end}} / {{count}} 件 {{page}} / {{pages}} ページ'); ?></div>
</div>

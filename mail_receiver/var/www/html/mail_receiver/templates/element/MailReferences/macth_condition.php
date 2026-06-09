<?php
use Cake\Core\Configure;
$macthConditionCss = $this->Form->error('analysis_conditions') ? 'error' : null;
?>

<div class="input <?= $macthConditionCss ?>">
    <label>分析条件</label>
    <!-- 件名フォーム -->
    <table id="macth_condition">
        <tr>
            <td>検索文字列</td>
            <td>一致条件</td>
        </tr>
        <tr>
            <!-- 件名フォーム -->
            <td>
                <label>件名</label>
                <?php
                    for ($i = 0; $i < 3; $i++) {
                        echo $this->Form->control('conditions[title][keyword][]', [
                            'maxLength' => 65,
                            'label' => false,
                            'value' => isset($mailReference['conditions']['title']['keyword'][$i])
                                ? $mailReference['conditions']['title']['keyword'][$i] : null,
                        ]);
                    }
                ?>
            </td>

            <!-- 件名の一致条件選択 -->
            <td>
                <?= $this->Form->control('conditions[title][search_type]', [
                    'default' => 'contain',
                    'type' => 'select',
                    'label' => '一致条件',
                    'options' => Configure::read('matchConditions'),
                    'value' => isset($mailReference['conditions']['title']['search_type'])
                        ? $mailReference['conditions']['title']['search_type'] : '',
                    'empty' => '選択してください',
                ]); ?>
            </td>
        </tr>
        <tr>
            <!-- 本文フォーム -->
            <td>
                <label>本文</label>
                <?php
                    for ($i = 0; $i < 3; $i++) {
                        echo $this->Form->control('conditions[content][keyword][]', [
                            'maxLength' => 65,
                            'label' => false,
                            'value' => isset($mailReference['conditions']['content']['keyword'][$i])
                                ? $mailReference['conditions']['content']['keyword'][$i] : null,
                        ]);
                    }
                ?>
            </td>

            <!-- 本文の一致条件選択 -->
            <td>
                <?= $this->Form->control('conditions[content][search_type]', [
                    'default' => 'contain',
                    'type' => 'select',
                    'label' => '一致条件',
                    'options' => Configure::read('matchConditions'),
                    'value' => isset($mailReference['conditions']['content']['search_type'])
                        ? $mailReference['conditions']['content']['search_type'] : '',
                    'empty' => '選択してください',
                ]); ?>
            </td>
        </tr>
    </table>
    <?= $this->Form->error('analysis_conditions') ?>
</div>

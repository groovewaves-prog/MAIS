<?php
namespace App\Model\Table;

use Cake\ORM\Table;
use Cake\Core\Configure;

class AppTable extends Table
{
    public static function defaultConnectionName(): string
    {
        if (file_exists(Configure::read('filePath.test'))) {
            // 片寄テスト
            return 'local';
        } elseif (file_exists(Configure::read('filePath.primary'))) {
            // primaryあり
            return 'default';
        } else {
            return 'standby';
        }
    }
}

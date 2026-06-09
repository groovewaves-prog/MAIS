<?php
namespace App\Model\Entity;

use Cake\ORM\Entity;

class Host extends Entity {
    protected $_accessible = [
        '*' => true,
        'hostid' => false
    ];
}

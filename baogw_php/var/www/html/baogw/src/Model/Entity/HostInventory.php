<?php
namespace App\Model\Entity;

use Cake\ORM\Entity;

class HostInventory extends Entity {

    protected $_accessible = [
        '*' => true,
        'hostid' => false
    ];
}

<?php
namespace App\Model\Entity;

use Cake\ORM\Entity;

class UsersGroup extends Entity {
    protected $_accessible = [
        '*' => true,
        'id' => false
    ];
}

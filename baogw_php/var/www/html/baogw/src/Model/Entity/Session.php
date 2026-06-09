<?php
namespace App\Model\Entity;

use Cake\ORM\Entity;

class Session extends Entity{
    protected $_accessible = [
        '*' => true,
        'sessionid' => false
    ];
}

<?php
namespace App\Model\Entity;

use Cake\ORM\Entity;

class GwEvent extends Entity {

    protected $_accessible = [
        '*' => true,
        'gw_eventid' => false
    ];
}

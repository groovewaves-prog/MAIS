<?php
namespace App\Model\Entity;

use Cake\ORM\Entity;

class GwRescueEvent extends Entity{

    protected $_accessible = [
        '*' => true,
        'gw_event_id' => false
    ];
}

<?php
namespace App\Model\Entity;

use Cake\ORM\Entity;

class Usrgrp extends Entity {
    protected $_accessible = [
        '*' => true,
        'usrgrpid' => false
    ];
}

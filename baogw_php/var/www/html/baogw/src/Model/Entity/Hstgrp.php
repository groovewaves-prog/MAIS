<?php
namespace App\Model\Entity;

use Cake\ORM\Entity;

/**
 * Hstgrp Entity
 *
 * @property int $groupid
 * @property string $name
 * @property int $internal
 * @property int $flags
 *
 * @property \App\Model\Entity\Host[] $hosts
 * @property \App\Model\Entity\Maintenance[] $maintenances
 * @property \App\Model\Entity\User[] $users
 */
class Hstgrp extends Entity
{

    /**
     * Fields that can be mass assigned using newEntity() or patchEntity().
     *
     * Note that when '*' is set to true, this allows all unspecified fields to
     * be mass assigned. For security purposes, it is advised to set '*' to false
     * (or remove it), and explicitly make individual fields accessible as needed.
     *
     * @var array
     */
    protected $_accessible = [
        '*' => true,
        'groupid' => false
    ];
}

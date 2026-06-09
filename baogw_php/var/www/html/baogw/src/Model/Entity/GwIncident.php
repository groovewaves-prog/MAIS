<?php
namespace App\Model\Entity;

use Cake\ORM\Entity;

/**
 * GwIncident Entity
 *
 * @property int $gw_incident_id
 * @property int $incident_status
 * @property \Cake\I18n\FrozenTime $update_time
 * @property string $customer_name
 * @property string $hostname
 * @property string $ci_name
 * @property string $kisys_incidentid
 *
 * @property \App\Model\Entity\GwIncident $gw_incident
 */
class GwIncident extends Entity
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
        'gw_incident_id' => false
    ];
}

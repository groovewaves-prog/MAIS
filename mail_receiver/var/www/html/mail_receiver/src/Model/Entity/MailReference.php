<?php
namespace App\Model\Entity;

use Cake\ORM\Entity;

/**
 * MailReference Entity
 *
 * @property int $id
 * @property string $sender_mail_address
 * @property int|null $is_invalid
 * @property string $customer_ci
 * @property string $customer_name
 * @property string $type
 * @property string $analysis_conditions
 * @property \Cake\I18n\FrozenTime|null $update_time
 * @property string|null $update_user
 */
class MailReference extends Entity
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
        'sender_mail_address' => true,
        'is_invalid' => true,
        'customer_ci' => true,
        'customer_name' => true,
        'type' => true,
        'analysis_conditions' => true,
        'update_time' => true,
        'update_user' => true,
        'ci_name' => true
    ];
}

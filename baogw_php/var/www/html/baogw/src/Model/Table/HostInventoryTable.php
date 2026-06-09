<?php
namespace App\Model\Table;

use Cake\ORM\Query;
use Cake\ORM\RulesChecker;
use Cake\ORM\Table;
use Cake\Validation\Validator;

class HostInventoryTable extends Table {

    public static function defaultConnectionName(): string{
        return 'zabbix';
    }

    public function initialize(array $config): void {
        parent::initialize($config);

        $this->setTable('host_inventory');
        $this->setDisplayField('name');
        $this->setPrimaryKey('hostid');
    }

    public function validationDefault(Validator $validator): \Cake\Validation\Validator {
        $validator
            ->allowEmpty('hostid', 'create');

        $validator
            ->integer('inventory_mode')
            ->requirePresence('inventory_mode', 'create')
            ->notEmpty('inventory_mode');

        $validator
            ->requirePresence('type', 'create')
            ->notEmpty('type');

        $validator
            ->requirePresence('type_full', 'create')
            ->notEmpty('type_full');

        $validator
            ->requirePresence('name', 'create')
            ->notEmpty('name');

        $validator
            ->requirePresence('alias', 'create')
            ->notEmpty('alias');

        $validator
            ->requirePresence('os', 'create')
            ->notEmpty('os');

        $validator
            ->requirePresence('os_full', 'create')
            ->notEmpty('os_full');

        $validator
            ->requirePresence('os_short', 'create')
            ->notEmpty('os_short');

        $validator
            ->requirePresence('serialno_a', 'create')
            ->notEmpty('serialno_a');

        $validator
            ->requirePresence('serialno_b', 'create')
            ->notEmpty('serialno_b');

        $validator
            ->requirePresence('tag', 'create')
            ->notEmpty('tag');

        $validator
            ->requirePresence('asset_tag', 'create')
            ->notEmpty('asset_tag');

        $validator
            ->requirePresence('macaddress_a', 'create')
            ->notEmpty('macaddress_a');

        $validator
            ->requirePresence('macaddress_b', 'create')
            ->notEmpty('macaddress_b');

        $validator
            ->requirePresence('hardware', 'create')
            ->notEmpty('hardware');

        $validator
            ->requirePresence('hardware_full', 'create')
            ->notEmpty('hardware_full');

        $validator
            ->requirePresence('software', 'create')
            ->notEmpty('software');

        $validator
            ->requirePresence('software_full', 'create')
            ->notEmpty('software_full');

        $validator
            ->requirePresence('software_app_a', 'create')
            ->notEmpty('software_app_a');

        $validator
            ->requirePresence('software_app_b', 'create')
            ->notEmpty('software_app_b');

        $validator
            ->requirePresence('software_app_c', 'create')
            ->notEmpty('software_app_c');

        $validator
            ->requirePresence('software_app_d', 'create')
            ->notEmpty('software_app_d');

        $validator
            ->requirePresence('software_app_e', 'create')
            ->notEmpty('software_app_e');

        $validator
            ->requirePresence('contact', 'create')
            ->notEmpty('contact');

        $validator
            ->requirePresence('location', 'create')
            ->notEmpty('location');

        $validator
            ->requirePresence('location_lat', 'create')
            ->notEmpty('location_lat');

        $validator
            ->requirePresence('location_lon', 'create')
            ->notEmpty('location_lon');

        $validator
            ->requirePresence('notes', 'create')
            ->notEmpty('notes');

        $validator
            ->requirePresence('chassis', 'create')
            ->notEmpty('chassis');

        $validator
            ->requirePresence('model', 'create')
            ->notEmpty('model');

        $validator
            ->requirePresence('hw_arch', 'create')
            ->notEmpty('hw_arch');

        $validator
            ->requirePresence('vendor', 'create')
            ->notEmpty('vendor');

        $validator
            ->requirePresence('contract_number', 'create')
            ->notEmpty('contract_number');

        $validator
            ->requirePresence('installer_name', 'create')
            ->notEmpty('installer_name');

        $validator
            ->requirePresence('deployment_status', 'create')
            ->notEmpty('deployment_status');

        $validator
            ->requirePresence('url_a', 'create')
            ->notEmpty('url_a');

        $validator
            ->requirePresence('url_b', 'create')
            ->notEmpty('url_b');

        $validator
            ->requirePresence('url_c', 'create')
            ->notEmpty('url_c');

        $validator
            ->requirePresence('host_networks', 'create')
            ->notEmpty('host_networks');

        $validator
            ->requirePresence('host_netmask', 'create')
            ->notEmpty('host_netmask');

        $validator
            ->requirePresence('host_router', 'create')
            ->notEmpty('host_router');

        $validator
            ->requirePresence('oob_ip', 'create')
            ->notEmpty('oob_ip');

        $validator
            ->requirePresence('oob_netmask', 'create')
            ->notEmpty('oob_netmask');

        $validator
            ->requirePresence('oob_router', 'create')
            ->notEmpty('oob_router');

        $validator
            ->requirePresence('date_hw_purchase', 'create')
            ->notEmpty('date_hw_purchase');

        $validator
            ->requirePresence('date_hw_install', 'create')
            ->notEmpty('date_hw_install');

        $validator
            ->requirePresence('date_hw_expiry', 'create')
            ->notEmpty('date_hw_expiry');

        $validator
            ->requirePresence('date_hw_decomm', 'create')
            ->notEmpty('date_hw_decomm');

        $validator
            ->requirePresence('site_address_a', 'create')
            ->notEmpty('site_address_a');

        $validator
            ->requirePresence('site_address_b', 'create')
            ->notEmpty('site_address_b');

        $validator
            ->requirePresence('site_address_c', 'create')
            ->notEmpty('site_address_c');

        $validator
            ->requirePresence('site_city', 'create')
            ->notEmpty('site_city');

        $validator
            ->requirePresence('site_state', 'create')
            ->notEmpty('site_state');

        $validator
            ->requirePresence('site_country', 'create')
            ->notEmpty('site_country');

        $validator
            ->requirePresence('site_zip', 'create')
            ->notEmpty('site_zip');

        $validator
            ->requirePresence('site_rack', 'create')
            ->notEmpty('site_rack');

        $validator
            ->requirePresence('site_notes', 'create')
            ->notEmpty('site_notes');

        $validator
            ->requirePresence('poc_1_name', 'create')
            ->notEmpty('poc_1_name');

        $validator
            ->requirePresence('poc_1_email', 'create')
            ->notEmpty('poc_1_email');

        $validator
            ->requirePresence('poc_1_phone_a', 'create')
            ->notEmpty('poc_1_phone_a');

        $validator
            ->requirePresence('poc_1_phone_b', 'create')
            ->notEmpty('poc_1_phone_b');

        $validator
            ->requirePresence('poc_1_cell', 'create')
            ->notEmpty('poc_1_cell');

        $validator
            ->requirePresence('poc_1_screen', 'create')
            ->notEmpty('poc_1_screen');

        $validator
            ->requirePresence('poc_1_notes', 'create')
            ->notEmpty('poc_1_notes');

        $validator
            ->requirePresence('poc_2_name', 'create')
            ->notEmpty('poc_2_name');

        $validator
            ->requirePresence('poc_2_email', 'create')
            ->notEmpty('poc_2_email');

        $validator
            ->requirePresence('poc_2_phone_a', 'create')
            ->notEmpty('poc_2_phone_a');

        $validator
            ->requirePresence('poc_2_phone_b', 'create')
            ->notEmpty('poc_2_phone_b');

        $validator
            ->requirePresence('poc_2_cell', 'create')
            ->notEmpty('poc_2_cell');

        $validator
            ->requirePresence('poc_2_screen', 'create')
            ->notEmpty('poc_2_screen');

        $validator
            ->requirePresence('poc_2_notes', 'create')
            ->notEmpty('poc_2_notes');

        return $validator;
    }
}

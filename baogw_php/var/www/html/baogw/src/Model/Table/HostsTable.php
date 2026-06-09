<?php
namespace App\Model\Table;

use Cake\ORM\Query;
use Cake\ORM\RulesChecker;
use Cake\ORM\Table;
use Cake\Validation\Validator;

class HostsTable extends Table {

    public static function defaultConnectionName(): string{
        return 'zabbix';
    }

    public function beforeFind(\Cake\Event\EventInterface $event, $entity) {
      //status 3 のテンプレートと、flags2の変数を除く
      $entity = $entity->where(['status is not' => '3' ])
                       ->where(['flags is not'  => '2' ]);
      return $entity;
    }

    public function initialize(array $config): void {
        parent::initialize($config);

        $this->setTable('hosts');
        $this->setDisplayField('name');
        $this->setPrimaryKey('hostid');

        //zabbixバージョンアップによりGroupsがHstgrpに変更
        $this->belongsToMany('Hstgrp', [
            'foreignKey' => 'host_id',
            'targetForeignKey' => 'group_id',
            'joinTable' => 'hosts_groups'
        ]);
        $this->belongsToMany('Maintenances', [
            'foreignKey' => 'host_id',
            'targetForeignKey' => 'maintenance_id',
            'joinTable' => 'maintenances_hosts'
        ]);
    }

    public function validationDefault(Validator $validator): \Cake\Validation\Validator {
        $validator
            ->allowEmpty('hostid', 'create');

        $validator
            ->allowEmpty('proxy_hostid');

        $validator
            ->requirePresence('host', 'create')
            ->notEmpty('host');

        $validator
            ->integer('status')
            ->requirePresence('status', 'create')
            ->notEmpty('status');

        $validator
            ->integer('disable_until')
            ->requirePresence('disable_until', 'create')
            ->notEmpty('disable_until');

        $validator
            ->requirePresence('error', 'create')
            ->notEmpty('error');

        $validator
            ->integer('available')
            ->requirePresence('available', 'create')
            ->notEmpty('available');

        $validator
            ->integer('errors_from')
            ->requirePresence('errors_from', 'create')
            ->notEmpty('errors_from');

        $validator
            ->integer('lastaccess')
            ->requirePresence('lastaccess', 'create')
            ->notEmpty('lastaccess');

        $validator
            ->integer('ipmi_authtype')
            ->requirePresence('ipmi_authtype', 'create')
            ->notEmpty('ipmi_authtype');

        $validator
            ->integer('ipmi_privilege')
            ->requirePresence('ipmi_privilege', 'create')
            ->notEmpty('ipmi_privilege');

        $validator
            ->requirePresence('ipmi_username', 'create')
            ->notEmpty('ipmi_username');

        $validator
            ->requirePresence('ipmi_password', 'create')
            ->notEmpty('ipmi_password');

        $validator
            ->integer('ipmi_disable_until')
            ->requirePresence('ipmi_disable_until', 'create')
            ->notEmpty('ipmi_disable_until');

        $validator
            ->integer('ipmi_available')
            ->requirePresence('ipmi_available', 'create')
            ->notEmpty('ipmi_available');

        $validator
            ->integer('snmp_disable_until')
            ->requirePresence('snmp_disable_until', 'create')
            ->notEmpty('snmp_disable_until');

        $validator
            ->integer('snmp_available')
            ->requirePresence('snmp_available', 'create')
            ->notEmpty('snmp_available');

        $validator
            ->allowEmpty('maintenanceid');

        $validator
            ->integer('maintenance_status')
            ->requirePresence('maintenance_status', 'create')
            ->notEmpty('maintenance_status');

        $validator
            ->integer('maintenance_type')
            ->requirePresence('maintenance_type', 'create')
            ->notEmpty('maintenance_type');

        $validator
            ->integer('maintenance_from')
            ->requirePresence('maintenance_from', 'create')
            ->notEmpty('maintenance_from');

        $validator
            ->integer('ipmi_errors_from')
            ->requirePresence('ipmi_errors_from', 'create')
            ->notEmpty('ipmi_errors_from');

        $validator
            ->integer('snmp_errors_from')
            ->requirePresence('snmp_errors_from', 'create')
            ->notEmpty('snmp_errors_from');

        $validator
            ->requirePresence('ipmi_error', 'create')
            ->notEmpty('ipmi_error');

        $validator
            ->requirePresence('snmp_error', 'create')
            ->notEmpty('snmp_error');

        $validator
            ->integer('jmx_disable_until')
            ->requirePresence('jmx_disable_until', 'create')
            ->notEmpty('jmx_disable_until');

        $validator
            ->integer('jmx_available')
            ->requirePresence('jmx_available', 'create')
            ->notEmpty('jmx_available');

        $validator
            ->integer('jmx_errors_from')
            ->requirePresence('jmx_errors_from', 'create')
            ->notEmpty('jmx_errors_from');

        $validator
            ->requirePresence('jmx_error', 'create')
            ->notEmpty('jmx_error');

        $validator
            ->requirePresence('name', 'create')
            ->notEmpty('name');

        $validator
            ->integer('flags')
            ->requirePresence('flags', 'create')
            ->notEmpty('flags');

        $validator
            ->allowEmpty('templateid');

        $validator
            ->requirePresence('description', 'create')
            ->notEmpty('description');

        $validator
            ->integer('tls_connect')
            ->requirePresence('tls_connect', 'create')
            ->notEmpty('tls_connect');

        $validator
            ->integer('tls_accept')
            ->requirePresence('tls_accept', 'create')
            ->notEmpty('tls_accept');

        $validator
            ->requirePresence('tls_issuer', 'create')
            ->notEmpty('tls_issuer');

        $validator
            ->requirePresence('tls_subject', 'create')
            ->notEmpty('tls_subject');

        $validator
            ->requirePresence('tls_psk_identity', 'create')
            ->notEmpty('tls_psk_identity');

        $validator
            ->requirePresence('tls_psk', 'create')
            ->notEmpty('tls_psk');

        return $validator;
    }
}

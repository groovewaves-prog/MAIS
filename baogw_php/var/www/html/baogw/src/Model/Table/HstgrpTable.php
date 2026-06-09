<?php
namespace App\Model\Table;

use Cake\ORM\Query;
use Cake\ORM\RulesChecker;
use Cake\ORM\Table;
use Cake\Validation\Validator;

class HstgrpTable extends Table {

    public static function defaultConnectionName(): string{
        return 'zabbix';
    }

    public function initialize(array $config): void {
        parent::initialize($config);

        $this->setTable('hstgrp');
        $this->setDisplayField('name');
        $this->setPrimaryKey('groupid');

        $this->belongsToMany('HostInventory', [
            'foreignKey' => 'groupid',
            'targetForeignKey' => 'hostid',
            'joinTable' => 'hosts_groups'
        ]);
        $this->belongsToMany('Maintenances', [
            'foreignKey' => 'group_id',
            'targetForeignKey' => 'maintenance_id',
            'joinTable' => 'maintenances_groups'
        ]);
        $this->belongsToMany('Users', [
            'foreignKey' => 'group_id',
            'targetForeignKey' => 'user_id',
            'joinTable' => 'users_groups'
        ]);
    }

    public function validationDefault(Validator $validator): \Cake\Validation\Validator {
        $validator
            ->allowEmpty('groupid', 'create');

        $validator
            ->requirePresence('name', 'create')
            ->notEmpty('name');

        $validator
            ->integer('internal')
            ->requirePresence('internal', 'create')
            ->notEmpty('internal');

        $validator
            ->integer('flags')
            ->requirePresence('flags', 'create')
            ->notEmpty('flags');

        return $validator;
    }
}

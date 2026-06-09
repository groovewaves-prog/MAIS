<?php
namespace App\Model\Table;

use Cake\ORM\Query;
use Cake\ORM\RulesChecker;
use Cake\ORM\Table;
use Cake\Validation\Validator;

class UsrgrpTable extends Table {

    public static function defaultConnectionName(): string {
        return 'zabbix';
    }

    public function initialize(array $config): void {
        parent::initialize($config);

        $this->setTable('usrgrp');
        $this->setDisplayField('name');
        $this->setPrimaryKey('usrgrpid');
    }

    public function validationDefault(Validator $validator): \Cake\Validation\Validator {
        $validator
            ->allowEmpty('usrgrpid', 'create');

        $validator
            ->requirePresence('name', 'create')
            ->notEmpty('name')
            ->add('name', 'unique', ['rule' => 'validateUnique', 'provider' => 'table']);

        $validator
            ->integer('gui_access')
            ->requirePresence('gui_access', 'create')
            ->notEmpty('gui_access');

        $validator
            ->integer('users_status')
            ->requirePresence('users_status', 'create')
            ->notEmpty('users_status');

        $validator
            ->integer('debug_mode')
            ->requirePresence('debug_mode', 'create')
            ->notEmpty('debug_mode');

        return $validator;
    }

    public function buildRules(RulesChecker $rules): \Cake\ORM\RulesChecker {
        $rules->add($rules->isUnique(['name']));

        return $rules;
    }
}

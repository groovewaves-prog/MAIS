<?php
namespace App\Model\Table;

use Cake\ORM\Query;
use Cake\ORM\RulesChecker;
use Cake\ORM\Table;
use Cake\Validation\Validator;

class UsersTable extends Table {

    public static function defaultConnectionName(): string {
        return 'zabbix';
    }

    public function initialize(array $config): void {
        parent::initialize($config);
        $this->setTable('users');
        $this->setDisplayField('name');
        $this->setPrimaryKey('userid');
        $this->hasOne('Sessions', ['foreignKey'=>'userid']);
        $this->belongsToMany('Usrgrp', [
            'foreignKey' => 'userid',
            'targetForeignKey' => 'usrgrpid',
            'joinTable' => 'users_groups'
        ]);
    }

    public function validationDefault(Validator $validator): \Cake\Validation\Validator {
        $validator
            ->allowEmpty('userid', 'create');

        $validator
            ->requirePresence('alias', 'create')
            ->notEmpty('alias')
            ->add('alias', 'unique', ['rule' => 'validateUnique', 'provider' => 'table']);

        $validator
            ->requirePresence('name', 'create')
            ->notEmpty('name');

        $validator
            ->requirePresence('surname', 'create')
            ->notEmpty('surname');

        $validator
            ->requirePresence('passwd', 'create')
            ->notEmpty('passwd');

        $validator
            ->requirePresence('url', 'create')
            ->notEmpty('url');

        $validator
            ->integer('autologin')
            ->requirePresence('autologin', 'create')
            ->notEmpty('autologin');

        $validator
            ->integer('autologout')
            ->requirePresence('autologout', 'create')
            ->notEmpty('autologout');

        $validator
            ->requirePresence('lang', 'create')
            ->notEmpty('lang');

        $validator
            ->integer('refresh')
            ->requirePresence('refresh', 'create')
            ->notEmpty('refresh');

        $validator
            ->integer('type')
            ->requirePresence('type', 'create')
            ->notEmpty('type');

        $validator
            ->requirePresence('theme', 'create')
            ->notEmpty('theme');

        $validator
            ->integer('attempt_failed')
            ->requirePresence('attempt_failed', 'create')
            ->notEmpty('attempt_failed');

        $validator
            ->requirePresence('attempt_ip', 'create')
            ->notEmpty('attempt_ip');

        $validator
            ->integer('attempt_clock')
            ->requirePresence('attempt_clock', 'create')
            ->notEmpty('attempt_clock');

        $validator
            ->integer('rows_per_page')
            ->requirePresence('rows_per_page', 'create')
            ->notEmpty('rows_per_page');

        return $validator;
    }

    public function buildRules(RulesChecker $rules): \Cake\ORM\RulesChecker {
        $rules->add($rules->isUnique(['alias']));

        return $rules;
    }
}

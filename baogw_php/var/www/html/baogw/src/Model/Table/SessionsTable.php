<?php
namespace App\Model\Table;

use Cake\ORM\Query;
use Cake\ORM\RulesChecker;
use Cake\ORM\Table;
use Cake\Validation\Validator;

class SessionsTable extends Table {

    public static function defaultConnectionName(): string{
        return 'zabbix';
    }

    public function initialize(array $config): void {
        parent::initialize($config);

        $this->setTable('sessions');
        $this->setDisplayField('sessionid');
        $this->setPrimaryKey('sessionid');
    }

    public function validationDefault(Validator $validator): \Cake\Validation\Validator {
        $validator
            ->allowEmpty('sessionid', 'create');

        $validator
            ->requirePresence('userid', 'create')
            ->notEmpty('userid');

        $validator
            ->integer('lastaccess')
            ->requirePresence('lastaccess', 'create')
            ->notEmpty('lastaccess');

        $validator
            ->integer('status')
            ->requirePresence('status', 'create')
            ->notEmpty('status');

        return $validator;
    }
}

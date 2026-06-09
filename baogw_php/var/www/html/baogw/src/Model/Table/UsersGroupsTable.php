<?php
namespace App\Model\Table;

use Cake\ORM\Query;
use Cake\ORM\RulesChecker;
use Cake\ORM\Table;
use Cake\Validation\Validator;

class UsersGroupsTable extends Table {

    public static function defaultConnectionName(): string {
        return 'zabbix';
    }

    public function initialize(array $config): void {
        parent::initialize($config);

        $this->setTable('users_groups');
        $this->setDisplayField('id');
        $this->setPrimaryKey('id');
    }

    public function validationDefault(Validator $validator): \Cake\Validation\Validator {
        $validator
            ->allowEmpty('id', 'create');

        $validator
            ->requirePresence('usrgrpid', 'create')
            ->notEmpty('usrgrpid');

        $validator
            ->requirePresence('userid', 'create')
            ->notEmpty('userid');

        return $validator;
    }
}

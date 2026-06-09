<?php
namespace App\Model\Table;

use Cake\ORM\Query;
use Cake\ORM\RulesChecker;
use Cake\ORM\Table;
use Cake\Validation\Validator;

class HostsGroupsTable extends Table {

    public static function defaultConnectionName(): string{
        return 'zabbix';
    }

    public function initialize(array $config): void {
        parent::initialize($config);

        $this->setTable('hosts_groups');
        $this->setDisplayField('hostgroupid');
        $this->setPrimaryKey('hostgroupid');
    }

    public function validationDefault(Validator $validator): \Cake\Validation\Validator {
        $validator
            ->allowEmpty('hostgroupid', 'create');

        $validator
            ->requirePresence('hostid', 'create')
            ->notEmpty('hostid');

        $validator
            ->requirePresence('groupid', 'create')
            ->notEmpty('groupid');

        return $validator;
    }
}

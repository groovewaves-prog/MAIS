<?php
namespace App\Model\Table;

use Cake\ORM\Query;
use Cake\ORM\RulesChecker;
use Cake\ORM\Table;
use Cake\Validation\Validator;

class GwRescueEventsTable extends Table{

  function disp($fieald_name){
    // $this->setTable('gw_events');
    return $this->setDisplayField($fieald_name);
  }
    public function initialize(array $config): void
    {
        parent::initialize($config);

        $this->setTable('gw_rescue_events');
        $this->setDisplayField('gw_event_id');
        $this->setPrimaryKey('gw_event_id');

        $this->belongsTo('GwEvents', [
            'foreignKey' => 'gw_event_id',
            'joinType' => 'INNER'
        ]);
        $this->belongsTo('GwIncidents', [
            'foreignKey' => 'gw_incident_id'
        ]);
    }

    public function validationDefault(Validator $validator): \Cake\Validation\Validator
    {
        $validator
            ->integer('event_status')
            ->allowEmpty('event_status');

        $validator
            ->dateTime('update_time')
            ->requirePresence('update_time', 'create')
            ->notEmpty('update_time');

        $validator
            ->dateTime('detected_time')
            ->requirePresence('detected_time', 'create')
            ->notEmpty('detected_time');

        $validator
            ->integer('detected_host')
            ->requirePresence('detected_host', 'create')
            ->notEmpty('detected_host');

        $validator
            ->requirePresence('customer_name', 'create')
            ->notEmpty('customer_name');

        $validator
            ->requirePresence('hostname', 'create')
            ->notEmpty('hostname');

        $validator
            ->dateTime('alarm_time')
            ->requirePresence('alarm_time', 'create')
            ->notEmpty('alarm_time');

        $validator
            ->requirePresence('ci_name', 'create')
            ->notEmpty('ci_name');

        $validator
            ->allowEmpty('device');

        $validator
            ->requirePresence('alarm_status', 'create')
            ->notEmpty('alarm_status');

        $validator
            ->allowEmpty('summary');

        $validator
            ->dateTime('checked_time')
            ->allowEmpty('checked_time');

        $validator
            ->allowEmpty('checked_user');

        $validator
            ->allowEmpty('op_comment');

        return $validator;
    }

    public function buildRules(RulesChecker $rules): \Cake\ORM\RulesChecker
    {
        $rules->add($rules->existsIn(['gw_event_id'], 'GwEvents'));
        $rules->add($rules->existsIn(['gw_incident_id'], 'GwIncidents'));

        return $rules;
    }
}

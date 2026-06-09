<?php
namespace App\Model\Table;

use Cake\ORM\Query;
use Cake\ORM\RulesChecker;
use Cake\ORM\Table;
use Cake\Validation\Validator;
use App\View\Helper\InputSetHelper;

class GwEventsTable extends Table
{

    function disp($fieald_name){
      // $this->setTable('gw_events');
      return $this->setDisplayField($fieald_name);
    }

    public function beforeSave(\Cake\Event\EventInterface $event, $entity) {
      //textarea内の改行コード\n\rが、DB上で2文字扱いとなり、
      //またjavascriptのlengthでそれをカウントできないため、DB保存前に\rは削除する。
      $entity->op_comment = InputSetHelper::str_replace("\r", "", $entity->op_comment);
      if (InputSetHelper::mb_strlen($entity->op_comment) > 512 ){
        return false;
      };
      return true;
    }

    public function initialize(array $config): void{
        parent::initialize($config);

        $this->setTable('gw_events');
        $this->setDisplayField('gw_event_id');
        $this->setPrimaryKey('gw_event_id');

        $this->belongsTo('GwIncidents');
    }

    public function validationDefault(Validator $validator): \Cake\Validation\Validator{
        // $validator
        //     ->allowEmpty('gw_event_id', 'create');
        //
        // $validator
        //     ->integer('event_status')
        //     ->allowEmpty('event_status');
        //
        // $validator
        //     ->dateTime('update_time')
        //     ->requirePresence('update_time', 'create')
        //     ->notEmpty('update_time');
        //
        // $validator
        //     ->dateTime('detected_time')
        //     ->requirePresence('detected_time', 'create')
        //     ->notEmpty('detected_time');
        //
        // $validator
        //     ->integer('detected_host')
        //     ->requirePresence('detected_host', 'create')
        //     ->notEmpty('detected_host');
        //
        // $validator
        //     ->requirePresence('customer_name', 'create')
        //     ->notEmpty('customer_name');
        //
        // $validator
        //     ->requirePresence('hostname', 'create')
        //     ->notEmpty('hostname');
        //
        // $validator
        //     ->dateTime('alarm_time')
        //     ->requirePresence('alarm_time', 'create')
        //     ->notEmpty('alarm_time');
        //
        // $validator
        //     ->requirePresence('ci_name', 'create')
        //     ->notEmpty('ci_name');
        //
        // $validator
        //     ->requirePresence('alarm_status', 'create')
        //     ->notEmpty('alarm_status');
        //
        // // 帆機情報
        // $validator
        //     ->allowEmpty('summary');
        //
        // $validator
        //     ->dateTime('checked_time')
        //     ->allowEmpty('checked_time');
        //
        // $validator
        //     ->allowEmpty('checked_user');
        //
        // $validator
        //     ->allowEmpty('op_comment');

        return $validator;
    }

    public function buildRules(RulesChecker $rules): \Cake\ORM\RulesChecker{
        $rules->add($rules->existsIn(['gw_incident_id'], 'GwIncidents'));
        // $rules->add($rules->existsIn(['device_id'], 'Devices'));

        return $rules;
    }
}

<?php
namespace App\Model\Table;

use Cake\ORM\Query;
use Cake\ORM\RulesChecker;
use Cake\ORM\Table;
use Cake\Validation\Validator;
use Cake\Event\Event;
use ArrayObject;
use Cake\Database\ValueBinder;
use App\View\Helper\InputSetHelper;

/**
 * GwIncidents Model
 *
 * @property \App\Model\Table\GwIncidentsTable|\Cake\ORM\Association\BelongsTo $GwIncidents
 *
 * @method \App\Model\Entity\GwIncident get($primaryKey, $options = [])
 * @method \App\Model\Entity\GwIncident newEntity($data = null, array $options = [])
 * @method \App\Model\Entity\GwIncident[] newEntities(array $data, array $options = [])
 * @method \App\Model\Entity\GwIncident|bool save(\Cake\Datasource\EntityInterface $entity, $options = [])
 * @method \App\Model\Entity\GwIncident patchEntity(\Cake\Datasource\EntityInterface $entity, array $data, array $options = [])
 * @method \App\Model\Entity\GwIncident[] patchEntities($entities, array $data, array $options = [])
 * @method \App\Model\Entity\GwIncident findOrCreate($search, callable $callback = null, $options = [])
 */
class GwIncidentsTable extends Table
{

    /**
     * Initialize method
     *
     * @param array $config The configuration for the Table.
     * @return void
     */
    public function initialize(array $config): void
    {
        parent::initialize($config);

        $this->setTable('gw_incidents');
        $this->setDisplayField('gw_incident_id');
        $this->setPrimaryKey('gw_incident_id');

        $this->hasMany('GwEvents');

        $this->hasOne('ErrorEvents', [
            'className' => 'GwEvents',
            'foreignKey' => 'gw_event_id',
            'bindingKey' => 'error_event_id',
            'property' => 'error_event'
        ]);

        $this->hasOne('NormalEvents', [
            'className' => 'GwEvents',
            'foreignKey' => 'gw_event_id',
            'bindingKey' => 'normal_event_id',
            'property' => 'normal_event'
        ]);
    }

    /**
     * Default validation rules.
     *
     * @param \Cake\Validation\Validator $validator Validator instance.
     * @return \Cake\Validation\Validator
     */
    public function validationDefault(Validator $validator): \Cake\Validation\Validator
    {
        $validator
            ->integer('incident_status')
            ->requirePresence('incident_status', 'create')
            ->notEmptyString('incident_status');

        $validator
            ->dateTime('update_time')
            ->requirePresence('update_time', 'create')
            ->notEmptyDateTime('update_time');

        $validator
            ->requirePresence('customer_name', 'create')
            ->notEmptyString('customer_name');

        $validator
            ->requirePresence('hostname', 'create')
            ->notEmptyString('hostname');

        $validator
            ->requirePresence('ci_name', 'create')
            ->notEmptyString('ci_name');

        $validator
            ->allowEmptyString('kisys_incidentid');

        return $validator;
    }

    /**
     * Returns a rules checker object that will be used for validating
     * application integrity.
     *
     * @param \Cake\ORM\RulesChecker $rules The rules object to be modified.
     * @return \Cake\ORM\RulesChecker
     */
    public function buildRules(RulesChecker $rules): \Cake\ORM\RulesChecker
    {
        // $rules->add($rules->existsIn(['gw_incident_id'], 'GwIncidents'));
        return $rules;
    }

    public function beforeFind(\Cake\Event\EventInterface $event, Query $query, ArrayObject $options, $primary)
    {
        // ソート時に NULL の値がソートの頭に表示されてしまうため、find()の前にフックして ORDER BY に IS NULL 条件を追加する
        $org_order = $query->clause('order');
        if (is_null($org_order)){
            return $query;
        }
        $binder = new ValueBinder();
        // $org_order_str => "ORDER BY <モデル名>.<カラム名> <ascもしくはdesc>"
        $org_order_str = $org_order->sql($binder);
        // $org_order_split => Array(
        //     [0] => "ORDER"
        //     [1] => "BY"
        //     [2] => "<モデル名>.<カラム名>"
        //     [3] => "<ascもしくはdesc>")
        $org_order_split = InputSetHelper::explode(' ', $org_order_str);
        $new_order_str = $org_order_split[2] . ' IS NULL, ' . $org_order_split[2] . ' ' . $org_order_split[3];
        $query->order([$new_order_str], true); // 第二引数にtrue指定で確実にORDER BYを上書きする
        return $query;
    }

}

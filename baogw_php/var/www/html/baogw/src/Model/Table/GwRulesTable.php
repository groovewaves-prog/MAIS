<?php
namespace App\Model\Table;

use Cake\ORM\Query;
use Cake\ORM\RulesChecker;
use Cake\ORM\Table;
use Cake\Validation\Validator;
use Cake\Controller\Component;

class GwRulesTable extends Table {


    public function beforeSave(\Cake\Event\EventInterface $event, $entity) {
        // var_dump($entity);
        // $query_gwRules = $this->find()
        //                     ->where(['customer_name ' => $entity->customer_name ])
        //                     ->where(['hostname ' => $entity->hostname ])
        //                     ->where(['ci_name ' => $entity->ci_name ])
        //                     ->where(['rule_set ' => $entity->rule_set ])
        //                     ->select('rule_id')
        //                     ->where(['rule_id is not' => $entity->rule_id ])
        //                     ->toArray()
        //                     ;
        // // $query_gwRules['rule_id']
        // if(count($query_gwRules['0'])>0) {
        //     var_dump($query_gwRules['0']['rule_id']);
        //     // $this->controler->Flash->error(__('ルールID{0}と重複するルールの為、登録できません。',$query_gwRules['0']['rule_id']));
        //     return $query_gwRules['0']['rule_id'];
        // }

    }

    public function initialize(array $config): void{
        parent::initialize($config);

        $this->setTable('gw_rules');
        $this->setDisplayField('rule_id');
        $this->setPrimaryKey('rule_id');
    }




    function disp($fieald_name){
        return $this->setDisplayField($fieald_name);
    }
    // public function beforeValidate() {
    //       $this->validate['start_time'] = array(
    //                 'checkdatetofrom' => array(
    //                     'rule' => array('checkDateToFrom', $this->data["end_time"]),
    //                     'message' => '開始日時と終了日時の関係が逆です',
    //                     'allowEmpty' => true,
    //                 ),
    //             );
    // }

    public function validationDefault(Validator $validator): \Cake\Validation\Validator{

        $validator
            ->integer('rule_id')
            ->allowEmptyString('rule_id', 'create');

        $validator
            ->integer('rule_set','数値を入力してください。')
            ->range('rule_set', ['min'=>0, 'max'=>5], '0から5の範囲で入力してください。')
            ->maxLength('rule_set','1','１桁で入力してください。')
            ->requirePresence('rule_set', 'create')
            ->notEmptyString('rule_set');

        $validator
            ->boolean('rule_status')
            ->requirePresence('rule_status', 'create')
            ->notEmptyString('rule_status');


        $validator
            ->notEmptyDate('start_time')
            // ->allowEmpty('start_time', 'create')
            ->add('start_time','custom',['rule'=>['custom',"/\d{4}\/\d{1,2}\/\d{1,2} \d{1,2}:\d{1,2}/"],
                                          'message'=>'日付を入力してください。']);

        $validator
            ->notEmptyDate('end_time');

        $validator
            ->requirePresence('customer_name', 'create')
            ->notEmptyString('customer_name')
            ->add('customer_name','custom',['rule'=>['custom',"/[^*]/"],
                                            'message'=>'*以外を入力してください。']);


        $validator
            ->requirePresence('hostname', 'create')
            ->notEmptyString('hostname');

        $validator
            ->requirePresence('ci_name', 'create')
            ->notEmptyString('ci_name');

        $validator
            ->integer('action_no','数値を入力してください。')
            // ->range('action_no', ['min'=>0, 'max'=>5], '0から5の範囲で入力してください。')
            // ->maxLength('action_no','1','１桁で入力してください。')
            ->requirePresence('action_no', 'create')
            ->notEmptyString('action_no');

        // $validator->add('end_time', ['lessThan' => ['rule' => ['comparison', '>=','start_time'], 'message' => '前後']]);
        // $validator->add('start_time', ['lessThan' => ['rule' => ['comparison', '<=','end_time'], 'message' => '前後']]);
        //     // ->add('start_time', ['comWitha' => ['rule' => ['compareWith', 'end_time'],'message' => 'パスワードが確認用と違います！']]);

        // $validator->add('start_time', ['comWitha' => ['rule' => ['comparison', '>=','end_time'],'message' => 'パスワードが確認用と違います！']]);
        // ->add('action_no', ['lessThan' => ['rule' => ['comparison', '>=','rule_set'], 'message' => '前後']]);

        return $validator;
    }
}

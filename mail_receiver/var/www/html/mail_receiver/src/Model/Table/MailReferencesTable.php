<?php

namespace App\Model\Table;

use Cake\ORM\Query;
use Cake\ORM\RulesChecker;
use Cake\Validation\Validator;

/**
 * MailReferences Model
 *
 * @method \App\Model\Entity\MailReference get($primaryKey, $options = [])
 * @method \App\Model\Entity\MailReference newEntity($data = null, array $options = [])
 * @method \App\Model\Entity\MailReference[] newEntities(array $data, array $options = [])
 * @method \App\Model\Entity\MailReference|false save(\Cake\Datasource\EntityInterface $entity, $options = [])
 * @method \App\Model\Entity\MailReference saveOrFail(\Cake\Datasource\EntityInterface $entity, $options = [])
 * @method \App\Model\Entity\MailReference patchEntity(\Cake\Datasource\EntityInterface $entity, array $data, array $options = [])
 * @method \App\Model\Entity\MailReference[] patchEntities($entities, array $data, array $options = [])
 * @method \App\Model\Entity\MailReference findOrCreate($search, callable $callback = null, $options = [])
 */
class MailReferencesTable extends AppTable
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

        $this->setTable('mail_references');
        $this->setDisplayField('id');
        $this->setPrimaryKey('id');
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
            ->integer('id')
            ->maxLength('id', 32);
        //->allowEmptyString('id', null, 'create');

        $validator
            ->email('sender_mail_address', false, 'メールアドレスは正しいフォーマットで入力してください')
            ->maxLength('sender_mail_address', 256, 'メールアドレスは256文字以下です')
            ->requirePresence('sender_mail_address')
            ->notEmptyString('sender_mail_address', 'メールアドレスは必須項目です');

        $validator
            ->integer('is_invalid')
            ->allowEmptyString('is_invalid');

        $validator
            ->scalar('customer_ci')
            ->maxLength('customer_ci', 64, '顧客名称略称は64文字以下です')
            ->requirePresence('customer_ci')
            ->notEmptyString('customer_ci', '顧客名称略称は必須項目です');

        $validator->setProvider('Custom', 'App\Model\Validation\CustomValidation');
        $validator->add('customer_ci', 'customerCiRuleName', [
            'rule' => ['isMatchAlphaNumericAndCustomSymbol'],
            'provider' => 'Custom',
            'message' => '顧客名称略称は半角英数字（記号可）で入力してください。'
        ]);

        $validator->add('customer_ci', 'customerNameRuleName', [
            'rule' => ['isNotMatchedControlCharacter'],
            'provider' => 'Custom',
            'message' => '顧客名称略称に登録できない文字列が含まれています'
        ]);

        $validator
            ->scalar('customer_name')
            ->maxLength('customer_name', 128, '顧客名称は128文字以下です')
            ->requirePresence('customer_name')
            ->notEmptyString('customer_name', '顧客名称は必須項目です')
            ->add('customer_name', 'customerNameRuleName', [
                'rule' => ['isNotMatchedControlCharacter'],
                'provider' => 'Custom',
                'message' => '顧客名称に登録できない文字列が含まれています'
            ]);

        $validator
            ->scalar('type')
            ->maxLength('type', 8)
            ->requirePresence('type')
            ->notEmptyString('type', 'タイプは必須項目です');

        $validator
            ->scalar('analysis_conditions')
            ->maxLength('analysis_conditions', 512, '分析条件は512文字以下です')
            // ->requirePresence('analysis_conditions')
            ->notEmptyString('analysis_conditions', '分析条件は必須項目です')
            ->add(
                'analysis_conditions',
                [
                    'unique' => [
                        'rule' => ['validateUnique', [
                            'scope' => [
                                'sender_mail_address',
                                'is_invalid'
                            ]
                        ]],
                        'provider' => 'table',
                        'message' => 'すでに同じ条件で「メール連携ルールが登録されています。」'
                    ]
                ]
            );

        $validator
            ->dateTime('update_time')
            ->allowEmptyDateTime('update_time');

        $validator
            ->scalar('update_user')
            ->maxLength('update_user', 32)
            ->allowEmptyString('update_user');

        $validator
            ->scalar('ci_name')
            ->maxLength('ci_name', 256, 'アラーム名は256文字以下です')
            ->notEmptyString('ci_name', 'アラーム名は必須項目です');

        return $validator;
    }
}

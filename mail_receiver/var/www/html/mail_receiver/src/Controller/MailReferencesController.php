<?php

namespace App\Controller;

use Cake\Core\Configure;
use App\Controller\AppController;
use App\Model\Entity\MailReference;
use App\Model\Table\MailReferencesTable;

/**
 * MailReferences Controller
 *
 * @property \App\Model\Table\MailReferencesTable $MailReferences
 *
 * @method \App\Model\Entity\MailReference[]|\Cake\Datasource\ResultSetInterface paginate($object = null, array $settings = [])
 */
class MailReferencesController extends AppController
{

    // ページネーションの設定
    public $paginate = [
        'limit' => 100, // 1ページに表示するデータ件数
        'order' => [
            'MailReferences.id' => 'desc'
        ]
    ];

    public function initialize(): void
    {
        parent::initialize();
        $this->loadComponent('Paginator');
    }

    /**
     * Index method
     *
     * @return \Cake\Http\Response|null
     */
    public function index()
    {
        // 検索のクエリ文字列を取得
        $customerName = $this->getRequest()->getQuery('customer_name');
        $senderMailAddress = $this->getRequest()->getQuery('sender_mail_address');

        $query = $this->MailReferences->find()
            ->where(['is_invalid' => 0]);

        // 顧客名称
        if ($customerName) {
            $query->where(['customer_name like' => '%' . $customerName . '%']);
        }

        // アドレス
        if ($senderMailAddress) {
            $query->where(['sender_mail_address like' => '%' . $senderMailAddress . '%']);
        }

        $mailReferences = $this->paginate($query);

        $this->set(compact('mailReferences'));
    }

    /**
     * View method
     *
     * @param string|null $id Mail Reference id.
     * @return \Cake\Http\Response|null
     * @throws \Cake\Datasource\Exception\RecordNotFoundException When record not found.
     */
    public function view($id = null)
    {
        $mailReference = $this->MailReferences->get($id, [
            'contain' => []
        ]);

        $this->set('mailReference', $mailReference);
    }

    /**
     * Add method
     *
     * @return \Cake\Http\Response|null Redirects on successful add, renders view otherwise.
     */
    public function add()
    {
        if ($this->getRequest()->is('post')) {
            $mailReference = $this->_save($this->request->getData());
        } else {
            $mailReference = $this->MailReferences->newEmptyEntity();
        }

        $this->set(compact('mailReference'));
    }

    /**
     * Edit method
     *
     * @param string|null $id Mail Reference id.
     * @return \Cake\Http\Response|null Redirects on successful edit, renders view otherwise.
     * @throws \Cake\Datasource\Exception\RecordNotFoundException When record not found.
     */
    public function edit($id)
    {
        $mailReference = $this->MailReferences->find()
            ->where(['id' => $id])
            ->where(['is_invalid' => 0])
            ->firstOrFail();

        if ($this->request->is(['patch', 'post', 'put'])) {
            $mailReference = $this->_save($this->getRequest()->getData(), $mailReference);
        } else {
            // 分析条件をデコードしてセット
            $mailReference->conditions = json_decode($mailReference['analysis_conditions'], true);
        }

        $this->set(compact('mailReference'));
    }

    /**
     * Delete method
     *
     * @param string|null $id Mail Reference id.
     * @return \Cake\Http\Response|null Redirects to index.
     * @throws \Cake\Datasource\Exception\RecordNotFoundException When record not found.
     */
    public function delete($id)
    {
        $this->getRequest()->allowMethod(['post']);

        $res = $this->MailReferences->query()
            ->update()
            ->set([
                'is_invalid' => 1,
                'update_time' => date('Y-m-d H:i:s'),
                'update_user' => $this->getRequest()->getSession()->read(Configure::read('sessionName.zabbixUsername')),
            ])
            ->where(['id' => $id])
            ->execute()
            ->rowCount();

        if ($res) {
            $this->Flash->success(__('データは削除されました'));
        } else {
            $this->Flash->error(__('データが削除できませんでした。再試行してください'));
        }

        return $this->redirect([
            'controller' => 'MailReferences',
            'action' => 'index'
        ]);
    }
    // 文字列の前後の空白文字(コントロール文字）を取り除く
    private function mbTrim($pString)
    {
        return preg_replace('/\A[\p{C}\p{Z}]++|[\p{C}\p{Z}]++\z/u', '', $pString);
    }
    private function _save($data, $mailReference = null)
    {
        // 未入力の配列を除去し、
        $data['conditions']['title']['keyword'] = array_filter($data['conditions']['title']['keyword']);
        // キーワードの前後の空白を削除し、
        for( $i = 0; $i < count($data['conditions']['title']['keyword']); $i++){
            $data['conditions']['title']['keyword'][$i] = $this->mbTrim($data['conditions']['title']['keyword'][$i]);
            //$this->log("#".$data['conditions']['title']['keyword'][$i]."#");
        }
        // ソートする
        sort($data['conditions']['title']['keyword']);

        // 未入力の配列を除去し、
        $data['conditions']['content']['keyword'] = array_filter($data['conditions']['content']['keyword']);
        // キーワードの前後の空白を削除し
        for( $i = 0; $i < count($data['conditions']['content']['keyword']); $i++){
            $data['conditions']['content']['keyword'][$i] = $this->mbTrim($data['conditions']['content']['keyword'][$i]);
            //$this->log("#".$data['conditions']['content']['keyword'][$i]."#");
        }
        // ソートする
        sort($data['conditions']['content']['keyword']);

        // JSONへエンコード（文字コードにエスケープを無し）
        $data['analysis_conditions'] = json_encode($data['conditions'], JSON_UNESCAPED_UNICODE);

        // 更新時刻と更新者
        $data['update_time'] = date('Y-m-d H:i:s');
        $data['update_user'] = $this->getRequest()->getSession()->read(Configure::read('sessionName.zabbixUsername'));

        // バリデーションで使用するので値をセットしておく
        $data['is_invalid'] = 0;

        if ($mailReference) {
            // 更新
            $mailReference = $this->MailReferences->patchEntity($mailReference, $data);
        } else {
            // 新規登録
            $mailReference = $this->MailReferences->newEntity($data);
        }

        if ($this->MailReferences->save($mailReference)) {
            // 登録成功
            $this->Flash->success(__('登録が完了しました'));
            return $this->redirect([
                'controller' => 'MailReferences',
                'action' => 'index'
            ]);
        }

        // 分析条件が含まれていないので追加
        $mailReference->conditions = $data['conditions'];

        // 登録失敗
        $this->Flash->error(__('登録ができませんでした。再試行してください'));

        return $mailReference;
    }
}

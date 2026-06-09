<?php
namespace App\Controller;

use App\Controller\AppController;
use Cake\Event\Event;

/**
 * Users Controller
 *
 * @property \App\Model\Table\UsersTable $Users
 *
 * @method \App\Model\Entity\User[] paginate($object = null, array $settings = [])
 */
class UsersController extends AppController{

    // var $components = array('ZbxAuth','Security');
    // public $components = array();
    // メインメニュー遷移させるかどうか。
    public function login() {

      //cookie有りだったら一度DBのsesionidを確認してOKだったら認証通す
      $zabbix_sessionid = $this->_read_cookie('zabbix_sessionid');
      if (!is_null($zabbix_sessionid)) {
        $user_info = $this->ZbxAuth->_zbx_api_get_user_info($zabbix_sessionid);
        $account_alias = $this->getRequest()->getSession()->read('account_alias');
        if (count($user_info)>0 && !is_null($account_alias)) {
          $this->Flash->success(__('すでに認証されています。別IDでログインしたい場合は一度ログアウトするか別ブラウザで開いてください。'));
          return $this->redirect(['controller'=>'mainMenu','action' => 'index']);
        }
      }

      //認証情報がない場合でpostリクエストがない
      if (!$this->getRequest()->is('post')) {
          return;
      }

      //認証情報がなく、postリクエスト有り。 IDとPWがsubmitされた。
      $zbx_username  = $this->getRequest()->getData('username');
      $zbx_password  = $this->getRequest()->getData('password');

      if (!$zbx_username){
          $this->Flash->error(__('ユーザ名を入力してください。'));
      }

      if (!$zbx_username){
          $this->Flash->error(__('パスワードを入力してください。'));
      }

      $zabbix_sessionid = $this->ZbxAuth->_zbx_api_login($zbx_username, $zbx_password);
      var_dump($zabbix_sessionid);
      $user_info     = $this->ZbxAuth->_zbx_api_get_user_info($zabbix_sessionid);
      //ユーザ情報が取得できたかどうかで認証が通ったかを確認する

      if (count($user_info)==0){
        $this->Flash->error(__('ログインに失敗しました。') );
        return;
      }else{
        // $this->Flash->success(__('認証に成功しました。'). $zabbix_sessionid);

        //クッキーとセッション保存
        $this->_write_cookie('zabbix_sessionid', $zabbix_sessionid);
        //zabbix仕様変更
        $account_alias=$user_info[0]['username'];
        $account_name=$user_info[0]['name'];
        $account_surname=$user_info[0]['surname'];
        $account_refresh=$user_info[0]['refresh'];
        $account_type=$user_info[0]['type'];

        $this->getRequest()->getSession()->write('account_alias', $account_alias);
        $this->getRequest()->getSession()->write('account_type', $account_type);
        $this->getRequest()->getSession()->write('account_name', $account_name);
        $this->getRequest()->getSession()->write('account_surname', $account_surname);
        $this->getRequest()->getSession()->write('account_refresh', $account_refresh);

        //メインメニューへ遷移する
        return $this->redirect(['controller'=>'mainMenu','action' => 'index']);
      }

    }

    // ======================================================================================================================================================
    // セッションとcookieの破棄
        public function logout(){

          //全セッションデータの破棄
          $this->getRequest()->getSession()->destroy();
          //Cokkei破棄
          $zabbix_sessionid = $this->_read_cookie('zabbix_sessionid');
          $result = $this->ZbxAuth->_zbx_api_logout($zabbix_sessionid);

        //   if ($result==true){
        //     $logout_result='ログアウトしました。';
        //     $this->_del_cookie('zabbix_sessionid');
        //   }else{
        //     $logout_result='ログアウトに失敗しました。';
        //   }
          $this->Flash->success(__('ログアウトしました。'));
          $this->redirect(['controller'=>'users','action' => 'login']);
        }
}

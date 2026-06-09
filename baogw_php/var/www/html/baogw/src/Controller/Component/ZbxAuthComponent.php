<?php
namespace App\Controller\Component;
use Cake\Controller\Component;
use Cake\Core\Configure;
use Cake\Core\Configure\Engine\PhpConfig;

class ZbxAuthComponent extends Component {

// ======================================================================================================================================================
    function initialize(array $config): void {
        //$this->Controller = $controller;
        //Controllerのインスタンスを取得
        $this->controler = $this->_registry->getController();

        return;
    }

// ======================================================================================================================================================
    //ページ遷移前 セッション情報を元に認証済みかチェック
    //認証条件 セッションとcookieを保持していること
    public function _check_authenticate($event){

        $account_alias = $this->controler->getRequest()->getSession()->read('account_alias');
        $this->controler->set('account_full_name', ''); //ログイン画面のundifined 抑止用
        $this->controler->set('account_type_name', ''); //ログイン画面のundifined 抑止用

        //Users login logout では認証チェックしない。
        $action=$event->getSubject()->getRequest()->getParam('action');
        $controller=$event->getSubject()->getRequest()->getParam('controller');
        $this->controler->set(compact('action'));
        if ($controller=="Users" && ($action=="login" || $action=="logout")){
           return;
        }

        //PHPセッションがなかったら、Zabbxi APIログアウトしてログイン画面へ
        if (!$account_alias) {
            $zabbix_sessionid = $this->controler->_read_cookie('zabbix_sessionid');
            if (!$zabbix_sessionid) {
                $result = $this->_zbx_api_logout($zabbix_sessionid);
            }
            $this->controler->Flash->error(__('ログインしてください。') );
            $this->controler->redirect(['controller'=>'users','action'=>'login']);
            return;
        }

        //zbxセッションがcookieに保存されていなかったらセッションを破棄してログイン画面へ
        $zabbix_sessionid = $this->controler->_read_cookie('zabbix_sessionid');
        $user_info     = $this->_zbx_api_get_user_info($zabbix_sessionid);
        if (count($user_info)==0){
            $this->controler->getRequest()->getSession()->destroy();
            $this->controler->Flash->error(__('ログインしてください。'));
            $this->controler->redirect(['controller'=>'users','action'=>'login']);
            return;
        }

        //zabbixバージョンアップによりUsers.aliasがusernameに変更
        $account_alias   = $user_info[0]['username'];
        $account_name    = $user_info[0]['name'];
        $account_surname = $user_info[0]['surname'];
        $account_refresh = $user_info[0]['refresh'];
        //zabbixバージョンアップによりUsers.typeがroleidに変更
        $account_type    = $user_info[0]['roleid'];
        $usrgrp_names = [];
        foreach ($user_info[0]['usrgrp'] as $usrgrp) {
            $usrgrp_names = array_merge($usrgrp_names, [$usrgrp['name']]);
        }

        //ログインはOK 再度セッション書き込み　ビューにも渡す
        $this->controler->getRequest()->getSession()->write('account_alias',   $account_alias);
        $this->controler->getRequest()->getSession()->write('account_name',    $account_name);
        $this->controler->getRequest()->getSession()->write('account_surname', $account_surname);
        $this->controler->getRequest()->getSession()->write('account_refresh', $account_refresh);
        $this->controler->getRequest()->getSession()->write('account_type',    $account_type);
        $this->controler->getRequest()->getSession()->write('usrgrp_names',    $usrgrp_names);
        $this->controler->getRequest()->getSession()->write('account_full_name',    $account_alias . ' (' . $account_surname . ' ' . $account_name . ')');

        if($account_type==2){
          $account_type_name = "Zabbix管理者";
        }elseif($account_type==3){
          $account_type_name = "Zabbix特権管理者";
        }elseif($account_type==1) {
          $account_type_name = "Zabbixユーザー";
        }

        $this->controler->set('account_alias',     $account_alias);
        $this->controler->set('account_name',      $account_name);
        $this->controler->set('account_surname',   $account_surname);
        $this->controler->set('account_refresh',   $account_refresh);
        $this->controler->set('account_type',      $account_type);
        $this->controler->set('usrgrp_names',      $usrgrp_names);
        $this->controler->set('account_type_name', $account_type_name);
        $this->controler->set('account_full_name', $account_alias . ' (' . $account_surname . ' ' . $account_name . ')');

        //他の運用者のグループ
        $other_user_group = [];
        array_push($other_user_group, Configure::read("HOWCOM_USER_GROUP"));
        $this->controler->getRequest()->getSession()->write('other_user_group', $other_user_group);
        $this->controler->set('other_user_group', $other_user_group);

    }

// ======================================================================================================================================================
    public function _zbx_api_get_user_info($zabbix_sessionid){
      $this->controler->loadModel('Users');
      $users_query=$this->controler->Users->find()->contain(['Sessions', 'Usrgrp'])->where(['Sessions.sessionid'=>$zabbix_sessionid,'Sessions.status'=>0]);
      $user_info = $users_query->toArray();
      return $user_info;
    }

// ======================================================================================================================================================

    public function _zbx_api_logout($zabbix_sessionid){
      $method = "user.logout";
      $auth   = $zabbix_sessionid;
      $params = [];
      $response = $this->_zbx_api($method, $auth, $params);
    }

// ======================================================================================================================================================
    public function _zbx_api_login($zbx_username, $zbx_password){

      $method = "user.login";
      $auth   = null;
      $params =['user'     =>$zbx_username,
                'password' =>$zbx_password
      ];
      $response = $this->_zbx_api($method,$auth,$params);

      if (property_exists($response, 'result')) {
          $zabbix_sessionid = $response->result;
      }  elseif (property_exists($response, 'error')) {
        //   return $response->error->data;
         $zabbix_sessionid  = "";
      }
      return $zabbix_sessionid;

    }

// ======================================================================================================================================================
    public function _zbx_api($method, $auth, $params){

      $zbx_api_url    = Configure::read("ZBX_API_URL");

      $request = [
        'jsonrpc'  => '2.0',
        'method'   => $method,
        'id'       => '1',
        'auth'     => $auth,
        'params'   => $params
      ];

      $request_json = json_encode($request);

      $opts['http'] =[
        'method'  => 'POST',
        'header'  => 'Content-Type: application/json-rpc',
        'content' => $request_json
      ];
      $context       = stream_context_create($opts);
      $response_json = file_get_contents($zbx_api_url, false, $context);
      $response      = json_decode($response_json);

      return $response;

    }



}

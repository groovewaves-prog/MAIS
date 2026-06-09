<?php
namespace App\Controller\Component;
use Cake\Controller\Component;
use Cake\Core\Configure;
use Cake\Core\Configure\Engine\PhpConfig;

class CMDBComponent extends Component {

// ======================================================================================================================================================
    function initialize(array $config): void {
        //Controllerのインスタンスを取得
        $this->controler = $this->_registry->getController();
        return;
    }

// ======================================================================================================================================================
    /**
     * [getAuth ユーザー情報取得]
     * @param  string $username ユーザー名
     * @param  string $password パスワード
     * @return array            ユーザー情報
     */
    public function getAuth($username, $password) {
      $ch = curl_init();
      $curl_post_data = array(
        "username" => $username,
        "password" => $password
      );
      $header = [
        'Content-Type: application/json',
      ];
      $CMDB_BUILD_URL = Configure::read('CMDB_BUILD_URL');
      curl_setopt($ch, CURLOPT_URL, $CMDB_BUILD_URL.'/services/rest/v3/sessions?scope=service');
      curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
      curl_setopt($ch, CURLOPT_CUSTOMREQUEST, 'POST');
      curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($curl_post_data));
      curl_setopt($ch, CURLOPT_HTTPHEADER, $header);
      curl_setopt($ch, CURLOPT_HEADER, true);
      curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, false);
      $curl_response = curl_exec($ch);
      $response = $this->getResult($ch, $curl_response);
      curl_close($ch);
      return $response;
    }

// ======================================================================================================================================================
    /**
     * [getProject プロジェクト情報検索]
     * @param  string $kisys K-ISYS顧客略称
     * @param  array  $auth  ユーザー情報
     * @return array         プロジェクト情報
     */
    public function getProject($kisys, $auth) {
      $ch = curl_init();
      $header = [
        'Content-Type: application/json',
        'CMDBuild-Authorization:'.$auth['data']['_id'],
      ];
      $CMDB_BUILD_URL = Configure::read('CMDB_BUILD_URL');
      $filter = 'filter='.urlencode('{"CQL":"from Project where CompanyCode = \''.$kisys.'\'"}');
      curl_setopt($ch, CURLOPT_URL, $CMDB_BUILD_URL.'/services/rest/v3/classes/Project/cards?'.$filter);
      curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
      curl_setopt($ch, CURLOPT_CUSTOMREQUEST, 'GET');
      curl_setopt($ch, CURLOPT_HTTPHEADER, $header);
      curl_setopt($ch, CURLOPT_HEADER, true);
      curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, false);
      $curl_response = curl_exec($ch);
      $response = $this->getResult($ch, $curl_response);
      curl_close($ch);
      return $response;
    }

// ======================================================================================================================================================
    /**
     * [getMachineInfo 運用機器情報検索]
     * @param  string $host    ホスト名
     * @param  string $project 運用管理情報ID
     * @param  array  $auth    ユーザー情報
     * @return array           運用機器情報
     */
    public function getMachineInfo($host, $project, $auth){
      $ch = curl_init();
      $header = [
        'Content-Type: application/json',
        'CMDBuild-Authorization:'.$auth['data']['_id'],
      ];
      $CMDB_BUILD_URL = Configure::read('CMDB_BUILD_URL');
      if ($host) {
        $filter = 'filter='.urlencode('{"CQL":" from Machine where Id in (/ (select \\"Id\\" from \\"Machine\\" where \\"ProjectCode\\" = '.$project.' and \\"FQDN\\" = \''.$host.'\' and (\\"Del_flg\\" = false or \\"Del_flg\\" is null))/)"}');
      } else {
        $filter = 'filter='.urlencode('{"CQL":" from Machine where Id in (/ (select \\"Id\\" from \\"Machine\\" where \\"ProjectCode\\" = '.$project.' and (\\"Del_flg\\" = false or \\"Del_flg\\" is null))/)"}');
      }
      curl_setopt($ch, CURLOPT_URL, $CMDB_BUILD_URL.'/services/rest/v3/classes/Machine/cards?'.$filter);
      curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
      curl_setopt($ch, CURLOPT_CUSTOMREQUEST, 'GET');
      curl_setopt($ch, CURLOPT_HTTPHEADER, $header);
      curl_setopt($ch, CURLOPT_HEADER, true);
      curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, false);
      $curl_response = curl_exec($ch);
      $response = $this->getResult($ch, $curl_response);
      curl_close($ch);
      return $response;
    }

// ======================================================================================================================================================
   /**
    * [getResult 結果取得]
    * @param  array $ch       curl
    * @param  json  $response json情報
    * @return array           jsonを展開したarray
    */
    public function getResult($ch, $response) {
      $header_size = curl_getinfo($ch, CURLINFO_HEADER_SIZE);
      $header = substr($response, 0, $header_size);
      $body = substr($response, $header_size);
      $result = json_decode($body, true);
      return $result;
    }


}

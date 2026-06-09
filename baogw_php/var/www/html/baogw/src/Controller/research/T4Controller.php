<?php
namespace App\Controller;

use App\Controller\AppController;
use Cake\Routing\Router;
use Cake\Core\Configure;
use Cake\Core\Exception\Exception;
use App\Controller\GwCreateExportData;
use SplFileObject;

class T4Controller extends AppController{

    public function index() {
        $param1 = '';
        $param2 = '';
        $param3 = '1';
        $query_params = $this->getRequest()->getQueryParams();
        if(!array_key_exists('param3', $query_params)){
            $this->redirect([
                          'action' => 'index',
                          '?' => [
                            'param1' => $param1 ,
                            'param2' => $param2 ,
                            'param3' => '1'
                          ]
                        ]);
        }

    }

}

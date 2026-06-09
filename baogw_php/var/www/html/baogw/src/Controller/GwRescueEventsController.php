<?php
namespace App\Controller;

use App\Controller\AppController;
use Cake\Routing\Router;

class GwRescueEventsController extends AppController{

    const SESSION_KEY_ACCOUNT_ALIAS       = "account_alias";

    public function initialize(): void
    {
        parent::initialize();
        $this->loadComponent('Request');
    }

// ======================================================================================================================================================
    public function index() {

        //GETパラメータをControllerとView用の変数セットする
        $filter_val=[];
        $filter_val = $this->_get_filter_vals($filter_val);

        //クエリビルド
        $query_gwEvents = $this->GwRescueEvents->find();
        // $query_gwEvents = $this->GwRescueEvents->find()->contain(['GwIncidents']);
        // $query_gwEvents = $this->_set_filter_condtions($query_gwEvents, $filter_val);

        //ページネーション用インスタンス生成
        $this->_gen_pagenate_instance($query_gwEvents, $filter_val['display_count']);
    }

// ------------------------------------------------------------------------------------------------------------------------------------------------------
    function _get_filter_vals($fileter_vals) {

        $fileter_vals['display_count']          = $this->Request->setRequest('display_count',5);
        // $fileter_vals['sort']                   = $this->Request->setRequest('sort');
        // $fileter_vals['direction']              = $this->Request->setRequest('direction');

        return $fileter_vals;
    }


// ------------------------------------------------------------------------------------------------------------------------------------------------------
    function _gen_pagenate_instance($query_gwEvents, $display_count){

        $this->paginate=[
            'limit' => $display_count,
            'maxLimit' => 1000,
            'order' => ['alarm_time' =>'DESC']
        ];
        $gwEvents = $this->paginate($query_gwEvents);
        $this->set(compact('gwEvents'));
    }
}

<?php

namespace App\Controller\Component;

use Cake\Controller\Component;

class RequestComponent extends Component {

// ------------------------------------------------------------------------------------------------------------------------------------------------------
    //Controllerのインスタンスを取得
    function initialize(array $config): void {
    //    $this->Controller = $controller;
       $this->controler = $this->_registry->getController();
       return;
    }

// ------------------------------------------------------------------------------------------------------------------------------------------------------
    // function _set_get_parameter_and_view_variable($var_name, $default_value = null) {
    function setRequest($var_name, $default_value = null) {
        // $this->Controller = $controller;
        $variable ="";
        //getパラメータがあるか
        //$_GET[$var_name]

        $query_params = $this->controler->getRequest()->getQueryParams();
        if(array_key_exists($var_name, $query_params)){
            $variable = $query_params[$var_name];

            // var_dump($var_name);
            // var_dump($variable);

            // if (is_array($variable)) {
            // }

        } else {

            //デフォルト値の指定があれば、setする
            if ($default_value){
                $variable = $default_value;
            }
        }
        // return $this->Controller->set;
        // var_dump($var_name . ":".$variable);
        $this->controler->set($var_name, $variable);
        return $variable;

    }

}

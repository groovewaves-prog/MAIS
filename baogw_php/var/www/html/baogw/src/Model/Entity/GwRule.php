<?php
namespace App\Model\Entity;

use Cake\ORM\Entity;
use Cake\Core\Configure;
use Cake\Core\Configure\Engine\PhpConfig;

class GwRule extends Entity{

    protected $_accessible = [
        '*' => true,
        'ruleid' => false
    ];

    protected $_virtual = array('rule_set_disp', 'action_no_disp');
    protected function _getRuleSetDisp() {
        $RULE_SET_NAME=[];
        $RULE_SET_NAME    = Configure::read("RULE_SET_NAME");
        if (array_key_exists($this->rule_set, $RULE_SET_NAME)){
            $rule_set_disp = $RULE_SET_NAME[$this->rule_set];
        }else{
            $rule_set_disp = h($this->rule_set) . ':' . __('不明なルール');
        }
        return $rule_set_disp;
    }

    protected function _getActionNoDisp() {

      $ACTION_NO_NAME=[];
      $ACTION_NO_NAME    = Configure::read("ACTION_NO_NAME");

      if (array_key_exists($this->action_no, $ACTION_NO_NAME)){
          $action_no_disp = $ACTION_NO_NAME[$this->action_no];
      }else{
          // $action_no = h($action_no) . ':' . __('不明なアクションNo');
          $action_no_disp = h($this->action_no) . ':' . __('編集禁止');
      }

      return $action_no_disp;
    }
}

<?php
declare(strict_types=1);

/**
 * CakePHP(tm) : Rapid Development Framework (https://cakephp.org)
 * Copyright (c) Cake Software Foundation, Inc. (https://cakefoundation.org)
 *
 * Licensed under The MIT License
 * For full copyright and license information, please see the LICENSE.txt
 * Redistributions of files must retain the above copyright notice.
 *
 * @copyright Copyright (c) Cake Software Foundation, Inc. (https://cakefoundation.org)
 * @link      https://cakephp.org CakePHP(tm) Project
 * @since     0.2.9
 * @license   https://opensource.org/licenses/mit-license.php MIT License
 */
namespace App\Controller;

use Cake\Controller\Controller;
use Cake\Event\Event;
use Cake\Core\Configure;
use Cake\Core\Configure\Engine\PhpConfig;
use Cake\Http\Cookie\Cookie;

/**
 * Application Controller
 *
 * Add your application-wide methods in the class below, your controllers
 * will inherit them.
 *
 * @link https://book.cakephp.org/4/en/controllers.html#the-app-controller
 */
class AppController extends Controller
{

// ======================================================================================================================================================
    public function beforeFilter(\Cake\Event\EventInterface $event){

      parent::beforeFilter($event);
      //  $this->Security->requireSecure();
      // $token = $this->request->getParam('_csrfToken');
    //   $this->Security->blackHoleCallback = "securityError";
    //   var_dump($token);
      $this->loadComponent('Flash');
    //   $this->_check_authenticate($event);

      $this->loadComponent('ZbxAuth');
      $this->ZbxAuth->_check_authenticate($event);

      $CURRENT_PRIMARY_FILE = Configure::read("CURRENT_PRIMARY_FILE");
      if (file_exists($CURRENT_PRIMARY_FILE)) {
        $this->set('MASTER_SLAVE','Master');
      } else {
        $this->set('MASTER_SLAVE','Slave');
      }
    }
    // function securityError() {
    //  $this->redirect('https://' . env('SERVER_NAME') . $this->here);
    // }
// ======================================================================================================================================================

    /**
     * Initialization hook method.
     *
     * Use this method to add common initialization code like loading components.
     *
     * e.g. `$this->loadComponent('FormProtection');`
     *
     * @return void
     */
    public function initialize(): void
    {
        parent::initialize();

        $this->loadComponent('RequestHandler');

      $this->loadComponent('ZbxAuth');
      $this->loadComponent('Security');

      $FLAG_NEW_DAY      = Configure::read("FLAG_NEW_DAY");
      $FLAG_NEW_HOUR     = Configure::read("FLAG_NEW_HOUR");
      $CURRENT_HOSTNAME  = Configure::read("CURRENT_HOSTNAME");
      $CURRENT_SERVER_IP = Configure::read("CURRENT_SERVER_IP");
      // Configure::write('Session',['timeoute'=>10]);
      $FLAG_PRIMARY      = Configure::read("FLAG_PRIMARY");
      // $session           = Configure::read("Session");
      // var_dump($session);
      // $SESSION_LIFETIME  = Configure::read("SESSION_LIFETIME");

      $this->set(compact('CURRENT_HOSTNAME'));
      $this->set(compact('CURRENT_SERVER_IP'));
      $this->set(compact('FLAG_PRIMARY'));
      $this->set(compact('FLAG_NEW_DAY'));
      $this->set(compact('FLAG_NEW_HOUR'));
    //   $this->set(compact('SESSION_LIFETIME'));

    //   $this->loadComponent('Security');
    //   $this->loadComponent('Csrf');
    }

// ======================================================================================================================================================
    public function _write_cookie($name, $value)  {
        $cookie = (new Cookie($name))
            ->withValue($value)
            ->withPath('/baogw/')
            ->withHttpOnly(true);
        $this->response = $this->response->withCookie($cookie); 
        return;
    }

// ======================================================================================================================================================
    public function _read_cookie($name) {
        $cookie = $this->getRequest()->getCookie($name);
        return $cookie;
    }

    public function _del_cookie($name) {
      $this->response = $this->response->withExpiredCookie(new Cookie($name)); 
      return null;
    }
}

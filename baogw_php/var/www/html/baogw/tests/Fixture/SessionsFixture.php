<?php
declare(strict_types=1);

namespace App\Test\Fixture;

use Cake\TestSuite\Fixture\TestFixture;

/**
 * SessionsFixture
 */
class SessionsFixture extends TestFixture
{
    /**
     * Init method
     *
     * @return void
     */
    public function init(): void
    {
        $this->records = [
            [
                'sessionid' => '9995258f-9939-4604-a63e-6fc9a4b77ce7',
                'userid' => 1,
                'lastaccess' => 1,
                'status' => 1,
            ],
        ];
        parent::init();
    }
}

<?php
declare(strict_types=1);

namespace App\Test\Fixture;

use Cake\TestSuite\Fixture\TestFixture;

/**
 * HstgrpFixture
 */
class HstgrpFixture extends TestFixture
{
    /**
     * Table name
     *
     * @var string
     */
    public $table = 'hstgrp';
    /**
     * Init method
     *
     * @return void
     */
    public function init(): void
    {
        $this->records = [
            [
                'groupid' => 1,
                'name' => 'Lorem ipsum dolor sit amet',
                'internal' => 1,
                'flags' => 1,
                'uuid' => 'Lorem ipsum dolor sit amet',
            ],
        ];
        parent::init();
    }
}

<?php
declare(strict_types=1);

namespace App\Test\TestCase\Model\Table;

use App\Model\Table\HstgrpTable;
use Cake\TestSuite\TestCase;

/**
 * App\Model\Table\HstgrpTable Test Case
 */
class HstgrpTableTest extends TestCase
{
    /**
     * Test subject
     *
     * @var \App\Model\Table\HstgrpTable
     */
    protected $Hstgrp;

    /**
     * Fixtures
     *
     * @var array<string>
     */
    protected $fixtures = [
        'app.Hstgrp',
    ];

    /**
     * setUp method
     *
     * @return void
     */
    protected function setUp(): void
    {
        parent::setUp();
        $config = $this->getTableLocator()->exists('Hstgrp') ? [] : ['className' => HstgrpTable::class];
        $this->Hstgrp = $this->getTableLocator()->get('Hstgrp', $config);
    }

    /**
     * tearDown method
     *
     * @return void
     */
    protected function tearDown(): void
    {
        unset($this->Hstgrp);

        parent::tearDown();
    }

    /**
     * Test validationDefault method
     *
     * @return void
     * @uses \App\Model\Table\HstgrpTable::validationDefault()
     */
    public function testValidationDefault(): void
    {
        $this->markTestIncomplete('Not implemented yet.');
    }

    /**
     * Test defaultConnectionName method
     *
     * @return void
     * @uses \App\Model\Table\HstgrpTable::defaultConnectionName()
     */
    public function testDefaultConnectionName(): void
    {
        $this->markTestIncomplete('Not implemented yet.');
    }
}

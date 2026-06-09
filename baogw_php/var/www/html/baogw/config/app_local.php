<?php
/*
 * Local configuration file to provide any overrides to your app.php configuration.
 * Copy and save this file as app_local.php and make changes as required.
 * Note: It is not recommended to commit files with credentials such as app_local.php
 * into source code version control.
 */
return [
    /*
     * Debug Level:
     *
     * Production Mode:
     * false: No error messages, errors, or warnings shown.
     *
     * Development Mode:
     * true: Errors and warnings shown.
     */
//    'debug' => filter_var(env('DEBUG', true), FILTER_VALIDATE_BOOLEAN),
    'debug' => true,

    /*
     * Security and encryption configuration
     *
     * - salt - A random string used in security hashing methods.
     *   The salt value is also used as the encryption key.
     *   You should treat it as extremely sensitive data.
     */
    'Security' => [
        'salt' => env('SECURITY_SALT', '82a33e125bb81b64b7bbcf4d9821f88195bacd40fb7fd87952f938e57d3ac1e1'),
    ],

    /*
     * Connection information used by the ORM to connect
     * to your application's datastores.
     *
     * See app.php for more configuration options.
     */
    'Datasources' => [
        'default' => [
            'className' => 'Cake\Database\Connection',
            'driver' => 'Cake\Database\Driver\Mysql',
            'persistent' => false,
            //'host' => 'localhost',
			'host' => '127.0.0.1',
            /*
             * CakePHP will use the default DB port based on the driver selected
             * MySQL on MAMP uses port 8889, MAMP users will want to uncomment
             * the following line and set the port accordingly
             */
            //'port' => 'non_standard_port_number',

            'username' => 'gwuser',
            'password' => '2017B@0gw',
            'database' => 'baogw',
            'encoding' => 'utf8',
            //'timezone' => 'Asia/Tokyo',
            'timezone' => '+09:00',
            'flags' => [],
            'cacheMetadata' => true,
            'log' => false,

            'quoteIdentifiers' => false,

            /*
             * If not using the default 'public' schema with the PostgreSQL driver
             * set it here.
             */
            //'schema' => 'myapp',

            /*
             * You can use a DSN string to set the entire configuration
             */
            'url' => env('DATABASE_URL', null),
        ],

        'zabbix' => [
            'className' => 'Cake\Database\Connection',
            'driver' => 'Cake\Database\Driver\Mysql',
            'persistent' => false,
            //'host' => '127.0.0.1',
            'host' => 'localhost',
            'username' => "zabbix",
            'password' => 'baogw@zabbix',
            'database' => 'zabbix',
            'encoding' => 'utf8',
            //'timezone' => 'Asia/Tokyo',
            'timezone' => '+09:00',
            'flags' => [],
            'cacheMetadata' => true,
            'log' => false,
            'quoteIdentifiers' => false,
            'url' => env('DATABASE_URL', null),
        ],

        /*
         * The test connection is used during the test suite.
         */
        'test' => [
            'className' => 'Cake\Database\Connection',
            'driver' => 'Cake\Database\Driver\Mysql',
            'persistent' => false,
            'host' => 'localhost',
            //'port' => 'non_standard_port_number',
            'username' => 'baogw',
            'password' => 'baogw',
            'database' => 'baogw',
            'encoding' => 'utf8',
            'timezone' => 'Asia/Tokyo',
            'cacheMetadata' => true,
            'quoteIdentifiers' => false,
            'log' => false,
            //'schema' => 'myapp',
            //'url' => env('DATABASE_TEST_URL', 'sqlite://127.0.0.1/tests.sqlite'),
            'url' => env('DATABASE_TEST_URL', null),
        ],
    ],

    /*
     * Email configuration.
     *
     * Host and credential configuration in case you are using SmtpTransport
     *
     * See app.php for more configuration options.
     */
    'EmailTransport' => [
        'default' => [
            'host' => 'localhost',
            'port' => 25,
            'username' => null,
            'password' => null,
            'client' => null,
            'url' => env('EMAIL_TRANSPORT_DEFAULT_URL', null),
        ],
    ],
];

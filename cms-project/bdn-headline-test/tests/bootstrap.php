<?php
$wp_tests_dir = getenv( 'WP_TESTS_DIR' )
	?: dirname( __DIR__ ) . '/vendor/wp-phpunit/wp-phpunit';
require_once $wp_tests_dir . '/includes/functions.php';

tests_add_filter( 'muplugins_loaded', function (): void {
	require dirname( __DIR__ ) . '/bdn-headline-test.php';
} );

require_once $wp_tests_dir . '/includes/bootstrap.php';

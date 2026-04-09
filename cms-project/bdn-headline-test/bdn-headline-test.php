<?php
/**
 * Plugin Name: BDN Headline A/B Test
 * Description: A/B/Y headline testing with GA4 tracking and auto-resolution.
 * Version: 1.0.0
 * Author: Dan MacLeod with Claude Code
 * Requires at least: 6.4
 * Requires PHP: 8.1
 * Text Domain: bdn-headline-test
 */

defined( 'ABSPATH' ) || exit;

define( 'BDN_HT_DIR', plugin_dir_path( __FILE__ ) );
define( 'BDN_HT_URL', plugin_dir_url( __FILE__ ) );

spl_autoload_register( function ( string $class ): void {
	$prefix = 'BDN_Headline_Test\\';
	if ( ! str_starts_with( $class, $prefix ) ) {
		return;
	}
	$relative = str_replace( '\\', '/', substr( $class, strlen( $prefix ) ) );
	$file = BDN_HT_DIR . 'includes/class-' . strtolower( str_replace( '_', '-', $relative ) ) . '.php';
	if ( file_exists( $file ) ) {
		require_once $file;
	}
} );

add_action( 'plugins_loaded', function (): void {
	$settings = new BDN_Headline_Test\Settings();
	$settings->register();

	( new BDN_Headline_Test\Post_Meta() )->register();
	( new BDN_Headline_Test\Title_Filter() )->register();
	( new BDN_Headline_Test\Frontend_Assets() )->register();
	( new BDN_Headline_Test\Cron_Resolver( $settings ) )->register();
	( new BDN_Headline_Test\Admin_Page() )->register();
} );

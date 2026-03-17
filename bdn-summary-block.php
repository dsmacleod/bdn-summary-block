<?php
/**
 * Plugin Name: BDN Story Summary Block
 * Description: Adds a Gutenberg block that generates AI-powered story summaries via Nota.
 * Version: 1.0.0
 * Author: Dan MacLeod with Claude Code
 * Requires at least: 6.4
 * Requires PHP: 8.1
 * Text Domain: bdn-summary-block
 */

defined( 'ABSPATH' ) || exit;

define( 'BDN_SUMMARY_DIR', plugin_dir_path( __FILE__ ) );
define( 'BDN_SUMMARY_URL', plugin_dir_url( __FILE__ ) );

spl_autoload_register( function ( string $class ): void {
    $prefix = 'BDN_Summary\\';
    if ( ! str_starts_with( $class, $prefix ) ) {
        return;
    }
    $relative = str_replace( '\\', '/', substr( $class, strlen( $prefix ) ) );
    $file = BDN_SUMMARY_DIR . 'includes/class-' . strtolower( str_replace( '_', '-', $relative ) ) . '.php';
    if ( file_exists( $file ) ) {
        require_once $file;
    }
} );

add_action( 'plugins_loaded', function (): void {
    $settings = new BDN_Summary\Summary_Settings();
    $settings->register();
    ( new BDN_Summary\Summary_Ajax( $settings ) )->register();
} );

add_action( 'init', function (): void {
    register_block_type( BDN_SUMMARY_DIR . 'build' );
} );

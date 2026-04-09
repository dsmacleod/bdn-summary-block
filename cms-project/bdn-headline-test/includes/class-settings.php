<?php

namespace BDN_Headline_Test;

class Settings {

	private const DEFAULTS = [
		'min_impressions'      => 1000,
		'max_duration_hours'   => 72,
		'ga4_property_id'      => '',
		'ga4_credentials_json' => '',
	];

	public function register(): void {
		add_action( 'admin_menu', [ $this, 'add_menu' ] );
		add_action( 'admin_init', [ $this, 'register_settings' ] );
	}

	public function get( string $key ): mixed {
		$default = self::DEFAULTS[ $key ] ?? '';
		$value   = get_option( "bdn_ht_{$key}", $default );
		if ( is_int( $default ) ) {
			return (int) $value;
		}
		return $value;
	}

	public function add_menu(): void {
		add_submenu_page(
			'tools.php',
			'Headline A/B Tests',
			'Headline Tests',
			'manage_options',
			'bdn-headline-test',
			[ $this, 'render_page' ],
		);
	}

	public function register_settings(): void {
		foreach ( array_keys( self::DEFAULTS ) as $key ) {
			register_setting( 'bdn_headline_test', "bdn_ht_{$key}" );
		}
	}

	public function render_page(): void {
		echo '<div class="wrap"><h1>Headline A/B Tests</h1></div>';
	}
}

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

	public function register_settings(): void {
		foreach ( array_keys( self::DEFAULTS ) as $key ) {
			register_setting( 'bdn_headline_test', "bdn_ht_{$key}" );
		}
	}

}

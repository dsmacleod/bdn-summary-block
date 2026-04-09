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
		add_action( 'admin_menu', [ $this, 'add_settings_page' ] );
	}

	public function add_settings_page(): void {
		add_submenu_page(
			'tools.php',
			'Headline Test Settings',
			'Headline Test Settings',
			'manage_options',
			'bdn-headline-test-settings',
			[ $this, 'render_settings_page' ]
		);
	}

	public function render_settings_page(): void {
		if ( ! current_user_can( 'manage_options' ) ) {
			return;
		}
		?>
		<div class="wrap">
			<h1><?php echo esc_html( get_admin_page_title() ); ?></h1>
			<form method="post" action="options.php">
				<?php
				settings_fields( 'bdn_headline_test' );
				do_settings_sections( 'bdn-headline-test-settings' );
				submit_button();
				?>
			</form>
		</div>
		<?php
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

		add_settings_section(
			'bdn_ht_ga4',
			'Google Analytics 4',
			null,
			'bdn-headline-test-settings'
		);

		add_settings_field(
			'bdn_ht_ga4_property_id',
			'GA4 Property ID',
			[ $this, 'render_text_field' ],
			'bdn-headline-test-settings',
			'bdn_ht_ga4',
			[ 'key' => 'ga4_property_id', 'placeholder' => '123456789' ]
		);

		add_settings_field(
			'bdn_ht_ga4_credentials_json',
			'GA4 Service Account JSON',
			[ $this, 'render_textarea_field' ],
			'bdn-headline-test-settings',
			'bdn_ht_ga4',
			[ 'key' => 'ga4_credentials_json' ]
		);

		add_settings_section(
			'bdn_ht_thresholds',
			'Test Thresholds',
			null,
			'bdn-headline-test-settings'
		);

		add_settings_field(
			'bdn_ht_min_impressions',
			'Minimum Impressions per Variant',
			[ $this, 'render_number_field' ],
			'bdn-headline-test-settings',
			'bdn_ht_thresholds',
			[ 'key' => 'min_impressions' ]
		);

		add_settings_field(
			'bdn_ht_max_duration_hours',
			'Maximum Test Duration (hours)',
			[ $this, 'render_number_field' ],
			'bdn-headline-test-settings',
			'bdn_ht_thresholds',
			[ 'key' => 'max_duration_hours' ]
		);
	}

	public function render_text_field( array $args ): void {
		$key   = $args['key'];
		$value = $this->get( $key );
		printf(
			'<input type="text" name="bdn_ht_%s" value="%s" class="regular-text" placeholder="%s" />',
			esc_attr( $key ),
			esc_attr( $value ),
			esc_attr( $args['placeholder'] ?? '' )
		);
	}

	public function render_textarea_field( array $args ): void {
		$key   = $args['key'];
		$value = $this->get( $key );
		printf(
			'<textarea name="bdn_ht_%s" rows="10" class="large-text code">%s</textarea>',
			esc_attr( $key ),
			esc_textarea( $value )
		);
	}

	public function render_number_field( array $args ): void {
		$key   = $args['key'];
		$value = $this->get( $key );
		printf(
			'<input type="number" name="bdn_ht_%s" value="%s" class="small-text" min="1" />',
			esc_attr( $key ),
			esc_attr( $value )
		);
	}

}

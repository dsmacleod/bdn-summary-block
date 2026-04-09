<?php

class Test_Settings extends WP_UnitTestCase {

	public function test_defaults(): void {
		$settings = new BDN_Headline_Test\Settings();
		$this->assertSame( 1000, $settings->get( 'min_impressions' ) );
		$this->assertSame( 72, $settings->get( 'max_duration_hours' ) );
		$this->assertSame( '', $settings->get( 'ga4_property_id' ) );
		$this->assertSame( '', $settings->get( 'ga4_credentials_json' ) );
	}

	public function test_get_returns_saved_value(): void {
		update_option( 'bdn_ht_min_impressions', 500 );
		$settings = new BDN_Headline_Test\Settings();
		$this->assertSame( 500, $settings->get( 'min_impressions' ) );
	}
}

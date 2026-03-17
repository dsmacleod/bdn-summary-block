<?php
use BDN_Summary\Summary_Settings;

class Test_Summary_Settings extends WP_UnitTestCase {

    public function tear_down(): void {
        delete_option( Summary_Settings::OPTION_AI_POLICY_URL );
        parent::tear_down();
    }

    public function test_returns_empty_string_when_url_not_set(): void {
        $settings = new Summary_Settings();
        $this->assertSame( '', $settings->get_ai_policy_url() );
    }

    public function test_returns_stored_url(): void {
        update_option( Summary_Settings::OPTION_AI_POLICY_URL, 'https://bangordailynews.com/ai-policy/' );
        $settings = new Summary_Settings();
        $this->assertSame( 'https://bangordailynews.com/ai-policy/', $settings->get_ai_policy_url() );
    }
}

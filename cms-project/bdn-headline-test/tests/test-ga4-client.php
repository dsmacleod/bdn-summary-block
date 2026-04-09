<?php

class Test_GA4_Client extends WP_UnitTestCase {

    public function test_parse_report_rows(): void {
        $rows = [
            [ 'post_id' => '123', 'variant_id' => 'a', 'event_name' => 'headline_test_impression', 'count' => 500 ],
            [ 'post_id' => '123', 'variant_id' => 'a', 'event_name' => 'headline_test_click', 'count' => 50 ],
            [ 'post_id' => '123', 'variant_id' => 'b', 'event_name' => 'headline_test_impression', 'count' => 480 ],
            [ 'post_id' => '123', 'variant_id' => 'b', 'event_name' => 'headline_test_click', 'count' => 72 ],
        ];

        $client = new BDN_Headline_Test\GA4_Client( '', '' );
        $stats  = $client->parse_rows( $rows );

        $this->assertSame( 500, $stats[123]['a']['impressions'] );
        $this->assertSame( 50, $stats[123]['a']['clicks'] );
        $this->assertSame( 480, $stats[123]['b']['impressions'] );
        $this->assertSame( 72, $stats[123]['b']['clicks'] );
    }

    public function test_chi_squared_significant(): void {
        $client = new BDN_Headline_Test\GA4_Client( '', '' );
        $result = $client->is_significant(
            [ 'impressions' => 1000, 'clicks' => 100 ],
            [ 'impressions' => 1000, 'clicks' => 150 ]
        );
        $this->assertTrue( $result );
    }

    public function test_chi_squared_not_significant(): void {
        $client = new BDN_Headline_Test\GA4_Client( '', '' );
        $result = $client->is_significant(
            [ 'impressions' => 1000, 'clicks' => 100 ],
            [ 'impressions' => 1000, 'clicks' => 102 ]
        );
        $this->assertFalse( $result );
    }
}

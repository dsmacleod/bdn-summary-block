<?php

class Test_Cron_Resolver extends WP_UnitTestCase {

	public function test_declares_winner_and_updates_title(): void {
		$post_id = self::factory()->post->create( [ 'post_title' => 'Original' ] );
		$variants = wp_json_encode( [
			[ 'id' => 'a', 'text' => 'Original' ],
			[ 'id' => 'b', 'text' => 'Better Headline' ],
		] );
		update_post_meta( $post_id, '_headline_variants', $variants );
		update_post_meta( $post_id, '_headline_test_status', 'active' );

		$resolver = new BDN_Headline_Test\Cron_Resolver(
			new BDN_Headline_Test\Settings()
		);

		$stats = [
			'a' => [ 'impressions' => 1000, 'clicks' => 50 ],
			'b' => [ 'impressions' => 1000, 'clicks' => 100 ],
		];

		$resolver->evaluate_test( $post_id, $stats );

		$this->assertSame( 'completed', get_post_meta( $post_id, '_headline_test_status', true ) );
		$this->assertSame( 'b', get_post_meta( $post_id, '_headline_test_winner', true ) );
		$this->assertSame( 'Better Headline', get_the_title( $post_id ) );
	}

	public function test_does_not_resolve_below_min_impressions(): void {
		$post_id = self::factory()->post->create( [ 'post_title' => 'Original' ] );
		$variants = wp_json_encode( [
			[ 'id' => 'a', 'text' => 'Original' ],
			[ 'id' => 'b', 'text' => 'Alt' ],
		] );
		update_post_meta( $post_id, '_headline_variants', $variants );
		update_post_meta( $post_id, '_headline_test_status', 'active' );

		$resolver = new BDN_Headline_Test\Cron_Resolver(
			new BDN_Headline_Test\Settings()
		);

		$stats = [
			'a' => [ 'impressions' => 50, 'clicks' => 5 ],
			'b' => [ 'impressions' => 50, 'clicks' => 10 ],
		];

		$resolver->evaluate_test( $post_id, $stats );

		$this->assertSame( 'active', get_post_meta( $post_id, '_headline_test_status', true ) );
	}
}

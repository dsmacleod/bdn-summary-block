<?php

namespace BDN_Headline_Test;

class Cron_Resolver {

	private Settings $settings;

	public function __construct( Settings $settings ) {
		$this->settings = $settings;
	}

	public function register(): void {
		add_action( 'bdn_ht_resolve_tests', [ $this, 'run' ] );

		if ( ! wp_next_scheduled( 'bdn_ht_resolve_tests' ) ) {
			wp_schedule_event( time(), 'hourly', 'bdn_ht_resolve_tests' );
		}
	}

	public function run(): void {
		$ga4 = new GA4_Client(
			$this->settings->get( 'ga4_property_id' ),
			$this->settings->get( 'ga4_credentials_json' )
		);

		$active_posts = get_posts( [
			'post_type'      => 'post',
			'posts_per_page' => -1,
			'meta_key'       => '_headline_test_status',
			'meta_value'     => 'active',
			'fields'         => 'ids',
		] );

		if ( empty( $active_posts ) ) {
			return;
		}

		$all_stats = $ga4->fetch_stats( $active_posts );
		if ( is_wp_error( $all_stats ) ) {
			return;
		}

		foreach ( $active_posts as $post_id ) {
			if ( isset( $all_stats[ $post_id ] ) ) {
				$this->evaluate_test( $post_id, $all_stats[ $post_id ] );
			}
		}
	}

	public function evaluate_test( int $post_id, array $stats ): void {
		$min_impressions = $this->settings->get( 'min_impressions' );

		foreach ( $stats as $variant_stats ) {
			if ( $variant_stats['impressions'] < $min_impressions ) {
				return;
			}
		}

		$variant_ids = array_keys( $stats );
		$ga4_client  = new GA4_Client( '', '' );

		$best_id  = $variant_ids[0];
		$best_ctr = $stats[ $best_id ]['clicks'] / max( 1, $stats[ $best_id ]['impressions'] );

		foreach ( $variant_ids as $vid ) {
			$ctr = $stats[ $vid ]['clicks'] / max( 1, $stats[ $vid ]['impressions'] );
			if ( $ctr > $best_ctr ) {
				$best_id  = $vid;
				$best_ctr = $ctr;
			}
		}

		$significant = true;
		foreach ( $variant_ids as $vid ) {
			if ( $vid === $best_id ) {
				continue;
			}
			if ( ! $ga4_client->is_significant( $stats[ $best_id ], $stats[ $vid ] ) ) {
				$significant = false;
				break;
			}
		}

		if ( ! $significant ) {
			return;
		}

		$this->declare_winner( $post_id, $best_id );
	}

	private function declare_winner( int $post_id, string $winner_id ): void {
		update_post_meta( $post_id, '_headline_test_status', 'completed' );
		update_post_meta( $post_id, '_headline_test_winner', $winner_id );

		$variants = json_decode(
			get_post_meta( $post_id, '_headline_variants', true ),
			true
		) ?: [];

		foreach ( $variants as $v ) {
			if ( $v['id'] === $winner_id ) {
				wp_update_post( [
					'ID'         => $post_id,
					'post_title' => $v['text'],
				] );
				break;
			}
		}
	}
}

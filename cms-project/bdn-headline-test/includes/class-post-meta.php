<?php

namespace BDN_Headline_Test;

class Post_Meta {

	public function register(): void {
		add_action( 'init', [ $this, 'register_meta' ] );
	}

	public function register_meta(): void {
		$meta_keys = [
			'_headline_variants'    => [
				'type'         => 'string',
				'description'  => 'JSON array of headline variants',
				'single'       => true,
				'show_in_rest' => true,
			],
			'_headline_test_status' => [
				'type'         => 'string',
				'description'  => 'Test status: active, completed, paused',
				'single'       => true,
				'show_in_rest' => true,
			],
			'_headline_test_winner' => [
				'type'         => 'string',
				'description'  => 'Winning variant ID',
				'single'       => true,
				'show_in_rest' => true,
			],
			'_headline_test_started' => [
				'type'         => 'string',
				'description'  => 'Timestamp when the test became active',
				'single'       => true,
				'show_in_rest' => true,
			],
		];

		foreach ( $meta_keys as $key => $args ) {
			register_post_meta( 'post', $key, array_merge( $args, [
				'auth_callback' => function () {
					return current_user_can( 'edit_posts' );
				},
			] ) );
		}
	}
}

<?php

class Test_Post_Meta extends WP_UnitTestCase {

	public function set_up(): void {
		parent::set_up();
		( new BDN_Headline_Test\Post_Meta() )->register();
	}

	public function test_variants_meta_registered(): void {
		$this->assertTrue(
			registered_meta_key_exists( 'post', '_headline_variants', 'post' )
		);
	}

	public function test_save_and_retrieve_variants(): void {
		$post_id  = self::factory()->post->create();
		$variants = [
			[ 'id' => 'a', 'text' => 'Original' ],
			[ 'id' => 'b', 'text' => 'Alternative' ],
		];
		update_post_meta( $post_id, '_headline_variants', wp_json_encode( $variants ) );
		$stored = json_decode( get_post_meta( $post_id, '_headline_variants', true ), true );
		$this->assertSame( 'Alternative', $stored[1]['text'] );
	}

	public function test_status_defaults_empty(): void {
		$post_id = self::factory()->post->create();
		$this->assertSame( '', get_post_meta( $post_id, '_headline_test_status', true ) );
	}
}

<?php

class Test_Title_Filter extends WP_UnitTestCase {

	private int $post_id;

	public function set_up(): void {
		parent::set_up();
		( new BDN_Headline_Test\Post_Meta() )->register();
		do_action( 'init' );
		( new BDN_Headline_Test\Title_Filter() )->register();

		$this->post_id = self::factory()->post->create( [ 'post_title' => 'Original' ] );
	}

	public function test_no_attribute_without_active_test(): void {
		$title = apply_filters( 'the_title', 'Original', $this->post_id );
		$this->assertStringNotContainsString( 'data-headline-test', $title );
	}

	public function test_adds_attribute_with_active_test(): void {
		$variants = wp_json_encode( [
			[ 'id' => 'a', 'text' => 'Original' ],
			[ 'id' => 'b', 'text' => 'Alt Headline' ],
		] );
		update_post_meta( $this->post_id, '_headline_variants', $variants );
		update_post_meta( $this->post_id, '_headline_test_status', 'active' );

		$title = apply_filters( 'the_title', 'Original', $this->post_id );
		$this->assertStringContainsString( 'data-headline-test', $title );
		$this->assertStringContainsString( (string) $this->post_id, $title );
	}

	public function test_no_attribute_in_admin(): void {
		set_current_screen( 'edit-post' );
		$variants = wp_json_encode( [
			[ 'id' => 'a', 'text' => 'Original' ],
			[ 'id' => 'b', 'text' => 'Alt' ],
		] );
		update_post_meta( $this->post_id, '_headline_variants', $variants );
		update_post_meta( $this->post_id, '_headline_test_status', 'active' );

		$title = apply_filters( 'the_title', 'Original', $this->post_id );
		$this->assertStringNotContainsString( 'data-headline-test', $title );
		set_current_screen( 'front' );
	}
}

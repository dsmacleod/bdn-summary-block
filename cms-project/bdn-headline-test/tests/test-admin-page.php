<?php

class Test_Admin_Page extends WP_UnitTestCase {

	public function test_query_finds_active_tests(): void {
		$p1 = self::factory()->post->create();
		$p2 = self::factory()->post->create();

		update_post_meta( $p1, '_headline_test_status', 'active' );
		update_post_meta( $p2, '_headline_test_status', 'completed' );

		$page  = new BDN_Headline_Test\Admin_Page();
		$posts = $page->get_test_posts( 'active' );

		$this->assertCount( 1, $posts );
		$this->assertEquals( $p1, $posts[0]->ID );
	}

	public function test_query_finds_all_tests(): void {
		$p1 = self::factory()->post->create();
		$p2 = self::factory()->post->create();

		update_post_meta( $p1, '_headline_test_status', 'active' );
		update_post_meta( $p2, '_headline_test_status', 'completed' );

		$page  = new BDN_Headline_Test\Admin_Page();
		$posts = $page->get_test_posts();

		$this->assertCount( 2, $posts );
	}
}

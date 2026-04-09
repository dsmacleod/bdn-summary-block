<?php

class Test_Integration extends WP_UnitTestCase {

    public function set_up(): void {
        parent::set_up();
        ( new BDN_Headline_Test\Post_Meta() )->register();
        do_action( 'init' );
        ( new BDN_Headline_Test\Title_Filter() )->register();
    }

    public function test_full_lifecycle(): void {
        // 1. Create a post.
        $post_id = self::factory()->post->create( [ 'post_title' => 'Original Headline' ] );

        // 2. Set up a test with two variants.
        $variants = wp_json_encode( [
            [ 'id' => 'a', 'text' => 'Original Headline' ],
            [ 'id' => 'b', 'text' => 'Clickbait Headline' ],
        ] );
        update_post_meta( $post_id, '_headline_variants', $variants );
        update_post_meta( $post_id, '_headline_test_status', 'active' );

        // 3. Verify title filter injects data attributes.
        $title = apply_filters( 'the_title', 'Original Headline', $post_id );
        $this->assertStringContainsString( 'data-headline-test', $title );

        // 4. Simulate resolution — variant B wins.
        $resolver = new BDN_Headline_Test\Cron_Resolver( new BDN_Headline_Test\Settings() );
        $resolver->evaluate_test( $post_id, [
            'a' => [ 'impressions' => 2000, 'clicks' => 100 ],
            'b' => [ 'impressions' => 2000, 'clicks' => 200 ],
        ] );

        // 5. Verify winner declared and title updated.
        $this->assertSame( 'completed', get_post_meta( $post_id, '_headline_test_status', true ) );
        $this->assertSame( 'b', get_post_meta( $post_id, '_headline_test_winner', true ) );
        $this->assertSame( 'Clickbait Headline', get_the_title( $post_id ) );

        // 6. Verify title filter no longer injects attributes.
        $title = apply_filters( 'the_title', 'Clickbait Headline', $post_id );
        $this->assertStringNotContainsString( 'data-headline-test', $title );
    }
}

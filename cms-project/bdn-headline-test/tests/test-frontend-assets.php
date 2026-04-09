<?php

class Test_Frontend_Assets extends WP_UnitTestCase {

    public function test_script_not_enqueued_in_admin(): void {
        set_current_screen( 'edit-post' );
        ( new BDN_Headline_Test\Frontend_Assets() )->register();
        do_action( 'wp_enqueue_scripts' );
        $this->assertFalse( wp_script_is( 'bdn-headline-test-frontend', 'enqueued' ) );
        set_current_screen( 'front' );
    }
}
